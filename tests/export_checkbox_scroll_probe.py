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


def create_export_project(url: str, shot_count: int = 14) -> dict:
    shots = []
    for index in range(shot_count):
        shots.append(
            {
                "client_id": f"SHOT-{index + 1:03d}",
                "type": "Medium Shot",
                "title": f"测试镜头 {index + 1}",
                "description": "复选框滚动回归测试。",
                "characters": [],
                "character_directions": {},
                "visual": {
                    "camera_angle": "Eye Level",
                    "dynamic_expression": "still",
                    "aspect_ratio": "3:4",
                    "resolution": "Auto",
                    "prompt": "干净的二维动画测试画面",
                    "scene": "室内",
                    "action": "静止",
                    "expression": "平静",
                    "lighting": "柔和顶光",
                    "style": "",
                },
                "source": {"anchor": "测试原文。", "adaptation_kind": "direct"},
                "post_text": [],
                "text_safe_areas": [],
                "warnings": [],
            }
        )
    manifest = {
        "schema_version": 1,
        "project": {"name": "导出复选框滚动测试"},
        "preferences": {
            "prompt_profile": "natural",
            "format": "vertical_comic",
            "panel_budget": shot_count,
            "adaptation_mode": "faithful",
            "character_mode": "user",
            "style_mode": "color_anime",
            "style_pack_id": "modern-seinen-v1",
            "style_prompt": "纯二维动画",
            "style_negative_prompt": "文字，水印",
            "bubble_pack_id": "jp-clean-v1",
        },
        "source_batch": {
            "batch_id": "BATCH-001",
            "selected_text": "测试原文。",
            "start_quote": "测试原文。",
            "end_quote": "测试原文。",
            "char_count": 5,
        },
        "world": {},
        "characters": [],
        "shots": shots,
        "checklist": [],
    }
    created = httpx.post(f"{url}/api/import/storyboard/projects", json=manifest, timeout=5)
    created.raise_for_status()
    result = created.json()
    project_response = httpx.get(f"{url}/api/projects/{result['project_id']}", timeout=5)
    project_response.raise_for_status()
    project = project_response.json()
    image = (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='320'%3E"
        "%3Crect width='240' height='320' fill='%2347c9e5'/%3E%3C/svg%3E"
    )
    for shot in project["state"]["shots"]:
        shot["content"]["lastImage"] = image
        shot["status"] = "已确认"
    patched = httpx.patch(
        f"{url}/api/projects/{result['project_id']}",
        json={"state": project["state"], "expected_revision": project["revision"]},
        timeout=5,
    )
    patched.raise_for_status()
    return result


def geometry(page) -> dict:
    return page.evaluate(
        """() => {
            const workspace = document.querySelector('.export-workspace');
            const list = document.querySelector('.export-film-list');
            const main = document.querySelector('main');
            const rect = workspace?.getBoundingClientRect();
            return {
                documentY: document.scrollingElement?.scrollTop || 0,
                bodyY: document.body.scrollTop || 0,
                listY: list?.scrollTop || 0,
                mainY: main?.scrollTop || 0,
                workspaceTop: rect?.top ?? null,
                workspaceBottom: rect?.bottom ?? null,
                mainTop: main?.getBoundingClientRect().top ?? null,
                viewportHeight: window.innerHeight,
            };
        }"""
    )


def checkbox_diagnostics(checkbox) -> dict:
    return checkbox.evaluate(
        """input => {
            const describe = element => {
                const rect = element.getBoundingClientRect();
                const style = getComputedStyle(element);
                return {
                    node: `${element.tagName.toLowerCase()}${element.id ? `#${element.id}` : ''}${element.className ? `.${String(element.className).trim().replace(/\\s+/g, '.')}` : ''}`,
                    top: rect.top,
                    bottom: rect.bottom,
                    left: rect.left,
                    right: rect.right,
                    scrollTop: element.scrollTop,
                    scrollHeight: element.scrollHeight,
                    clientHeight: element.clientHeight,
                    overflowY: style.overflowY,
                    position: style.position,
                };
            };
            const ancestors = [];
            for (let node = input.parentElement; node; node = node.parentElement) {
                ancestors.push(describe(node));
            }
            return {
                input: describe(input),
                visual: describe(input.nextElementSibling),
                label: describe(input.parentElement),
                offsetParent: input.offsetParent
                    ? `${input.offsetParent.tagName.toLowerCase()}#${input.offsetParent.id || ''}.${String(input.offsetParent.className || '').trim().replace(/\\s+/g, '.')}`
                    : null,
                activeElement: document.activeElement === input,
                documentY: document.scrollingElement?.scrollTop || 0,
                ancestors,
            };
        }"""
    )


def run_probe(url: str) -> dict:
    project = create_export_project(url)
    failures = []
    samples = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={
                "width": int(os.environ.get("EXPORT_PROBE_WIDTH", "1600")),
                "height": int(os.environ.get("EXPORT_PROBE_HEIGHT", "900")),
            }
        )
        page.goto(project["open_url"], wait_until="domcontentloaded")
        page.wait_for_function(
            "projectId => document.querySelector('#projectSelect')?.value === projectId",
            arg=project["project_id"],
        )
        page.locator('.nav-item[data-view="export"]').click()
        checks = page.locator("[data-export-shot-id]")
        if checks.count() != 14:
            failures.append(f"expected 14 export checkboxes, found {checks.count()}")
        else:
            target = checks.nth(5)
            initial = geometry(page)
            initial_diagnostics = checkbox_diagnostics(target)
            if initial_diagnostics["offsetParent"] != "label#.export-shot-check":
                failures.append(
                    "export checkbox is not positioned inside its own visible control: "
                    f"{initial_diagnostics['offsetParent']}"
                )
            target.scroll_into_view_if_needed()
            for index in range(5, 14):
                checkbox = checks.nth(index)
                checkbox.scroll_into_view_if_needed()
                before = geometry(page)
                if before["mainY"] != 0:
                    failures.append(
                        f"shot {index + 1} scrolled the clipped main stage to {before['mainY']}"
                    )
                if abs(before["workspaceTop"] - initial["workspaceTop"]) > 4:
                    failures.append(
                        f"shot {index + 1} displaced export workspace while entering view: "
                        f"{initial['workspaceTop']} to {before['workspaceTop']}"
                    )
                checkbox.uncheck()
                page.wait_for_timeout(50)
                after = geometry(page)
                samples.append({"shot": index + 1, "before": before, "after": after})
                if abs(after["documentY"] - before["documentY"]) > 2:
                    failures.append(
                        f"shot {index + 1} moved document scroll from "
                        f"{before['documentY']} to {after['documentY']}"
                    )
                if abs(after["workspaceTop"] - before["workspaceTop"]) > 2:
                    failures.append(
                        f"shot {index + 1} moved export workspace from "
                        f"{before['workspaceTop']} to {after['workspaceTop']}"
                    )
                if after["workspaceBottom"] <= 0:
                    failures.append(f"shot {index + 1} moved the export workspace outside the viewport")
                if after["mainY"] != 0:
                    failures.append(
                        f"shot {index + 1} checkbox change scrolled the clipped main stage to {after['mainY']}"
                    )
            screenshot_path = os.environ.get("EXPORT_PROBE_SCREENSHOT")
            if screenshot_path:
                page.screenshot(path=screenshot_path, full_page=False)
        browser.close()
    return {"failures": failures, "samples": samples}


def main() -> int:
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="frame-export-scroll-") as temp_dir:
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
    return 1 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
