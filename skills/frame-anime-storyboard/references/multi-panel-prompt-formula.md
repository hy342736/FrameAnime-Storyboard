# Multi-Panel Prompt Formula

Use this only when one generated image must contain multiple comic panels. The Agent decides whether the beat benefits from a multi-panel image and writes the complete prompt; FrameAnimeDesk does not choose the layout.

## Required Order

Every English multi-panel prompt follows this order:

`[layout and exact panel count] + [shared character appearance anchor] + [panel-by-panel location and action] + [visual style and border control] + [aspect ratio parameters]`

Each panel carries one visual beat. Keep the base scene, time, lighting direction, and character state coherent across adjacent panels.

## Layout Vocabulary

- `A 4-panel comic strip in a 2x2 grid layout, clean white borders between panels.` Use for a standard four-panel sequence. Prefer `--ar 3:4` or `--ar 4:5`.
- `A vertical 3-panel webtoon strip, stacked vertically from top to bottom, clean gutters.` Use for a phone-oriented sequence. Prefer `--ar 9:16` or `--ar 1:2`.
- `A cinematic 3-panel horizontal filmstrip layout, side by side with thin borders.` Use for a wide spatial progression. Prefer `--ar 16:9` or `--ar 21:9` when supported.
- `A 3-panel dynamic manga page layout, asymmetrical diagonal panels, one dominant splash panel with two inset reaction panels.` Replace `3-panel` with the exact planned count. Use only for action or emotional impact. Prefer `--ar 2:3` or `--ar 3:4`.
- `A 2-panel split comic strip, side-by-side split composition` or `top-and-bottom split composition.` Use for a clear contrast or before/after beat.
- `A 9-panel 3x3 grid layout contact sheet, sequential breakdown.` Use `A 6-panel 2x3 grid layout contact sheet` for six panels. Use only for an intentional expression or micro-action sheet, not ordinary story coverage.

## Hard Constraints

1. State the exact panel count and use explicit positions such as `Panel 1 (top-left)`, `Panel 2 (top-right)`, `Panel 3 (bottom-left)`, and `Panel 4 (bottom-right)`.
2. Include `featuring the same character across all panels:` followed by fixed hair, face, costume, palette, signature feature, and carried prop details.
3. Keep the visual environment and lighting basis coherent unless the prompt explicitly describes a visible transition.
4. In the fourth layer include the visual style and border treatment, then the exact constraint `clean panels, no text, no gibberish speech bubbles`; also exclude logo and watermark. Use `clean gutters`, `clean white borders`, or another explicit border treatment appropriate to the selected layout.
5. Put the aspect ratio in the fifth and final layer, such as `vertical comic composition, --ar 3:4`. Nothing may follow the aspect-ratio parameter. Set the shot's `visual.aspect_ratio` to the same explicit value; `Auto` is invalid for a multi-panel request.

FrameAnimeDesk sends a recognized multi-panel prompt as the exact final positive prompt. Therefore the fourth layer must contain the complete selected visual style and relevant exclusions rather than relying on the application's ordinary project-style text compiler. The selected style reference images may still accompany the request when the provider supports image input; image attachment does not alter the prompt order.

## Example Shape

`A 2-panel split comic strip, top-and-bottom split composition, featuring the same character across all panels: a teenage boy with messy black hair, blue school jacket, red wristband. Panel 1 (top): medium shot, he notices the unopened letter on the desk, tense expression. Panel 2 (bottom): close-up, his hand reaches toward the letter, eyes fixed on it. Clean 2D anime line art, flat cel shading, clean panels, clean white gutters, no text, no gibberish speech bubbles, no logo, no watermark, vertical comic composition, --ar 3:4`

Do not generate a multi-panel image merely because the chapter has many beats. A normal chapter remains a sequence of separate shots; a multi-panel prompt is one image request containing only a tightly related mini-sequence.
