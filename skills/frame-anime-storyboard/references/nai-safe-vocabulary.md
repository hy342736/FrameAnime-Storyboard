# NAI Safe Vocabulary and Composition Library

This is a curated working library of generic visual concepts for writing new NAI storyboard manifests. It is not a prompt dump and not a guarantee that every provider treats every tag identically.

The library covers reusable safe domains: medium and rendering, quality restraint, camera and composition, color and light, character appearance, hair and face, clothing, poses and gestures, expressions and gaze, environments, weather and time, food and props, everyday scenes, festivals, fantasy settings, special compositions, and multi-character blocking. It intentionally omits explicit sexual content, fetishized or nude clothing, sexual violence, gore, blood, mutilation, torture, artist-name strings, copyrighted character or franchise/style imitation, brand marks, and unsupported sampler/step/CFG folklore.

## How to Use This Library

Choose the visual fact first, then select the smallest vocabulary group that expresses it. A shot normally needs:

1. subject count and character identity;
2. pose, action, expression, and gaze;
3. shot distance, viewpoint, crop, and composition;
4. location, time, weather, and important props;
5. light source, direction, shadow, and palette;
6. one coherent rendering medium;
7. a short, shot-specific negative prompt.

Use commas as separators. Keep a tag close to the noun it qualifies. Repeat the character's identifying details inside that character's block in a multi-character shot. Do not concatenate every synonym in a category. A term is useful only when it changes what should be visible.

Use these vocabulary items as English generation-facing content. The project's Chinese source passage, title, source anchor, checklist explanation, and post-production dialogue remain outside this library and must not be copied into the positive prompt.

## Subject Count and Identity

Use the count that matches the intended visible cast:

- `solo`, `1girl`, `1boy`, `1person` for one clear subject;
- `2girls`, `2boys`, `2people`, `multiple people` for a small visible group;
- `group`, `crowd`, `background people` only when the group itself matters;
- `no humans`, `empty scene`, `animal focus`, `object focus` when no human is intended.

For continuity, pair each count with a compact identity block. Useful identity cues include `adult woman`, `adult man`, `young adult`, `elderly woman`, `slender build`, `average build`, `broad shoulders`, `short stature`, `distinctive face`, `freckles`, `round glasses`, `earring`, `hair ornament`, and a named project identifier when that identifier is already English. Do not use age ambiguity or sexualized body descriptors as a shortcut for identity.

For multiple subjects, explicitly state geometry: `character on frame left`, `character on frame right`, `foreground`, `background`, `near the doorway`, `one step apart`, `standing side by side`, `facing each other`, `back to back`, `between the two characters`, `behind the table`, `hands visible`, `clear separation between figures`.

## Hair, Face, and Eyes

### Hair Shape

Useful hair construction terms include:

- length: `short hair`, `medium hair`, `long hair`, `very long hair`;
- shape: `straight hair`, `wavy hair`, `curly hair`, `messy hair`, `fluffy hair`, `floating hair`;
- arrangement: `ponytail`, `high ponytail`, `side ponytail`, `twin tails`, `braid`, `single braid`, `side braid`, `hair bun`, `low bun`, `half updo`, `hair ribbon`;
- fringe: `blunt bangs`, `side-swept bangs`, `parted bangs`, `asymmetrical bangs`, `hair between eyes`, `long bangs`, `ahoge`;
- placement: `hair over one eye`, `hair over shoulder`, `side locks`, `sidelocks`, `stray hair`, `hair strand across face`;
- color: `black hair`, `brown hair`, `dark blue hair`, `silver hair`, `white hair`, `blonde hair`, `red hair`, `pink hair`, `purple hair`, `green hair`, `two-tone hair`, `colored inner hair`.

Pick one length, one shape, one arrangement, and one or two colors. Do not list every hairstyle at once. If a color is important to continuity, put it early in the character block and repeat it only when the model needs reinforcement.

### Face and Eyes

Useful visible cues include `blue eyes`, `green eyes`, `gray eyes`, `amber eyes`, `red eyes`, `violet eyes`, `brown eyes`, `sharp eyes`, `soft eyes`, `round eyes`, `narrow eyes`, `half-closed eyes`, `closed eyes`, `downcast eyes`, `looking to the side`, `looking up`, `looking down`, `eye contact`, `profile`, `freckles`, `beauty mark`, `eyepatch`, `glasses`, `round glasses`, `thin eyebrows`, `furrowed brows`, `open mouth`, `closed mouth`, `parted lips`, and `covered mouth`.

