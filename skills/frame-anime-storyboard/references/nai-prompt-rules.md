# NAI and Tag-Oriented Anime Prompt Rules

Read this reference and [nai-safe-vocabulary.md](nai-safe-vocabulary.md) only when FrameAnimeDesk resolves the generation prompt profile as `nai`, or when the user explicitly says the target is NovelAI or another tag-oriented anime model. These rules refine provider-neutral visual direction for anime-specialized models. The companion vocabulary library covers reusable safe visual concepts; neither file is an exhaustive tag dictionary or a promise of provider behavior.

Preserve only generic, observable visual concepts. Exclude artist strings, copyrighted style imitation, large uncurated prompt collections, and unsupported model folklore. Examples in this reference are guidance rather than guaranteed provider behavior.

## Keep Two Layers

First decide the story beat, character blocking, camera, canvas, light, and rendering behavior using `visual-direction-rules.md`. Persist those decisions in concise English in the normal storyboard fields, then compile the final English positive and negative prompts. The Chinese conversation remains the planning surface; the saved NAI project is the image-facing review surface.

Then make the image-facing wording easy for FrameAnimeDesk's NAI compiler to organize:

- Use compact English visual phrases for every generation-facing concept. If an exact translation is uncertain, use plain factual English rather than leaving Chinese or inventing a specialized tag.
- Keep names attached to each character's appearance, position, action, expression, and gaze. Never put all appearances first and all actions later in a multi-character shot.
- Do not write bracket weights, numeric weights, artist names, work-title imitation, sampler, scheduler, steps, CFG, or seed into shot fields.
- Do not replace a precise story fact with a fashionable quality tag.
- Source quotations, shot titles, checklist notes, and post-production text may remain Chinese because they are excluded from generation. Do not place literal dialogue into image-facing fields.

FrameAnimeDesk treats the saved `nai_positive_prompt` and `nai_negative_prompt` as the complete remote generation contract. It normalizes and orders the positive tags, and sends exclusions as a separate `negative_prompt` when the configured Images-compatible endpoint accepts that field. It does not append World Bible, character-library fields, style analysis, project style prompts, or references at send time. Therefore every visible fact required by the current shot must be present once in the final positive prompt.

## Minimal Transmission Contract

Keep rich context in the project for planning, editing, traceability, and continuity review, but do not copy it wholesale into every final prompt.

Include in the positive prompt only what is visible and necessary in the current image:

- cast count;
- each visible character's few identity-critical appearance and costume cues;
- current pose, action, expression, gaze, and spatial relationship;
- camera distance and viewpoint;
- immediate location anchors, time or weather only when visually relevant;
- active light and palette relationship;
- one concise rendering treatment.

Do not include world name, history, factions, political or magic-system explanation, rules and taboos, off-screen geography, character role or personality labels, plot summary, source prose, dialogue, continuity commentary, reference mapping, output-size prose, or repeated synonyms. A world or character fact may enter the prompt only after rewriting it as a concrete visible fact needed in that image. For example, omit `the city bans magic`; include `concealed glowing sigil under her sleeve` only when the sigil is actually visible and story-relevant.

Keep the negative prompt short and shot-relevant. Do not paste the entire project exclusion library into every request. Normally retain text/logo/watermark, accidental extra or duplicate people for character shots, identity merging for multi-character shots, and a small number of anatomy or media conflicts that are plausible for this image.

## Prompt Order and Density

Build the positive prompt in this order unless a shot needs a clear exception:

1. cast count and subject type;
2. one grouped identity/action block per named character;
3. shared interaction and spatial relationship;
4. camera distance, viewpoint, crop, and composition;
5. location, time, weather, and important props;
6. light source, direction, shadow behavior, and palette;
7. one coherent medium/rendering treatment;
8. a restrained quality finish.

Keep the decisive nouns and relationships early. Remove duplicates and near-synonyms. Do not treat a longer prompt as a better prompt. Use braces or numeric emphasis only when the user explicitly understands the target provider's syntax and asks for it; the Skill's default manifest uses unweighted phrases.

## Character Vocabulary

Describe only visible, reusable facts:

