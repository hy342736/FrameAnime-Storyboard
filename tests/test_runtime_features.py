import asyncio
import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.browser_session import BrowserSession, TextOnlyGenerationResponse
from app.config import Settings, load_settings
from app.mirror_adapter import MirrorImageAdapter, ReferenceUploadResult


def make_settings(root: Path) -> Settings:
    settings = Settings(
        data_dir=root / "data",
        mirror_url="https://example.test",
        mirror_chat_url="",
        headless=True,
        browser_profile_dir=root / "profile",
        image_dir=root / "generated",
        reference_dir=root / "references",
        generation_timeout_seconds=60,
        local_api_key="",
    )
    settings.image_dir.mkdir(parents=True)
    settings.reference_dir.mkdir(parents=True)
    return settings


class EmptyLocator:
    async def count(self):
        return 0


class EmptyPage:
    def locator(self, _selector):
        return EmptyLocator()


class ErrorBodyLocator:
    def __init__(self, text):
        self.text = text

    async def inner_text(self, timeout=None):
        return self.text


class ScopedLocator:
    def __init__(self, texts=None):
        self.texts = texts or []

    @property
    def last(self):
        return ErrorBodyLocator(self.texts[-1])

    async def count(self):
        return len(self.texts)


class StyledErrorBodyLocator(ErrorBodyLocator):
    def __init__(self, text, red):
        super().__init__(text)
        self.red = red

    async def is_visible(self):
        return True

    async def evaluate(self, _script):
        return self.red


class StyledScopedLocator(ScopedLocator):
    def __init__(self, text, red):
        super().__init__([text])
        self.text = text
        self.red = red

    @property
    def last(self):
        return StyledErrorBodyLocator(self.text, self.red)


class ImageListLocator:
    def __init__(self, page):
        self.page = page

    async def all(self):
        self.page.polls += 1
        return [ReadyImage()] if self.page.polls >= 2 else []


class ReadyImage:
    async def get_attribute(self, name):
        return "https://images.example.test/result.png" if name == "src" else None

    async def is_visible(self):
        return True

    async def bounding_box(self):
        return {"width": 1024, "height": 1024}


class NamedReadyImage(ReadyImage):
    def __init__(self, source, *, html_source=None, natural_size=(1024, 1024)):
        self.source = source
        self.html_source = html_source if html_source is not None else source
        self.natural_size = natural_size

    async def get_attribute(self, name):
        return self.html_source if name == "src" else None

    async def evaluate(self, _script):
        return {
            "identity": self.source,
            "natural_width": self.natural_size[0],
            "natural_height": self.natural_size[1],
        }


class AttachmentLikeImage(NamedReadyImage):
    async def evaluate(self, script):
        if "data-frame-generation-attachment" in script:
            return True
        return await super().evaluate(script)


class StaticImageListLocator:
    def __init__(self, images):
        self.images = images

    async def all(self):
        return self.images


class MixedTextMultiImagePage:
    def __init__(self, images):
        self.images = images

    def locator(self, selector):
        if selector == "img":
            return StaticImageListLocator(self.images)
        return ScopedLocator(["generation explanation text"] if "assistant" in selector else [])

    async def wait_for_timeout(self, _milliseconds):
        return None


class AttachmentAndGeneratedPage(MixedTextMultiImagePage):
    pass


class AssistantResponse:
    def __init__(self, text, baseline=False):
        self.text = text
        self.baseline = baseline

    async def evaluate(self, _script):
        self.baseline = True

    async def get_attribute(self, name):
        if name == "data-frame-response-baseline" and self.baseline:
            return "true"
        return None

    async def is_visible(self):
        return True

    async def inner_text(self, timeout=None):
        return self.text


class AssistantResponseLocator:
    def __init__(self, page):
        self.page = page

    async def all(self):
        return self.page.responses


class TextOnlyResponsePage:
    def __init__(self, responses=None):
        self.responses = responses or []

    def locator(self, selector):
        if selector == "img":
            return StaticImageListLocator([])
        if selector == "main [data-message-author-role='assistant']":
            return AssistantResponseLocator(self)
        return ScopedLocator()

    async def wait_for_timeout(self, _milliseconds):
        return None