Use `heterochromia` only when the story or character design requires it. Use `profile` together with a visible gaze direction when a true side view matters. Avoid combining `looking at viewer`, `looking away`, `looking down`, and `eye contact` for the same character unless the shot intentionally shows different subjects with those actions.

## Clothing Construction

Describe clothing as garment, layer, material or color, and one construction detail. Safe everyday and professional vocabulary includes:

- tops: `white shirt`, `blouse`, `turtleneck sweater`, `hoodie`, `cardigan`, `vest`, `collared shirt`, `sailor collar`, `detached collar`, `long sleeves`, `short sleeves`, `wide sleeves`, `puffy sleeves`;
- outerwear: `trench coat`, `wool coat`, `long coat`, `short jacket`, `hooded cape`, `capelet`, `raincoat`, `winter coat`, `work jacket`, `lab coat`, `military coat`, `apron`;
- lower garments: `pleated skirt`, `long skirt`, `trousers`, `wide-leg pants`, `dress pants`, `shorts`, `culottes`, `hakama`, `overalls`;
- dresses and formal wear: `long dress`, `shirt dress`, `formal dress`, `ceremonial robe`, `traditional kimono`, `yukata`, `hanfu`, `qipao`, `school uniform`, `business suit`, `vestment`, `stage costume`;
- footwear: `ankle boots`, `knee boots`, `lace-up boots`, `loafers`, `mary jane shoes`, `sneakers`, `sandals`, `wooden sandals`, `indoor shoes`;
- accessories: `scarf`, `necktie`, `ribbon`, `brooch`, `pendant`, `earrings`, `hair ornament`, `hairpin`, `gloves`, `wristwatch`, `belt`, `shoulder bag`, `backpack`, `sheathed sword`, `tool belt`;
- materials and finish: `wool`, `cotton`, `linen`, `leather`, `denim`, `knit texture`, `embroidered trim`, `gold trim`, `silver clasp`, `brass buttons`, `layered fabric`, `visible seams`, `weathered fabric`, `wet fabric`.

For continuity, specify a stable base outfit and state intentional changes with `alternate outfit`, `winter version`, `work clothes`, `ceremonial version`, or `rain-soaked outerwear`. Do not combine incompatible eras or unrelated costume systems without an explicit story reason. Exclude underwear, lingerie, fetish clothing, transparent sexualized garments, and erotic body emphasis from generated story prompts.

## Poses and Body Language

### Basic Poses

`standing`, `sitting`, `kneeling`, `squatting`, `lying down`, `leaning against wall`, `leaning forward`, `leaning back`, `walking`, `running`, `jumping`, `falling`, `floating`, `turning around`, `looking back`, `reaching`, `bending slightly`, `resting chin on hand`, `arms crossed`, `hands behind back`, `one knee raised`, `legs crossed`, `kneeling beside`, `standing on stairs`.

### Hand and Prop Actions

`holding a book`, `opening a book`, `holding an umbrella`, `holding a cup`, `holding a letter`, `holding a lantern`, `holding a camera`, `holding a flower`, `holding a suitcase`, `holding a sword`, `wearing a backpack`, `adjusting glasses`, `adjusting a hat`, `tucking hair behind ear`, `touching the window`, `pointing toward the street`, `reaching for a door handle`, `writing at a desk`, `turning a page`, `handing a letter to`, `offering a cup`, `passing a document`, `supporting by the shoulder`, `waving`, `saluting`, `waving goodbye`.

Attach ownership and contact explicitly: `CHR-001 holds the letter`, `CHR-002 reaches toward the letter`, `left hand holding`, `right hand on the door handle`. The application may replace project identifiers with nearby natural English, but the relationship must remain unambiguous. Avoid vague `holding something` when the prop changes the story.

### Motion and Fabric

Use one or two motion cues when they explain the image: `wind-blown hair`, `coat billowing`, `flowing ribbons`, `falling leaves`, `falling petals`, `splashing water`, `steam rising`, `smoke drifting`, `motion lines`, `motion blur`, `dynamic pose`, `midair`, `dust particles`, `light particles`. Do not use motion blur in a quiet close-up unless the shot intentionally shows movement.

