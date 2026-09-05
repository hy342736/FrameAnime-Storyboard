"""Browser-side capability adapter for mirror sites.

Mirror sites do not share a stable upload API. The adapter intentionally keeps
the default behavior conservative: detect a file input, attach local files when
the page exposes one, and report an explicit capability result otherwise.
Site-specific selectors can be added here without changing project storage or
the generation workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from playwright.async_api import Page
from playwright.async_api import Error as PlaywrightError


@dataclass
class ReferenceUploadResult:
    requested: int
    attached: int
    supported: bool


class MirrorImageAdapter:
    file_input_selector = "input[type='file']"

    def __init__(self, page: Page) -> None:
        self.page = page

    async def attach(self, paths: list[Path]) -> ReferenceUploadResult:
        existing = [path for path in paths if path.is_file()]
        if not existing:
            return ReferenceUploadResult(len(paths), 0, False)

        inputs = self.page.locator(self.file_input_selector)
        if not await inputs.count():
            return ReferenceUploadResult(len(paths), 0, False)

        try:
            # Re-selecting the same files does not fire change on several React
            # uploaders unless the native input is cleared first.
            await inputs.first.set_input_files([])
            await inputs.first.set_input_files([str(path) for path in existing])
            await self.page.wait_for_timeout(1200)
            return ReferenceUploadResult(len(paths), len(existing), True)
        except PlaywrightError:
            # Some sites expose a single-file input even when their UI accepts
            # multiple attachments. Keep the first reference useful in that case.
            try:
                await inputs.first.set_input_files([])
                await inputs.first.set_input_files(str(existing[0]))
                await self.page.wait_for_timeout(1200)
                return ReferenceUploadResult(len(paths), 1, True)
            except PlaywrightError:
                return ReferenceUploadResult(len(paths), 0, True)


class MirrorConversationAdapter:
    """Hide mirror-site new-chat selectors behind one small interface."""

    new_chat_name = re.compile(r"^(新聊天|新建聊天|New chat)$", re.IGNORECASE)

    def __init__(self, page: Page) -> None:
        self.page = page

    async def start_new(self, fallback_url: str) -> None:
        for role in ("button", "link"):
            try:
                candidates = self.page.get_by_role(role, name=self.new_chat_name)
                if await candidates.count() and await candidates.first.is_visible():
                    await candidates.first.click()
                    await self.page.wait_for_timeout(500)
                    return
            except PlaywrightError:
                continue
        await self.page.goto(fallback_url, wait_until="domcontentloaded")