- life stage and silhouette: `adult woman`, `adult man`, `slender build`, `broad shoulders`, `short stature`;
- hair: length, shape, color, fringe, tied state, and one distinctive feature;
- face and eyes: eye color, eyebrow shape, freckles, glasses, or another stable cue when established;
- clothing: garment type, construction, color, layer, footwear, and recurring accessory;
- expression and gaze: `restrained smile`, `furrowed brows`, `wide eyes`, `looking at CHR-002`, `looking away`;
- pose and gesture: `standing`, `kneeling`, `leaning forward`, `arms crossed`, `holding a letter with both hands`, `reaching toward`.

Do not use value judgments about bodies, race-coded stereotypes, or age-ambiguous sexualized descriptions. Character names are binding labels for the project, not a substitute for visible DNA.

## Clothing and Props

Prefer concrete construction over broad fashion labels: `navy wool coat over a white shirt`, `orange scarf tied loosely`, `black ankle boots`, `silver rectangular wristwatch`. Keep one recognizable costume per continuity span and call out intentional changes. Attach every held or exchanged prop to its owner and hand when that ownership matters.

Safe clothing vocabulary may cover everyday, school, workplace, historical, ceremonial, protective, and fantasy garments when appropriate to the story. Exclude lingerie/fetish prompt lists and sexualized clothing guidance from this Skill.

## Environment and Palette

For outdoor scenes, combine a place type with terrain, season/weather, time, and two or three visible anchors: `coastal town street, wet asphalt, utility poles, closed shops, after rain, blue hour`. For interiors, name room function, architecture/materials, important furniture, practical light sources, and signs of use: `small apartment entryway, white plaster walls, dark wood floor, shoe cabinet, umbrella stand, cool ceiling light`.

Control color with a small relationship rather than a color dump: `cool cyan ambient light with one warm coral accent`, `low-saturation blue-gray background, natural skin tones`, or `white concrete, teal signage, orange safety markings`. Keep project palette in English World Bible fields and shot-specific deviations in the shot.

## Composition and Special Layouts

Use composition terms only when they solve a visual problem: `centered composition`, `rule of thirds`, `symmetrical composition`, `diagonal composition`, `foreground framing`, `negative space on upper right`, `reflection in window`, `silhouette`, `depth of field`. A split composition, mirror/reflection shot, foreground occlusion, or frame-within-frame must still describe one readable primary beat and must reserve post-text space without asking the model to draw a bubble.

For food, tools, vehicles, documents, and other props, describe visible type, material, state, placement, and owner. Avoid brand marks and readable text.

## Safe Interaction Vocabulary

For multi-character emotion and action, prefer observable geometry and contact: `standing one step apart`, `facing each other`, `avoiding eye contact`, `handing a letter to`, `supporting by the shoulder`, `walking side by side`, `one character in foreground and one near the doorway`. Keep interactions non-sexual and story-relevant. Festivals and fantasy scenes may use generic visual elements such as lanterns, paper streamers, market stalls, ceremonial robes, floating light particles, ancient stone gates, or luminous plants without naming copyrighted settings.

## Stable Vocabulary

Use only the concepts that match the actual shot.

Camera distance:

- `extreme wide shot`: geography or scale;
- `wide shot`: environment-led staging or several bodies;
- `full body`: whole-body action;
- `medium shot`: dialogue, gestures, and two-character interaction;
- `cowboy shot`: crop around thighs or knees when hands and expressions both matter;
- `close-up`: one face, hand, or clue;
- `extreme close-up`: one tiny decisive detail.

Viewpoint:

- `eye level`, `front view`, `from side`, `profile`, `from behind`;
- `from behind, looking back` only for a real look-back beat;
- `from above` or `directly above` for vulnerability or spatial pattern;
- `from below` for authority, threat, or scale;
- `dutch angle`, `foreshortening`, or `fisheye` only with a narrative reason.

When a side view must show a true profile, add the visible gaze direction rather than relying on `from side` alone. Do not combine contradictory views.

Rendering behavior:

- clean anime flat color: `clean lineart`, `flat color`, `cel shading`;
- animation-frame finish: `anime illustration`, `anime screencap`, `anime coloring`;
- painterly finish: describe softer edge control, richer tonal transitions, visible brush texture, or `no lineart` only when the selected art direction requires them;
- monochrome drawing: `monochrome`, `greyscale`, then the intended `pencil sketch`, `lineart`, `crosshatching`, or ink behavior;
- chibi: `chibi`, `chibi only` when the whole figure must remain chibi;
- pixel work: `pixel art`; do not mix it casually with unrelated painterly or artist-style strings.

