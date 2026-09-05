---
name: frame-anime-storyboard
description: Turn short fiction, fanfic, or a selected prose passage into a reviewable comic storyboard project in a locally running FrameAnimeDesk. Use when the user wants to select a passage, create or continue a storyboard project, or revise specific ungenerated shots. Do not use for whole-novel adaptation, general image generation, or automatic batch generation.
---

# FrameAnime Storyboard Director

Convert a short prose selection into structured FrameAnimeDesk characters, world context, shots, and post-production text. The installed FrameAnimeDesk desktop application is the production target; a source-mode browser preview is only a development surface. Stop after writing a reviewable project; the user reviews each shot and clicks Generate in FrameAnimeDesk.

Resolve every relative resource path against the directory containing this `SKILL.md`, not against the user's current project directory.

## Non-Negotiable Boundaries

- Target Codex users with the FrameAnimeDesk desktop application running locally.
- Never trigger image generation, click Generate, or promise that every planned shot will pass the selected image provider.
- Never trigger project export or download a delivery file. Export is available only after the user has reviewed and generated every included shot.
- Never edit `workspace.json` directly. Use the local atomic import API through `scripts/frame_anime_client.py`.
- Do not create or mutate a project until the required confirmation immediately preceding that mutation.
- A failed mutation gets no automatic retry. Report the failure and keep the validated manifest available for inspection.
- Prefer quality and readable visual beats over minimizing image count.

## Intake

Before intake, discover and diagnose the running desktop application without asking the user for a port:

```powershell
python <skill-directory>/scripts/frame_anime_client.py doctor
```

If diagnosis finds no compatible desktop instance, ask the user to start the installed FrameAnimeDesk application and rerun the check. Do not treat an unrelated local web server as FrameAnimeDesk. If multiple compatible instances exist without a valid runtime descriptor, report their URLs and ask the user which one to target.

After diagnosis, read the choices exposed by that exact desktop instance:

```powershell
python <skill-directory>/scripts/frame_anime_client.py capabilities
python <skill-directory>/scripts/frame_anime_client.py style-packs
python <skill-directory>/scripts/frame_anime_client.py bubble-packs
```

Do not hard-code IDs or assume that the built-in catalog is unchanged.
Read `storyboard_import_max_shots` from capabilities and use it as the current technical batch ceiling. The expected value for this Skill version is 50; if an older application omits it or reports a lower value, state that limitation and do not prepare a manifest above the reported ceiling.

Inspect the capability response's `generation` object before asking about the image model:

- Every project has one persistent `prompt_profile`: `natural` for GPT/instruction-following image models, or `nai` for NovelAI and other tag-oriented anime models. It is a project fact, not a per-shot or temporary provider setting.
- For a new project, resolve the prompt route in this order: (1) an explicit user request such as “GPT版”, “GPT路径”, or “自然语言提示词” forces `natural`; (2) an explicit request for NovelAI, NAI, or tag prompts forces `nai`; (3) only when neither route is requested may the capability response's model/profile propose a route. When the user explicitly chooses GPT, do not read, infer from, or follow the configured model name for prompt-language selection; the model name is transport/provider metadata, not the user's requested prompt route. State that the project will use Chinese natural-language generation fields and persist `preferences.prompt_profile: natural`. If the profile is unknown and the user has not chosen a route, ask one concise choice between GPT natural language and NAI English tags. Do not create the project while the choice remains unknown.
- Write the confirmed value to `preferences.prompt_profile`. For continuation and targeted revision, read and inherit the stored project profile. Never change it in an append or revision manifest, and stop on a conflict instead of translating or overwriting existing project content.
- A provider or model configured later must match the project's stored profile. Explain that the user should create a separate project when they want to take the same story through the other prompt route.