class TransientErrorPage:
    def __init__(self):
        self.polls = 0

    def locator(self, selector):
        if selector == "img":
            return ImageListLocator(self)
        if selector == "main [data-testid='generation-error']":
            return ScopedLocator(["解析网络错误"] if self.polls <= 1 else [])
        if selector == "main button[data-testid*='retry' i]":
            return ScopedLocator(["重试"] if self.polls <= 1 else [])
        return ScopedLocator()

    async def wait_for_timeout(self, _milliseconds):
        return None


class PersistentErrorPage:
    def locator(self, selector):
        if selector == "img":
            return ImageListLocatorWithoutResult()
        if selector == "main [data-testid='generation-error']":
            return ScopedLocator(["Something went wrong. Please try again."])
        if selector == "main button[data-testid*='retry' i]":
            return ScopedLocator(["Try again"])
        return ScopedLocator()

    async def wait_for_timeout(self, _milliseconds):
        return None


class ImageListLocatorWithoutResult:
    async def all(self):
        return []


class DelayedPromptEchoPage:
    def __init__(
        self,
        prompt_echo,
        image_poll=5,
        prompt_selector="main [data-message-author-role='assistant']",
        extra_selector_texts=None,
    ):
        self.prompt_echo = prompt_echo
        self.image_poll = image_poll
        self.prompt_selector = prompt_selector
        self.extra_selector_texts = extra_selector_texts or {}
        self.polls = 0

    def locator(self, selector):
        if selector == "img":
            return DelayedImageListLocator(self)
        if selector == self.prompt_selector:
            return ScopedLocator([self.prompt_echo])
        if selector in self.extra_selector_texts:
            return ScopedLocator(self.extra_selector_texts[selector])
        return ScopedLocator()

    async def wait_for_timeout(self, _milliseconds):
        return None


class DelayedImageListLocator:
    def __init__(self, page):
        self.page = page

    async def all(self):
        self.page.polls += 1
        return [ReadyImage()] if self.page.polls >= self.page.image_poll else []


class VisualErrorPage:
    def __init__(self, text, red, image_poll=None):
        self.text = text
        self.red = red
        self.image_poll = image_poll
        self.polls = 0

    def locator(self, selector):
        if selector == "img":
            if self.image_poll is None:
                return ImageListLocatorWithoutResult()
            return DelayedImageListLocator(self)
        if selector == "main [role='alert']":
            return StyledScopedLocator(self.text, self.red)
        return ScopedLocator()

    async def wait_for_timeout(self, _milliseconds):
        return None


class LoginPage:
    def locator(self, _selector):
        return EmptyLocatorWithCount(1)

    def get_by_role(self, _role, name=None):
        return EmptyLocatorWithCount(1 if name == "登录" else 0)


class PartialUploadPage:
    url = "https://example.test"

    def __init__(self):
        self.reloaded = False

    async def wait_for_timeout(self, _milliseconds):
        return None

    async def reload(self, wait_until=None):
        self.reloaded = wait_until == "domcontentloaded"


class PartialUploadAdapter:
    def __init__(self, _page):
        pass

    async def attach(self, paths):
        return ReferenceUploadResult(len(paths), 1, True)


class EmptyLocatorWithCount:
    def __init__(self, count):
        self._count = count

    async def count(self):
        return self._count


class ConversationPage:
    def __init__(self, url="https://example.test/"):
        self.url = url
        self.visited = []

    async def goto(self, url, wait_until=None):
        self.url = url
        self.visited.append((url, wait_until))


class FakeConversationAdapter:
    started = False

    def __init__(self, page):
        self.page = page

    async def start_new(self, fallback_url):
        type(self).started = True
        self.page.url = fallback_url


