# Staged Manifest Drafting

Read this reference when a confirmed batch exceeds 8 shots or the complete storyboard manifest is likely to make one model response long enough to fail through a streaming gateway.

The purpose is transport reliability. Preserve the Agent's recommended count and the user's confirmed adaptation choices. Do not lower the panel count merely to shorten output.

## Short-Response Workflow

1. Before detailed shot drafting, create a lightweight beat index for the full confirmed count. Each entry contains only sequence number, scene task, one primary visual moment, source anchor cue, and layout role. Check count, causality, emotional progression, and chapter rhythm. Show the user only the concise adaptation summary and count decision already required by `SKILL.md`; do not paste the full technical manifest.
2. After the user confirms the plan, create a temporary staging directory outside the story source and application data directories. Keep a `base.json` containing project metadata, preferences, source batch, world, characters, and checklist, with `shots` omitted or empty.
3. Draft fully specified shots in ordered JSON-array chunks. Use at most 5 shots per chunk for a `natural` project and at most 3 shots per chunk for an `nai` project because NAI requires additional prompt fields. Save each completed chunk immediately as `shots-001-005.json`, `shots-006-010.json`, and so on. A chunk file contains only its shot array.
4. Keep each progress message to one or two sentences: state the completed range and the next range. Do not repeat finished shot details in chat. Continue to the next chunk without requesting approval unless the approved story treatment must change.
5. If execution is interrupted, inspect the staging directory and resume at the first missing shot range. Never regenerate or overwrite completed chunks without checking them. This makes a disconnected stream recoverable rather than forcing the whole chapter to restart.
6. Assemble chunks structurally, never with string concatenation:

```powershell
python <skill-directory>/scripts/assemble_manifest.py --base <base.json> --output <manifest.json> <ordered-shot-chunk.json> [...]
```

7. Run the normal manifest validator on the assembled file. Fix only the failing chunk or base field, reassemble, and validate again. Then show the short pre-mutation summary and obtain the required final confirmation before the single local `create` or `append` call.

The local import request may contain the complete validated manifest because it travels to FrameAnimeDesk over loopback rather than through the model streaming gateway. Do not split one approved project into several projects merely to avoid model-output timeouts.

## Invariants

- Chunk boundaries are drafting checkpoints, not narrative boundaries and not application import batches.
- The assembled shot count must equal `preferences.panel_budget` exactly and remain within the capability-reported ceiling.
- Shot `client_id` values must be unique across chunks.
- Chunk order must preserve source chronology and the approved beat index.
- Do not expose the full source, character DNA, prompts, or manifest in commentary when local files already preserve them.
- Do not automatically retry a failed application mutation. Preserve the validated staging files and report the failure.