Avoid vague stacks such as every quality adjective, every lighting effect, and several incompatible media in one prompt. A clean, internally consistent rendering description is more useful.

## Lighting

Name the real source and direction before adding an effect:

- source or time: `sunlight`, `moonlight`, `window light`, `candlelight`, `neon lighting`, `stage lights`, `spotlight`, `golden hour`, `twilight`;
- direction: `front lighting`, `sidelighting`, `backlighting`, `top lighting`, `underlighting`, `rim lighting`;
- shadow behavior: `soft shadow`, `hard shadow`, `deep shadow`, `subtle shadow`, `dappled sunlight`;
- atmosphere used sparingly: `bloom`, `volumetric lighting`, `light particles`, `lens flare`.

Use `soft lighting` for subdued overcast, rain, snow, or intimate interiors. Use stronger contrast or `chiaroscuro` only when the dramatic beat needs it. Do not combine soft low-contrast light with several aggressive contrast terms unless the shot explicitly has separate light zones. For cold-warm contrast, state the source relationship, such as cool ambient rain light with warm shop light, rather than merely listing colors.

## Canvas and Subject Scale

The API's actual width and height control the canvas; a ratio written only in prose is not reliable. Match composition to the selected ratio:

- portrait canvases suit full body, single-character posture, and vertical depth;
- square canvases suit half body, face-led moments, and balanced single beats;
- landscape canvases suit two-character upper-body interaction, horizontal movement, and environment-led staging.

Do not request distant full bodies when faces and subtle interaction are the story evidence. Use a medium or cowboy shot instead. FrameAnimeDesk rounds NAI-oriented dimensions to model-friendly multiples, but the provider may still reject unsupported sizes.

## Multiple Characters

Tag-oriented models are less reliable than instruction-following models at binding many attributes to different people. For every selected character, repeat the name with:

- stable face and hair cues;
- frame position and facing direction;
- individual action and held prop;
- expression and gaze target.

State visible geometry such as left/right order, foreground/background, distance, and who touches or hands an object to whom. Keep one primary shared interaction. Warn the user when a shot depends on exact identity or prop binding without references; do not block manual generation solely for this risk.

## Negative Prompt

Use a short shot-relevant exclusion list. Normally include readable text, logo, watermark, accidental extra people, duplicate character, merged bodies, wrong prop ownership, and the rendering media that conflict with the chosen style. Add anatomy exclusions only when useful. Do not ban `multiple views` when the user intentionally requested a split composition.

If the selected endpoint does not support a native negative prompt, FrameAnimeDesk may have to place exclusions into positive text or omit them. Never promise equivalent behavior across providers.

## Learning from Artist Strings

When a user supplies artist strings or named-style examples, do not use them as default prompt content. Extract observable properties and rewrite them as generic controls: `thin confident linework`, `bold graphic outlines`, `soft watercolor edges`, `limited pastel palette`, `high-contrast monochrome`, `flat cel shading`, `muted colors`, `rough pencil texture`, `cinematic rim lighting`, or `detailed environmental background`. Store those generic properties in the project's editable style analysis and English style prompt.

Do not automatically emit a named artist, an `artist:` token, a list of artists, `official style`, or `style of <artist/work>` in a storyboard manifest. Named artist strings are unstable across model versions, can dominate the character design, and turn a reproducible project into an imitation request. If the user explicitly supplies an artist string for private experimentation, preserve it only as a user-visible note outside the generated manifest and ask them to replace it with observable style traits before importing. The same rule applies to franchise names, game/anime titles, official-art labels, and character names from unrelated works.

Useful style extraction questions are: are contours clean or rough; is line weight uniform or varied; are colors flat, pastel, muted, saturated, or monochrome; are shadows cel-shaped or softly blended; are backgrounds detailed or minimal; is the medium ink, pencil, watercolor, oil, pixel, 3D, or photographic; is the camera cinematic, editorial, graphic, or manga-like; and does the palette have a deliberate warm/cool relationship? Answer those questions instead of copying the source string.

## Pre-Import Check

Before import, confirm that:

- the NAI vocabulary expresses the already-decided visual intent rather than replacing it;
- each character's facts remain grouped and distinguishable;
- camera distance, angle, canvas, and subject scale agree;
- light source, direction, shadow, and atmosphere do not contradict one another;
- the style requests one coherent medium;
- no artist string, copyrighted work imitation, unsupported generation setting, literal dialogue, or prompt-dump residue entered the manifest.
