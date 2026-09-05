# NAI5 Comic Direction and Conception

This reference provides reusable planning methods for NAI5-oriented comic direction. It is not a prompt dump, a guarantee of model behavior, or permission to copy artist names, franchise terms, or unsupported sampler settings.

## 1. Decide How Much Conception Is Needed

Classify the request before writing a shot:

- **Formed visual request:** subject, action, setting, camera, and mood are already specified. Preserve the intent and only resolve contradictions or missing production facts.
- **Subject without a scene:** the user has a character or object but no concrete moment. Add one coherent situation, camera, spatial arrangement, and light direction; disclose the additions.
- **Theme or direction only:** offer two or three materially different visual concepts. Change at least two of subject/action, setting, camera, spatial hierarchy, or lighting. A different hair color is not a different concept.
- **Open request:** offer two or three concepts, including one restrained or non-obvious option such as negative space, a distant small figure, a strong hard-light setup, a back view, or an environment-led composition.

Do not invent a large world bible to compensate for a missing visual decision. Ask the user to choose when the difference would change the story or project identity.

## 2. Industrial Order: Story, Space, Action, Light

For every shot, reason in this order:

1. **Story beat:** identify the one fact the viewer must understand or feel in this image.
2. **Space and camera:** set camera height, viewing direction, shot size, focal subject, and foreground/midground/background before placing characters.
3. **Action:** freeze one observable moment with a clear subject, verb, object, and receiver. State who does what to whom, or what physical evidence shows the emotion.
4. **Light and tone:** choose the source direction, color temperature, contrast, and material response after the space and action are stable.

Do not use light effects, particles, flowers, or depth-of-field language as substitutes for missing staging. Every foreground occluder must agree with the same camera position. Do not put all characters at equal scale on one plane unless a deliberate group tableau calls for it.

## 3. Spatial Layering for Complex Scenes

When a shot contains several characters, a large object, or a broad location, write a single integrated global visual contract with at least three depth layers:

- environment and atmosphere;
- midground visual focus and character blocking;
- background architecture, landscape, or scale object;
- optional foreground frame, obstruction, or nearby prop;
- one coherent light path that crosses the scene.

Use plain spatial anchors: `frame left`, `frame right`, `center midground`, `upper background`, `left foreground`, `behind`, `in front of`, `near the doorway`, `partially occluded`, and `taking up the upper half`. Bind each prop to its owner and each gaze to a visible target.

The old NAI regional-prompt idea of allocating empty Character slots to a narration box is not used by FrameAnimeDesk. A narration box is `post_text`, and a multi-panel page is one complete Agent-authored final prompt. Keep spatial planning in the integrated prompt and the structured character directions; do not reintroduce a software Character-slot layout system.

## 4. NAI5 Field Division

For a NAI project, preserve the following separation while keeping each final shot prompt self-contained:

- **Positive prompt:** visible subject count, camera, composition, current action, interaction, expression or gaze when needed, visible setting, light/color, and concise medium/quality controls.
- **Character direction:** identity, stable appearance, current costume, position, action, expression, and gaze target. Repeat the chosen costume and identity anchors at shot level when text-only generation is used.
- **Negative prompt / UC:** only likely failures for this shot: extra or duplicate figures, merged bodies, wrong prop ownership, unreadable text, watermark, and a small number of direct medium conflicts.

Use tags for discrete facts such as count, body position, camera height, basic pose, clothing form, or a focal body part. Use short sentences for spatial relationships, physical interactions, occupied area, ongoing action, light direction, and transitions. Keep a tag close to the noun it qualifies. Do not repeat the entire appearance block in the global prompt, but do not omit the visible identity facts from the final prompt when the endpoint receives only the final positive/negative fields.

Do not place plot summary, world history, faction names, personality labels, dialogue, continuity commentary, or reference-management notes in the NAI positive prompt. Convert a required world fact into a visible object or condition only when it appears in the shot. Keep quality terms at the end and remove redundant synonyms before saving.

Treat weights, `transparent background`, complexity labels, and provider-specific syntax as optional integration details, not universal storyboard rules. FrameAnimeDesk's normal manifest uses unweighted English phrases and application resolution controls; never add sampler, CFG, seed, or undocumented parameters to a storyboard.

## 5. Comic Beats and Reading Flow

Use the prose-to-panel triage from `storyboard-rules.md` before drafting:

- **Keep:** causal reveals, irreversible actions, relationship turns, clue setup/payoff, and spatial facts the reader cannot infer.
- **Visualize:** inner thoughts or exposition that can become an object, gesture, contrast, or environmental evidence.
- **Compress:** repeated travel, routine actions, redundant dialogue, and transitional description when causality survives.
- **Cut:** decorative material that does not change understanding, emotion, or rhythm.

Normally give each shot one primary visual moment. Split a beat when a reveal, a consequential action, and a reaction would otherwise compete for the same image. Establish geography before close reactions; vary shot size and angle; reserve the largest composition for the climax or key reveal; end on a readable unresolved image when the source calls for continuation.

Default Japanese manga reading direction is right-to-left only when the chosen output format is a page intended for that convention. Vertical webtoon and user-specified left-to-right formats override it. Reading direction changes panel order, gaze flow, and speech placement; it does not automatically require an irregular layout.

## 6. Multi-Panel Generation

Use one generated multi-panel image only for a tightly coupled cause/reaction, short action progression, contrast, detail-to-main relationship, or impact beat. Use separate storyboard shots when viewpoint, time, location, or character state changes. Never create multi-panels merely to increase panel count.

When used, the final English prompt must follow the project's five-layer formula:

1. exact layout and panel count;
2. `featuring the same character across all panels:` plus fixed appearance, costume, hair, accessories, and carried props;
3. one independently positioned beat per panel using explicit locations such as `top-left`, `top`, `bottom`, `left`, or `right`;
4. complete style, clean gutters/borders, and `clean panels, no text, no gibberish speech bubbles`;
5. an explicit aspect-ratio parameter as the final characters of the prompt.

Do not place literal dialogue in the image prompt. Create dialogue, narration, SFX, and bubble assets as post-production data. Do not use the old “one Character slot per person or text box” recipe; it conflicts with the current FrameAnimeDesk contract and makes the final prompt incomplete.

## 7. Final Quality Gate

Before saving a NAI shot, verify:

- one primary beat is evident and physically drawable;
- camera, foreground, midground, background, and character positions agree;
- each visible character has one resolved current costume and one unambiguous action;
- visual prompt fields contain English only and no literal dialogue;
- positive prompt is minimal but self-contained;
- negative prompt is short and shot-relevant;
- multi-panel prompts use the exact formula, exact count, explicit positions, fixed continuity anchor, and non-`Auto` matching ratio;
- no artist string, copyrighted work imitation, unsupported parameter, or prompt-dump residue remains.