## Expressions, Emotion, and Gaze

Visible expression vocabulary includes `neutral expression`, `expressionless`, `calm smile`, `gentle smile`, `light smile`, `serious`, `determined`, `focused`, `thoughtful`, `confused`, `surprised`, `shocked`, `worried`, `sad`, `restrained sadness`, `anxious`, `embarrassed`, `shy smile`, `annoyed`, `angry`, `frown`, `furrowed brows`, `teary eyes`, `crying`, `closed eyes`, `open mouth`, `nervous smile`, `awkward expression`, `tired eyes`, `sleepy`, `relieved`, `proud`, `curious`, `playful`, `frightened`, `lonely`.

Gaze is a separate control: `looking at viewer`, `looking at another character`, `looking at CHR-002`, `looking away`, `looking down`, `looking up`, `looking toward the doorway`, `looking toward the light`, `eye contact`, `sideways glance`, `head turned toward`, `face turned away`. One character can look away while another maintains eye contact; state that separately. Do not turn an abstract emotion into an unobservable tag if a gesture or gaze can carry it.

## Camera Distance and Crop

Choose the crop based on story evidence:

- `extreme wide shot`: geography, scale, isolation, or a group in an environment;
- `wide shot`: full staging, several bodies, movement through a location;
- `full body`: whole-body pose or action;
- `cowboy shot`: thigh/knee crop when both hand action and face matter;
- `medium shot`: dialogue, gestures, and two-person interaction;
- `upper body`: torso, arms, and expression;
- `close-up`: face, hand, letter, tool, or clue;
- `extreme close-up`: a tiny decisive detail such as an eye, seal, key, or cracked object;
- `portrait`: face-led or bust-led presentation when environment is secondary.

Match canvas to crop. Portrait ratios support a full figure or vertical depth; landscape ratios support a horizontal exchange or environment; square ratios support face-led or centered compositions. The actual API width and height remain authoritative; tags cannot override an incompatible canvas.

## Viewpoint and Lens Language

Use one primary viewpoint and only compatible modifiers:

- `eye level`, `front view`, `from side`, `profile`, `from behind`, `over-the-shoulder`, `from above`, `directly above`, `from below`;
- `low angle`, `high angle`, `dutch angle`, `dynamic angle`, `foreshortening`, `perspective`, `vanishing point`;
- `fisheye`, `wide-angle lens`, `telephoto compression`, `shallow depth of field`, `deep depth of field`, `foreground blur`, `background blur`, `bokeh`.

`from behind, looking back` means the subject is genuinely turning back. `from side` does not guarantee a profile; add `profile` and a gaze direction if needed. Avoid `from above` and `from below` together unless the shot deliberately contains separate spatial viewpoints, which is usually better represented as a split composition.

## Composition and Framing

Useful composition controls include `centered composition`, `symmetrical composition`, `asymmetrical composition`, `rule of thirds`, `diagonal composition`, `triangular composition`, `leading lines`, `negative space`, `foreground framing`, `frame within frame`, `reflection`, `reflection in window`, `mirror reflection`, `silhouette`, `overlapping foreground`, `subject off-center`, `balanced composition`, `dynamic perspective`, `low horizon`, `high horizon`, `close framing`, `full environment`, `subject focus`, `object focus`, `face focus`, `hand focus`.

Use negative space to reserve lettering: `negative space on upper right`, `clean space above the characters`, `open sky on the left`, `uncluttered lower third`. Never ask the image model to draw readable speech, captions, bubbles, logos, signs, or page text. The app adds post-production text later.

### Special Layouts

For an intentional special layout, combine the layout with a single readable beat:

- `split composition`: two simultaneous locations or viewpoints with a clear divider;
- `multiple views`: only when several views are the actual subject, never as a generic quality tag;
- `reflection in water`, `reflection in glass`, `mirror reflection`: make the reflecting surface visible;
- `foreground silhouette`, `doorway framing`, `window framing`, `curtain framing`: use an object to establish depth;
- `montage`, `faint background faces`, `background panels`: use sparingly for memory or information design, and disclose that it is a special composition;
- `comic panel`, `manga panel`, `speech bubble area`, `white border`: use only as composition or post-production planning, never as a request for generated readable text.

Do not place `multiple views` in a negative prompt when the story deliberately needs it. Conversely, use it as a negative only when unwanted duplicated viewpoints are a known failure mode.

