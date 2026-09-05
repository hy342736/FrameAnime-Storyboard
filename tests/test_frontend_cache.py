import asyncio
import unittest

import httpx

from app.main import app


class FrontendCacheTests(unittest.TestCase):
    def test_frontend_documents_are_never_cached(self):
        async def request_frontend():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                return await asyncio.gather(
                    client.get("/"),
                    client.get("/app.js?v=6"),
                    client.get("/styles.css?v=6"),
                )

        responses = asyncio.run(request_frontend())
        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get("cache-control"), "no-store, max-age=0")
            self.assertEqual(response.headers.get("pragma"), "no-cache")

        self.assertIn('id="projectSelect"', responses[0].text)
        self.assertIn('id="newProjectButton"', responses[0].text)
        self.assertIn('id="loginButton"', responses[0].text)
        self.assertIn('data-view="director"', responses[0].text)
        self.assertIn('data-view="characters"', responses[0].text)
        self.assertIn('data-view="world"', responses[0].text)
        self.assertIn('data-view="style"', responses[0].text)
        self.assertIn('data-view="storyboard"', responses[0].text)
        self.assertIn('data-view="export"', responses[0].text)
        self.assertIn('data-view="settings"', responses[0].text)
        self.assertIn("app.js?v=24", responses[0].text)
        self.assertIn("styles.css?v=24", responses[0].text)
        self.assertIn("/assets/app-icon.png?v=16", responses[0].text)
        self.assertNotIn("SKILL LOADED", responses[0].text)
        self.assertNotIn("Anime AI Art Director", responses[0].text)
        self.assertNotIn("本地工作区", responses[0].text)
        self.assertNotIn("v0.1", responses[0].text)
        self.assertIn('id="saveStatusText"', responses[0].text)
        self.assertIn('id="overviewCharacterCount"', responses[0].text)
        self.assertIn('id="overviewShotCount"', responses[0].text)
        self.assertIn('id="overviewReferenceCount"', responses[0].text)
        self.assertIn('setSaveStatus("saving", "正在保存...")', responses[1].text)
        self.assertIn('setSaveStatus("saved", "已保存")', responses[1].text)
        self.assertIn('setSaveStatus("error", "保存失败，本机副本已保留")', responses[1].text)
        self.assertIn("storyboardContractPanel", responses[1].text)
        self.assertIn("sourceBatches", responses[1].text)
        self.assertIn("postText", responses[1].text)
        self.assertIn("textSafeAreas", responses[1].text)
        self.assertIn('URLSearchParams(window.location.search).get("project_id")', responses[1].text)
        self.assertIn("expected_revision", responses[1].text)
        self.assertIn("项目已在其他窗口更新", responses[1].text)
        self.assertIn("checkForProjectUpdates", responses[1].text)
        self.assertIn("检测到 Skill 新建的项目", responses[1].text)
        self.assertIn('actionLabel: "查看项目"', responses[1].text)
        self.assertIn('actionLabel: "重新载入"', responses[1].text)
        self.assertIn("document.body.dataset.activeView = state.activeView", responses[1].text)
        self.assertIn('closest(".nav-item[data-view]")', responses[1].text)
        self.assertIn("lineart-director.png", responses[2].text)
        self.assertIn("pattern-seated.png", responses[2].text)
        self.assertIn("pattern-kimono.png", responses[2].text)
        self.assertIn("generation_warning", responses[1].text)
        self.assertIn("toast-error", responses[1].text)
        self.assertIn("重试", responses[1].text)
        self.assertIn("selectedCharacters", responses[1].text)
        self.assertIn("data-character-toggle", responses[1].text)
        self.assertIn("data-character-detail", responses[1].text)
        self.assertIn("generation-origin", responses[1].text)
        self.assertNotIn('|| "未定义身份"', responses[1].text)
        self.assertNotIn('|| "待补充外貌锁定"', responses[1].text)
        self.assertIn('data-edit-character=', responses[1].text)
        self.assertIn('data-editing-character-id=', responses[1].text)
        self.assertIn('更新角色', responses[1].text)
        self.assertIn("Reference Image Mapping", responses[1].text)
        self.assertIn("selected_character_ids", responses[1].text)
        self.assertIn("单个镜头最多锁定 6 个角色", responses[1].text)
        self.assertIn("画面比例", responses[1].text)
        self.assertIn("输出分辨率", responses[1].text)
        self.assertIn("4K / 4096px", responses[1].text)
        self.assertIn('data-generation-mode="mirror"', responses[1].text)
        self.assertIn('data-generation-mode="api"', responses[1].text)
        self.assertIn('data-secret-setting="image_api_key"', responses[1].text)
        self.assertIn("test-image-api", responses[1].text)
        self.assertIn("channel-switch", responses[2].text)
        self.assertIn("character-selector-field", responses[2].text)
        self.assertIn("shot-frame", responses[1].text)
        self.assertIn("preview-panel", responses[1].text)
        self.assertIn('id="generateButton"', responses[1].text)
        self.assertIn('id="saveWorldButton"', responses[1].text)
        self.assertIn('id="addShotButton"', responses[1].text)
        self.assertIn('data-move-shot="up"', responses[1].text)
        self.assertIn("data-upload-reference", responses[1].text)
        self.assertIn("data-delete-ref", responses[1].text)
        self.assertIn("data-replace-reference", responses[1].text)
        self.assertIn('id="saveSettingsButton"', responses[1].text)
        self.assertIn("projectConversationStrip", responses[1].text)
        self.assertIn("bindCurrentConversation", responses[1].text)
        self.assertIn("startNewProjectConversation", responses[1].text)
        self.assertIn("openProjectConversation", responses[1].text)
        self.assertIn("unbindProjectConversation", responses[1].text)
        self.assertIn("loadConversationBinding", responses[1].text)


if __name__ == "__main__":
    unittest.main()
