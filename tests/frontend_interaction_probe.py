import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import httpx
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(url: str) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            if httpx.get(url, timeout=0.5).status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.1)
    raise RuntimeError(f"Server did not start: {url}")


def imported_project(url: str) -> dict:
    text = "莉亚在雨夜站台等候。列车灯掠过时，她将信封递到寒色面前。"
    manifest = {
        "schema_version": 1,
        "project": {"name": "深链接分镜项目", "description": "浏览器契约测试"},
        "preferences": {
            "prompt_profile": "natural", "format": "vertical_comic", "panel_budget": 1,
            "adaptation_mode": "faithful", "character_mode": "user", "style_mode": "color_anime",
            "style_pack_id": "modern-seinen-v1", "style_prompt": "纯二维彩色动画",
            "style_negative_prompt": "文字，水印", "style_analysis": {}, "bubble_pack_id": "jp-clean-v1",
        },
        "source_batch": {
            "batch_id": "BATCH-001", "source_title": "雨夜来信", "source_file": "story.txt",
            "selected_text": text, "start_quote": "莉亚在雨夜站台等候。", "end_quote": "列车灯掠过时，她将信封递到寒色面前。", "char_count": len(text),
        },
        "world": {"name": "雾港", "visual": "冷蓝雨夜与暖黄站灯"},
        "characters": [{
            "client_id": "CHR-001", "name": "莉亚", "role": "守望者", "faction": "", "personality": "沉静",
            "appearance": "", "costume": "", "signature": "", "source_facts": ["雨夜站台等候"], "ai_supplements": [],
            "needs_user_input": ["补充外貌与服装"], "reference_requests": ["上传正面角色设定图"],
        }],
        "shots": [{
            "client_id": "SHOT-001", "type": "Medium Shot", "title": "递出信封", "description": "莉亚递出信封。",
            "characters": ["CHR-001"], "character_directions": {"CHR-001": {"costume": "深蓝雨衣", "position": "画面左侧", "action": "递出信封", "expression": "迟疑"}},
            "visual": {"camera_angle": "Eye Level", "dynamic_expression": "still", "panel_layout": "single", "panel_beats": [{"label": "第 1 格", "visual": "莉亚递出信封"}], "aspect_ratio": "3:4", "resolution": "Auto", "prompt": "右上保留干净对白区，不绘制文字", "scene": "旧站台 / 深夜", "action": "递出信封", "expression": "迟疑", "lighting": "冷蓝与暖黄", "style": "彩色动画"},
            "source": {"anchor": "列车灯掠过时，她将信封递到寒色面前。", "adaptation_kind": "direct"},
            "post_text": [{"kind": "dialogue", "text": "这封信给你。", "speaker_id": "CHR-001", "position": "top-right", "style": "speech"}],
            "text_safe_areas": ["top-right"], "warnings": [],
        }],
        "checklist": [{"kind": "character_reference", "owner_client_id": "CHR-001", "message": "上传正面角色设定图", "blocking": False}],
    }
    response = httpx.post(f"{url.rstrip('/')}/api/import/storyboard/projects", json=manifest, timeout=5)
    response.raise_for_status()
    return response.json()