## Scene, Place, Time, and Weather

### Outdoor Places

Combine place type, visible anchors, time, and weather:

- `city street`, `residential street`, `alley`, `shopping street`, `market street`, `train station`, `railway platform`, `bus stop`, `bridge`, `rooftop`, `school courtyard`, `playground`, `park`, `garden`, `flower field`, `forest`, `bamboo forest`, `mountain path`, `coastal town`, `beach`, `riverbank`, `lake`, `desert`, `wasteland`, `snowy field`;
- anchors: `utility poles`, `street lamps`, `railway tracks`, `station sign without readable text`, `shop windows`, `wooden fence`, `stone wall`, `bench`, `bicycle rack`, `puddles`, `cobblestone path`, `wrought iron railing`, `flower beds`, `windmill`, `tower`, `stairs`;
- atmosphere: `open sky`, `cloudy sky`, `mist`, `sea fog`, `light rain`, `heavy rain`, `snowfall`, `falling leaves`, `falling petals`, `wind`, `dusty air`, `wet pavement`, `long shadows`.

### Indoor Places

`apartment entryway`, `bedroom`, `living room`, `kitchen`, `cafe`, `restaurant`, `library`, `classroom`, `office`, `laboratory`, `workshop`, `radio room`, `theater stage`, `backstage`, `train interior`, `shop interior`, `greenhouse`, `church interior`, `castle hall`, `wooden veranda`, `traditional room`, `archive room`, `underground chamber`.

Add materials and set dressing: `white plaster walls`, `dark wood floor`, `tatami floor`, `paper screens`, `shoe cabinet`, `umbrella stand`, `bookshelves`, `desk lamp`, `wooden table`, `cafe counter`, `paper documents`, `potted plant`, `curtains`, `window`, `stained glass window`, `old machinery`, `cables`, `shelves`, `storage boxes`, `stone columns`, `arched doorway`, `wall clock`, `hanging lantern`.

### Time and Weather

`morning`, `late morning`, `afternoon`, `golden hour`, `sunset`, `dusk`, `blue hour`, `twilight`, `night`, `midnight`, `before dawn`, `sunny`, `overcast`, `after rain`, `rainy`, `snowy`, `foggy`, `windy`, `humid`, `dry air`, `summer`, `autumn`, `winter`, `spring`.

Use one or two weather signals and connect them to the scene: `after rain, wet pavement and reflected street lights`; `winter evening, visible breath and snow on the railing`; `summer afternoon, hard sunlight and short shadows`.

## Light Sources and Shadow Behavior

### Sources and Direction

`sunlight`, `moonlight`, `window light`, `skylight`, `candlelight`, `lantern light`, `firelight`, `street lamp`, `fluorescent light`, `desk lamp`, `neon lighting`, `stage lights`, `spotlight`, `rim light`, `backlighting`, `front lighting`, `sidelighting`, `top lighting`, `underlighting`, `dappled sunlight`, `reflected light`, `ambient light`.

### Shadow and Effects

`soft shadow`, `hard shadow`, `deep shadow`, `subtle shadow`, `long shadow`, `cast shadow`, `contact shadow`, `rim lighting`, `chiaroscuro`, `light rays`, `volumetric lighting`, `bloom`, `light particles`, `lens flare`, `glow`, `reflected highlights`, `wet surface reflections`, `window shadow`, `tree shadow`, `colored light`, `flickering light`.

Name the source and direction first. Examples: `cool moonlight from the window, soft shadows`; `warm sunset backlighting, rim light on the hair`; `cyan neon sidelighting with a small coral reflected highlight`. Do not stack `soft lighting`, `hard shadow`, `deep shadow`, and `high contrast` without describing separate light zones.

## Color and Material Control

Useful palette language includes `white theme`, `black and white`, `blue theme`, `cyan theme`, `teal accents`, `orange accents`, `coral accents`, `red and gold`, `blue and white`, `muted colors`, `pastel colors`, `limited palette`, `high contrast`, `low contrast`, `cool tone`, `warm tone`, `cool-warm contrast`, `monochrome`, `greyscale`, `duotone`, `inverted colors`, `colorful`, `desaturated background`, `natural skin tones`.

