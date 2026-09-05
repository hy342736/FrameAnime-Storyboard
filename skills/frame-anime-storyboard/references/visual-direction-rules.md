# Visual Direction Rules

Read this reference when analyzing a built-in or custom style, translating a visual beat into a shot, or filling the manifest's `visual` fields. These rules describe visual intent, not syntax for a particular image model.

## Direct the Story Before the Camera

For every panel, write one private sentence answering: **what must the audience notice, feel, or understand here?** Choose framing, camera position, composition, lighting, and focus only after that answer is clear.

Use visual emphasis in this order:

1. the story-bearing subject or interaction;
2. the action, expression, prop, or distance that proves the beat;
3. the environmental information needed to read place and causality;
4. atmosphere and decorative detail.

Do not use an unusual angle merely to make a quiet beat look dynamic. A neutral eye-level composition is preferable when it communicates the relationship and action clearly. Across adjacent panels, vary framing only when the narrative emphasis, power relation, distance, orientation, or information changes.

## Choose Shot Size by Information Need

Use only shot types accepted by FrameAnimeDesk:

- `Extreme Wide Shot`: geography, scale, isolation, arrival, or a major location reveal. Keep characters readable as silhouettes and name the important environmental evidence.
- `Wide Shot`: body placement, multiple-character blocking, travel direction, or environment-led action.
- `Full Shot`: whole-body action, posture, costume silhouette, or interaction requiring hands and feet.
- `Medium Shot`: default for dialogue, gestures, object handling, and two-character relationship beats.
- `Close Up`: a decisive expression, clue, hand action, or object reveal. Name the single focus explicitly.
- `Extreme Close Up`: a tiny decisive detail or peak reaction. Use sparingly and do not demand unrelated body or background information.

Do not treat close-ups as a generic quality fix. Cropping removes information; use it only when the removed context is not needed in that panel. Establish a new or confusing location before relying on close views.

Match the canvas to the intended information:

- `vertical_comic` normally uses `3:4`, favoring single-character body language and vertical depth;
- `horizontal_storyboard` uses `16:9`, favoring environment, movement direction, and two-character spacing;
- `square_social` uses `1:1`, favoring one centered or clearly balanced primary moment.

Do not cram a wide multi-character tableau into a narrow panel. If the selected format cannot preserve essential staging, simplify the blocking or disclose why that beat needs a different ratio.

## Choose Camera Position Deliberately

- `Eye Level`: neutral observation, conversational equality, intimacy without judgment, and most continuity shots.
- high or overhead view: vulnerability, surveillance, pattern, crowd geography, or spatial clarification. A directly overhead view must have a strong floor-plan or shape reason.
- low view: authority, threat, awe, resistance, or vertical scale. Keep anatomy and horizon readable.
- front view: direct confrontation, address, symmetry, or an unambiguous identity reveal.
- side/profile view: movement direction, emotional separation, parallel action, or a readable kiss/argument silhouette. Make gaze and head direction explicit when they matter.
- rear view: departure, concealment, audience alignment with what the character sees, or withheld identity. Do not simultaneously demand a fully visible face unless the beat is explicitly a look-back.
- look-back view: use only when turning back is itself meaningful; specify body facing away and head turning back.
- Dutch angle: instability, danger, disorientation, or sudden imbalance. Avoid repeated use and avoid it for ordinary dialogue.
- foreshortening: a limb, object, or movement advancing toward the viewer. Name what advances and keep it to one dominant action.
- fisheye or extreme lens distortion: subjective panic, peephole surveillance, speed, or deliberate comic distortion. Never use as generic cinematic decoration.

Use one dominant shot size, one dominant viewing direction, and at most one special-perspective device. Resolve contradictions such as front view plus rear view, full body plus extreme close-up, or neutral symmetry plus extreme Dutch angle before writing the manifest.

## Block Characters and Maintain Continuity

For each selected character, state frame position, facing direction, action, gaze target, and expression only to the degree needed by the beat. For multi-character shots, describe the relationship as visible geometry: left/right order, foreground/background, distance, touch, occlusion, or eyeline.

Maintain across adjacent shots unless the story changes them:

