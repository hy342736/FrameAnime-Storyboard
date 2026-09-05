# FrameAnimeDesk Storyboard Import Contract

Read this reference before constructing a manifest, importing a new project, appending a batch, revising shots, or uploading a user-provided reference.

## Runtime

The production target is the installed FrameAnimeDesk desktop application. Its port is dynamic. The desktop launcher atomically publishes `%LOCALAPPDATA%\FrameAnimeDesk\runtime.json` (or `%FRAME_ANIME_DESK_HOME%\runtime.json`) while it is running and removes its own descriptor on exit.

The client resolves the application in this order: explicit `--base-url`, `FRAME_ANIME_DESK_URL`, the runtime descriptor, then a verified loopback scan of ports 8000-8039. Every candidate must pass both `/health` and the application identity/capability check. Do not ask the user to discover or enter the desktop port during normal use. `--base-url` is a troubleshooting override only. Pass an optional local API key with `--api-key` or `FRAME_ANIME_DESK_API_KEY`.

Check the runtime before mutation:

```powershell
python <skill-directory>/scripts/frame_anime_client.py discover
python <skill-directory>/scripts/frame_anime_client.py doctor
```

Required capability response:

```json
{
  "app_name": "FrameAnimeDesk",
  "app_version": "0.3.0",
  "runtime_mode": "desktop",
  "storyboard_import": true,
  "storyboard_import_protocol_version": 1,
  "storyboard_import_max_shots": 50,
  "schema_versions": [1],
  "project_revision": true,
  "deep_link": true,
  "style_packs": true,
  "custom_style_packs": true,
  "bubble_packs": true,
  "generation": {
    "mode": "api",
    "channel": "User-configured API name",
    "model": "nai-diffusion-5-curated",
    "protocol": "images",
    "prompt_profile": "nai",
    "configured_prompt_profile": "auto",
    "supports_reference_images": false
  }
}
```

`generation.prompt_profile` is the application's resolved provider dialect. It may propose the type of a new project only when the user has not explicitly chosen a route. An explicit user request for GPT, GPT version, GPT path, or natural-language prompts takes precedence over the configured model/profile and sets `preferences.prompt_profile` to `natural`; an explicit NAI/NovelAI/tag-prompt request sets it to `nai`. The model name is transport/provider metadata and must not silently change the user's requested prompt route. Every created project persists its own `preferences.prompt_profile` as `promptProfile`: `natural` or `nai`. Continuation and targeted revision inherit that value. If the configured provider dialect conflicts with the project, report the conflict rather than translating or overwriting project content; a new project is required to change routes.

Mutation commands repeat this preflight automatically. If the installed desktop runtime identity, minimum application version, protocol version 1, schema version 1, revision protection, or deep-link support is absent, do not fall back to a source-mode development server, editing storage, or replacing the whole project state.

## Endpoints

```text
GET   /api/import/storyboard/capabilities
POST  /api/import/storyboard/projects
POST  /api/import/storyboard/projects/{project_id}/append
PATCH /api/import/storyboard/projects/{project_id}/shots/{shot_id}
```

The existing endpoints remain the read/reference surface:

```text
GET  /api/projects
GET  /api/projects/{project_id}
POST /api/projects/{project_id}/references
GET  /api/style-packs
GET  /api/bubble-packs
POST /api/style-packs/custom
```

New-project import and append must be atomic. Append and revision must reject stale `expected_revision` values with HTTP 409. A rejected request leaves the project unchanged.

## Manifest Version 1

Use snake_case on the import boundary. The server maps it to FrameAnimeDesk's internal state.

`preferences.panel_budget` is required and is the exact panel count the Agent recommended from the source analysis and the user confirmed for this batch. There is no default. The manifest's `shots` array must contain exactly that many meaningful shots. Each batch is limited to 1-50 shots; 50 is a technical ceiling, not a target. Represent a larger approved adaptation as multiple confirmed batches.

The template uses a non-numeric placeholder deliberately. Replace it with the confirmed integer before validation; never copy an example count as the Agent's decision.