class RuntimeFeatureTests(unittest.TestCase):
    def test_generate_retries_text_only_response_once_in_same_conversation(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-text-retry-") as directory:
            root = Path(directory)
            session = BrowserSession(make_settings(root))
            page = TextOnlyResponsePage()
            page.url = "https://example.test/c/project-chat"
            submissions = []
            waits = 0
            output = root / "generated" / "project-test" / "generated" / "result.png"
            output.parent.mkdir(parents=True)
            output.write_bytes(b"result")

            async def get_page():
                return page

            async def no_op(*_args, **_kwargs):
                return None

            async def image_sources(_page):
                return set()

            async def submit_prompt(_page, prompt):
                submissions.append(prompt)

            async def wait_for_new_image(*_args, **_kwargs):
                nonlocal waits
                waits += 1
                if waits == 1:
                    raise TextOnlyGenerationResponse("text only")
                return object()

            async def save_image(*_args, **_kwargs):
                return output

            session._get_page = get_page
            session._prepare_project_conversation = no_op
            session._image_sources = image_sources
            session._mark_assistant_response_baseline = no_op
            session._page_visual_error_message = AsyncMock(return_value="")
            session._submit_prompt = submit_prompt
            session._wait_for_new_image = wait_for_new_image
            session._save_image = save_image

            result = asyncio.run(session.generate("draw", "project-test", conversation_url=page.url))

            self.assertEqual(output, result.path)
            self.assertEqual(2, waits)
            self.assertEqual("draw", submissions[0])
            self.assertIn("直接调用图片生成工具", submissions[1])

    def test_generate_stops_after_second_text_only_response(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-text-retry-stop-") as directory:
            root = Path(directory)
            session = BrowserSession(make_settings(root))
            page = TextOnlyResponsePage()
            page.url = "https://example.test/c/project-chat"
            submissions = []

            async def get_page():
                return page

            async def no_op(*_args, **_kwargs):
                return None

            async def submit_prompt(_page, prompt):
                submissions.append(prompt)

            session._get_page = get_page
            session._prepare_project_conversation = no_op
            session._image_sources = AsyncMock(return_value=set())
            session._mark_assistant_response_baseline = no_op
            session._page_visual_error_message = AsyncMock(return_value="")
            session._submit_prompt = submit_prompt
            session._wait_for_new_image = AsyncMock(
                side_effect=TextOnlyGenerationResponse("text only")
            )

            with self.assertRaisesRegex(RuntimeError, "连续两次只返回文字"):
                asyncio.run(session.generate("draw", "project-test", conversation_url=page.url))

            self.assertEqual(2, len(submissions))

    def test_completed_text_only_assistant_response_is_classified(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-text-only-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = TextOnlyResponsePage([AssistantResponse("这是可直接复制的绘图提示词")])

            with self.assertRaises(TextOnlyGenerationResponse):
                asyncio.run(session._wait_for_new_image(page, set()))

    def test_existing_assistant_response_is_not_classified_as_current_result(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-old-response-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            session.settings.generation_timeout_seconds = 0.001
            page = TextOnlyResponsePage([AssistantResponse("上一轮只有文字")])
            asyncio.run(session._mark_assistant_response_baseline(page))

            with self.assertRaisesRegex(TimeoutError, "等待图片结果超时"):
                asyncio.run(session._wait_for_new_image(page, set()))

    def test_mixed_text_multi_image_response_selects_first_image(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-multi-output-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            first = NamedReadyImage("https://images.example.test/first.png")
            second = NamedReadyImage("https://images.example.test/second.png")
            page = MixedTextMultiImagePage([first, second])

            selected = asyncio.run(session._wait_for_new_image(page, set()))

            self.assertIs(first, selected)

    def test_reference_attachment_is_rejected_when_it_looks_new(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-reference-result-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            session.settings.generation_timeout_seconds = 0.001
            reference = AttachmentLikeImage("https://images.example.test/reference-thumb-new.png")
            generated = NamedReadyImage("https://images.example.test/generated.png")
            page = AttachmentAndGeneratedPage([reference, generated])

            selected = asyncio.run(
                session._wait_for_new_image(
                    page,
                    {"https://images.example.test/reference-original.png"},
                )
            )

            self.assertIs(generated, selected)

    def test_current_src_detects_lazy_loaded_image_despite_shared_placeholder_src(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-current-src-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            session.settings.generation_timeout_seconds = 0.001
            generated = NamedReadyImage(
                "https://images.example.test/generated.png",
                html_source="data:image/gif;base64,shared-placeholder",
                natural_size=(1024, 1365),
            )
            page = MixedTextMultiImagePage([generated])

            selected = asyncio.run(
                session._wait_for_new_image(
                    page,
                    {"data:image/gif;base64,shared-placeholder"},
                )
            )

            self.assertIs(generated, selected)

    def test_generation_wait_extends_soft_deadline_while_page_is_actively_generating(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-active-generation-") as directory:
            settings = make_settings(Path(directory))
            settings.generation_timeout_seconds = 2
            session = BrowserSession(settings)
            page = DelayedPromptEchoPage("", image_poll=5)

            class Clock:
                def __init__(self):
                    self.value = 0

                def time(self):
                    self.value += 1
                    return self.value

            clock = Clock()
            session._page_generation_active = AsyncMock(return_value=True)
            with patch("app.browser_session.asyncio.get_running_loop", return_value=clock):
                image = asyncio.run(session._wait_for_new_image(page, set()))

            self.assertIsInstance(image, ReadyImage)
            self.assertGreaterEqual(session._page_generation_active.await_count, 1)

    def test_generation_records_image_baseline_after_reference_upload(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-upload-baseline-") as directory:
            root = Path(directory)
            reference = root / "reference.png"
            reference.write_bytes(b"reference")
            session = BrowserSession(make_settings(root))
            page = PartialUploadPage()
            page.url = "https://example.test/c/project-chat"
            events = []
            captured_before = set()
            captured_initial_error = ""
            output = root / "generated" / "project-test" / "generated" / "result.png"
            output.parent.mkdir(parents=True)
            output.write_bytes(b"result")

            class CompleteUploadAdapter:
                def __init__(self, _page):
                    pass

                async def attach(self, paths):
                    events.append("attach")
                    return ReferenceUploadResult(len(paths), len(paths), True)

            async def image_sources(_page):
                events.append("baseline")
                return {"uploaded-reference"}

            async def visual_error(_page):
                events.append("error-baseline")
                return "old page error"

            async def wait_for_new_image(_page, before, *, initial_visual_error=""):
                nonlocal captured_before, captured_initial_error
                captured_before = before
                captured_initial_error = initial_visual_error
                return object()

            async def no_op(*_args, **_kwargs):
                return None

            async def save_image(*_args, **_kwargs):
                return output

            async def get_page():
                return page

            session._get_page = get_page
            session._prepare_project_conversation = no_op
            session._image_sources = image_sources
            session._page_visual_error_message = visual_error
            session._submit_prompt = no_op
            session._wait_for_new_image = wait_for_new_image
            session._save_image = save_image

            with patch("app.browser_session.MirrorImageAdapter", CompleteUploadAdapter):
                asyncio.run(session.generate("draw", "project-test", [reference], True, page.url))

            self.assertEqual(["attach", "baseline", "error-baseline"], events)
            self.assertEqual({"uploaded-reference"}, captured_before)
            self.assertEqual("old page error", captured_initial_error)

    def test_fresh_install_has_no_default_mirror_url(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-empty-mirror-") as directory:
            root = Path(directory)
            environment = {
                "DATA_DIR": str(root / "data"),
                "IMAGE_DIR": str(root / "generated"),
                "REFERENCE_DIR": str(root / "references"),
            }
            with patch.dict(os.environ, environment, clear=True):
                settings = load_settings()
            self.assertEqual("", settings.mirror_url)

    def test_empty_mirror_url_fails_before_browser_start(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-empty-mirror-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            session.settings.mirror_url = ""

            async def fail_if_browser_starts():
                raise AssertionError("browser should not start without a mirror URL")

            session._get_page = fail_if_browser_starts
            with self.assertRaisesRegex(RuntimeError, "请先在设置中填写镜像站网址"):
                asyncio.run(session.open_for_login())
            self.assertIsNone(session.playwright)

    def test_directory_status_reports_writable_paths(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-runtime-") as directory:
            settings = make_settings(Path(directory))
            result = settings.directory_status()
            self.assertTrue(result["valid"])
            self.assertTrue(result["directories"]["image_dir"]["writable"])
            self.assertTrue(result["directories"]["reference_dir"]["writable"])

    def test_browser_session_status_is_safe_before_start(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-session-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            self.assertEqual(
                {
                    "started": False,
                    "context_open": False,
                    "page_open": False,
                    "page_url": "",
                },
                session.status(),
            )

    def test_adapter_reports_missing_upload_capability(self):
        async def check():
            return await MirrorImageAdapter(EmptyPage()).attach([Path("missing.png")])

        result = asyncio.run(check())
        self.assertEqual(1, result.requested)
        self.assertEqual(0, result.attached)
        self.assertFalse(result.supported)

    def test_login_page_gets_a_clear_generation_error(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-login-") as directory:
            session = BrowserSession(make_settings(Path(directory)))

            async def submit():
                await session._submit_prompt(LoginPage(), "test")

            with self.assertRaisesRegex(RuntimeError, "处于登录页"):
                asyncio.run(submit())

    def test_transient_current_error_does_not_abort_before_image_appears(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-transient-error-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            image = asyncio.run(session._wait_for_new_image(TransientErrorPage(), set()))
            self.assertIsInstance(image, ReadyImage)

    def test_prompt_echo_does_not_abort_a_slow_successful_generation(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-slow-prompt-echo-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = DelayedPromptEchoPage("错误手部，可读文字，Logo，水印", image_poll=5)
            image = asyncio.run(session._wait_for_new_image(page, set()))
            self.assertIsInstance(image, ReadyImage)
            self.assertEqual(5, page.polls)

    def test_role_alert_prompt_echo_does_not_abort_a_slow_successful_generation(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-slow-role-alert-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = DelayedPromptEchoPage(
                "照片感，3D渲染，错误手部，可读文字，Logo，水印",
                image_poll=5,
                prompt_selector="main [role='alert']",
            )
            image = asyncio.run(session._wait_for_new_image(page, set()))
            self.assertIsInstance(image, ReadyImage)
            self.assertEqual(5, page.polls)

    def test_structured_error_and_retry_do_not_override_a_late_image(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-late-recovery-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = DelayedPromptEchoPage(
                "Something went wrong. Please try again.",
                image_poll=5,
                prompt_selector="main [data-testid='generation-error']",
                extra_selector_texts={
                    "main button[data-testid*='retry' i]": ["Try again"],
                },
            )
            image = asyncio.run(session._wait_for_new_image(page, set()))
            self.assertIsInstance(image, ReadyImage)
            self.assertEqual(5, page.polls)

    def test_visible_red_error_with_unknown_wording_stops_generation(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-red-error-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            session.settings.generation_timeout_seconds = 0.1
            page = VisualErrorPage("今日次数已用完，请更换可用节点", red=True)
            with self.assertRaisesRegex(RuntimeError, "今日次数已用完"):
                asyncio.run(session._wait_for_new_image(page, set()))

    def test_neutral_alert_with_same_wording_does_not_override_a_late_image(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-neutral-alert-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = VisualErrorPage("今日次数已用完，请更换可用节点", red=False, image_poll=5)
            image = asyncio.run(session._wait_for_new_image(page, set()))
            self.assertIsInstance(image, ReadyImage)
            self.assertEqual(5, page.polls)

    def test_late_image_wins_before_red_error_becomes_stable(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-red-error-recovery-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = VisualErrorPage("节点暂时不可用", red=True, image_poll=2)
            image = asyncio.run(session._wait_for_new_image(page, set()))
            self.assertIsInstance(image, ReadyImage)
            self.assertEqual(2, page.polls)

    def test_red_error_left_by_previous_request_does_not_pollute_new_success(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-stale-red-error-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = VisualErrorPage("上一轮连接已中断", red=True, image_poll=5)
            image = asyncio.run(
                session._wait_for_new_image(
                    page,
                    set(),
                    initial_visual_error="上一轮连接已中断",
                )
            )
            self.assertIsInstance(image, ReadyImage)
            self.assertEqual(5, page.polls)

    def test_image_wins_when_red_error_is_visible_in_the_same_poll(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-image-error-same-poll-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = VisualErrorPage("节点暂时不可用", red=True, image_poll=1)
            image = asyncio.run(session._wait_for_new_image(page, set()))
            self.assertIsInstance(image, ReadyImage)
            self.assertEqual(1, page.polls)

    def test_no_image_reaches_the_configured_timeout(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-persistent-error-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            session.settings.generation_timeout_seconds = 0.001
            with self.assertRaisesRegex(TimeoutError, "等待图片结果超时"):
                asyncio.run(session._wait_for_new_image(PersistentErrorPage(), set()))

    def test_bound_project_routes_to_its_exact_conversation_url(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-bound-conversation-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = ConversationPage("https://example.test/c/other-project")
            asyncio.run(
                session._prepare_project_conversation(
                    page,
                    "https://example.test/c/current-project",
                    force_new=False,
                )
            )
            self.assertEqual(
                [("https://example.test/c/current-project", "domcontentloaded")],
                page.visited,
            )

    def test_unbound_project_starts_a_new_conversation(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-new-conversation-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = ConversationPage("https://example.test/c/other-project")
            FakeConversationAdapter.started = False
            with patch("app.browser_session.MirrorConversationAdapter", FakeConversationAdapter):
                asyncio.run(session._prepare_project_conversation(page, "", force_new=True))
            self.assertTrue(FakeConversationAdapter.started)

    def test_only_same_mirror_origin_conversation_urls_are_accepted(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-conversation-origin-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            self.assertEqual(
                "https://example.test/c/project-chat",
                session._validated_conversation_url("https://example.test/c/project-chat"),
            )
            with self.assertRaisesRegex(ValueError, "镜像站"):
                session._validated_conversation_url("https://other.test/c/project-chat")

    def test_partial_multi_character_upload_stops_before_prompt_and_clears_draft(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-multi-character-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = PartialUploadPage()
            submitted = False

            async def get_page():
                return page

            async def image_sources(_page):
                return set()

            async def submit_prompt(_page, _prompt):
                nonlocal submitted
                submitted = True

            async def prepare_project_conversation(_page, _conversation_url, force_new):
                return None

            session._get_page = get_page
            session._image_sources = image_sources
            session._submit_prompt = submit_prompt
            session._prepare_project_conversation = prepare_project_conversation

            async def generate():
                with patch("app.browser_session.MirrorImageAdapter", PartialUploadAdapter):
                    await session.generate(
                        "two characters",
                        reference_paths=[Path("first.png"), Path("second.png")],
                        require_all_references=True,
                    )

            with self.assertRaisesRegex(RuntimeError, "1 / 2"):
                asyncio.run(generate())
            self.assertTrue(page.reloaded)
            self.assertFalse(submitted)

    def test_failure_after_conversation_creation_carries_conversation_url(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-generation-error-url-") as directory:
            session = BrowserSession(make_settings(Path(directory)))
            page = PartialUploadPage()
            page.url = "https://example.test/c/failed-generation-chat"

            async def get_page():
                return page

            async def prepare_project_conversation(_page, _conversation_url, force_new):
                return None

            async def image_sources(_page):
                return set()

            async def submit_prompt(_page, _prompt):
                return None

            async def wait_for_new_image(_page, _before, *, initial_visual_error=""):
                raise RuntimeError("provider failed after prompt submission")

            session._get_page = get_page
            session._prepare_project_conversation = prepare_project_conversation
            session._image_sources = image_sources
            session._submit_prompt = submit_prompt
            session._wait_for_new_image = wait_for_new_image

            with self.assertRaisesRegex(RuntimeError, "provider failed") as captured:
                asyncio.run(session.generate("draw", project_id="project-test"))

            self.assertEqual(
                "https://example.test/c/failed-generation-chat",
                captured.exception.conversation_url,
            )


if __name__ == "__main__":
    unittest.main()
