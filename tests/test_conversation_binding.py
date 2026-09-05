import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from app.config import Settings
from app.main import app
from app.storage import WorkspaceStorage


def make_storage(root: Path) -> WorkspaceStorage:
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
    return WorkspaceStorage(settings)


class FakeConversationSession:
    def __init__(self):
        self.current_url = "https://example.test/c/current-browser-chat"
        self.opened = ""
        self.started_new = False

    async def current_conversation_url(self):
        return self.current_url

    async def open_conversation(self, url):
        self.opened = url
        return url

    async def start_new_conversation(self):
        self.started_new = True
        return "https://example.test/"


class ConversationBindingTests(unittest.TestCase):
    def request(self, storage, session, method, path, json=None):
        async def send():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8001") as client:
                return await client.request(method, path, json=json)

        with patch("app.main.storage", storage), patch("app.main.session", session):
            return asyncio.run(send())

    def test_bind_open_new_and_unbind_project_conversation(self):
        with tempfile.TemporaryDirectory(prefix="conversation-api-") as directory:
            storage = make_storage(Path(directory))
            project = storage.create_project("雨夜来信")
            session = FakeConversationSession()
            path = f"/api/projects/{project['id']}/conversation"

            initial = self.request(storage, session, "GET", path)
            self.assertEqual(200, initial.status_code)
            self.assertEqual("unbound", initial.json()["status"])

            bound = self.request(storage, session, "POST", f"{path}/bind-current")
            self.assertEqual(200, bound.status_code, bound.text)
            self.assertEqual("bound", bound.json()["status"])
            self.assertEqual(session.current_url, bound.json()["url"])
            self.assertIn("雨夜来信", bound.json()["title"])

            renamed = self.request(
                storage,
                session,
                "PATCH",
                f"/api/projects/{project['id']}",
                {"name": "雾港来信"},
            )
            self.assertEqual(200, renamed.status_code, renamed.text)
            self.assertIn("雾港来信", storage.get_conversation_binding(project["id"])["title"])

            opened = self.request(storage, session, "POST", f"{path}/open")
            self.assertEqual(200, opened.status_code, opened.text)
            self.assertEqual(session.current_url, session.opened)

            started = self.request(storage, session, "POST", f"{path}/new")
            self.assertEqual(200, started.status_code, started.text)
            self.assertTrue(session.started_new)
            self.assertEqual("pending", started.json()["status"])
            self.assertIsNone(storage.get_conversation_binding(project["id"]))

            removed = self.request(storage, session, "DELETE", path)
            self.assertEqual(200, removed.status_code, removed.text)
            self.assertEqual("unbound", removed.json()["status"])


if __name__ == "__main__":
    unittest.main()