```jsonc
{
  "schema_version": 1,
  "project": {
    "name": "Project title",
    "description": "Short local project description"
  },
  "preferences": {
    "prompt_profile": "natural",
    "format": "vertical_comic",
    "panel_budget": <confirmed-panel-count>,
    "adaptation_mode": "faithful",
    "character_mode": "user",
    "style_mode": "color_anime",
    "style_pack_id": "modern-seinen-v1",
    "style_prompt": "Clean color anime illustration, readable silhouettes",
    "style_negative_prompt": "readable text, watermark",
    "style_analysis": {
      "linework": "Clean continuous 2D linework",
      "character_rendering": "Natural adult anime proportions",
      "coloring": "Two-level cel shading",
      "background": "Detailed modern city backgrounds",
      "palette_lighting": "Muted blue-gray with restrained warm light",
      "composition": "Cinematic medium and environmental shots",
      "exclusions": "No photorealism, 3D render, text, or watermark"
    },
    "bubble_pack_id": "jp-clean-v1"
  },
  "source_batch": {
    "batch_id": "BATCH-001",
    "source_title": "Optional source title",
    "source_file": "story.txt",
    "selected_text": "Only the confirmed contiguous source selection",
    "start_quote": "Exact opening sentence",
    "end_quote": "Exact closing sentence",
    "char_count": 46
  },
  "world": {
    "name": "",
    "era": "",
    "country": "",
    "city": "",
    "geography": "",
    "technology": "",
    "magic": "",
    "history": "",
    "factions": "",
    "rules": "",
    "conflict": "",
    "weather": "",
    "time": "",
    "visual": "",
    "materials": ""
  },
  "characters": [
    {
      "client_id": "CHR-001",
      "name": "Character name",
      "role": "",
      "faction": "",
      "personality": "",
      "appearance": "",
      "costume": "",
      "signature": "",
      "source_facts": ["Explicit fact from the selected text"],
      "ai_supplements": [],
      "needs_user_input": ["Add a front-view character reference"],
      "reference_requests": ["Character design reference"]
    }
  ],
  "shots": [
    {
      "client_id": "SHOT-001",
      "type": "Medium Shot",
      "title": "Short shot title",
      "description": "One visual beat",
      "characters": ["CHR-001"],
      "character_directions": {
        "CHR-001": {
          "costume": "one resolved current-scene outfit, not alternatives",
          "position": "frame left",
          "action": "holds the unopened letter",
          "expression": "restrained worry"
        }
      },
      "visual": {
        "camera_angle": "Eye Level",
        "dynamic_expression": "still",
        "aspect_ratio": "3:4",
        "resolution": "Auto",
        "prompt": "Visual intent without literal dialogue text",
        "scene": "location / time / local weather",
        "action": "shared event and interaction",
        "expression": "overall emotional atmosphere",
        "lighting": "lighting design",
        "style": "style constraints"
      },
      "layout_meta": {
        "row_index": 1,
        "slot_index": 1,
        "gutter_bottom": 120,
        "border_style": "solid_black_2px",
        "inset_config": null
      },
      "source": {
        "anchor": "Only the confirmed contiguous source selection",
        "adaptation_kind": "direct"
      },
      "post_text": [
        {
          "kind": "dialogue",
          "text": "Short exact dialogue",
          "speaker_id": "CHR-001",
          "position": "top-right",
          "style": "speech",
          "bubble_semantic": "dialogue",
          "bubble_asset_id": ""
        }
      ],
      "text_safe_areas": ["top-right"],
      "warnings": []
    }
  ],
  "checklist": [
    {
      "kind": "character_reference",
      "owner_client_id": "CHR-001",
      "message": "Upload a front-view identity reference in the character library",
      "blocking": false
    }
  ]
}
```

`visual.camera_angle` must be `Eye Level`, `Low Angle`, `High Angle`, `POV`, or `Over Shoulder`. `visual.dynamic_expression` must be `still`, `action_peak`, `speed_lines`, `motion_blur`, `follow_composition`, or `impact_composition`. For a vertical batch of 8 or more shots, the Skill client rejects fewer than 50% non-`still` expressions, fewer than two camera angles, or a run of more than four identical angles.

Multi-panel layout is decided only by the Agent-authored English final prompt, not by an application selector or automatic prompt composer. Follow [multi-panel-prompt-formula.md](multi-panel-prompt-formula.md) when one generated image contains multiple panels. The client recognizes multi-panel prompt markers and requires: an exact `N-panel` count; `featuring the same character across all panels:` plus fixed appearance and costume; every `Panel N` with an explicit parenthesized position; visual style and clean gutter/border control; `clean panels, no text, no gibberish speech bubbles`; and an aspect-ratio parameter at the end. That final ratio must match an explicit non-`Auto` `visual.aspect_ratio`. FrameAnimeDesk sends a recognized contract without appending ordinary project-style text, so the Agent must include the complete visual style in layer four; selected style reference images may still be attached. The legacy `visual.panel_layout` and `visual.panel_beats` fields remain accepted for backward compatibility but do not determine, rewrite, or validate the final layout.

`layout_meta` is the separate chapter compositor contract. It is optional for legacy manifests and should be supplied by new storyboard imports. `row_index` is the vertical reading row, `slot_index` is the slot within that row (1-3), and `gutter_bottom` is the intended vertical breathing space in compositor pixels. `border_style` may be `none`, `solid_black_2px`, `solid_white_2px`, or `broken_panel`. The metadata controls later multi-shot page assembly and post-text targeting; it never asks the image model to create sub-panels or draw readable lettering.