For `nai`, read [references/nai-prompt-rules.md](references/nai-prompt-rules.md) and [references/nai-safe-vocabulary.md](references/nai-safe-vocabulary.md) before proposing art direction or writing any generation-facing field. The vocabulary library is the application's curated reference for reusable visual concepts: medium, quality restraint, camera, composition, color, light, character anatomy and appearance, clothing, poses, expressions, environments, objects, everyday scenes, festivals, fantasy, special layouts, and multi-character blocking. Store character visual DNA, World Bible visual facts, art direction, per-character directions, and shot visual ingredients in English for project editing and continuity review. Compile each shot's final positive and negative prompts as a minimal, self-contained generation contract: only visible current-shot facts belong in the positive prompt, while the negative prompt contains only concise failure exclusions. FrameAnimeDesk sends these two final fields without automatically appending World Bible, character-library, style-analysis, or project-style text. Chinese remains valid for source text and anchors, project and shot titles, structural notes, checklist messages, and post-production dialogue/narration/SFX because those values are not sent to the image model. Apply the rules without copying prompt dumps, artist strings, copyrighted work imitation, sexual or bloody material, sampler folklore, or unsupported parameters into the manifest.

For `natural`, do not load the NAI reference. Store complete instruction-following visual direction in the user's working language; do not flatten it into tag strings or require separate NAI prompts. Unless the user explicitly requests it, never write the Chinese term `写实` into any project, character, shot, positive prompt, negative prompt, or editable generation-facing field. Describe the intended visible property directly instead, such as natural proportions, accurate perspective, clear structure, flat skin color, photographic texture, or continuous volume shading. When the selected style is two-dimensional anime or manga and reference images will not reach the provider, make the medium contract explicit and non-negotiable: name the finished two-dimensional image type, drawn linework, flat color behavior, shadow edge behavior, and character-surface treatment. Clarify that natural proportions, accurate perspective, or cinematic composition do not authorize photographic faces, realistic skin, painterly volume rendering, or 3D edges. Put those conflicts in the style exclusions as concrete hard prohibitions.

Accept pasted text and `.txt`, `.md`, or `.docx` files. Accept text-based PDFs when reliable extraction is available. Do not claim support for scanned PDFs, image-only text, or EPUB unless the current environment can extract them faithfully.

Show the user every available option while presenting these defaults:

```text
Project: new story (or continue an existing project)
Format: vertical comic (or horizontal storyboard, square social post)
Panel count: Agent recommends after analyzing the confirmed source range; user decides
Adaptation: faithful (or visual adaptation)
Character completion: user completes key characters (or Agent completes them)
```

Do not ask the user to choose a panel count before reading the source. If the user supplies a count in advance, treat it as a preference to evaluate, not a binding limit, and explain whether it can represent the selected material cleanly.

After identifying the key characters, inspect whether the source provides enough stable visual facts for each character: approximate age or life stage, face or hair cues, body silhouette, recurring costume, palette, and one distinguishing element. Also consider whether the user supplied character references. If one or more key characters lack both usable visual facts and references, do not silently create empty character records. Ask one explicit project-level decision and name the affected characters:

```text
These key characters have no stable visual design in the source and no reference images: <names>.
Recommended for a quick trial: Agent completes editable character designs from role, era, personality, and story context.
Other options: keep them incomplete for you to edit later, or pause and upload character references.
Should the Agent complete them?
```

Recommend Agent completion when the user says they are only trying the workflow, have no character sheets, or have no strong design preference. Do not assume consent merely because references are absent. Use one decision for all affected characters by default, while allowing the user to override individual characters.

Ask about visual style separately after reading the source range. Show every available style pack by display name, identify one recommendation for this passage, and state why it fits. Also offer a custom style and, for continuations, inheriting the existing project style. User instructions and uploaded style references override recommendations.

For a custom style, require exactly one primary style image and accept zero to three auxiliary images. The user normally uploads these in FrameAnimeDesk. If the user explicitly asks the Agent to create the style, inspect only the confirmed images, draft editable analysis for linework, character rendering, coloring, background, palette and lighting, composition, and exclusions, then show that analysis plus the compiled positive and negative prompts. Obtain confirmation immediately before calling `create-style`; do not silently register images as a style. All confirmed style images accompany each generation request, while the analysis and prompts remain editable in the Art Direction view.

Show every available bubble pack once and recommend one. Bubble selection controls post-production only. Assign each text block a semantic intent (`dialogue`, `thought`, `narration`, `shout`, or `sfx`) and leave the concrete bubble asset automatic unless the user requests an override. Keep dialogue and narration concise and rely on the picture for information that can be shown visually. Never ask the image model to draw readable dialogue, captions, or bubbles.