Material cues include `wet asphalt`, `oxidized copper`, `brushed metal`, `rusted metal`, `old glass`, `cracked glass`, `polished wood`, `rough stone`, `cobblestone`, `paper texture`, `fabric texture`, `wool texture`, `silk folds`, `leather texture`, `ceramic cup`, `transparent water`, `frosted glass`, `crystal`, `smoke`, `steam`, `dust`, `petals`, `leaves`.

Prefer a palette relationship instead of a color list. Use `white concrete with cyan signage and restrained orange safety markings`, not ten unrelated color tags. Match material to light: `wet asphalt reflecting cool blue street lamps`, `brass machinery catching warm rim light`.

## Rendering and Medium

Choose one coherent rendering family:

- anime finish: `anime illustration`, `anime screencap`, `anime coloring`, `clean anime lineart`, `flat color`, `cel shading`;
- linework: `clean lineart`, `bold lineart`, `thin lineart`, `varying line weight`, `colored lineart`, `rough lineart`, `sketchy lineart`, `crosshatching`;
- traditional media: `pencil sketch`, `graphite drawing`, `colored pencil`, `watercolor`, `gouache`, `acrylic paint`, `oil painting`, `ink drawing`, `dry brush texture`, `paper texture`, `rough brushwork`;
- print and comic: `monochrome manga`, `halftone shadow`, `screen tones`, `comic cover composition`, `white border`, `black ink`, `limited print palette`;
- graphic and stylized: `flat graphic design`, `poster composition`, `silhouette`, `stained glass pattern`, `mosaic pattern`, `pixel art`, `simple shapes`, `bold color blocks`;
- three-dimensional or photographic only when explicitly required: `3d render`, `game screenshot`, `photographic background`, `realistic materials`. Do not mix these casually with clean flat anime rendering.

Quality vocabulary should be restrained: `best quality`, `high quality`, `highres`, `detailed background`, `intricate details`, `sharp focus`, `crisp edges`, `refined linework`, `finished illustration`, `cinematic composition`. These do not repair wrong anatomy, wrong identities, or a contradictory scene. Avoid very long stacks of near-synonyms and avoid unsupported numeric weights in the storyboard manifest.

## Food, Objects, and Everyday Activity

Safe object vocabulary includes `tea cup`, `coffee cup`, `steaming mug`, `bento box`, `rice bowl`, `ramen bowl`, `cake slice`, `pastry`, `fruit`, `apple`, `strawberry`, `taiyaki`, `salad`, `soup`, `chopsticks`, `teapot`, `plate`, `vase`, `book`, `notebook`, `letter`, `envelope`, `key`, `pocket watch`, `camera`, `phone`, `microphone`, `umbrella`, `suitcase`, `briefcase`, `bicycle`, `train`, `lantern`, `flower`, `bouquet`, `map`, `document stack`, `pen`, `paintbrush`, `guitar`, `handheld game console`, `computer`, `radio equipment`, `mechanical gears`, `toolbox`, `sword`, `scabbard`, `shield`, `staff`, `crystal`, `telescope`.

Everyday action vocabulary includes `reading`, `writing`, `studying`, `drinking tea`, `eating`, `cooking`, `shopping`, `cleaning`, `working at a desk`, `checking a watch`, `waiting at a station`, `walking home`, `opening an umbrella`, `looking through a window`, `watering plants`, `arranging flowers`, `playing an instrument`, `taking a photograph`, `repairing machinery`, `sorting documents`, `serving coffee`, `exchanging a letter`.

Avoid brand names, readable labels, logos, product packaging text, and real-world identifying marks. Say `unlabeled can`, `blank sign`, or `plain document` when text must not appear.

## Festivals and Cultural Environments

Generic festive vocabulary includes `festival`, `lantern festival`, `summer festival`, `new year celebration`, `parade`, `market stalls`, `paper lanterns`, `streamers`, `fireworks`, `confetti`, `festival decorations`, `ceremonial stage`, `traditional clothing`, `hand fan`, `flower arrangement`, `wooden stall`, `crowd in the background`, `warm evening light`, `festive atmosphere`, `red and gold palette`, `music performance`, `dance performance`, `lion dance costume`.

Use culturally specific clothing or objects only when the scene calls for them: `kimono`, `yukata`, `hakama`, `haori`, `hanfu`, `qipao`, `paper talisman`, `torii gate`, `shimenawa`, `wooden veranda`, `tea room`. Describe generic architecture and decoration rather than naming a copyrighted fictional setting. Keep the image focused on the story beat; a festival is context, not permission to fill every region with props.

