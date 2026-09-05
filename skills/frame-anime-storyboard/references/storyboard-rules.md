# Storyboard Rules

Read this reference when selecting source material, adapting prose, creating characters, or drafting shots.

## Adaptation Modes

`faithful` is the default. Preserve event order, relationships, motives, and consequential details. Compress dialogue and turn internal narration into visible action without changing its meaning.

`visual` may merge minor beats and add connective actions or transitions. It must not change the core plot, character motive, outcome, or relationship. Mark additions as `agent_bridge`.

Do not offer unrestricted rewriting in V1.

## Formats

- `vertical_comic`: default. Prefer 3:4 panels; use a different ratio only when a major establishing or vertical beat benefits.
- `horizontal_storyboard`: use 16:9 consistently.
- `square_social`: use 1:1 consistently.

Each shot produces one clean-plate still image. The storyboard also records optional `layout_meta` for a later page/comic compositor; V1 does not silently assemble pages or long strips during import.

## Commercial Chapter Rhythm

Treat a chapter as a readable sequence, not a bag of illustrations. Before drafting shots, mark four possible functions: `setup`, `development`, `climax`, and `hook`. A shot should change information, pressure, relationship, or audience expectation. Use shot-size contrast deliberately: wide or cinematic-wide to orient, medium for interaction, close-up for evidence/reaction, and a visually dominant full-width beat for the climax. Maintain screen direction, costume state, prop ownership, and light direction across adjacent shots unless the story deliberately changes them.

For a typical 2,000-3,000 Chinese-character web-fiction chapter, use three broad planning bands: compact 8-12, recommended 15-20 with room to extend to 21-22 when the meaningful beat count warrants it, and detailed 25-30 for major action, dense emotional conflict, or complex ensemble blocking. These are calibration bands, not formulas or defaults. Recommend one exact count after analyzing the selected source. Compact mode must explicitly disclose which setup, reaction, transition, atmosphere, or secondary detail is compressed. Avoid a sequence of evenly sized medium shots with the same camera angle, subject scale, and emotional temperature.

### Storyboard-Language Floor

For a `vertical_comic` batch of 8 or more shots, at least 50% of shots must use a truthful non-`still` dynamic expression. Use at least two camera angles and never repeat one angle for more than four consecutive shots. Do not meet the quota by relabeling static dialogue: a non-`still` shot must visibly show an action peak, weight shift, directional follow, controlled speed cue, restrained moving-part blur, impact relationship, entrance, handoff, changed distance, or consequential reaction.

The 50% floor applies to visible narrative movement and deliberate shot language, not to multi-panel image count. Multi-panel and irregular-page prompts remain an Agent decision based on the beat. Use them when cause/reaction, a brief progression, contrast, main/detail, or impact genuinely belongs in one generated image; do not add them mechanically.

Apply the three-second principle: each shot should be readable as one primary visual moment and normally introduce no more than one new piece of story information. When one proposed image asks the audience to discover a setting or reveal, read consequential dialogue, and follow a physical action at the same time, split those functions into two or three causal shots. Do not split a beat merely to inflate the count.

## Layout Metadata

New shots should include `layout_meta` when the intended result will be assembled as a comic page or vertical webtoon sequence:

- `single_panel`: ordinary clean plate;
- `full_width`: opener, reveal, major environment, or climax;
- `split_row_2`: cause/reaction, conversational counterpoint, or two simultaneous details;
- `progression_row_3`: three closely related micro-actions, with no more than three sub-panels;
- `inset_panel`: a main scene plus one phone, eye, document, or prop detail;
- `cinematic_wide`: a breathing panel, location transition, or time passage.

Use `row_index` and `slot_index` to preserve reading order. Use `gutter_bottom` to create vertical breathing room after an emotional beat or time jump. Use `border_style` for panel treatment, and `inset_config` only for an actual inset. For multi-panel image prompts, describe each sub-panel explicitly and keep the overall action causal. Do not let the model render dialogue or interface text; `post_text` and screen UI remain separate compositor layers.

## Adaptation Triage

Before counting panels, divide the confirmed range into scenes or coherent dramatic units. Give each unit one **scene task**: the story state, relationship, audience understanding, or emotional condition that must be different by the end. A unit without a meaningful change is normally context to compress, not a sequence to reproduce beat by beat.

Build a private adaptation ledger and classify each source beat by function and treatment:

- **Keep:** indispensable cause or outcome, relationship change, emotional turning point, setup/payoff clue, reveal, decision, or spatial fact needed to understand later action.
- **Visualize:** valuable internal thought, exposition, summary, atmosphere, or prose voice that cannot be photographed directly. Convert it into observable evidence such as behavior, hesitation, gaze, object use, distance, environment, contrast, or composition. Preserve meaning without inventing a new plot fact.
- **Compress:** repeated emotion or description, routine process movement, or several beats that produce the same unchanged story state. Merge them into the strongest representative visual moment.
- **Cut:** material whose removal causes no meaningful loss to causality, relationship progression, emotional continuity, clue setup/payoff, or spatial comprehension.

