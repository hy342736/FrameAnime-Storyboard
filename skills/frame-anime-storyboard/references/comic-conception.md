# Shared Comic Conception

Use this provider-neutral planning reference for every route. It does not prescribe NAI tags or GPT syntax.

## 1. Start With the Dramatic Beat

Before writing a shot, privately answer: **what must the reader notice, feel, or understand in this image?** Keep one primary beat per shot. A beat that requires a reveal, an irreversible action, and a reaction usually needs separate causal shots rather than one overloaded prompt.

Classify source material as:

- **Keep:** causality, irreversible actions, relationship turns, clues and payoffs, and spatial facts needed to understand the scene.
- **Visualize:** inner thoughts or exposition that can become a gesture, object, contrast, facial change, or environmental evidence.
- **Compress:** repeated travel, routine actions, redundant dialogue, and transitions whose causal role survives compression.
- **Cut:** decoration that changes neither understanding, emotion, nor rhythm.

Do not derive the shot count from character count alone. Count meaningful visual beats, scene changes, consequential actions, reactions, reveals, dialogue density, and spatial transitions. Recommend one exact count and explain what is retained or compressed before drafting.

## 2. Build the Space Before Styling It

For each shot, establish in this order:

1. camera height, viewing direction, and shot size;
2. foreground, midground, and background;
3. character left/right order, depth, facing direction, and gaze target;
4. the focal subject and the quiet area reserved for later text;
5. only then, lighting, palette, atmosphere, and rendering behavior.

Complex scenes need visible geometry: who is closer, who is behind whom, who touches or looks at what, which object blocks part of the view, and where movement travels. Keep one dominant shot size and at most one special perspective device. Use an establishing or neutral view before a close reaction when the location or blocking would otherwise be unclear.

## 3. Freeze a Drawable Action

Describe one observable moment with a subject, verb, object, and receiver: who does what to whom, what changes, and what physical evidence proves the emotion. Avoid abstract directions such as “show tension” without a gesture, distance, prop state, expression, or posture.

Resolve the action phase precisely: anticipation, contact, result, or reaction. Resolve incompatible states instead of listing alternatives: eyes fully closed or open, prop held or dropped, seated or standing, sleeves rolled or unrolled. A temporary change persists into later shots until a visible action reverses it.

## 4. Maintain a Continuity Ledger

Across adjacent shots, track:

- character identity, hair, costume, accessories, damage, wetness, and dirt;
- left/right screen direction, entrances, exits, and gaze direction;
- held objects, hand occupancy, and prop ownership;
- location layout, time, weather, key light direction, and action phase.

Every shot must resolve the current state of relevant attributes. Do not ask the model to choose between multiple costumes or poses. For text-only generation, repeat the necessary identity and current-costume anchors in the shot-level generation prompt even when they also exist in the character library.

## 5. Use Multi-Panel Images Selectively

One generated image may contain multiple panels only when the panels form a tightly coupled cause/reaction, short action progression, contrast, detail-to-main relationship, or impact beat. Use separate shots when time, location, viewpoint, or character state changes substantially. Multi-panel composition is authored by the Agent in the final provider prompt; it is not selected by an application layout control.

When a multi-panel image is used, specify the exact count, each panel's position, the shared character and costume anchor, clean gutters, and no generated text. Keep the same light and basic setting across panels unless the change is the point of the beat. Follow the project's provider-specific prompt contract for the final syntax.

## 6. Translate Prose Into Image Evidence

Do not copy plot summaries, personality labels, or world history into every image prompt. Convert only visible facts needed for the current shot: a framed photograph, a damaged object, a change in distance, a hand stopping another hand, a reflected silhouette, or a character's changed expression. The image prompt should be self-contained enough for its one shot while remaining concise.

The conversational planning layer may remain Chinese. Generation-facing fields follow the selected project route: GPT uses clear natural-language instructions; NAI uses concise English tag/sentence fields. The planning method is shared, but provider-specific syntax, parameters, weights, and negative-prompt conventions are not.

## 7. Quality Gate

Before saving a shot, confirm that:

- the beat is readable at thumbnail size;
- camera, depth layers, blocking, and action agree;
- each relevant character has one current costume and one action;
- the next shot can follow without an unexplained state jump;
- text-safe space does not cover faces, hands, clues, or the focal action;
- the chosen aspect ratio fits the staging;
- style language describes visible rendering behavior, not only mood or subject matter.
