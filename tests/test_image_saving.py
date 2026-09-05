import asyncio
import base64
import tempfile
import unittest
from pathlib import Path

from app.browser_session import BrowserSession
from app.config import Settings


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


class BlobImage:
    def __init__(self):
        self.screenshot_called = False

    async def get_attribute(self, name):
        return "blob:https://example.test/original" if name == "src" else None

    async def evaluate(self, _script, _argument=None):
        return False

    async def hover(self):
        return None

    async def screenshot(self, path, type):
        self.screenshot_called = True
        Path(path).write_bytes(b"rendered-preview")


class BlobPage:
    def __init__(self, original):
        self.original = original

    async def evaluate(self, _script, source):
        if source != "blob:https://example.test/original":
            return None
        encoded = base64.b64encode(self.original).decode("ascii")
        return {"data_url": f"data:image/png;base64,{encoded}", "mime_type": "image/png"}


class Download:
    def __init__(self, path):
        self._path = path
        self.suggested_filename = "mirror-original.webp"

    async def path(self):
        return self._path


class DownloadInfo:
    def __init__(self, download):
        self.value = asyncio.sleep(0, result=download)


class DownloadContext:
    def __init__(self, download):
        self.info = DownloadInfo(download)

    async def __aenter__(self):
        return self.info

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class DownloadControl:
    def __init__(self):
        self.clicked = False

    async def click(self, force=False):
        self.clicked = force

    async def evaluate(self, _script):
        return None


class DownloadImage(BlobImage):
    async def evaluate(self, _script, _argument=None):
        return True


class DownloadPage:
    def __init__(self, download_path):
        self.control = DownloadControl()
        self.download = Download(download_path)

    def locator(self, _selector):
        return self.control

    def expect_download(self, timeout):
        assert timeout == 5000
        return DownloadContext(self.download)


class CandidateImage:
    async def evaluate(self, _script, _argument=None):
        return {
            "current_src": "/preview.png",
            "src": "/thumbnail.png",
            "srcset": "/medium.png 800w, /full.png 2048w",
            "original": "/original.png",
            "anchor": "",
        }


class CandidatePage:
    url = "https://example.test/chat"


class ImageSavingTests(unittest.TestCase):
    def test_uses_website_download_original_action_without_reencoding(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-site-download-") as directory:
            root = Path(directory)
            original = b"RIFF\x10\x00\x00\x00WEBPwebsite-original-bytes"
            downloaded_path = root / "browser-download.tmp"
            downloaded_path.write_bytes(original)
            session = BrowserSession(make_settings(root))
            page = DownloadPage(downloaded_path)
            image = DownloadImage()

            output = asyncio.run(session._save_image(page, image, "project-test"))

            self.assertEqual(original, output.read_bytes())
            self.assertEqual(".webp", output.suffix)
            self.assertTrue(page.control.clicked)
            self.assertFalse(image.screenshot_called)

    def test_blob_image_saves_original_bytes_instead_of_preview_screenshot(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-original-image-") as directory:
            original = b"full-resolution-original-image-bytes"
            session = BrowserSession(make_settings(Path(directory)))
            image = BlobImage()

            output = asyncio.run(session._save_image(BlobPage(original), image, "project-test"))

            self.assertEqual(original, output.read_bytes())
            self.assertFalse(image.screenshot_called)

    def test_prefers_largest_srcset_candidate_before_preview_sources(self):
        with tempfile.TemporaryDirectory(prefix="anime-desk-source-order-") as directory:
            session = BrowserSession(make_settings(Path(directory)))

            sources = asyncio.run(session._image_source_candidates(CandidatePage(), CandidateImage()))

            self.assertEqual("https://example.test/full.png", sources[0])
            self.assertLess(
                sources.index("https://example.test/original.png"),
                sources.index("https://example.test/preview.png"),
            )


if __name__ == "__main__":
    unittest.main()
