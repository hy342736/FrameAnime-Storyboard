import asyncio
import base64
from dataclasses import dataclass
import mimetypes
from pathlib import Path
import re
from typing import Any
from urllib.parse import unquote_to_bytes, urljoin, urlsplit, urlunsplit
from uuid import uuid4

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright
from playwright.async_api import Error as PlaywrightError

from .config import Settings
from .mirror_adapter import MirrorConversationAdapter, MirrorImageAdapter


class TextOnlyGenerationResponse(RuntimeError):
    """The provider completed a new assistant turn without producing an image."""


@dataclass
class GenerationResult:
    path: Path
    references_requested: int = 0
    references_attached: int = 0
    reference_warning: str = ""
    generation_warning: str = ""
    conversation_url: str = ""


class BrowserSession:
    """Owns one persistent browser context and serializes generations."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.start_lock = asyncio.Lock()
        self.generation_lock = asyncio.Lock()

    async def start(self) -> None:
        async with self.start_lock:
            if self.playwright is not None:
                return
            self.settings.browser_profile_dir.mkdir(parents=True, exist_ok=True)
            self.settings.image_dir.mkdir(parents=True, exist_ok=True)
            self.playwright = await async_playwright().start()
            try:
                await self._launch_context()
            except Exception:
                await self.playwright.stop()
                self.playwright = None
                raise

    async def stop(self) -> None:
        if self.context is not None:
            await self.context.close()
        if self.playwright is not None:
            await self.playwright.stop()
        self.context = None
        self.page = None
        self.playwright = None

    async def open_for_login(self) -> str:
        target_url = self._mirror_url()
        page = await self._get_page()
        try:
            await page.goto(target_url, wait_until="domcontentloaded")
        except PlaywrightError as exc:
            if "Target page, context or browser has been closed" not in str(exc):
                raise
            await self._launch_context()
            page = await self._get_page()
            await page.goto(target_url, wait_until="domcontentloaded")
        return page.url

    async def generate(
        self,
        prompt: str,
        project_id: str = "project-default",
        reference_paths: list[Path] | None = None,
        require_all_references: bool = False,
        conversation_url: str = "",
    ) -> GenerationResult:
        if not prompt.strip():
            raise ValueError("prompt 不能为空")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", project_id):
            raise ValueError("项目 ID 无效")
        reference_paths = reference_paths or []
        async with self.generation_lock:
            page = await self._get_page()
            await self._prepare_project_conversation(
                page,
                conversation_url,
                force_new=not conversation_url,
            )
            try:
                await page.wait_for_timeout(1000)

                upload_result = await MirrorImageAdapter(page).attach(reference_paths)
                attached = upload_result.attached
                if require_all_references and attached != len(reference_paths):
                    try:
                        await page.reload(wait_until="domcontentloaded")
                    except PlaywrightError:
                        pass
                    raise RuntimeError(
                        f"多角色镜头需要完整参考图映射；镜像站仅附加了 {attached} / {len(reference_paths)} 张，已停止生成并清空未发送草稿"
                    )
                # Upload thumbnails are page images too. Establish the baseline
                # only after attachments settle so they can never become output.
                before = await self._image_sources(page)
                await self._mark_assistant_response_baseline(page)
                initial_visual_error = await self._page_visual_error_message(page)
                await self._submit_prompt(page, prompt.strip())
                try:
                    image = await self._wait_for_new_image(
                        page,
                        before,
                        initial_visual_error=initial_visual_error,
                    )
                except TextOnlyGenerationResponse:
                    # Some chat frontends occasionally explain or rewrite the
                    # prompt instead of invoking their image tool. Correct this
                    # once in the same conversation, then stop to avoid loops.
                    before = await self._image_sources(page)
                    await self._mark_assistant_response_baseline(page)
                    retry_visual_error = await self._page_visual_error_message(page)
                    await self._submit_prompt(
                        page,
                        "请直接调用图片生成工具，根据我上一条消息生成且只生成 1 张图片。"
                        "不要输出提示词、分析或改写说明，请返回实际生成的图片。",
                    )
                    try:
                        image = await self._wait_for_new_image(
                            page,
                            before,
                            initial_visual_error=retry_visual_error,
                        )
                    except TextOnlyGenerationResponse as exc:
                        raise RuntimeError(
                            "网页端连续两次只返回文字，没有调用图片生成工具；"
                            "该站点可能不支持通过聊天指令稳定生图"
                        ) from exc
                generation_warning = ""
                output = await self._save_image(page, image, project_id)
            except Exception as exc:
                try:
                    captured_url = self._current_conversation_url(page)
                except (AttributeError, TypeError, ValueError):
                    captured_url = ""
                if captured_url:
                    exc.conversation_url = captured_url
                raise
            if attached == len(reference_paths):
                warning = ""
            elif not upload_result.supported:
                warning = "镜像站未检测到可用的图片上传控件，参考图已保存在本地但未发送"
            else:
                warning = f"镜像站只接受了 {attached} / {len(reference_paths)} 张参考图，其余参考图仍保存在本地"
            return GenerationResult(
                path=output,
                references_requested=len(reference_paths),
                references_attached=attached,
                reference_warning=warning,
                generation_warning=generation_warning,
                conversation_url=self._current_conversation_url(page),
            )

    async def current_conversation_url(self) -> str:
        async with self.generation_lock:
            page = await self._get_page()
            return self._validated_conversation_url(page.url)

    async def open_conversation(self, conversation_url: str) -> str:
        async with self.generation_lock:
            page = await self._get_page()
            await self._prepare_project_conversation(page, conversation_url, force_new=False)
            return page.url

    async def start_new_conversation(self) -> str:
        async with self.generation_lock:
            page = await self._get_page()
            await self._prepare_project_conversation(page, "", force_new=True)
            return page.url

    async def test_connection(self) -> str:
        target_url = self._mirror_url()
        page = await self._get_page()
        await page.goto(
            target_url,
            wait_until="domcontentloaded",
            timeout=max(10, int(self.settings.generation_timeout_seconds * 1000)),
        )
        return page.url

    def _mirror_url(self, use_chat_url: bool = False) -> str:
        target_url = (
            self.settings.mirror_chat_url or self.settings.mirror_url
            if use_chat_url
            else self.settings.mirror_url
        )
        if not target_url:
            raise RuntimeError("请先在设置中填写镜像站网址")
        return target_url

    @staticmethod
    def _normalized_url(value: str) -> str:
        parsed = urlsplit(value)
        path = parsed.path.rstrip("/") or "/"
        query = "" if re.search(r"/(?:c|chat|conversation)/[^/?#]+", path, re.IGNORECASE) else parsed.query
        return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, query, ""))

    def _validated_conversation_url(self, value: str) -> str:
        candidate = value.strip()
        parsed = urlsplit(candidate)
        allowed_origins = {
            (urlsplit(self._mirror_url()).scheme.lower(), urlsplit(self._mirror_url()).netloc.lower()),
            (urlsplit(self._mirror_url(use_chat_url=True)).scheme.lower(), urlsplit(self._mirror_url(use_chat_url=True)).netloc.lower()),
        }
        if (
            parsed.scheme not in {"http", "https"}
            or (parsed.scheme.lower(), parsed.netloc.lower()) not in allowed_origins
        ):
            raise ValueError("对话网址不属于当前镜像站")
        conversation_path = re.search(r"/(?:c|chat|conversation)/[^/?#]+", parsed.path, re.IGNORECASE)
        conversation_query = re.search(r"(?:conversation|chat)(?:_id|Id|id)?=", parsed.query, re.IGNORECASE)
        if not conversation_path and not conversation_query:
            raise ValueError("当前页面不是可识别的镜像站对话")
        return candidate

    def _current_conversation_url(self, page: Page) -> str:
        try:
            return self._validated_conversation_url(page.url)
        except ValueError:
            return ""

    async def _prepare_project_conversation(
        self,
        page: Page,
        conversation_url: str,
        *,
        force_new: bool,
    ) -> None:
        if conversation_url and not force_new:
            target = self._validated_conversation_url(conversation_url)
            if self._normalized_url(page.url) != self._normalized_url(target):
                await page.goto(target, wait_until="domcontentloaded")
            if self._normalized_url(page.url) != self._normalized_url(target):
                raise RuntimeError("项目绑定的镜像站对话已失效，请重新绑定")
            return
        await MirrorConversationAdapter(page).start_new(self._mirror_url(use_chat_url=True))

    def status(self) -> dict[str, object]:
        context_open = self.context is not None and not self.context.is_closed()
        page_open = self.page is not None and not self.page.is_closed()
        return {
            "started": self.playwright is not None,
            "context_open": context_open,
            "page_open": page_open,
            "page_url": self.page.url if page_open and self.page is not None else "",
        }

    async def _get_page(self) -> Page:
        if self.playwright is None:
            await self.start()
        if self.context is None or self.context.is_closed():
            await self._launch_context()
        if self.page is not None and not self.page.is_closed():
            return self.page
        live_pages = [page for page in self.context.pages if not page.is_closed()]
        if live_pages:
            self.page = live_pages[-1]
        else:
            try:
                self.page = await self.context.new_page()
            except PlaywrightError as exc:
                if "Target page, context or browser has been closed" not in str(exc):
                    raise
                await self._launch_context()
                self.page = await self.context.new_page()
        return self.page

    async def _launch_context(self) -> None:
        if self.playwright is None:
            raise RuntimeError("浏览器会话尚未启动")
        if self.context is not None:
            try:
                await self.context.close()
            except PlaywrightError:
                pass
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.settings.browser_profile_dir),
            headless=self.settings.headless,
            no_viewport=True,
            args=["--start-maximized"],
        )
        self.page = None

    async def _submit_prompt(self, page: Page, prompt: str) -> None:
        # 镜像站前端可能改 placeholder，因此优先按语义查找，再退回通用输入框。
        password_input = page.locator("input[type='password']")
        login_button = page.get_by_role("button", name="登录")
        password_candidate = password_input.last if hasattr(password_input, "last") else password_input
        login_candidate = login_button.last if hasattr(login_button, "last") else login_button
        if (
            await password_input.count()
            and await login_button.count()
            and (not hasattr(password_candidate, "is_visible") or await password_candidate.is_visible())
            and (not hasattr(login_candidate, "is_visible") or await login_candidate.is_visible())
        ):
            raise RuntimeError("镜像站当前处于登录页，请先在浏览器窗口中完成登录")
        candidates = [
            page.locator("textarea").last,
            page.locator("[contenteditable='true']").last,
        ]
        editor = None
        for candidate in candidates:
            if await candidate.count() and await candidate.is_visible():
                editor = candidate
                break
        if editor is None:
            raise RuntimeError("找不到聊天输入框；请确认已登录且页面已加载完成")

        message = (
            "@创建图片 请直接调用图片生成工具，生成且只生成 1 张图片。"
            "不要分析、改写或只输出绘图提示词；请返回实际生成的图片。"
            f"\n\n{prompt}"
        )
        await editor.fill(message)
        await editor.press("Enter")

        if await self._wait_for_prompt_submission(page, editor, timeout_seconds=4):
            return

        send_selectors = (
            "button[type='submit']",
            "button[aria-label*='发送' i]",
            "button[aria-label*='send' i]",
            "button[data-testid*='send' i]",
        )
        for selector in send_selectors:
            try:
                button = page.locator(selector).last
                if await button.count() and await button.is_visible() and await button.is_enabled():
                    await button.click()
                    break
            except (PlaywrightError, AttributeError):
                continue
        if not await self._wait_for_prompt_submission(page, editor, timeout_seconds=12):
            raise RuntimeError("参考图已进入输入区，但提示词未成功发送；请等待附件加载完成后重试")

    async def _wait_for_prompt_submission(self, page: Page, editor: Any, timeout_seconds: float) -> bool:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            try:
                current = await editor.evaluate(
                    "element => 'value' in element ? element.value : (element.textContent || '')"
                )
                if not str(current or "").strip():
                    return True
            except (PlaywrightError, AttributeError):
                return True
            await page.wait_for_timeout(250)
        return False

    async def _image_sources(self, page: Page) -> set[str]:
        sources: set[str] = set()
        for image in await page.locator("img").all():
            probe = await self._image_probe(image)
            identity = str(probe.get("identity") or "").strip()
            if identity:
                sources.add(identity)
            try:
                await image.evaluate(
                    "image => image.setAttribute('data-frame-generation-baseline', 'true')"
                )
            except (AttributeError, PlaywrightError):
                pass
        return sources

    async def _mark_assistant_response_baseline(self, page: Page) -> None:
        """Mark existing assistant turns so only this request's reply is observed."""

        selectors = (
            "main [data-message-author-role='assistant']",
            "main [data-role='assistant']",
            "main [data-testid*='assistant-message' i]",
            "main [data-testid*='message_assistant' i]",
        )
        for selector in selectors:
            try:
                for response in await page.locator(selector).all():
                    await response.evaluate(
                        "element => element.setAttribute('data-frame-response-baseline', 'true')"
                    )
            except (AttributeError, PlaywrightError, TypeError):
                continue

    async def _new_assistant_response_text(self, page: Page) -> str:
        """Return text from the newest assistant turn created after the baseline."""

        selectors = (
            "main [data-message-author-role='assistant']",
            "main [data-role='assistant']",
            "main [data-testid*='assistant-message' i]",
            "main [data-testid*='message_assistant' i]",
        )
        newest = ""
        seen: set[str] = set()
        for selector in selectors:
            try:
                responses = await page.locator(selector).all()
            except (AttributeError, PlaywrightError, TypeError):
                continue
            for response in responses:
                try:
                    if await response.get_attribute("data-frame-response-baseline") == "true":
                        continue
                    if not await response.is_visible():
                        continue
                    text = " ".join((await response.inner_text(timeout=1000)).split())
                except (AttributeError, PlaywrightError, TypeError):
                    continue
                if text and text not in seen:
                    seen.add(text)
                    newest = text[:4000]
        return newest

    async def _image_probe(self, image: Any) -> dict[str, Any]:
        try:
            result = await image.evaluate(
                """image => {
                    const lazySource = image.getAttribute('data-original')
                        || image.getAttribute('data-src')
                        || image.getAttribute('data-lazy-src')
                        || '';
                    const responsiveSource = image.currentSrc || '';
                    const htmlSource = image.getAttribute('src') || image.src || '';
                    const srcset = image.getAttribute('srcset') || '';
                    return {
                        identity: lazySource || responsiveSource || htmlSource || srcset,
                        natural_width: Number(image.naturalWidth || 0),
                        natural_height: Number(image.naturalHeight || 0),
                    };
                }"""
            )
            if isinstance(result, dict):
                return result
        except (AttributeError, PlaywrightError, TypeError):
            pass
        try:
            source = await image.get_attribute("src")
        except (AttributeError, PlaywrightError):
            source = ""
        return {"identity": source or "", "natural_width": 0, "natural_height": 0}

    async def _is_reference_attachment(self, image: Any) -> bool:
        """Reject input attachments even when a mirror clones or rewrites their img node."""

        try:
            result = await image.evaluate(
                """image => {
                    const attachmentSelector = [
                        '[data-frame-generation-attachment]', '[data-attachment]',
                        '[data-upload]', '[data-reference]', '[data-file]',
                        '[data-testid*="attachment" i]', '[data-testid*="upload" i]',
                        '[class*="attachment" i]', '[class*="upload" i]',
                        '[class*="reference" i]'
                    ].join(',');
                    let node = image;
                    for (let depth = 0; node && depth < 10; depth += 1, node = node.parentElement) {
                        if (node.matches?.(attachmentSelector)) return true;
                        if (node.matches?.('[data-message-author-role="user"], [data-role="user"]')) return true;
                        if (node.matches?.('[data-message-author-role="assistant"], [data-role="assistant"]')) return false;
                    }
                    return false;
                }"""
            )
            return result is True
        except (AttributeError, PlaywrightError, TypeError):
            return False

    async def _page_visual_error_message(self, page: Page) -> str:
        """Return a visible, semantically scoped error that is actually rendered red."""

        selectors = (
            "main [role='alert']",
            "main [aria-live='assertive']",
            "main [data-state='error']",
            "main [data-status='error']",
            "main [data-testid*='error' i]",
            "main [class*='error' i]",
        )
        red_style_check = r"""
            element => {
                const isRed = value => {
                    const match = String(value || '').match(
                        /rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:\s*[,\/]\s*([\d.]+))?\s*\)/i
                    );
                    if (!match) return false;
                    const red = Number(match[1]);
                    const green = Number(match[2]);
                    const blue = Number(match[3]);
                    const alpha = match[4] === undefined ? 1 : Number(match[4]);
                    return alpha >= 0.2
                        && red >= 110
                        && red - green >= 45
                        && red - blue >= 30
                        && red >= green * 1.45;
                };
                const nodes = [element, ...element.querySelectorAll('*')].slice(0, 80);
                return nodes.some(node => {
                    const style = getComputedStyle(node);
                    return [
                        style.color,
                        style.backgroundColor,
                        style.borderTopColor,
                        style.borderRightColor,
                        style.borderBottomColor,
                        style.borderLeftColor,
                        style.outlineColor,
                    ].some(isRed);
                });
            }
        """
        for selector in selectors:
            try:
                candidates = page.locator(selector)
                if not await candidates.count():
                    continue
                candidate = candidates.last
                if not await candidate.is_visible():
                    continue
                if not await candidate.evaluate(red_style_check):
                    continue
                text = " ".join((await candidate.inner_text(timeout=1000)).split())
            except (PlaywrightError, AttributeError, TypeError):
                continue
            if 1 <= len(text) <= 500:
                return text[:280]
        return ""

    async def _page_generation_active(self, page: Page) -> bool:
        """Detect semantic generation activity without depending on site copy."""

        selectors = (
            "main [aria-busy='true']",
            "main button[aria-label*='停止' i]",
            "main button[aria-label*='取消' i]",
            "main button[aria-label*='stop' i]",
            "main button[aria-label*='cancel' i]",
            "main button[data-testid*='stop' i]",
            "main button[data-testid*='cancel' i]",
        )
        for selector in selectors:
            try:
                candidates = page.locator(selector)
                if not await candidates.count():
                    continue
                candidate = candidates.last
                if await candidate.is_visible():
                    return True
            except (PlaywrightError, AttributeError, TypeError):
                continue
        return False

    async def _wait_for_new_image(
        self,
        page: Page,
        before: set[str],
        *,
        initial_visual_error: str = "",
    ) -> Any:
        loop = asyncio.get_running_loop()
        started_at = loop.time()
        soft_deadline = started_at + self.settings.generation_timeout_seconds
        hard_deadline = soft_deadline + min(
            max(self.settings.generation_timeout_seconds, 120),
            900,
        )
        consecutive_visual_errors = 0
        latest_visual_error = ""
        stale_visual_error = initial_visual_error
        active_seen = False
        stable_text = ""
        stable_text_polls = 0
        while True:
            # DOM order matches the provider's visual output order, so when a
            # response contains several images the first generated image wins.
            for image in await page.locator("img").all():
                try:
                    if await image.get_attribute("data-frame-generation-baseline") == "true":
                        continue
                except (AttributeError, PlaywrightError):
                    pass
                if await self._is_reference_attachment(image):
                    continue
                probe = await self._image_probe(image)
                identity = str(probe.get("identity") or "").strip()
                if not identity or identity in before:
                    continue
                if not await image.is_visible():
                    continue
                natural_width = float(probe.get("natural_width") or 0)
                natural_height = float(probe.get("natural_height") or 0)
                if natural_width >= 256 and natural_height >= 256:
                    return image
                box = await image.bounding_box()
                if box and box["width"] >= 256 and box["height"] >= 256:
                    return image
            visual_error = await self._page_visual_error_message(page)
            if visual_error and visual_error != stale_visual_error:
                consecutive_visual_errors += 1
                latest_visual_error = visual_error
            elif visual_error:
                consecutive_visual_errors = 0
                latest_visual_error = ""
            else:
                consecutive_visual_errors = 0
                latest_visual_error = ""
                stale_visual_error = ""
            if consecutive_visual_errors >= 3:
                raise RuntimeError(f"镜像站生成失败：{latest_visual_error}")

            generation_active = await self._page_generation_active(page)
            active_seen = active_seen or generation_active
            response_text = await self._new_assistant_response_text(page)
            if response_text and not generation_active:
                if response_text == stable_text:
                    stable_text_polls += 1
                else:
                    stable_text = response_text
                    stable_text_polls = 1
                # Sites with semantic busy/stop controls can be classified
                # sooner after those controls disappear. Unknown sites get a
                # longer quiet window so slow streaming text is not cut off.
                quiet_polls_required = 3 if active_seen else 8
                if stable_text_polls >= quiet_polls_required:
                    raise TextOnlyGenerationResponse(
                        "网页端本次回复已结束，但只返回了文字，没有生成图片"
                    )
            else:
                stable_text = response_text
                stable_text_polls = 0
            now = loop.time()
            if now >= soft_deadline:
                if now < hard_deadline and generation_active:
                    soft_deadline = min(hard_deadline, now + 30)
                else:
                    break
            await page.wait_for_timeout(1000)
        raise TimeoutError("等待图片结果超时；镜像站页面可能仍在生成，未判定为登录失效")

    async def _save_image(self, page: Page, image: Any, project_id: str) -> Path:
        downloaded = await self._download_original_from_page(page, image)
        if downloaded is not None:
            content, mime_type = downloaded
            return self._write_original_image(content, mime_type, project_id)

        for source in await self._image_source_candidates(page, image):
            payload = await self._read_original_image(page, source)
            if payload is None:
                continue
            content, mime_type = payload
            return self._write_original_image(content, mime_type, project_id)
        raise RuntimeError("无法读取网页原图；未保存低清预览，请在镜像站确认原图已经加载完成后重试")

    async def _download_original_from_page(self, page: Page, image: Any) -> tuple[bytes, str] | None:
        """Use the site's own original-image download action when one is available."""

        marker = f"codex-original-{uuid4().hex}"
        try:
            await image.hover()
        except (AttributeError, PlaywrightError):
            pass
        try:
            found = await image.evaluate(
                """(image, marker) => {
                    const pattern = /(download|original|\u4e0b\u8f7d|\u539f\u56fe)/i;
                    let node = image.parentElement;
                    while (node && node !== document.body) {
                        const controls = [...node.querySelectorAll('button, a[href], [role="button"]')];
                        const control = controls.find(candidate => {
                            const label = [
                                candidate.getAttribute('aria-label'),
                                candidate.getAttribute('title'),
                                candidate.getAttribute('data-testid'),
                                candidate.hasAttribute('download') ? 'download' : '',
                                candidate.textContent
                            ].filter(Boolean).join(' ');
                            return pattern.test(label);
                        });
                        if (control) {
                            control.setAttribute('data-codex-original-download', marker);
                            return true;
                        }
                        node = node.parentElement;
                    }
                    return false;
                }""",
                marker,
            )
        except (AttributeError, PlaywrightError):
            return None
        if not found:
            return None

        selector = f'[data-codex-original-download="{marker}"]'
        try:
            control = page.locator(selector)
            async with page.expect_download(timeout=5000) as download_info:
                await control.click(force=True)
            download = await download_info.value
            downloaded_path = await download.path()
            if downloaded_path is None:
                return None
            content = Path(downloaded_path).read_bytes()
            if not content:
                return None
            mime_type = mimetypes.guess_type(download.suggested_filename or "")[0] or ""
            return content, mime_type
        except (AttributeError, OSError, PlaywrightError):
            return None
        finally:
            try:
                await page.locator(selector).evaluate("element => element.removeAttribute('data-codex-original-download')")
            except (AttributeError, PlaywrightError):
                pass

    def _write_original_image(self, content: bytes, mime_type: str, project_id: str) -> Path:
        suffix = self._image_suffix(mime_type, content)
        output = self.settings.image_dir / project_id / "generated" / f"{uuid4().hex}{suffix}"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)
        return output

    async def _image_source_candidates(self, page: Page, image: Any) -> list[str]:
        metadata: dict[str, Any] = {}
        try:
            metadata = await image.evaluate(
                """image => {
                    const anchor = image.closest('a[href]') || image.parentElement?.querySelector('a[href][download]');
                    return {
                        current_src: image.currentSrc || '',
                        src: image.src || image.getAttribute('src') || '',
                        srcset: image.getAttribute('srcset') || '',
                        original: image.getAttribute('data-original') || image.getAttribute('data-src') || '',
                        anchor: anchor?.href || ''
                    };
                }"""
            )
        except (AttributeError, PlaywrightError):
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}

        sources: list[str] = []
        srcset = str(metadata.get("srcset") or "")
        if srcset:
            entries = []
            for item in srcset.split(","):
                parts = item.strip().split()
                if not parts:
                    continue
                descriptor = parts[-1] if len(parts) > 1 else "0w"
                match = re.match(r"([0-9.]+)(w|x)$", descriptor)
                score = float(match.group(1)) if match else 0.0
                entries.append((score, parts[0]))
            sources.extend(source for _, source in sorted(entries, reverse=True))

        for key in ("anchor", "original", "current_src", "src"):
            source = str(metadata.get(key) or "").strip()
            if source:
                sources.append(source)
        if not sources:
            source = await image.get_attribute("src")
            if source:
                sources.append(source)

        page_url = getattr(page, "url", "")
        unique: list[str] = []
        for source in sources:
            resolved = urljoin(page_url, source) if page_url and not source.startswith(("blob:", "data:")) else source
            if resolved and resolved not in unique:
                unique.append(resolved)
        return unique

    async def _read_original_image(self, page: Page, source: str) -> tuple[bytes, str] | None:
        if source.startswith("data:image/"):
            return self._decode_data_url(source)

        if source.startswith(("http://", "https://")) and self.context is not None:
            try:
                response = await self.context.request.get(source)
                if response.ok:
                    content = await response.body()
                    mime_type = response.headers.get("content-type", "").split(";", 1)[0]
                    if content:
                        return content, mime_type
            except PlaywrightError:
                pass

        try:
            result = await page.evaluate(
                """async source => {
                    try {
                        const response = await fetch(source, { credentials: 'include' });
                        if (!response.ok) return null;
                        const blob = await response.blob();
                        const dataUrl = await new Promise((resolve, reject) => {
                            const reader = new FileReader();
                            reader.onload = () => resolve(reader.result);
                            reader.onerror = () => reject(reader.error);
                            reader.readAsDataURL(blob);
                        });
                        return { data_url: dataUrl, mime_type: blob.type || response.headers.get('content-type') || '' };
                    } catch (_) {
                        return null;
                    }
                }""",
                source,
            )
        except (AttributeError, PlaywrightError):
            return None
        if not isinstance(result, dict) or not isinstance(result.get("data_url"), str):
            return None
        content, data_mime_type = self._decode_data_url(result["data_url"])
        return content, str(result.get("mime_type") or data_mime_type)

    @staticmethod
    def _decode_data_url(value: str) -> tuple[bytes, str]:
        header, encoded = value.split(",", 1)
        mime_type = header[5:].split(";", 1)[0] or "image/png"
        if ";base64" in header.lower():
            return base64.b64decode(encoded), mime_type
        return unquote_to_bytes(encoded), mime_type

    @staticmethod
    def _image_suffix(mime_type: str, content: bytes) -> str:
        normalized = mime_type.lower().split(";", 1)[0].strip()
        suffixes = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "image/avif": ".avif",
        }
        if normalized in suffixes:
            return suffixes[normalized]
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return ".png"
        if content.startswith(b"\xff\xd8\xff"):
            return ".jpg"
        if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
            return ".webp"
        return ".img"