Use this loss test whenever treatment is uncertain: if removing the beat makes a later event confusing, a relationship shift abrupt, an emotional turn unearned, or a reveal unprepared, do not cut it. Keep or visualize the minimum evidence that prevents that loss.

Do not equate scale with importance. A quiet refusal, missed gaze, changed handling of a recurring object, or silence after dialogue can carry more narrative weight than routine movement or decorative spectacle. Conversely, do not retain a beat merely because the prose is vivid; preserve its function or strongest visual signal.

For the user-facing panel decision, summarize the ledger concisely:

- what the recommended version keeps as the dramatic spine;
- which non-visual material will be visualized and how;
- which repeated/process beats will be compressed;
- any subplot, explanation, or texture that will be omitted.

Match the user's language. For Chinese output, label these four lines `保留主线`, `视觉转译`, `压缩`, and `省略` rather than exposing the internal English treatment names.

Do not dump a paragraph-by-paragraph audit unless the user requests it. The ledger guides selection and makes adaptation losses explicit; it is not another long deliverable.

## Selecting Visual Beats

A panel must add at least one of: new information, action outcome, emotional change, reveal, spatial orientation, or meaningful transition. Do not create a new panel merely to change framing.

Estimate panels only after selecting the contiguous source range. Build a beat list before proposing counts. Consider:

- one establishing panel when location or spatial relationships must be understood;
- each consequential action or changed story state;
- reactions that change the audience's interpretation or establish motive;
- reveals that need visual emphasis rather than sharing a panel with their aftermath;
- transitions needed to keep time and space readable;
- dialogue exchanges that require distinct expressions or shifts in power.

Select beats from the adaptation ledger, not directly from sentence boundaries. Every retained panel must serve the scene task and must have a concrete visual subject. When a scene contains setup, change, and consequence, preserve the causal order; do not show only the result if that would make the change feel arbitrary.

Treat routine process actions such as walking, opening doors, sitting down, handing over ordinary objects, or traveling as connective material unless the action carries tension, a clue, a relationship gesture, a spatial reveal, or an irreversible change. Compress a chain of unchanged process actions into one transition or omit it.

For internal monologue, choose one visible piece of evidence rather than illustrating every sentence. Prefer an action, withheld action, expression shift, meaningful prop, altered distance, or environmental contrast that another character or the audience could observe. Use concise post-production thought text only when the image cannot preserve the essential meaning by itself.

For exposition and backstory, reveal the minimum information needed at the moment it becomes useful. Prefer environmental evidence, props, consequences, or brief dialogue over a dedicated explanation panel. Do not scatter required setup so widely that its later payoff becomes unrecognizable.

Do not use a characters-per-panel or words-per-panel formula. Several sentences may form one visual moment, while one short sentence may contain a cause, reveal, and reaction that need separate panels.

Offer three concrete counts:

- `recommended`: complete causal and emotional readability with one primary visual moment per panel;
- `compact`: merge low-priority reactions, atmosphere, or transitions, and disclose the resulting losses;
- `detailed`: separate important reactions, reveals, action phases, or location changes, and disclose the resulting gains.

Compact mode must not remove the only evidence supporting a later relationship turn, emotional beat, or clue payoff. Detailed mode may give such evidence its own panel, but must not restore repeated prose or routine process merely to increase the count.

The recommended value must be the Agent's actual judgment, not the midpoint by default. Keep compact and detailed alternatives materially distinct; do not invent extra panels that only change camera framing.

When a selection exceeds roughly 4,000 Chinese characters and contains several scene tasks or an emotional reversal plus aftermath, treat 20 shots as a likely compact treatment rather than an automatic recommendation. Check that setup, turn, consequence, emotional recovery, and closing hook each retain enough causal evidence. Do not spend most shots on repeated debate or process and then compress the relationship payoff into one or two images.

After the user confirms a count, use it as the target shot count and set the manifest's `panel_budget` to that number. Never exceed it without renewed confirmation, and do not silently return fewer shots. If the chosen count would require filler or would collapse incompatible primary moments, explain this before mutation and ask to change the count or adaptation mode.

A single manifest may contain 1-50 shots. Treat 50 as a technical ceiling rather than a planning target. For material requiring more than 50 panels, recommend the total first, then split it at scene or chapter boundaries into batches of at most 50. Show what story range and panel count each batch covers. Do not compress the entire selection merely to satisfy the single-batch limit.