For an NAI/tag-oriented project, set `preferences.prompt_profile` to `nai`. Every value that can enter image generation must already be English in the manifest. Source text and anchors, project/shot titles, checklist messages, and `post_text.text` may remain in the user's language. The shot visual object additionally requires final positive and negative prompts:

```json
{
  "preferences": {
    "prompt_profile": "nai",
    "style_prompt": "clean lineart, flat color, cel shading",
    "style_negative_prompt": "photorealistic, 3d render, text, watermark"
  },
  "world": {
    "era": "contemporary Japan",
    "city": "quiet coastal town",
    "visual": "white concrete, cyan signage, restrained coral accents"
  },
  "shots": [
    {
      "title": "门口的迟疑",
      "character_directions": {
        "CHR-001": {
          "position": "frame left, foreground",
          "action": "holds the unopened letter with both hands",
          "expression": "restrained worry, looking toward CHR-002"
        }
      },
      "visual": {
        "prompt": "tense homecoming at the entryway",
        "scene": "modern Japanese home, entryway, evening",
        "action": "two adults hesitate before exchanging a letter",
        "expression": "restrained tension",
        "lighting": "cool interior light, warm sunset outside",
        "style": "clean lineart, flat color, cel shading",
        "nai_positive_prompt": "2people, adult woman on frame left holding an unopened letter, adult man on frame right avoiding eye contact, modern Japanese entryway, evening, medium shot, eye level, cool interior light, warm sunset outside, clean lineart, flat color, cel shading",
        "nai_negative_prompt": "extra people, merged bodies, duplicate person, wrong prop ownership, bad hands, readable text, logo, watermark"
      },
      "post_text": [
        {"kind": "dialogue", "text": "你还是回来了。", "position": "top-right", "style": "speech"}
      ]
    }
  ]
}
```

For `nai`, English is required in `preferences.style_prompt`, `preferences.style_negative_prompt`, every `style_analysis` value, all World Bible fields, character `role`, `faction`, `personality`, `appearance`, `costume`, and `signature`, each `character_directions` value, and all shot `visual` values. `nai_positive_prompt` and `nai_negative_prompt` are mandatory and non-empty. The client and server reject CJK in those generation-facing fields before mutation.

For `append`, omit `project` and normally omit `world`. `characters` contains only newly introduced key characters. Existing characters are referenced by their real IDs. `preferences.prompt_profile` remains required and must exactly match the stored project profile; a mismatch returns HTTP 409 and leaves the project unchanged. The append request body wraps the manifest:

```json
{
  "expected_revision": 7,
  "manifest": {
    "schema_version": 1,
    "preferences": {"prompt_profile": "natural"},
    "source_batch": {},
    "existing_character_ids": ["CHR-001"],
    "characters": [],
    "shots": [],
    "checklist": []
  }
}
```

The server assigns collision-free final IDs where needed and returns the mapping.

For a new project, `style_pack_id`, `style_prompt`, and `bubble_pack_id` are required by the Skill client. Read the live choices with `style-packs` and `bubble-packs`; never guess an ID from this example. `style_analysis`, `style_prompt`, and `style_negative_prompt` are editable project copies. Appending normally omits these fields so the project keeps its established art direction and lettering pack.

`bubble_semantic` lets the Agent select dialogue, thought, narration, shout, or sound-effect intent. Leave `bubble_asset_id` empty for the project's bubble pack to choose its semantic default. Set it only when the user requests a particular bubble asset. Bubble fields are post-production metadata and are never sent to the image model.

To create a custom style after the user confirms the images and analysis, prepare the profile JSON and call:

```powershell
python <skill-directory>/scripts/frame_anime_client.py create-style <profile.json> <primary-image> --auxiliary <optional-image> --auxiliary <optional-image>
```

The primary image is required and there may be zero to three auxiliary images. The application accepts PNG, JPG, JPEG, and WebP.

## Responses

Create and append return:

```json
{
  "project_id": "project-abc123",
  "project_name": "Project title",
  "revision": 1,
  "created_character_ids": { "CHR-001": "CHR-001" },
  "created_shot_ids": { "SHOT-001": "SHOT-001" },
  "shot_count": 8,
  "warnings": [],
  "open_url": "http://127.0.0.1:8000/?project_id=project-abc123"
}
```

The app should preserve unknown future fields when editing known data.

## Targeted Revision

Revision operates only on explicitly named shots. Request body:

```json
{
  "expected_revision": 7,
  "allow_generated_shot_change": false,
  "patch": {
    "description": "Revised visual beat",
    "visual": { "camera_angle": "Low Angle" }
  }
}
```

The server rejects generated-shot changes unless `allow_generated_shot_change` is true. It never removes generation history as part of a storyboard revision.

## Reference Upload

Only upload a file the user supplied and explicitly asked the Agent to associate. Use the existing multipart endpoint and one of `character`, `world`, or `shot` as owner type. Never infer an owner when names are ambiguous.