Read [references/storyboard-rules.md](references/storyboard-rules.md) before analyzing the source or drafting shots.
Read [references/visual-direction-rules.md](references/visual-direction-rules.md) before analyzing a style reference, choosing shot composition, or writing any shot visual field. Apply its provider-neutral visual decisions first; never copy model-specific tag syntax into the storyboard merely because it appeared in a tutorial or prompt dictionary.
Read [references/comic-conception.md](references/comic-conception.md) for every storyboard request. Apply its beat triage, space-before-style order, drawable-action test, continuity ledger, prose-to-image translation, and multi-panel quality gate to both GPT and NAI projects.
For NAI5 comic conception, sparse requests, complex spatial scenes, or multi-character interactions, also read [references/nai5-comic-direction.md](references/nai5-comic-direction.md). Use its story-space-action-light pipeline, NAI field separation, and comic beat quality gate. The current FrameAnimeDesk contract remains the authoritative implementation.

## Capacity and Range

Estimate whether the whole input can be read and reasoned about reliably using its character count, paragraph count, cast size, and scene span. Never silently truncate. If it exceeds current capacity, stop promptly and propose a smaller chapter, scene, or passage.

Run a lightweight content-risk check before asking the user to approve a range. Follow the current Agent and image-provider policies. Flag material likely to fail later and stop on prohibited content rather than creating a project.

Recommend one contiguous source range. Show its exact opening sentence, exact closing sentence, and why it forms a coherent visual unit. Do not combine distant passages.

Before recommending a panel count, apply the adaptation triage in `storyboard-rules.md`: identify each scene task and classify meaningful beats as Keep, Visualize, Compress, or Cut. Use the loss test for causality, relationship progression, emotional continuity, clue setup/payoff, and spatial comprehension. This is required even for short inputs; it improves selection and does not expand the Skill into whole-novel adaptation.

After the range is clear, count its meaningful visual beats and present a panel decision before drafting the manifest:

- **Recommended:** one exact panel count with a short explanation of pacing and coverage.
- **Compact:** a lower exact count and which reactions, transitions, atmosphere, or secondary details would be merged or omitted.
- **Detailed:** a higher exact count and which emotions, reveals, actions, or spatial transitions would gain their own panels.

Alongside these counts, give one concise adaptation summary: the dramatic spine being kept, the important prose or inner thought being turned into visible evidence, the repeated/process material being compressed, and any material being omitted. Match the user's language; in Chinese, label these lines `保留主线`, `视觉转译`, `压缩`, and `省略`. Do not expose a long paragraph-by-paragraph ledger unless the user asks for it.

Do not derive these counts from character count alone. Account for scene changes, consequential actions, reaction beats, reveals, dialogue density, spatial clarity, and the chosen adaptation mode. State which option you recommend rather than giving three neutral choices. Let the user confirm one count or request another. Do not construct the final shot list or mutate FrameAnimeDesk until the user has confirmed both the source range and panel count.

For a normal 2,000-3,000 Chinese-character web-fiction chapter, use these commercial-webtoon ranges as decision guidance, never as fixed defaults: `compact` is usually 8-12 shots, `recommended` is usually 15-20 shots and may extend to 21-22 for dense meaningful turns, and `detailed` is usually 25-30 shots for major action, dense emotional conflict, or complex ensemble blocking. The Agent must still derive and recommend one exact count from the confirmed source range. Apply the three-second principle: each shot should carry one primary visual moment and normally no more than one new piece of story information. Split a beat that simultaneously requires a reveal, consequential dialogue, and physical action into two or three causal shots instead of overloading one image. A commercial-feeling sequence needs variation in shot scale and visual rhythm: establish geography, enter the action, show a reaction, advance the conflict, isolate a clue or emotion, give the climax a larger visual beat, then end on a readable unresolved image. For a `vertical_comic` batch of 8 or more shots, at least half of the shots must use a truthful non-`still` `dynamic_expression`; do not relabel static dialogue merely to meet the quota. Use at least two camera angles and never repeat one angle for more than four consecutive shots.

