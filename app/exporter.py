from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from typing import Any, Callable
from urllib.parse import unquote, urlparse
import zipfile

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .bubble_packs import BubblePackLibrary
from .storage import safe_child


class ExportError(ValueError):
    pass


@dataclass(frozen=True)
class ExportOptions:
    format: str
    include_lettering: bool = True
    width: int = 1080
    gap: int = 24
    frame_duration_seconds: float = 3.0
    shot_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExportArtifact:
    path: Path
    media_type: str
    filename: str


FORMATS = {"png_bundle", "vertical_comic", "pdf", "video"}
POSITION_ANCHORS = {
    "top-left": (0.04, 0.04),
    "top-right": (0.58, 0.04),
    "left": (0.04, 0.34),
    "right": (0.58, 0.34),
    "bottom": (0.29, 0.68),
}


def automatic_lettering_width(text: str, semantic: str = "dialogue") -> float:
    length = len(re.sub(r"\s+", "", text))
    if semantic == "thought":
        return 0.22 if length <= 8 else 0.24 if length <= 16 else 0.30
    if length <= 8:
        return 0.24
    if length <= 16:
        return 0.30
    return 0.36


def normalized_lettering_layout(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    def number(key: str, fallback: float) -> float:
        try:
            candidate = float(value.get(key, fallback))
        except (TypeError, ValueError):
            return fallback
        return candidate if candidate == candidate else fallback

    width = min(0.48, max(0.14, number("width", 0.24)))
    x = min(1.0 - width, max(0.0, number("x", 0.04)))
    y = min(0.92, max(0.0, number("y", 0.04)))
    font_scale = min(1.4, max(0.6, number("fontScale", number("font_scale", 1))))
    rotation = min(180.0, max(-180.0, number("rotation", 0)))
    return {"x": x, "y": y, "width": width, "flip": bool(value.get("flip", False)), "fontScale": font_scale, "rotation": rotation}


def export_project(
    project: dict[str, Any],
    image_root: Path,
    bubble_library: BubblePackLibrary,
    options: ExportOptions,
    lettering_asset_resolver: Callable[[str], Path | None] | None = None,
) -> ExportArtifact:
    if options.format not in FORMATS:
        raise ExportError("不支持的导出格式")
    all_shots = (project.get("state") or {}).get("shots") or []
    if not all_shots:
        raise ExportError("当前项目没有可导出的镜头")
    if options.shot_ids:
        requested = set(options.shot_ids)
        known = {str(shot.get("id") or "") for shot in all_shots}
        unknown = [shot_id for shot_id in options.shot_ids if shot_id not in known]
        if unknown:
            raise ExportError(f"所选镜头不存在：{', '.join(dict.fromkeys(unknown))}")
        shots = [shot for shot in all_shots if str(shot.get("id") or "") in requested]
    else:
        shots = all_shots
    if not shots:
        raise ExportError("请至少选择一个要导出的镜头")

    missing: list[str] = []
    sources: list[Path] = []
    for shot in shots:
        shot_id = str(shot.get("id") or "未编号镜头")
        image_url = str((shot.get("content") or {}).get("lastImage") or "").strip()
        try:
            source = resolve_generated_image(image_root, image_url, project_id=str(project.get("id") or ""))
        except ExportError:
            missing.append(shot_id)
            continue
        if not source.is_file():
            missing.append(shot_id)
            continue
        sources.append(source)
    if missing:
        raise ExportError(f"以下镜头缺少可用成图：{', '.join(missing)}")

    project_id = str(project.get("id") or "project")
    output_dir = safe_child(image_root, project_id, "exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(str(project.get("name") or project_id))
    panels = [
        compose_panel(
            source,
            shot,
            project,
            bubble_library,
            options.include_lettering,
            lettering_asset_resolver,
        )
        for source, shot in zip(sources, shots)
    ]
    try:
        if options.format == "png_bundle":
            path = output_dir / f"{stem}-分镜PNG.zip"
            write_png_bundle(path, panels, shots, project)
            return ExportArtifact(path, "application/zip", path.name)
        if options.format == "vertical_comic":
            path = output_dir / f"{stem}-竖版长图.png"
            write_vertical_comic(path, panels, options.width, options.gap, shots)
            return ExportArtifact(path, "image/png", path.name)
        if options.format == "pdf":
            path = output_dir / f"{stem}-分镜.pdf"
            write_pdf(path, panels)
            return ExportArtifact(path, "application/pdf", path.name)
        path = output_dir / f"{stem}-推漫.mp4"
        write_video(path, panels, options.width, options.frame_duration_seconds)
        return ExportArtifact(path, "video/mp4", path.name)
    finally:
        for panel in panels:
            panel.close()


def resolve_generated_image(image_root: Path, image_url: str, project_id: str) -> Path:
    parsed = urlparse(image_url)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise ExportError("镜头图片地址不是本地生成图")
    prefix = "/images/"
    if not parsed.path.startswith(prefix):
        raise ExportError("镜头图片地址不是本地生成图")
    parts = Path(unquote(parsed.path[len(prefix):])).parts
    if len(parts) < 3 or parts[0] != project_id or parts[1] != "generated":
        raise ExportError("镜头图片地址无效")
    try:
        return safe_child(image_root, *parts)
    except ValueError as exc:
        raise ExportError("镜头图片地址无效") from exc


def compose_panel(
    source: Path,
    shot: dict[str, Any],
    project: dict[str, Any],
    bubble_library: BubblePackLibrary,
    include_lettering: bool,
    lettering_asset_resolver: Callable[[str], Path | None] | None = None,
) -> Image.Image:
    try:
        with Image.open(source) as opened:
            panel = ImageOps.exif_transpose(opened).convert("RGBA")
    except (OSError, ValueError) as exc:
        raise ExportError(f"无法读取镜头图片：{shot.get('id', source.name)}") from exc
    blocks = [
        item for item in (shot.get("postText") or [])
        if str(item.get("text") or "").strip() and not bool(item.get("hidden", False))
    ]
    if not include_lettering or not blocks:
        return panel

    lettering = (project.get("state") or {}).get("lettering") or {}
    pack_id = str(lettering.get("bubblePackId") or "jp-clean-v1")
    pack = bubble_library.get_pack(pack_id)
    has_image_blocks = any(str(item.get("elementType") or "") != "text" for item in blocks)
    if pack is None and has_image_blocks:
        panel.close()
        raise ExportError(f"项目选择的气泡包不存在：{pack_id}")
    defaults = (pack or {}).get("semantic_defaults") or {}
    offsets: dict[str, int] = {}
    for block in blocks:
        if str(block.get("elementType") or "") == "text":
            place_text_element(
                panel,
                str(block.get("text") or "").strip(),
                block.get("position"),
                offsets.get(str(block.get("position") or "top-left"), 0),
                layout=block.get("layout"),
                font_scale=float((block.get("layout") or {}).get("fontScale", (block.get("layout") or {}).get("font_scale", 1)) or 1),
            )
            position = str(block.get("position") or "top-left")
            offsets[position] = offsets.get(position, 0) + 1
            continue
        position = str(block.get("position") or "top-right")
        custom_reference_id = str(block.get("bubbleReferenceId") or "")
        asset_id = str(block.get("bubbleAssetId") or defaults.get(block.get("bubbleSemantic") or block.get("kind") or "dialogue") or "")
        if custom_reference_id:
            asset_path = lettering_asset_resolver(custom_reference_id) if lettering_asset_resolver else None
            if asset_path is None or not asset_path.is_file():
                panel.close()
                raise ExportError(f"镜头 {shot.get('id', '')} 的自定义气泡不存在")
            asset = {"semantic_type": "dialogue"}
        elif not asset_id:
            panel.close()
            raise ExportError(f"镜头 {shot.get('id', '')} 的文字没有可用气泡")
        else:
            asset = next((item for item in (pack.get("assets") or []) if str(item.get("id") or "") == asset_id), None)
            if asset is None:
                panel.close()
                raise ExportError(f"镜头 {shot.get('id', '')} 选择的气泡不存在：{asset_id}")
            asset_path = bubble_library.asset_path(pack_id, asset_id)
        offset = offsets.get(position, 0)
        place_lettering(
            panel,
            asset_path,
            str(block.get("text") or "").strip(),
            position,
            offset,
            layout=block.get("layout"),
            font_scale=float((block.get("layout") or {}).get("fontScale", (block.get("layout") or {}).get("font_scale", 1)) or 1),
            semantic=str(block.get("bubbleSemantic") or block.get("kind") or "dialogue"),
            add_light_backing=str(asset.get("semantic_type") or "") == "thought",
        )
        offsets[position] = offset + 1
    return panel


def place_text_element(
    panel: Image.Image,
    text: str,
    position: str,
    offset: int,
    layout: Any = None,
    font_scale: float = 1.0,
) -> None:
    """Draw a free text box without requiring or compositing a bubble image."""
    panel_width, panel_height = panel.size
    custom = normalized_lettering_layout(layout)
    width_ratio = custom["width"] if custom else automatic_lettering_width(text, "narration")
    box_width = min(max(48, int(panel_width * width_ratio)), int(panel_width * 0.72))
    # Text boxes need a real vertical budget even on short landscape panels;
    # otherwise fit_text's inner safety area can be smaller than one glyph line.
    box_height = min(max(96, int(panel_height * 0.42)), max(96, panel_height))
    font, lines = fit_text(text, box_width, box_height, font_scale=font_scale)
    layer = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    spacing = max(3, int(font.size * 0.2))
    boxes = [draw.textbbox((0, 0), line, font=font, stroke_width=0) for line in lines]
    heights = [box[3] - box[1] for box in boxes]
    total_height = sum(heights) + spacing * max(0, len(lines) - 1)
    cursor_y = max(0, (box_height - total_height) // 2)
    for line, box, line_height in zip(lines, boxes, heights):
        line_width = box[2] - box[0]
        x = max(0, (box_width - line_width) // 2)
        draw.text((x, cursor_y), line, font=font, fill=(255, 255, 255, 255), stroke_width=max(1, font.size // 14), stroke_fill=(12, 18, 26, 230))
        cursor_y += line_height + spacing
    if custom:
        x = int(panel_width * custom["x"])
        y = int(panel_height * custom["y"])
        rotation = custom["rotation"]
    else:
        anchor = POSITION_ANCHORS.get(position, POSITION_ANCHORS["top-left"])
        x = int(panel_width * anchor[0])
        y = int(panel_height * anchor[1]) + offset * max(36, int(box_height * 0.62))
        rotation = 0
    if rotation:
        rotated = layer.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)
        layer.close()
        layer = rotated
        x -= (layer.width - box_width) // 2
        y -= (layer.height - box_height) // 2
    x = min(max(0, x), max(0, panel_width - layer.width))
    y = min(max(0, y), max(0, panel_height - layer.height))
    panel.alpha_composite(layer, (x, y))
    layer.close()


def place_lettering(
    panel: Image.Image,
    asset_path: Path,
    text: str,
    position: str,
    offset: int,
    layout: Any = None,
    font_scale: float = 1.0,
    semantic: str = "dialogue",
    add_light_backing: bool = False,
) -> None:
    panel_width, panel_height = panel.size
    custom = normalized_lettering_layout(layout)
    width_ratio = custom["width"] if custom else automatic_lettering_width(text, semantic)
    bubble_width = min(max(48, int(panel_width * width_ratio)), int(panel_width * 0.48))
    with Image.open(asset_path) as opened:
        bubble = opened.convert("RGBA")
    ratio = bubble_width / bubble.width
    bubble = bubble.resize((bubble_width, max(1, int(bubble.height * ratio))), Image.Resampling.LANCZOS)
    original_size = bubble.size
    if add_light_backing:
        backing = Image.new("RGBA", bubble.size, (0, 0, 0, 0))
        inset_x = int(bubble.width * 0.08)
        inset_y = int(bubble.height * 0.04)
        ImageDraw.Draw(backing).ellipse(
            (inset_x, inset_y, bubble.width - inset_x, int(bubble.height * 0.91)),
            fill=(255, 255, 255, 238),
        )
        backing.alpha_composite(bubble)
        bubble.close()
        bubble = backing
    if custom and custom["flip"]:
        bubble = ImageOps.mirror(bubble)
    if custom:
        x = int(panel_width * custom["x"])
        y = int(panel_height * custom["y"])
    else:
        anchor = POSITION_ANCHORS.get(position, POSITION_ANCHORS["top-right"])
        x_ratio = 1.0 - width_ratio - 0.08 if position in {"top-right", "right"} else anchor[0]
        if position == "bottom":
            x_ratio = (1.0 - width_ratio) / 2
        x = int(panel_width * x_ratio)
        y = int(panel_height * anchor[1]) + offset * max(36, int(bubble.height * 0.62))
    x = min(max(0, x), max(0, panel_width - bubble.width))
    if not custom:
        y = min(max(0, y), max(0, panel_height - bubble.height))

    font, lines = fit_text(text, bubble.width, bubble.height, font_scale=font_scale)
    draw = ImageDraw.Draw(bubble)
    spacing = max(3, int(font.size * 0.2))
    boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    line_heights = [box[3] - box[1] for box in boxes]
    total_height = sum(line_heights) + spacing * max(0, len(lines) - 1)
    cursor_y = (bubble.height - total_height) // 2 - int(bubble.height * 0.03)
    for line, box, line_height in zip(lines, boxes, line_heights):
        line_width = box[2] - box[0]
        draw.text(((bubble.width - line_width) // 2, cursor_y), line, font=font, fill=(18, 23, 28, 255))
        cursor_y += line_height + spacing
    rotation = custom["rotation"] if custom else 0
    if rotation:
        rotated = bubble.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)
        bubble.close()
        bubble = rotated
        x -= (bubble.width - original_size[0]) // 2
        y -= (bubble.height - original_size[1]) // 2
        x = min(max(0, x), max(0, panel_width - bubble.width))
        y = min(max(0, y), max(0, panel_height - bubble.height))
    panel.alpha_composite(bubble, (x, y))
    bubble.close()


def fit_text(text: str, bubble_width: int, bubble_height: int, font_scale: float = 1.0) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    max_width = int(bubble_width * 0.58)
    max_height = int(bubble_height * 0.48)
    preferred = max(18, int(bubble_width * 0.09 * min(1.4, max(0.6, font_scale))))
    for size in range(preferred, 9, -1):
        font = load_font(size)
        lines = wrap_text(text, font, max_width)
        draw = ImageDraw.Draw(Image.new("L", (1, 1)))
        heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
        if len(lines) <= 5 and sum(heights) + max(0, len(lines) - 1) * int(size * 0.2) <= max_height:
            return font, lines
    raise ExportError(f"后期文字过长，无法放入气泡：{text[:18]}...")


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    lines: list[str] = []
    current = ""
    for char in text.replace("\r", "").replace("\n", "\n"):
        if char == "\n":
            if current:
                lines.append(current)
                current = ""
            continue
        candidate = current + char
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.truetype("DejaVuSans.ttf", size=size)


def normalized_panel(panel: Image.Image, width: int) -> Image.Image:
    height = max(1, round(panel.height * width / panel.width))
    return panel.resize((width, height), Image.Resampling.LANCZOS).convert("RGB")


def write_png_bundle(path: Path, panels: list[Image.Image], shots: list[dict[str, Any]], project: dict[str, Any]) -> None:
    with TemporaryDirectory(prefix="frame-png-") as temp_name:
        temp = Path(temp_name)
        files = []
        for index, (panel, shot) in enumerate(zip(panels, shots), 1):
            filename = f"{index:03d}_{safe_filename(str(shot.get('id') or 'SHOT'))}_{safe_filename(str(shot.get('title') or '镜头'))}.png"
            panel.convert("RGB").save(temp / filename, "PNG", optimize=True)
            files.append(filename)
        manifest = {
            "project_id": project.get("id"),
            "project_name": project.get("name"),
            "shot_count": len(shots),
            "files": files,
        }
        (temp / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file in [*(temp / name for name in files), temp / "manifest.json"]:
                archive.write(file, file.name)


def _bordered_panel(panel: Image.Image, border_style: str) -> Image.Image:
    color = "black" if border_style in {"solid_black_2px", "broken_panel"} else "white"
    if border_style not in {"solid_black_2px", "solid_white_2px", "broken_panel"}:
        return panel
    bordered = ImageOps.expand(panel, border=2, fill=color)
    panel.close()
    return bordered


def _vertical_rows(
    panels: list[Image.Image], shots: list[dict[str, Any]], width: int, gap: int,
) -> list[tuple[Image.Image, int]]:
    explicit_layout = any(
        isinstance(shot.get("layoutMeta"), dict) and
        ("rowIndex" in shot["layoutMeta"] or "row_index" in shot["layoutMeta"])
        for shot in shots
    )
    if not explicit_layout:
        return [
            (normalized_panel(panel, width), gap if index < len(panels) - 1 else 0)
            for index, panel in enumerate(panels)
        ]
    grouped: dict[int, list[tuple[int, Image.Image, dict[str, Any]]]] = {}
    for index, (panel, shot) in enumerate(zip(panels, shots), 1):
        layout = shot.get("layoutMeta") if isinstance(shot.get("layoutMeta"), dict) else {}
        row = max(1, int(layout.get("rowIndex", layout.get("row_index", index)) or index))
        slot = max(1, int(layout.get("slotIndex", layout.get("slot_index", 1)) or 1))
        grouped.setdefault(row, []).append((slot, panel, layout))
    rows: list[tuple[Image.Image, int]] = []
    for row_number in sorted(grouped):
        entries = sorted(grouped[row_number], key=lambda item: item[0])
        slot_width = max(1, (width - gap * (len(entries) - 1)) // len(entries))
        rendered = [
            _bordered_panel(normalized_panel(panel, slot_width), str(layout.get("borderStyle") or layout.get("border_style") or "none"))
            for _, panel, layout in entries
        ]
        row_height = max(item.height for item in rendered)
        canvas = Image.new("RGB", (width, row_height), "white")
        x = 0
        for item in rendered:
            canvas.paste(item, (x, 0))
            x += slot_width + gap
            item.close()
        gutter = max(
            int(layout.get("gutterBottom", layout.get("gutter_bottom", gap)) or 0)
            for _, _, layout in entries
        )
        rows.append((canvas, gutter))
    return rows


def write_vertical_comic(
    path: Path, panels: list[Image.Image], width: int, gap: int,
    shots: list[dict[str, Any]] | None = None,
) -> None:
    rows = _vertical_rows(panels, shots or [{} for _ in panels], width, gap)
    try:
        height = sum(panel.height + gutter for panel, gutter in rows)
        if height > 65500 or width * height > 120_000_000:
            raise ExportError("竖版长图尺寸过大，请降低输出宽度或分批导出")
        canvas = Image.new("RGB", (width, height), "white")
        y = 0
        for panel, gutter in rows:
            canvas.paste(panel, (0, y))
            y += panel.height + gutter
        canvas.save(path, "PNG", optimize=True)
        canvas.close()
    finally:
        for panel, _ in rows:
            panel.close()


def write_pdf(path: Path, panels: list[Image.Image]) -> None:
    pages = [panel.convert("RGB") for panel in panels]
    try:
        pages[0].save(path, "PDF", save_all=True, append_images=pages[1:], resolution=150.0)
    finally:
        for page in pages:
            page.close()


def write_video(path: Path, panels: list[Image.Image], width: int, duration: float) -> None:
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise ExportError("视频导出组件未安装，请重新安装或更新 FrameAnimeDesk") from exc
    video_width = min(1080, width)
    video_height = 1920
    with TemporaryDirectory(prefix="frame-video-") as temp_name:
        temp = Path(temp_name)
        concat_lines: list[str] = []
        for index, panel in enumerate(panels):
            frame = Image.new("RGB", (video_width, video_height), (12, 18, 22))
            fitted = ImageOps.contain(panel.convert("RGB"), (video_width, video_height), Image.Resampling.LANCZOS)
            frame.paste(fitted, ((video_width - fitted.width) // 2, (video_height - fitted.height) // 2))
            frame_path = temp / f"frame-{index:04d}.png"
            frame.save(frame_path, "PNG")
            frame.close()
            fitted.close()
            concat_lines.extend([f"file '{frame_path.as_posix()}'", f"duration {duration:.3f}"])
        concat_lines.append(f"file '{(temp / f'frame-{len(panels) - 1:04d}.png').as_posix()}'")
        concat_path = temp / "frames.txt"
        concat_path.write_text("\n".join(concat_lines), encoding="utf-8")
        command = [
            imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path),
            "-vf", "fps=30", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path),
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0 or not path.is_file() or path.stat().st_size == 0:
            path.unlink(missing_ok=True)
            detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "未知编码错误"
            raise ExportError(f"MP4 编码失败：{detail}")


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "-", value).strip(" .-")
    cleaned = re.sub(r"\s+", "-", cleaned)
    return (cleaned[:60] or "FrameAnimeDesk")
