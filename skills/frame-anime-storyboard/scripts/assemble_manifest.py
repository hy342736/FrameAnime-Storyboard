#!/usr/bin/env python3
"""Assemble a FrameAnimeDesk manifest from a base object and shot-array chunks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON from {path}: {exc}") from exc


def assemble(base_path: Path, chunk_paths: list[Path]) -> dict[str, Any]:
    manifest = read_json(base_path)
    if not isinstance(manifest, dict):
        raise ValueError("base JSON must be an object")
    if manifest.get("shots") not in (None, []):
        raise ValueError("base JSON shots must be omitted or empty")

    shots: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for chunk_path in chunk_paths:
        chunk = read_json(chunk_path)
        if not isinstance(chunk, list) or not chunk:
            raise ValueError(f"shot chunk must be a non-empty array: {chunk_path}")
        for index, shot in enumerate(chunk):
            if not isinstance(shot, dict):
                raise ValueError(f"shot chunk item must be an object: {chunk_path}[{index}]")
            client_id = shot.get("client_id")
            if not isinstance(client_id, str) or not client_id.strip():
                raise ValueError(f"shot client_id is required: {chunk_path}[{index}]")
            if client_id in seen_ids:
                raise ValueError(f"duplicate shot client_id: {client_id}")
            seen_ids.add(client_id)
            shots.append(shot)

    preferences = manifest.get("preferences")
    budget = preferences.get("panel_budget") if isinstance(preferences, dict) else None
    if not isinstance(budget, int) or isinstance(budget, bool):
        raise ValueError("base preferences.panel_budget must be an integer")
    if len(shots) != budget:
        raise ValueError(f"assembled shot count {len(shots)} does not match panel_budget {budget}")

    manifest["shots"] = shots
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("chunks", nargs="+", type=Path)
    args = parser.parse_args()

    manifest = assemble(args.base, args.chunks)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "shot_count": len(manifest["shots"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