- screen direction and left/right ordering;
- entrances, exits, and where characters are looking;
- held objects and which hand holds them;
- costume state, damage, wetness, dirt, and other accumulated changes;
- time, weather, dominant light direction, and location layout.

Keep a private state ledger for eyes, mouth, posture, hand occupancy, prop ownership, costume state, damage/wetness, and entry/exit position. Each shot must resolve one current state for every relevant attribute. Do not simultaneously request closed eyes and watching, holding and dropping the same prop, seated and stepping backward, or rolled and unrolled sleeves. A changed state persists into following shots until a visible beat reverses it.

Choose one current costume for every selected character in every shot. A character-library costume field may contain alternatives for home, work, school, flashback, hospital, or weather; never send all alternatives without resolving the current scene. Repeat the chosen current costume in that character's shot-level direction when text-only generation is used. For a multi-panel image, explicitly require the same chosen costume, accessories, hairstyle, damage state, and carried props in every sub-panel unless the story beat visibly changes one of them.

Temporary costume changes are state transitions, not fresh designs. If sleeves are rolled up, a jacket is removed, hair is loosened, or clothing becomes wet or damaged, persist that exact state until a visible action reverses it. For deception such as pretending to sleep, request fully closed eyelids and communicate awareness through a later eye insert, POV shot, withheld smile, or subsequent reveal; do not combine “pretending asleep” with “eyes barely open” unless the peek itself is the sole story beat.

When crossing to the opposite side of an interaction would reverse screen direction, include a neutral re-establishing view or make the spatial change explicit. Never merge two identities or duplicate a character to satisfy a complicated pose.

## Reserve Space for Post-Production Text

Design text safe areas as part of the composition, not as an afterthought. Keep the reserved area visually quiet, away from faces, hands, clues, and high-contrast edges. Place the speaking character so the bubble tail can point toward them without crossing another face.

Balance composition around the actual `post_text` positions. Do not reserve several competing empty areas when the panel has only one text block. Do not ask the image model to draw bubbles, captions, sound-effect lettering, or readable text.

## Analyze Style as Editable Visual DNA

Describe what is visibly present rather than naming an artist, copyrighted title, model, LoRA, sampler, or quality incantation. Fill the existing `style_analysis` fields with concrete, reusable observations:

- `linework`: presence, weight, variation, edge hardness, color, cleanliness, and hatching;
- `character_rendering`: proportions, facial simplification, eye treatment, anatomy stylization, and surface detail;
- `coloring`: flat/cel/painterly treatment, number and softness of shadow levels, blending, and texture;
- `background`: detail density, perspective treatment, material rendering, edge control, and character/background separation;
- `palette_lighting`: hue range, saturation, value contrast, key/fill/rim behavior, shadow color, and atmosphere;
- `composition`: typical subject scale, camera energy, negative space, depth layering, and focal hierarchy;
- `exclusions`: visible traits that must not drift in, plus text, watermark, unintended media, or incompatible rendering.

Do not infer a style from subject matter alone. School uniforms, fantasy props, or a particular character are content, not rendering style.

For a custom pack, treat the required primary image as the authority for the overall visual identity. Use zero to three auxiliary images only to clarify named dimensions such as linework, lighting, or background treatment. If an auxiliary image conflicts with the primary, preserve the primary unless the user explicitly identifies the auxiliary dimension as an override. Do not average incompatible references into a vague hybrid.

The analysis is a proposal. Show it to the user in editable language before style creation, and revise it when the user identifies a wrong inference.

## Compile Provider-Neutral Prompts

Write the shot's visual intent in clear natural language. Keep stable project style only in `preferences.style_prompt`. Set `visual.style` to an empty string unless that shot has a concrete, user-approved deviation from the project style; when a deviation exists, describe only the difference. Never copy the project style block into every shot. Avoid repeating the same long style block in `scene`, `action`, `lighting`, and `style`.

Assemble information in this conceptual order:

1. medium and intended finished-image type;
2. named characters and stable visual DNA;
3. one primary action or interaction;
4. expression and gaze evidence;
5. location, time, weather, and essential props;
6. shot size, camera position, character blocking, and focal hierarchy;
7. lighting, palette, atmosphere, and depth treatment;
8. requested linework, coloring, background, and material behavior;
9. one clean text safe area without literal lettering.