One panel should contain one primary visual moment. Avoid putting cause, reaction, and aftermath into one image when separate images would be clearer.

## Characters

Create a character record when a named person affects the plot, speaks consequential dialogue, or recurs and needs visual continuity. Keep unnamed extras in the shot description.

Separate source facts from Agent supplements:

- `source_facts`: explicit in the selected text.
- `ai_supplements`: visual details inferred or proposed by the Agent.
- `needs_user_input`: important missing details the user should complete.

In user-completion mode, keep supplements minimal. In Agent-completion mode, produce a coherent reusable appearance and costume while preserving every source fact.

When the source and user references do not establish a stable design, ask whether the user wants Agent completion before drafting characters. Recommend it for a low-friction trial, but require the user's choice. Ask once for the affected cast rather than interrogating the user about every missing field.

For each Agent-completed character, provide:

- a recognizable face and hair profile;
- an age/life-stage and body-silhouette cue when it can be inferred responsibly;
- a recurring costume suitable for role, era, weather, and action;
- a restrained palette compatible with the chosen art style;
- one distinguishing prop, accessory, or shape cue.

Write these concrete details into `appearance`, `costume`, and `signature`, and duplicate the inferential record in `ai_supplements` so the user can audit what came from the Agent. Never overwrite contradictory source facts. Do not use placeholder prose inside visual fields.

## World and Scene

The World Bible contains only project-wide facts: era, geography, technology, magic, history, factions, rules, conflict, weather patterns, time rules, visual palette, and materials.

Put the current location, time, local weather, props, and set dressing in the shot's scene field. Recurring locations can use named World Bible reference images with notes; V1 has no location entities.

## Source Traceability

Persist only the confirmed selection, not the full uploaded document. Each shot gets a concise exact `source_anchor`, normally 60-100 Chinese characters and never a paraphrase presented as a quotation.

Use one adaptation kind:

- `direct`: directly visualizes source action or description.
- `visualized`: converts narration, internal thought, or compressed dialogue into a visual beat.
- `agent_bridge`: adds a disclosed connective action or transition.

## Post-Production Text

Do not ask the image model to render dialogue, captions, or Chinese text. Reserve negative space in composition and store exact text separately.

Each ordinary text block contains:

- kind: `dialogue`, `narration`, or `sfx`;
- exact concise text;
- optional speaker character ID;
- position: `top-left`, `top-right`, `left`, `right`, or `bottom`;
- style: `speech`, `thought`, `caption`, or `sfx`.

Default limits:

- no more than two dialogue/narration blocks per panel;
- one additional essential sound effect is allowed;
- dialogue should usually be at most 15 Chinese characters;
- narration should usually be at most 25 Chinese characters.

If text exceeds these limits, shorten it without changing meaning or move part of it to another panel. The visual prompt must name the reserved clean area but must not include literal text that the model might draw.

## References

The user primarily uploads references. Request only references with meaningful continuity value:

- named key-character identity, costume, or required fandom fidelity;
- a recurring iconic location;
- a user-requested art direction that prose cannot communicate reliably;
- an unusual pose or composition central to a shot.

References are optional unless the user explicitly requires high fidelity. State what to upload, why, and where it belongs. Never search for or download fandom or real-person images without a separate user request.

## Content and Provider Risk

Run the current Agent policy first. Also warn when gore, explicit sexual material, real-person depiction, or other sensitive content is likely to be rejected by the configured image provider. Do not process sexual content involving minors, non-consensual sexual content, or disallowed real-person sexual/deceptive material.

Do not decide whether the user owns a fandom IP. Remind them that publication and commercial use may require permission.

## Quality Check

Before manifest validation, verify that:

- every shot maps to the confirmed contiguous selection;
- every shot serves a declared scene task and comes from a `Keep` or `Visualize` decision;
- removing compressed or cut material does not break causality, relationship progression, emotional continuity, clue payoff, or spatial comprehension;
- internal thought and exposition have concrete visible evidence rather than illustration of abstract prose;
- the shot count exactly matches the user's confirmed count for this batch;
- shot order preserves causality and readable spatial continuity;
- at least half of an 8+ shot vertical batch uses truthful non-`still` dynamic expression;
- an 8+ shot vertical batch uses at least two camera angles, with no run longer than four identical angles;
- every selected character exists and identities are not merged;
- no shot carries multiple incompatible primary moments;
- eye state, posture, hand occupancy, costume state, prop ownership, and action phase contain no internal contradiction and persist correctly across adjacent shots;
- every Agent-authored multi-panel prompt follows the strict five-layer English formula and does not rely on software layout metadata;
- global world facts are not duplicated as noisy shot prose;
- text safe areas match post-production text positions;
- reference requests are specific and non-blocking unless fidelity requires them;
- no image generation request is present.
