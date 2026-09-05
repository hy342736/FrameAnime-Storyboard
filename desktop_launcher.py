from __future__ import annotations

import socket
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen

from app.runtime import (
    configure_packaged_environment,
    packaged_data_root,
    remove_runtime_descriptor,
    write_runtime_descriptor,
)


configure_packaged_environment()


def available_port(start: int = 8000, attempts: int = 40) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
            try:
                candidate.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("找不到可用的本地端口（已检查 8000-8039）")


def wait_until_ready(url: str, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{url}/health", timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, URLError):
            time.sleep(0.1)
    raise RuntimeError("工作台本地服务启动超时")


def show_fatal_error(message: str) -> None:
    try:
        log_file = packaged_data_root() / "startup-error.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text(message, encoding="utf-8")
        message = f"{message}\n\n诊断日志：{log_file}"
    except OSError:
        pass
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, "FRAME 启动失败", 0x10)
    except Exception:
        print(message)


def main() -> int:
    server = None
    server_thread = None
    runtime_published = False
    try:
        import uvicorn
        import webview
        from app.main import app as fastapi_app

        port = available_port()
        url = f"http://127.0.0.1:{port}"
        config = uvicorn.Config(
            fastapi_app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(config)
        server.install_signal_handlers = lambda: None
        server_thread = threading.Thread(target=server.run, name="frame-local-server", daemon=True)
        server_thread.start()
        wait_until_ready(url)
        write_runtime_descriptor(port)
        runtime_published = True

        webview.create_window(
            "FRAME - Anime Production Desk",
            url=url,
            width=1280,
            height=800,
            min_size=(980, 680),
            maximized=True,
            background_color="#17242d",
        )
        webview.start()
        return 0
    except Exception as exc:
        show_fatal_error(str(exc))
        return 1
    finally:
        if runtime_published:
            remove_runtime_descriptor()
        if server is not None:
            server.should_exit = True
        if server_thread is not None:
            server_thread.join(timeout=15)


if __name__ == "__main__":
    raise SystemExit(main())
