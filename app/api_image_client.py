from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
import mimetypes
from io import BytesIO
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from .config import Settings


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


@dataclass
class ApiGenerationResult:
    path: Path
    references_requested: int = 0
    references_attached: int = 0
    reference_warning: str = ""
    generation_warning: str = ""
    prompt_profile: str = "natural"
    requested_size: str = ""
    actual_size: str = ""


class ApiImageClient:
    """Calls one user-configured OpenAI-compatible image endpoint."""

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = settings
        self.transport = transport

    def validate_configuration(self) -> None:
        parsed = urlparse(self.settings.image_api_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("API 地址必须是有效的 http:// 或 https:// 网址")
        if not self.settings.image_api_model.strip():
            raise ValueError("请填写生图模型名称")
        if not self.settings.image_api_key.strip():
            raise ValueError("请先保存 API Key")
        if self.settings.image_api_protocol not in {"images", "responses"}:
            raise ValueError("不支持的 API 协议")

    async def test_connection(self) -> str:
        self.validate_configuration()
        async with self._client() as client:
            response = await client.get(self._endpoint("models"))
            if response.status_code in {404, 405}:
                return f"{self.settings.image_api_name} 地址可达；节点不提供模型列表，将在首次生成时验证 Key"
            self._raise_for_status(response)
        return f"{self.settings.image_api_name} 连接成功"

    async def generate(
        self,
        prompt: str,
        project_id: str,
        reference_paths: list[Path] | None = None,
        aspect_ratio: str = "Auto",
        resolution: str = "Auto",
        negative_prompt: str = "",
        style_prompt: str = "",
        style_negative_prompt: str = "",
    ) -> ApiGenerationResult:
        self.validate_configuration()
        reference_paths = [path for path in (reference_paths or []) if path.is_file()]
        protocol = self.settings.image_api_protocol
        prompt_profile = self.resolved_prompt_profile()
        if prompt_profile == "nai":
            # Rich project context is kept for editing. The two final NAI prompt
            # fields are the complete generation contract and must not be expanded.
            compiled_prompt, embedded_negative = self._compile_nai_prompt(prompt, "", "")
            compiled_negative = self._flatten_nai_tags([embedded_negative, negative_prompt])
        else:
            compiled_prompt, compiled_negative = self.compile_prompt(
                prompt,
                style_prompt,
                style_negative_prompt,
            )
        if prompt_profile == "nai" and (CJK_RE.search(compiled_prompt) or CJK_RE.search(compiled_negative)):
            raise ValueError("NAI 项目的最终正负提示词必须全部使用英文；请检查镜头与艺术指导字段")
        if protocol == "responses":
            if prompt_profile == "nai" and compiled_negative:
                compiled_prompt = f"{compiled_prompt}\nundesired content: {compiled_negative}"
            requested_size = self._pixel_size(aspect_ratio, resolution)
            payload = self._responses_payload(compiled_prompt, reference_paths, requested_size)
            endpoint = self._endpoint("responses")
            attached = len(reference_paths)
            warning = ""
        else:
            payload = self._images_payload(
                compiled_prompt,
                aspect_ratio,
                resolution,
                negative_prompt=compiled_negative,
                prompt_profile=prompt_profile,
            )
            endpoint = self._endpoint("images/generations")
            attached = 0
            warning = (
                f"当前 Images / 仅文字协议不支持图片输入，已保留画风与角色的文字设定，"
                f"但未发送 {len(reference_paths)} 张画风、角色或场景参考图"
                if reference_paths
                else ""
            )
            requested_size = str(payload.get("size") or "")

        async with self._client() as client:
            response = await client.post(endpoint, json=payload)
            self._raise_for_status(response)
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("API 没有返回有效 JSON") from exc
            image_value = self._find_image_value(body)
            if image_value is None:
                raise RuntimeError("API 返回成功，但响应中没有可识别的图片 URL 或 Base64 数据")
            content, mime_type = await self._read_image_value(client, image_value)

        actual_size = self._image_dimensions(content)
        generation_warning = self._dimension_warning(aspect_ratio, requested_size, actual_size)
        output = self._save(content, mime_type, project_id)
        return ApiGenerationResult(
            path=output,
            references_requested=len(reference_paths),
            references_attached=attached,
            reference_warning=warning,
            generation_warning=generation_warning,
            prompt_profile=prompt_profile,
            requested_size=requested_size,
            actual_size=actual_size,
        )

    def resolved_prompt_profile(self) -> str:
        configured = self.settings.image_api_prompt_profile
        if configured != "auto":
            return configured
        model = self.settings.image_api_model.lower()
        if re.search(r"(?:^|[^a-z0-9])(?:nai|novel[-_ ]?ai)(?:$|[^a-z0-9])", model):
            return "nai"
        return "natural"

    def compile_prompt(
        self,
        prompt: str,
        style_prompt: str = "",
        style_negative_prompt: str = "",
    ) -> tuple[str, str]:
        """Compile the portable director prompt for the configured model family."""

        if self.resolved_prompt_profile() == "nai":
            return self._compile_nai_prompt(prompt, style_prompt, style_negative_prompt)
        return self._compile_natural_prompt(prompt, style_prompt, style_negative_prompt), ""

    @staticmethod
    def _compile_natural_prompt(prompt: str, style_prompt: str, negative_prompt: str) -> str:
        if not style_prompt.strip() and not negative_prompt.strip():
            return prompt.strip()
        sections: list[str] = []
        if style_prompt.strip():
            sections.append(
                "[RENDERING MEDIUM - HIGHEST PRIORITY]\n"
                "必须是完成度高的纯二维日漫插画，不是真人摄影、仿真人剧照、照片化数字绘画或三维渲染。"
                "自然仅指人体比例、透视和环境逻辑可信，绝不授权照片化脸部或真人皮肤质感。"
                "人物必须具有清晰手绘二维描线、干净平面色块和清楚的硬边赛璐璐阴影；"
                "不得使用照片化真人面孔、深法令纹、重眼窝或皮肤毛孔，不得使用连续柔和明暗塑造脸部体积。\n"
                f"{style_prompt.strip()}"
            )
        if prompt.strip():
            sections.append(f"[SHOT CONTENT]\n{prompt.strip()}")
        if negative_prompt.strip():
            sections.append(
                "[STRICT EXCLUSIONS]\n"
                "以下项目是硬性禁止项，不得以风格化、电影感或照片化细节为理由忽略：\n"
                f"{negative_prompt.strip()}"
            )
        return "\n\n".join(section for section in sections if section)

    @classmethod
    def _compile_nai_prompt(
        cls,
        prompt: str,
        style_prompt: str,
        style_negative_prompt: str,
    ) -> tuple[str, str]:
        embedded_negative: list[str] = []
        groups: dict[str, list[str]] = {
            "quality": [],
            "cast": [],
            "character": [],
            "action": [],
            "camera": [],
            "scene": [],
            "lighting": [],
            "style": [],
            "detail": [],
        }
        current_character = ""
        metadata_headings = {
            "characters in frame",
            "identity separation",
            "output format",
            "reference image mapping",
            "reference rule",
        }
        for raw_line in prompt.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            negative_match = re.match(r"^\[negative prompt\]\s*(.*)$", line, re.IGNORECASE)
            if negative_match:
                if negative_match.group(1).strip():
                    embedded_negative.append(negative_match.group(1).strip())
                continue
            heading_match = re.match(r"^\[([^]]+)\]\s*(.*)$", line)
            if heading_match:
                raw_heading = heading_match.group(1).strip()
                heading = raw_heading.lower()
                remainder = heading_match.group(2).strip()
                character_match = re.match(r"character\s+\d+\s*:\s*[^/]+/\s*(.+)", raw_heading, re.IGNORECASE)
                if character_match:
                    current_character = character_match.group(1).strip()
                    continue
                if heading == "characters in frame":
                    count_match = re.match(r"(\d+)", remainder)
                    if count_match:
                        count = int(count_match.group(1))
                        groups["cast"].append("1person" if count == 1 else f"{count}people")
                    continue
                if heading == "camera":
                    groups["camera"].append(cls._normalize_nai_camera(remainder))
                    continue
                if heading in metadata_headings:
                    continue
                line = remainder

            field_match = re.match(r"^([^:]+):\s*(.*)$", line)
            if field_match:
                field = field_match.group(1).strip().lower()
                value = field_match.group(2).strip()
                if not value:
                    continue
                if field in {"identity", "appearance lock", "costume lock"}:
                    groups["character"].append(cls._with_character(current_character, value))
                elif field == "position and orientation":
                    groups["character"].append(cls._with_character(current_character, value))
                elif field in {"individual action", "expression and eye line"}:
                    groups["action"].append(cls._with_character(current_character, value))
                elif field in {"interaction and shared event", "overall mood", "shot intent"}:
                    groups["action"].append(value)
                elif field in {
                    "scene / time", "world name", "era", "country / region", "city / location",
                    "geography", "technology", "magic system", "history", "factions",
                    "rules / taboos", "core conflict", "weather", "time rules",
                    "materials / environment",
                }:
                    groups["scene"].append(value)
                elif field == "lighting":
                    groups["lighting"].append(value)
                elif field in {"style", "visual palette"}:
                    groups["style"].append(value)
                else:
                    groups["detail"].append(value)
                continue

            target = "quality" if re.search(r"masterpiece|best quality|high quality|absurdres|very aesthetic", line, re.IGNORECASE) else "detail"
            groups[target].append(line)

        groups["style"].append(style_prompt.strip())
        ordered = [
            *groups["quality"], *groups["cast"], *groups["character"], *groups["action"],
            *groups["camera"], *groups["scene"], *groups["lighting"], *groups["style"],
            *groups["detail"],
        ]
        positive = cls._flatten_nai_tags(ordered)
        negative = cls._flatten_nai_tags([*embedded_negative, style_negative_prompt])
        return positive, negative

    @staticmethod
    def _with_character(character: str, value: str) -> str:
        grouped_value = re.sub(r"\s*[,，]\s*", " and ", value)
        # Chinese project labels are useful in the editor but must not leak into NAI text.
        if character and not CJK_RE.search(character):
            return f"{character}: {grouped_value}"
        return grouped_value

    @staticmethod
    def _normalize_nai_camera(value: str) -> str:
        aliases = {
            "extreme wide shot": "extreme wide shot",
            "wide shot": "wide shot",
            "full shot": "full body",
            "medium shot": "medium shot",
            "close up": "close-up",
            "extreme close up": "extreme close-up",
            "eye level": "eye level",
            "high angle": "from above",
            "low angle": "from below",
            "overhead": "directly above",
            "front view": "front view",
            "side view": "from side",
            "rear view": "from behind",
            "dutch angle": "dutch angle",
        }
        tags = []
        for item in re.split(r"[,，]", value):
            normalized = item.strip().lower()
            if not normalized or normalized in {"static", "none", "auto"}:
                continue
            tags.append(aliases.get(normalized, normalized))
        return ", ".join(tags)

    @staticmethod
    def _flatten_nai_tags(values: list[str]) -> str:
        tags: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = re.sub(r"\[[^]]+\]", "", str(value or ""))
            for tag in re.split(r"[,，;；\n]+", cleaned):
                normalized = " ".join(tag.strip().split()).strip(" .")
                key = normalized.casefold()
                if normalized and key not in seen:
                    seen.add(key)
                    tags.append(normalized)
        return ", ".join(tags)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.settings.image_api_key}",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(self.settings.image_api_timeout_seconds),
            follow_redirects=True,
            transport=self.transport,
        )

    def _endpoint(self, suffix: str) -> str:
        base = self._api_root()
        normalized_suffix = suffix.strip("/")
        if base.endswith(f"/{normalized_suffix}"):
            return base
        return f"{base}/{normalized_suffix}"

    def _api_root(self) -> str:
        base = self.settings.image_api_base_url.rstrip("/")
        for endpoint in ("/images/generations", "/responses", "/models"):
            if base.endswith(endpoint):
                return base[: -len(endpoint)].rstrip("/")
        return base

    def _images_payload(
        self,
        prompt: str,
        aspect_ratio: str,
        resolution: str,
        *,
        negative_prompt: str = "",
        prompt_profile: str = "natural",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.settings.image_api_model,
            "prompt": prompt,
            "n": 1,
        }
        size = (
            self._nai_pixel_size(aspect_ratio, resolution)
            if prompt_profile == "nai"
            else self._pixel_size(aspect_ratio, resolution)
        )
        if size:
            payload["size"] = size
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        return payload

    def _responses_payload(self, prompt: str, reference_paths: list[Path], size: str = "") -> dict[str, Any]:
        if reference_paths:
            content: list[dict[str, str]] = [{"type": "input_text", "text": prompt}]
            for path in reference_paths:
                mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
                encoded = base64.b64encode(path.read_bytes()).decode("ascii")
                content.append({"type": "input_image", "image_url": f"data:{mime_type};base64,{encoded}"})
            model_input: Any = [{"role": "user", "content": content}]
        else:
            model_input = prompt
        image_tool: dict[str, Any] = {"type": "image_generation"}
        if size:
            image_tool["size"] = size
        return {
            "model": self.settings.image_api_model,
            "input": model_input,
            "tools": [image_tool],
        }

    @staticmethod
    def _pixel_size(aspect_ratio: str, resolution: str) -> str:
        long_edge = {"1K": 1024, "2K": 2048, "4K": 4096}.get(resolution, 1024)
        if ":" not in aspect_ratio:
            return ""
        try:
            ratio_width, ratio_height = (int(part) for part in aspect_ratio.split(":", 1))
        except ValueError:
            return ""
        if ratio_width <= 0 or ratio_height <= 0:
            return ""
        width = long_edge if ratio_width >= ratio_height else round(long_edge * ratio_width / ratio_height)
        height = long_edge if ratio_height >= ratio_width else round(long_edge * ratio_height / ratio_width)
        return f"{width}x{height}"

    @staticmethod
    def _image_dimensions(content: bytes) -> str:
        try:
            from PIL import Image

            with Image.open(BytesIO(content)) as image:
                return f"{image.width}x{image.height}"
        except (OSError, ValueError):
            return ""

    @staticmethod
    def _dimension_warning(aspect_ratio: str, requested_size: str, actual_size: str) -> str:
        ratio_match = re.fullmatch(r"(\d+):(\d+)", aspect_ratio or "")
        actual_match = re.fullmatch(r"(\d+)x(\d+)", actual_size or "")
        if not ratio_match or not actual_match:
            return ""
        expected = int(ratio_match.group(1)) / int(ratio_match.group(2))
        actual = int(actual_match.group(1)) / int(actual_match.group(2))
        if abs(actual / expected - 1) <= 0.04:
            return ""
        requested = f"，请求尺寸 {requested_size}" if requested_size else ""
        return f"返回图片比例不符：选择 {aspect_ratio}{requested}，实际 {actual_size}。结果已保留，请确认或重试"

    @staticmethod
    def _nai_pixel_size(aspect_ratio: str, resolution: str) -> str:
        long_edge = {"1K": 1024, "2K": 2048, "4K": 4096}.get(resolution, 1024)
        if ":" not in aspect_ratio:
            return f"{long_edge}x{long_edge}"
        try:
            ratio_width, ratio_height = (int(part) for part in aspect_ratio.split(":", 1))
        except ValueError:
            return f"{long_edge}x{long_edge}"
        if ratio_width <= 0 or ratio_height <= 0:
            return f"{long_edge}x{long_edge}"
        width = long_edge if ratio_width >= ratio_height else long_edge * ratio_width / ratio_height
        height = long_edge if ratio_height >= ratio_width else long_edge * ratio_height / ratio_width
        width = max(64, round(width / 64) * 64)
        height = max(64, round(height / 64) * 64)
        return f"{width}x{height}"

    @classmethod
    def _find_image_value(cls, value: Any) -> str | None:
        if isinstance(value, dict):
            for key in ("b64_json", "image_url", "url", "result"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
                if isinstance(candidate, dict):
                    nested = cls._find_image_value(candidate)
                    if nested:
                        return nested
            for key in ("data", "output", "content", "images"):
                nested = cls._find_image_value(value.get(key))
                if nested:
                    return nested
        elif isinstance(value, list):
            for item in value:
                nested = cls._find_image_value(item)
                if nested:
                    return nested
        return None

    async def _read_image_value(self, client: httpx.AsyncClient, value: str) -> tuple[bytes, str]:
        if value.startswith("data:image/"):
            header, encoded = value.split(",", 1)
            mime_type = header[5:].split(";", 1)[0]
            return base64.b64decode(encoded), mime_type
        if value.startswith(("http://", "https://")):
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.image_api_timeout_seconds),
                follow_redirects=True,
                transport=self.transport,
            ) as download_client:
                response = await download_client.get(value)
                self._raise_for_status(response)
                mime_type = response.headers.get("content-type", "").split(";", 1)[0]
                if not response.content:
                    raise RuntimeError("API 图片 URL 返回了空文件")
                return response.content, mime_type
        try:
            content = base64.b64decode(value, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise RuntimeError("API 返回的图片数据既不是 URL，也不是有效 Base64") from exc
        if not content:
            raise RuntimeError("API 返回了空图片")
        return content, ""

    def _save(self, content: bytes, mime_type: str, project_id: str) -> Path:
        suffix = self._image_suffix(mime_type, content)
        output = self.settings.image_dir / project_id / "generated" / f"{uuid4().hex}{suffix}"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)
        return output

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
        raise RuntimeError("API 返回的内容不是可识别的图片格式")

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.is_success:
            return
        detail = ""
        try:
            body = response.json()
            if isinstance(body, dict):
                error = body.get("error")
                if isinstance(error, dict):
                    detail = str(error.get("message") or error.get("code") or "")
                detail = detail or str(body.get("detail") or body.get("message") or "")
        except ValueError:
            detail = response.text[:300]
        if response.status_code == 403 and "TOKEN_PER_REQUEST_GEMS_LIMIT_EXCEEDED" in detail:
            raise RuntimeError(
                "单次生成额度超限：当前请求的提示词、参考图或生成规格超过节点允许的 Gems 上限。"
                "请精简提示词、减少参考图，或降低输出规格后重试"
            )
        suffix = f"：{detail[:500]}" if detail else ""
        raise RuntimeError(f"生图 API 返回 HTTP {response.status_code}{suffix}")
