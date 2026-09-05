import tempfile
import unittest
from pathlib import Path

from app.config import Settings
from app.storage import WorkspaceStorage


class WorkspaceStorageTests(unittest.TestCase):
    def make_storage(self):
        root = Path(tempfile.mkdtemp(prefix="anime-desk-test-"))
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
        return root, WorkspaceStorage(settings)

    def test_project_and_reference_are_isolated(self):
        root, storage = self.make_storage()
        first = storage.create_project("第一项目")
        second = storage.create_project("第二项目")

        reference = storage.add_reference(
            project_id=first["id"],
            owner_type="world",
            owner_id="world-bible",
            file_name="mood.png",
            mime_type="image/png",
            content=b"png-data",
            reference_type="world_impression",
        )

        self.assertEqual([reference["id"]], [item["id"] for item in storage.list_references(first["id"])])
        self.assertTrue(reference["is_primary"])
        self.assertEqual([], storage.list_references(second["id"]))
        reference_path = storage.reference_file(reference["id"])
        self.assertTrue(reference_path and reference_path.is_file())
        self.assertIn(first["id"], str(reference_path))

        storage.delete_project(first["id"])
        self.assertIsNone(storage.get_project(first["id"]))
        self.assertFalse(reference_path.exists())
        self.assertIsNotNone(storage.get_project(second["id"]))
        self.assertTrue(root.exists())

    def test_reference_metadata_can_be_reordered_and_replaced(self):
        _, storage = self.make_storage()
        project = storage.create_project("排序项目")
        first = storage.add_reference(project_id=project["id"], owner_type="shot", owner_id="SHOT-001", file_name="a.png", mime_type="image/png", content=b"a")
        second = storage.add_reference(project_id=project["id"], owner_type="shot", owner_id="SHOT-001", file_name="b.png", mime_type="image/png", content=b"b")

        storage.update_reference(first["id"], sort_order=1, enabled=False, note="新说明")
        storage.update_reference(second["id"], sort_order=0)
        storage.update_reference(second["id"], is_primary=True)
        listed = storage.list_references(project["id"], "shot", "SHOT-001")
        self.assertEqual([second["id"], first["id"]], [item["id"] for item in listed])
        self.assertFalse(listed[1]["enabled"])
        self.assertEqual("新说明", listed[1]["note"])
        self.assertTrue(listed[0]["is_primary"])
        self.assertFalse(listed[1]["is_primary"])

        storage.replace_reference_file(first["id"], file_name="updated.jpg", mime_type="image/jpeg", content=b"updated")
        path = storage.reference_file(first["id"])
        self.assertTrue(path and path.suffix == ".jpg")
        self.assertEqual(b"updated", path.read_bytes())

    def test_project_lettering_asset_is_stored_separately(self):
        _, storage = self.make_storage()
        project = storage.create_project("排字素材项目")
        asset = storage.add_reference(
            project_id=project["id"],
            owner_type="lettering",
            owner_id="bubble-library",
            file_name="custom-bubble.png",
            mime_type="image/png",
            content=b"transparent-bubble",
            enabled=False,
        )
        self.assertEqual("lettering", asset["owner_type"])
        self.assertEqual(
            [asset["id"]],
            [item["id"] for item in storage.list_references(project["id"], "lettering", "bubble-library")],
        )

    def test_project_conversation_bindings_are_isolated_and_do_not_change_revision(self):
        _, storage = self.make_storage()
        first = storage.create_project("第一项目")
        second = storage.create_project("第二项目")

        binding = storage.set_conversation_binding(
            first["id"],
            url="https://example.test/c/first-conversation",
            title="第一项目 · FRAME-first",
        )

        self.assertEqual(first["id"], binding["project_id"])
        self.assertEqual("https://example.test/c/first-conversation", binding["url"])
        self.assertEqual(binding, storage.get_conversation_binding(first["id"]))
        self.assertIsNone(storage.get_conversation_binding(second["id"]))
        self.assertEqual(first["revision"], storage.get_project(first["id"])["revision"])

        storage.delete_project(first["id"])
        self.assertIsNone(storage.get_conversation_binding(first["id"]))

    def test_conversation_binding_survives_storage_reload(self):
        _, storage = self.make_storage()
        project = storage.create_project("重载项目")
        storage.set_conversation_binding(
            project["id"],
            url="https://example.test/c/reload-conversation",
            title="重载项目",
        )

        reloaded = WorkspaceStorage(storage.settings)
        self.assertEqual(
            "https://example.test/c/reload-conversation",
            reloaded.get_conversation_binding(project["id"])["url"],
        )


if __name__ == "__main__":
    unittest.main()