Multi-panel comics are decided by the Agent during shot writing, not by a FrameAnimeDesk layout control. Use them when the source needs a tightly coupled cause/reaction, brief action progression, main-detail relationship, contrast, or impact page; do not add them to satisfy a numeric quota. Prefer separate shots when viewpoint, time, location, or character state changes. Write the complete English generation prompt directly into the shot's `visual.prompt` for natural projects and `visual.nai_positive_prompt` for NAI projects, following [references/multi-panel-prompt-formula.md](references/multi-panel-prompt-formula.md) in strict five-layer order: layout and exact panel count, shared character appearance anchor, independently positioned panel beats, style and border control, then the aspect-ratio parameter. Every panel must use explicit positional wording such as `top-left`, `top`, `bottom`, `left`, or `right`. Require the exact phrase `featuring the same character across all panels:`, fixed costume/hair/signature details, and `clean panels, no text, no gibberish speech bubbles`. The aspect-ratio parameter must end the prompt and must exactly match the shot's explicit `visual.aspect_ratio`; `Auto` is invalid for a multi-panel shot. A recognized multi-panel prompt is sent as the exact final positive prompt, so include the complete selected visual style and necessary exclusions inside its fourth layer. FrameAnimeDesk may still attach the selected style reference images, but it does not append project-style text before or after this Agent contract. Do not expose a panel selector in the application as the source of this decision. Legacy `visual.panel_layout` and `visual.panel_beats` may be read for backward compatibility but must not determine or rewrite the final prompt.

`layout_meta` is only the chapter export compositor. Use `row_index` and `slot_index` to place separate generated shot images, `gutter_bottom` for vertical breathing space, and `border_style` for exported borders. It does not instruct the image model. New manifests should set `visual.dynamic_expression` to one of `still`, `action_peak`, `speed_lines`, `motion_blur`, `follow_composition`, or `impact_composition`; the chosen value must describe the actual visible action phase and agree with the action, character directions, and integrated prompt. Do not use video-camera movement terms for static comics. Do not write a production mode or per-shot duration because those controls are not part of still-image generation. Video export duration remains a global export option.

The confirmed count is the target shot count for that batch. Do not pad the storyboard with framing-only panels. A single import may contain 1-50 shots; 50 is a technical ceiling, not a target. If a coherent draft cannot meet the chosen count, stop before mutation, explain the conflict, and ask the user to revise the count or adaptation mode. If the material merits more than 50 panels, recommend the total count and a chapter/scene batch plan with no more than 50 panels per batch. Obtain confirmation for the overall plan and then confirm each batch immediately before writing it; do not compress content merely to fit one import.

## Confirmation and Mutation

For a new project, approval of the displayed options, exact source range, and exact panel count authorizes one project creation. Set `preferences.panel_budget` to the confirmed batch count and build exactly that many meaningful shots before validating and sending the manifest. Every new shot should carry `layout_meta` when a later comic compositor is intended. Resolve one current costume in every selected character's `character_directions.costume`; never leave a list of scene alternatives for the model to choose.

The displayed options and pre-mutation summary must name the permanent project prompt route. For `nai`, also state that generation-facing project data will be written and stored in English even when the source and conversation are Chinese. Do not silently translate an already-created natural project into NAI or vice versa.

The pre-mutation summary must also state the character-completion choice, list every character the Agent will complete, and distinguish source facts from proposed visual details. If the user chose Agent completion, approval of that summary authorizes those disclosed visual inferences for this project creation only.

The pre-mutation summary must preserve the confirmed adaptation decisions. If drafting reveals that a planned cut would break causality, relationship progression, emotional continuity, clue payoff, or spatial comprehension, stop before mutation and present the revised treatment or panel count for confirmation.

The same summary must name the selected style pack and bubble pack, state how many style references will accompany generation, and disclose any edits made to the pack's default prompt or analysis. Write the confirmed live IDs to `preferences.style_pack_id` and `preferences.bubble_pack_id`; copy the editable analysis and positive/negative prompts into the manifest. Do not substitute a generic style label for an available pack.

For a continuation:

1. Read the current project and revision.
2. Read the stored `promptProfile`, report whether this is a GPT natural-language or NAI English-tag project, and prepare all new generation-facing fields in that same route.
3. Confirm the exact source range.
4. Present the recommended, compact, and detailed panel counts; obtain the user's panel decision.
5. Show the append summary, confirmed new shot count, new key characters, and continuity conflicts.
6. Obtain a second confirmation immediately before appending.

Continuation preserves existing shots, characters, world fields, references, and generation history. Add new characters only. Do not overwrite conflicting established facts; report them for the user to resolve.