## Fantasy, Science Fiction, and Constructed Worlds

Safe generic fantasy vocabulary includes `fantasy city`, `ancient stone gate`, `castle hall`, `gothic church`, `wooden cottage`, `magical library`, `floating island`, `luminous plants`, `crystal cave`, `enchanted forest`, `glowing runes`, `floating lanterns`, `fairy lights`, `storybook atmosphere`, `dreamlike landscape`, `mythical creature silhouette`, `dragon silhouette`, `winged creature`, `spirit lights`, `magic circle`, `alchemical workshop`, `ceremonial staff`, `crystal sword`, `ornate armor`, `traveler's cloak`.

Safe science-fiction vocabulary includes `futuristic city`, `space station corridor`, `research laboratory`, `robotics workshop`, `mechanical parts`, `brass machinery`, `copper pipes`, `holographic display without readable text`, `neon signs without text`, `protective armor`, `utility harness`, `visor`, `headset`, `control room`, `radio equipment`, `antenna`, `industrial hangar`, `maintenance platform`, `cool artificial light`.

Use generic concepts instead of franchise terms, named fictional characters, official art, or “style of” a living artist or copyrighted work. The project can preserve its own original world terms in source notes while the visual prompt describes visible features.

## Safe Multi-Character Blocking

For each character, write a separate compact block with the same order:

`[English identity label] + [appearance] + [costume] + [position/facing] + [individual action] + [expression/gaze]`.

Then write one shared event and one spatial relation. Example:

`CHR-001, adult woman, short silver hair, blue eyes, navy coat, frame left foreground, holding an unopened letter with both hands, restrained worry, looking toward CHR-002; CHR-002, adult man, dark brown hair, gray jacket, frame right near the doorway, one hand on the door handle, conflicted expression, avoiding eye contact; two adults standing one step apart, tense homecoming, medium shot, eye level, negative space on upper right`

The example is a structure, not a mandatory literal prompt. Do not put all cast appearances in one block and all actions in another. Avoid more than one primary shared action unless the shot is explicitly a group tableau. When exact hand or prop binding is critical, use a reference image and state the mapping in the manifest; text alone cannot guarantee identity fidelity.

## Negative Prompt Recipes

Keep negatives short and relevant. Start with global artifact exclusions only when useful:

- text and branding: `readable text, logo, watermark, signature, username`;
- identity duplication: `extra person, duplicate person, cloned face, merged bodies, fused figures`;
- anatomy: `bad anatomy, bad hands, extra fingers, missing fingers, malformed limbs, wrong proportions`;
- framing: `cropped head, out of frame, cut off hands, accidental border, black bars`;
- quality: `blurry, low quality, jpeg artifacts, unfinished, oversaturated`;
- medium conflict: `photorealistic, 3d render, pixel art, monochrome, no lineart` only when those conflict with the selected medium;
- prop ownership: `wrong prop ownership, duplicated prop, floating object` when the shot depends on a specific exchange.

Do not ban `multiple views` when a split composition or deliberate multi-view design is intended. Do not use body-value, race-coded, sexualized, or age-based negative lists. Do not copy long negative-prompt dumps. Add one exclusion only when it addresses a likely failure in this shot.

## Weight and Provider Notes

FrameAnimeDesk V1 stores unweighted English phrases by default. If a user explicitly asks for provider-specific weighting, keep it in a user-editable final prompt and explain that syntax and strength vary by model version. Do not put sampler, scheduler, steps, CFG, seed, or undocumented “magic” parameters into storyboard visual fields. Canvas dimensions belong to the application's resolution controls.

## Preflight Checklist

Before saving an NAI shot, check:

- all generation-facing values are English;
- the subject count matches the visible cast;
- each named character has grouped appearance, costume, position, action, expression, and gaze;
- the shared event is singular and readable;
- camera distance agrees with the story evidence and canvas ratio;
- viewpoint terms do not contradict one another;
- the scene has a place, time, and only the props that matter;
- lighting names a source and direction before effects;
- palette and medium are coherent;
- lettering space is described as clean negative space, not as generated text;
- negative prompt is short, relevant, and free of prohibited or value-laden content;
- no artist string, copyrighted work imitation, explicit sexual content, or gore entered the manifest.
