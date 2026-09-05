from dataclasses import dataclass, fields
import json
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    data_dir: Path
    mirror_url: str
    mirror_chat_url: str
    headless: bool
    browser_profile_dir: Path
    image_dir: Path
    reference_dir: Path
    generation_timeout_seconds: float
    local_api_key: str
    generation_mode: str = "mirror"
    image_api_name: str = "默认 API 节点"
    image_api_base_url: str = ""
    image_api_protocol: str = "responses"
    image_api_model: str = "gpt-image-1"
    image_api_prompt_profile: str = "auto"
    image_api_key: str = ""
    image_api_timeout_seconds: float = 240

    @property
    def persistent_file(self) -> Path:
        return self.data_dir / "settings.json"

    def public(self) -> dict[str, object]:
        return {
            "mirror_url": self.mirror_url,
            "mirror_chat_url": self.mirror_chat_url,
            "headless": self.headless,
            "browser_profile_dir": str(self.browser_profile_dir),
            "image_dir": str(self.image_dir),
            "reference_dir": str(self.reference_dir),
            "generation_timeout_seconds": self.generation_timeout_seconds,
            "generation_mode": self.generation_mode,
            "image_api_name": self.image_api_name,
            "image_api_base_url": self.image_api_base_url,
            "image_api_protocol": self.image_api_protocol,
            "image_api_model": self.image_api_model,
            "image_api_prompt_profile": self.image_api_prompt_profile,
            "image_api_timeout_seconds": self.image_api_timeout_seconds,
            "has_image_api_key": bool(self.image_api_key),
        }

    def directory_status(self) -> dict[str, object]:
        result: dict[str, object] = {"valid": True, "directories": {}}
        for key, path in (("image_dir", self.image_dir), ("reference_dir", self.reference_dir)):
            resolved = path.expanduser().resolve()
            exists = resolved.exists()
            is_directory = resolved.is_dir()
            writable = os.access(resolved, os.W_OK) if is_directory else False
            result["directories"][key] = {
                "path": str(resolved),
                "exists": exists,
                "is_directory": is_directory,
                "writable": writable,
            }
            if not (exists and is_directory and writable):
                result["valid"] = False
        return result

    def update(self, values: dict[str, object], persist: bool = True) -> None:
        if "mirror_url" in values:
            self.mirror_url = str(values["mirror_url"]).strip().rstrip("/")
        if "mirror_chat_url" in values:
            self.mirror_chat_url = str(values["mirror_chat_url"]).strip().rstrip("/")
        if "headless" in values:
            self.headless = bool(values["headless"])
        if "browser_profile_dir" in values:
            self.browser_profile_dir = Path(str(values["browser_profile_dir"]))
        if "image_dir" in values:
            self.image_dir = Path(str(values["image_dir"]))
        if "reference_dir" in values:
            self.reference_dir = Path(str(values["reference_dir"]))
        if "generation_timeout_seconds" in values:
            timeout = float(values["generation_timeout_seconds"])
            if timeout < 10 or timeout > 3600:
                raise ValueError("生图超时时间必须在 10 到 3600 秒之间")
            self.generation_timeout_seconds = timeout
        if "generation_mode" in values:
            mode = str(values["generation_mode"]).strip().lower()
            if mode not in {"mirror", "api"}:
                raise ValueError("生成模式只能是镜像站或 API")
            self.generation_mode = mode
        if "image_api_name" in values:
            self.image_api_name = str(values["image_api_name"]).strip()[:120] or "默认 API 节点"
        if "image_api_base_url" in values:
            self.image_api_base_url = str(values["image_api_base_url"]).strip().rstrip("/")
        if "image_api_protocol" in values:
            protocol = str(values["image_api_protocol"]).strip().lower()
            if protocol not in {"images", "responses"}:
                raise ValueError("API 协议只能是 Images 或 Responses")
            self.image_api_protocol = protocol
        if "image_api_model" in values:
            self.image_api_model = str(values["image_api_model"]).strip()[:160]
        if "image_api_prompt_profile" in values:
            profile = str(values["image_api_prompt_profile"]).strip().lower()
            if profile not in {"auto", "natural", "nai"}:
                raise ValueError("提示词格式只能是自动、自然语言或 NAI 标签")
            self.image_api_prompt_profile = profile
        if values.get("image_api_key"):
            self.image_api_key = str(values["image_api_key"]).strip()
        if values.get("clear_image_api_key"):
            self.image_api_key = ""
        if "image_api_timeout_seconds" in values:
            timeout = float(values["image_api_timeout_seconds"])
            if timeout < 10 or timeout > 3600:
                raise ValueError("API 请求超时必须在 10 到 3600 秒之间")
            self.image_api_timeout_seconds = timeout
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.reference_dir.mkdir(parents=True, exist_ok=True)
        if persist:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            stored = {
                key: value
                for key, value in self.public().items()
                if key not in {"browser_profile_dir", "has_image_api_key"}
            }
            stored["image_api_key"] = self.image_api_key
            self.persistent_file.write_text(json.dumps(stored, ensure_ascii=False, indent=2), encoding="utf-8")


def load_settings() -> Settings:
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    settings = Settings(
        data_dir=data_dir,
        mirror_url=os.getenv("MIRROR_URL", "").strip().rstrip("/"),
        mirror_chat_url=os.getenv("MIRROR_CHAT_URL", "").strip().rstrip("/"),
        headless=_as_bool(os.getenv("HEADLESS"), False),
        browser_profile_dir=Path(os.getenv("BROWSER_PROFILE_DIR", ".browser-profile")),
        image_dir=Path(os.getenv("IMAGE_DIR", "data/generated")),
        reference_dir=Path(os.getenv("REFERENCE_DIR", "data/references")),
        generation_timeout_seconds=float(os.getenv("GENERATION_TIMEOUT_SECONDS", "600")),
        local_api_key=os.getenv("LOCAL_API_KEY", ""),
        generation_mode=os.getenv("GENERATION_MODE", "mirror"),
        image_api_name=os.getenv("IMAGE_API_NAME", "默认 API 节点"),
        image_api_base_url=os.getenv("IMAGE_API_BASE_URL", "").strip().rstrip("/"),
        image_api_protocol=os.getenv("IMAGE_API_PROTOCOL", "responses"),
        image_api_model=os.getenv("IMAGE_API_MODEL", "gpt-image-1"),
        image_api_prompt_profile=os.getenv("IMAGE_API_PROMPT_PROFILE", "auto"),
        image_api_key=os.getenv("IMAGE_API_KEY", ""),
        image_api_timeout_seconds=float(os.getenv("IMAGE_API_TIMEOUT_SECONDS", "240")),
    )
    settings_file = settings.persistent_file
    if settings_file.is_file():
        try:
            stored = json.loads(settings_file.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                settings.update(stored, persist=False)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    settings.image_dir.mkdir(parents=True, exist_ok=True)
    settings.reference_dir.mkdir(parents=True, exist_ok=True)
    return settings