Use `visual.prompt` for the integrated visual intent, then keep `scene`, `action`, `expression`, `lighting`, and `style` concise and mutually consistent. Concrete instructions such as “soft window key light from frame left” are stronger than piles of vague quality adjectives.

Negative prompts should prevent likely drift, not become a universal dump. Include readable text, watermark, unwanted rendering medium, accidental extra characters or duplicate views when relevant, and direct conflicts with the selected style. Do not ban `multiple views` globally if the user deliberately requests a split composition, but prefer one independent image per storyboard panel. For deliberate multi-panel output, define exact panel geometry and count, then write one numbered visual beat per panel. Treat panel-count detection after generation as advisory: reject obvious extra/missing panels, but let the user confirm ambiguous border layouts instead of discarding a usable image.

Use only static-comic dynamic expressions: still, peak action, speed lines, restrained motion blur, follow composition, or impact composition. A still image cannot pan, tilt, dolly, or track over time; never describe those as operational camera movement controls.

Make the selected dynamic expression visible in the integrated prompt:

- `still`: stable silhouette and one held instant, with no speed lines or blur;
- `action_peak`: one exact anticipation/contact/result phase, clear weight shift, and readable limb direction;
- `speed_lines`: directional lines behind the moving subject while face, hands, costume, and key prop stay sharp;
- `motion_blur`: restrained blur only on the moving limb, hair tips, or prop, with the endpoint sharp;
- `follow_composition`: the subject enters open space and environment lines reinforce the movement path;
- `impact_composition`: one dominant contact or reaction point with strong foreground scale and compressed depth.

Do not mark a static conversation pose as non-`still` merely to satisfy the chapter quota. Redesign the beat around a truthful gesture, entrance, handoff, changed distance, reaction, or object interaction, or leave it `still` and let another shot carry the movement.

For a `natural` project using a two-dimensional anime or manga style without provider-attached style references, descriptive mood alone is insufficient. The editable project style prompt must begin with a binding medium statement in the user's working language and cover all four controls:

1. the finished output is a pure two-dimensional anime, manga, TV-animation still, anime-film still, or commercial anime illustration;
2. characters use visible drawn linework and clean flat color regions;
3. shadows use a stated small number of hard-edged cel levels rather than continuous realistic volume shading;
4. faces and skin remain visibly drawn and flat, even when anatomy, perspective, environments, or composition are described as realistic or cinematic.

Add matching exclusions for photography, live-action faces, realistic skin texture, semi-realistic digital painting, soft continuous volume rendering, unoutlined characters, and 3D/CGI. Unless the user explicitly requests it, do not write the Chinese term `写实` into generation-facing project data, including exclusions; name the unwanted visible trait directly. Treat broad terms such as cinematic, natural proportions, detailed materials, and depth of field as drift risks unless the same prompt explicitly limits what they mean. Do not rely on generic labels such as `日漫风格` or `高质量二次元` to enforce the rendering medium.

Never assume bracket weighting, numeric weights, tag ordering, artist strings, work-title imitation, quality tags, or negative-prompt syntax transfers between providers. Keep any provider-specific conversion isolated to the generation integration; it is not part of storyboard reasoning.

## Visual QA Before Import

For every shot, verify:

- the composition makes the declared story beat obvious at thumbnail size;
- shot size preserves the required face, hands, body action, and environment rather than requesting all at once;
- camera angle has a narrative reason and does not contradict character facing;
- aspect ratio fits the number of characters, movement direction, and required environment;
- one subject or interaction owns the focal hierarchy;
- adjacent shots preserve screen direction, props, costume state, location, time, and light direction;
- eye state, posture, hand occupancy, prop state, costume state, and action phase are internally consistent;
- the dynamic expression is visible in the integrated prompt rather than existing only as metadata;
- text safe areas match every post-production block and do not cover story evidence;
- style fields describe rendering behavior rather than subject matter or imitation labels;
- primary and auxiliary references have clear, non-conflicting roles;
- prompts contain no literal dialogue and no provider-specific folklore presented as a universal rule.

If a shot fails because it asks one still image to show incompatible moments or viewpoints, revise the beat allocation or return to the user for a panel-count decision. Do not hide the conflict in a longer prompt.