def run_probe(url: str) -> dict:
    failures = []
    contract_text = ""
    imported = imported_project(url)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        console_errors = []
        settings_responses = []
        generate_requests = []
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on(
            "response",
            lambda response: settings_responses.append({"status": response.status, "method": response.request.method})
            if response.url.endswith("/api/settings")
            else None,
        )
        page.on("request", lambda request: generate_requests.append(request.url) if "/api/generate" in request.url else None)
        page.route(
            "**/api/generate",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=(
                    '{"url":"data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' '
                    'width=\'16\' height=\'16\'%3E%3C/svg%3E","generation_mode":"api",'
                    '"generation_channel":"interaction probe","generation_model":"test",'
                    '"style_pack_id":"","reference_warning":"","generation_warning":""}'
                ),
            ),
        )
        page.goto(imported["open_url"], wait_until="domcontentloaded")
        page.wait_for_function(
            "projectId => document.querySelector('#projectSelect')?.value === projectId",
            arg=imported["project_id"],
            timeout=5000,
        )
        if page.locator("#projectSelect").input_value() != imported["project_id"]:
            failures.append("project deep link did not select the imported project")
        contract_panel = page.locator(".storyboard-contract-panel")
        contract_panel.wait_for(state="visible", timeout=5000)
        contract_text = contract_panel.inner_text()
        if contract_panel.count() != 1:
            failures.append("imported storyboard metadata is not visible in the director")
        elif "列车灯掠过时，她将信封递到寒色面前。" not in contract_text:
            failures.append("source anchor is not visible in the director")
        post_text_editor = page.locator("[data-post-text]")
        if post_text_editor.count() != 1 or post_text_editor.input_value() != "这封信给你。":
            failures.append("post-production text is not visible in the director")
        if "提示，不阻断生成" not in contract_text:
            failures.append("non-blocking checklist label is missing")
        if not page.locator("#generateButton").is_enabled():
            failures.append("incomplete import checklist incorrectly blocks manual generation")
        if page.locator('.conversation-strip[data-conversation-status="unbound"]').count() != 1:
            failures.append("unbound project conversation status is not visible in the director")
        if page.locator("#bindCurrentConversationButton").count() != 1:
            failures.append("bind-current conversation action is missing")
        if page.locator("#newProjectConversationButton").count() != 1:
            failures.append("new project conversation action is missing")

        selected_before_external_import = page.locator("#projectSelect").input_value()
        newly_imported = imported_project(url)
        try:
            page.wait_for_function(
                "() => document.querySelector('#toastRegion')?.textContent.includes('检测到 Skill 新建的项目')",
                timeout=8000,
            )
        except Exception:
            failures.append("page did not detect a Skill-created project")
        if page.locator("#projectSelect").input_value() != selected_before_external_import:
            failures.append("external project import switched the active project automatically")
        if not page.locator("#generateButton").is_enabled():
            failures.append("external project notification disabled manual generation")
        if generate_requests:
            failures.append("external project detection triggered image generation")
        view_action = page.locator('[data-toast-key^="new-project-"] .toast-action')
        if view_action.count():
            view_action.click()
            page.wait_for_function(
                "projectId => document.querySelector('#projectSelect')?.value === projectId",
                arg=newly_imported["project_id"],
                timeout=5000,
            )
            if page.locator("#projectSelect").input_value() != newly_imported["project_id"]:
                failures.append("View project action did not switch to the Skill-created project")
        else:
            failures.append("Skill-created project notification has no View project action")
        if generate_requests:
            failures.append("viewing a Skill-created project triggered image generation")

        for view in ("characters", "world", "storyboard", "settings", "director"):
            page.locator(f'.nav-item[data-view="{view}"]').click()
            if page.locator("body").get_attribute("data-active-view") != view:
                failures.append(f"navigation did not activate {view}")

        mode = page.locator('select[data-field="mode"]')
        options = mode.locator("option").evaluate_all("options => options.map(option => option.value)")
        if len(options) > 1:
            page.evaluate(
                """() => {
                    window.__saveStatuses = [document.querySelector('#saveStatusText')?.textContent || ''];
                    new MutationObserver(() => window.__saveStatuses.push(document.querySelector('#saveStatusText')?.textContent || ''))
                        .observe(document.querySelector('#saveStatus'), { attributes: true, childList: true, subtree: true });
                }"""
            )
            mode.select_option(options[1])
            if mode.input_value() != options[1]:
                failures.append("director mode selection did not persist")
            page.wait_for_timeout(900)
            save_statuses = page.evaluate("window.__saveStatuses")
            if "正在保存..." not in save_statuses:
                failures.append("dynamic save status did not enter saving state")
            if page.locator("#saveStatusText").inner_text() != "已保存":
                failures.append("dynamic save status did not finish as saved")

        if int(page.locator("#overviewCharacterCount").inner_text()) != page.locator(".character-choice").count():
            failures.append("project overview character count is inaccurate")
        if int(page.locator("#overviewShotCount").inner_text()) != page.locator(".shot-rail-item").count():
            failures.append("project overview shot count is inaccurate")

        editor_box = page.locator(".editor-panel").bounding_box()
        preview_box = page.locator(".preview-panel").bounding_box()
        if not editor_box or not preview_box or preview_box["y"] < editor_box["y"] + editor_box["height"]:
            failures.append("preview panel is not placed below the director editor")
        if page.locator("#panelLayoutSelect, [data-panel-beat]").count():
            failures.append("director still exposes software-controlled multi-panel layout controls")
        authoring_note = page.locator(".prompt-authoring-note")
        if authoring_note.count() != 1 or "Agent" not in authoring_note.inner_text():
            failures.append("director does not explain that the Agent authors multi-panel prompts")

        requests_before_generation_buttons = len(generate_requests)
        page.locator("#generateButton").click()
        page.wait_for_timeout(400)
        if len(generate_requests) != requests_before_generation_buttons + 1:
            failures.append("top generate button did not issue a generation request")

        lettering_button = page.locator("[data-edit-lettering]").first
        if lettering_button.count() != 1 or not lettering_button.is_enabled():
            failures.append("generated shot did not expose the visual lettering editor")
        else:
            page.locator("#addPostTextButton").click()
            post_texts = page.locator("[data-post-text]")
            if post_texts.count() != 2:
                failures.append("adding a second post-text block did not persist")
            else:
                post_texts.nth(1).fill("第二条排字")
            page.locator("[data-post-semantic]").first.select_option("thought")
            page.locator("[data-post-bubble]").first.select_option("cheerful")
            lettering_button = page.locator("[data-edit-lettering]").first
            lettering_button.click()
            proof = page.locator(".lettering-proof-overlay")
            if proof.count() != 1 or not proof.is_visible():
                failures.append("visual lettering editor did not open")
            else:
                if page.locator(".proof-bubble[data-lettering-index]").count() != 2:
                    failures.append("visual lettering editor did not show both post-text bubbles")
                if page.locator("[data-add-lettering-asset]").count():
                    failures.append("lettering editor still shows the duplicated built-in asset button tray")
                bubble_dropzone = page.locator("#letteringBubbleDropzone")
                custom_bubble_added = False
                if bubble_dropzone.count() != 1:
                    failures.append("lettering editor does not expose a working transparent-bubble dropzone")
                else:
                    page.evaluate(
                        """() => {
                            const bytes = Uint8Array.from(atob('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+Xj2yAAAAAElFTkSuQmCC'), char => char.charCodeAt(0));
                            const transfer = new DataTransfer();
                            transfer.items.add(new File([bytes], 'custom-bubble.png', { type: 'image/png' }));
                            document.querySelector('#letteringProofFrame').dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer: transfer, clientX: 420, clientY: 280 }));
                        }"""
                    )
                    try:
                        page.wait_for_function(
                            "() => document.querySelectorAll('.proof-bubble[data-lettering-index]').length === 3",
                            timeout=5000,
                        )
                        custom_bubble_added = True
                    except Exception:
                        failures.append("dropping a transparent PNG on the lettering canvas did not add an element")
                page.locator("#letteringRotationRange").fill("24")
                rotated_style = page.locator("#letteringProofBubble").get_attribute("style") or ""
                if "--lettering-rotation:24deg" not in rotated_style.replace(" ", ""):
                    failures.append(f"lettering rotation was not reflected in the proof: {rotated_style}")
                if custom_bubble_added:
                    page.locator("#deleteLetteringElementButton").click()
                    if page.locator(".proof-bubble[data-lettering-index]").count() != 2:
                        failures.append("deleting a free-position lettering element did not update the proof")
                page.locator('.proof-bubble[data-lettering-index="0"]').dispatch_event("pointerdown")
                proof_after = page.locator("#letteringProofBubble").evaluate(
                    "element => getComputedStyle(element, '::after').content"
                )
                if proof_after not in {"", "none", "normal"}:
                    failures.append(f"lettering proof adds an unwanted backing ellipse: {proof_after}")
                updated_lettering_text = "排字界面同步后的文字"
                page.locator("#letteringTextInput").fill(updated_lettering_text)
                asset_select = page.locator("#letteringAssetSelect")
                asset_values = asset_select.locator("option").evaluate_all("options => options.map(option => option.value)")
                updated_asset = asset_values[-1] if len(asset_values) > 1 else asset_values[0]
                asset_select.select_option(updated_asset)
                bubble_box = page.locator("#letteringProofBubble").bounding_box()
                if bubble_box:
                    initial_style = page.locator("#letteringProofBubble").get_attribute("style") or ""
                    page.mouse.move(bubble_box["x"] + bubble_box["width"] / 2, bubble_box["y"] + bubble_box["height"] / 2)
                    page.mouse.down()
                    page.mouse.move(bubble_box["x"] + bubble_box["width"] / 2 - 35, bubble_box["y"] + bubble_box["height"] / 2 + 25)
                    page.mouse.up()
                    dragged_style = page.locator("#letteringProofBubble").get_attribute("style") or ""
                    if dragged_style == initial_style:
                        failures.append("dragging the proof bubble did not change its position")
                page.locator("#letteringWidthRange").fill("20")
                page.locator("#letteringXRange").fill("8")
                page.locator("#letteringYRange").fill("12")
                bubble_style = page.locator("#letteringProofBubble").get_attribute("style") or ""
                if "width: 20%" not in bubble_style or "left: 8%" not in bubble_style or "top: 12%" not in bubble_style:
                    failures.append("lettering ranges did not update the proof bubble")
                page.locator(".proof-hide-toggle").click()
                if "is-hidden" not in (page.locator("#letteringProofBubble").get_attribute("class") or ""):
                    failures.append("hidden lettering was not reflected in the proof")
                page.locator(".proof-hide-toggle").click()
                page.locator("#closeLetteringEditorDoneButton").click()
                if page.locator(".lettering-proof-overlay").count():
                    failures.append("lettering editor did not close")
                if page.locator("[data-post-text]").first.input_value() != updated_lettering_text:
                    failures.append("lettering text did not sync back to the director post-text editor")
                if page.locator("[data-post-bubble]").first.input_value() != updated_asset:
                    failures.append("lettering asset did not sync back to the director post-text editor")
                layout_summary = page.locator(".post-layout-summary").first
                if layout_summary.count() != 1:
                    failures.append("director post-text editor does not show the custom lettering layout")
                else:
                    summary_text = layout_summary.inner_text()
                    if "水平 8%" not in summary_text or "垂直 12%" not in summary_text or "大小 20%" not in summary_text:
                        failures.append(f"director custom lettering layout is stale: {summary_text}")
                lettering_button = page.locator("[data-edit-lettering]").first
                lettering_button.click()
                reopened_style = page.locator("#letteringProofBubble").get_attribute("style") or ""
                compact_reopened_style = reopened_style.replace(" ", "")
                if "width:20%" not in compact_reopened_style or "left:8%" not in compact_reopened_style or "top:12%" not in compact_reopened_style:
                    failures.append(f"lettering layout did not persist after reopening: {reopened_style}")
                page.locator("#closeLetteringEditorButton").click()

        page.locator('.nav-item[data-view="export"]').click()
        export_check = page.locator("[data-export-shot-id]").first
        if export_check.count() != 1:
            failures.append("export view did not show the generated shot selection")
        else:
            export_check.uncheck()
            if not page.locator(".export-workspace").is_visible():
                failures.append("export view disappeared after changing a shot checkbox")
            if export_check.is_checked():
                failures.append("export shot checkbox did not stay unchecked")
            export_check.check()
            if not page.locator(".export-workspace").is_visible() or not export_check.is_checked():
                failures.append("export shot checkbox could not be reselected")

        page.locator('.nav-item[data-view="director"]').click()

        # Re-generating a shot with an existing image must still expose the
        # in-flight state while the provider response is delayed.
        page.evaluate(
            """() => {
                const originalFetch = window.fetch;
                window.__heldGenerationCalls = 0;
                window.fetch = (input, options) => {
                    if (String(input).includes('/api/generate')) {
                        window.__heldGenerationCalls += 1;
                        return new Promise(resolve => {
                            window.__releaseHeldGeneration = () => {
                                window.fetch = originalFetch;
                                resolve(new Response(JSON.stringify({
                                    url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16'%3E%3C/svg%3E",
                                    generation_mode: 'api',
                                    generation_channel: 'delayed interaction probe',
                                    generation_model: 'test',
                                    style_pack_id: '',
                                    reference_warning: '',
                                    generation_warning: '',
                                }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
                            };
                        });
                    }
                    return originalFetch(input, options);
                };
            }"""
        )
        page.locator("#generateButtonBottom").click()
        page.wait_for_timeout(150)
        if page.evaluate("window.__heldGenerationCalls") != 1:
            failures.append("bottom generate button did not issue a generation request")
        if page.locator("#generateButton").inner_text().strip() != "生成中...":
            failures.append("top generate button did not show delayed generation state")
        if page.locator("#generateButtonBottom").inner_text().strip() != "生成中...":
            failures.append("bottom generate button did not show delayed generation state")
        if page.locator("#generateButton").is_enabled() or page.locator("#generateButtonBottom").is_enabled():
            failures.append("generation buttons remained enabled during delayed generation")
        if "生成中" not in page.locator('.shot-rail-item.active').inner_text():
            failures.append("active shot did not show delayed generation state")
        page.evaluate("window.__releaseHeldGeneration()")
        page.wait_for_function("() => document.querySelector('#generateButton')?.textContent.includes('生成当前镜头')")

        for ratio_name, width, height in (("landscape", 1600, 900), ("square", 900, 900), ("portrait", 900, 1600)):
            page.locator("#imageResult").evaluate(
                """(element, size) => {
                    element.innerHTML = `<img id="adaptive-preview-probe" alt="preview ratio probe"
                        src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='${size.width}' height='${size.height}'%3E%3Crect width='100%25' height='100%25' fill='%2347c9e5'/%3E%3C/svg%3E" />`;
                }""",
                {"width": width, "height": height},
            )
            probe_image = page.locator("#adaptive-preview-probe")
            probe_image.wait_for(state="visible")
            image_box = probe_image.bounding_box()
            result_box = page.locator("#imageResult").bounding_box()
            if not image_box or not result_box:
                failures.append(f"{ratio_name} adaptive preview image did not render")
                continue
            displayed_ratio = image_box["width"] / image_box["height"]
            expected_ratio = width / height
            if abs(displayed_ratio - expected_ratio) > 0.02:
                failures.append(f"{ratio_name} preview ratio was distorted or cropped: {displayed_ratio:.3f}")
            if (
                image_box["x"] < result_box["x"] - 1
                or image_box["y"] < result_box["y"] - 1
                or image_box["x"] + image_box["width"] > result_box["x"] + result_box["width"] + 1
                or image_box["y"] + image_box["height"] > result_box["y"] + result_box["height"] + 1
            ):
                failures.append(f"{ratio_name} preview extends outside its container")

        page.locator('.nav-item[data-view="characters"]').click()
        if page.locator("[data-edit-character]").count():
            page.locator("[data-edit-character] h3").first.click()
            if page.locator("#characterFormSlot .library-form").count() != 1:
                failures.append("character card did not open the editor")

        page.locator('.nav-item[data-view="settings"]').click()
        page.locator('[data-generation-mode="api"]').click()
        page.wait_for_timeout(1200)
        if "active" not in (page.locator('[data-generation-mode="api"]').get_attribute("class") or ""):
            failures.append("API generation mode did not become active")

        mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
        mobile_page.goto(url, wait_until="domcontentloaded")
        mobile_page.locator('.nav-item[data-view="director"]').click()
        mobile_widths = mobile_page.locator("body").evaluate(
            "element => ({ clientWidth: element.clientWidth, scrollWidth: element.scrollWidth })"
        )
        if mobile_widths["scrollWidth"] > mobile_widths["clientWidth"]:
            failures.append("mobile director layout overflows the viewport")
        mobile_editor_box = mobile_page.locator(".editor-panel").bounding_box()
        mobile_preview_box = mobile_page.locator(".preview-panel").bounding_box()
        if (
            not mobile_editor_box
            or not mobile_preview_box
            or mobile_preview_box["y"] < mobile_editor_box["y"] + mobile_editor_box["height"]
        ):
            failures.append("mobile preview panel is not placed below the director editor")
        mobile_page.close()

        browser.close()
    return {"failures": failures, "console_errors": console_errors, "settings_responses": settings_responses}


def main() -> int:
    port = free_port()
    url = f"http://127.0.0.1:{port}/"
    with tempfile.TemporaryDirectory(prefix="frame-interaction-probe-") as temp_dir:
        environment = os.environ.copy()
        environment.update(
            {
                "DATA_DIR": str(Path(temp_dir) / "data"),
                "IMAGE_DIR": str(Path(temp_dir) / "generated"),
                "REFERENCE_DIR": str(Path(temp_dir) / "references"),
            }
        )
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_for_server(url)
            result = run_probe(url)
        finally:
            process.terminate()
            process.wait(timeout=10)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["failures"] or result["console_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