Read [references/import-contract.md](references/import-contract.md) before creating a manifest or calling the API. Validate a manifest before mutation:

For any confirmed batch above 8 shots, or whenever the complete manifest is likely to require a long model response, also read [references/staged-drafting.md](references/staged-drafting.md). Draft and persist the manifest in small recoverable chunks instead of emitting or constructing every detailed shot in one response. This is an Agent-output reliability rule; it does not reduce the confirmed panel count or the application's 50-shot import ceiling.

Never print a complete multi-shot manifest in chat. Keep user-facing progress concise. After the user confirms the source range and panel count, chunk drafting may continue without asking for approval after every chunk. Pause only when a continuity conflict, unsafe inference, or required missing decision changes the approved plan. The required confirmation immediately before application mutation still applies after the final assembled manifest passes validation.

Validate the assembled manifest before mutation:

```powershell
python <skill-directory>/scripts/frame_anime_client.py validate <manifest.json>
```

Then use `create` or `append`. Mutation commands automatically repeat the application-version and import-protocol preflight immediately before writing. If FrameAnimeDesk is offline, tell the user to start the desktop application. Do not search for and launch an unknown executable.

## References and Missing Information

Create character records only for named characters with plot relevance. Describe unnamed extras inside shots unless they recur and require continuity.

In user-completion mode, create a key-character scaffold using only explicit source facts. Record missing appearance and costume fields for the user, and request references only when the user wants stronger identity consistency. Do not fill missing fields with phrases such as “原文未提供” or “待用户补充”; keep them editable and put the explanation in `needs_user_input`.

In Agent-completion mode, produce a usable and internally coherent visual DNA for every affected key character. Fill appearance, costume, and signature with concrete image-facing details appropriate to the source's era, role, personality, relationships, and visual style. Cover a recognizable face/hair profile, body silhouette or life stage, recurring costume and palette, and one distinguishing element. Preserve every explicit source fact and avoid stereotypes. Put every inferred fact in `ai_supplements`; never present it as a quotation or source fact. The result remains a proposal the user can edit in FrameAnimeDesk.

Agent completion creates text-based character designs; it does not fabricate uploaded reference images. In the FrameAnimeDesk mirror channel, a multi-character shot may be tried without character references when every unreferenced character has complete appearance and costume DNA; tell the user that cross-shot face, hair, and clothing consistency may be weaker. Uploaded references remain preferable for fidelity, and another configured provider may impose stricter requirements. Do not promise exact identity consistency from text alone.

The user normally uploads references in FrameAnimeDesk. Explain exactly which image is needed and whether it belongs to a character, the World Bible, or a shot. Upload a conversation attachment only after the user explicitly asks the Agent to do so and confirms its owner.

Use one global World Bible for stable era, rules, palette, technology, and style. Put concrete location, time, weather, and set dressing in each shot. Do not invent a location library.

In an NAI project, write every World Bible field that may enter generation context in concise English. Keep only source quotations, user-facing titles, checklist explanations, and post-production text in Chinese. Do not save Chinese first with a promise to translate only at send time; the persisted project itself is the reviewable NAI prompt source.

## Revisions

Support targeted revisions such as changing one shot or merging specified shots. Read the current project first and patch only the named shots through the revision endpoint. Protect shots with generation history: explain the inconsistency and obtain explicit confirmation before changing one.

Targeted revisions inherit the project's stored prompt profile. A revision may update `nai_positive_prompt` and `nai_negative_prompt` only for an NAI project and must keep all revised generation-facing values in English. It must never convert the project profile.

## Completion

After a successful write, report:

- project name and project ID;
- selected source range and imported panel count;
- created key characters;
- missing character, world, style, and shot references;
- any Agent-supplied details or adaptation omissions;
- the returned project link;
- a reminder that FrameAnimeDesk will offer a non-disruptive “查看项目” action, after which the user should inspect the project and generate images manually.

When all shots in the intended delivery range have user-approved generated images, point the user to FrameAnimeDesk's **导出** module. It can create an ordered PNG bundle, one vertical comic PNG, a one-shot-per-page PDF, or a silent MP4, with optional post-production lettering. Do not imply that creating the storyboard also created these files. If any shot lacks a generated image, explain that FrameAnimeDesk blocks export and identify those shots from the current project state.
