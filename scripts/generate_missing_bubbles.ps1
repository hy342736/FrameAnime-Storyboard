param(
    [ValidateSet("D", "E", "F", "G", "H", "all")]
    [string]$Group = "all",
    [string]$GeneratorPath = $env:FRAME_ANIME_IMAGE_GENERATOR
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$outputRoot = Join-Path $projectRoot "assets\bubble-packs\jp-clean"
if ([string]::IsNullOrWhiteSpace($GeneratorPath)) {
    throw "请通过 -GeneratorPath 或 FRAME_ANIME_IMAGE_GENERATOR 指定 generate_image.py 路径。"
}
$generator = $GeneratorPath
$backgroundTool = Join-Path $PSScriptRoot "make_bubble_background_transparent.py"

$items = @(
    @{ Code="D01"; File="D01-标准尖刺喊叫气泡-右尾.png"; Description="A standard shouting speech bubble based on a wide oval, with evenly spaced sharp spikes around the edge and one clear pointed tail extending to the right." },
    @{ Code="D02"; File="D02-标准尖刺喊叫气泡-左尾.png"; Description="A standard shouting speech bubble based on a wide oval, with evenly spaced sharp spikes around the edge and one clear pointed tail extending to the left." },
    @{ Code="D03"; File="D03-放射爆炸形气泡.png"; Description="A dramatic radial explosion speech bubble shaped like an exploding sun, with long exaggerated triangular rays and no tail." },
    @{ Code="D04"; File="D04-粗短尖刺愤怒气泡.png"; Description="An angry shouting bubble made from thick short blunt triangular spikes, dense and forceful, with a compressed heavy silhouette and no tail." },
    @{ Code="D05"; File="D05-细密尖刺惊讶气泡.png"; Description="A surprised exclamation bubble with many fine closely spaced sharp spikes around an oval center, energetic but clean, no tail." },
    @{ Code="D06"; File="D06-不稳定恐慌气泡.png"; Description="A panic speech bubble with irregular alternating long and short spikes, visibly unstable and frantic while retaining a large usable white interior, no tail." },
    @{ Code="D07"; File="D07-锯齿爆裂咆哮气泡.png"; Description="A roaring speech bubble with a jagged ruptured-looking outline, angular broken zigzag edges and a large readable white center, no tail." },
    @{ Code="D08"; File="D08-云朵爆炸激动气泡.png"; Description="An excited speech bubble halfway between a soft cloud and an explosion frame, alternating rounded lobes and restrained pointed bursts, lively rather than angry, no tail." },
    @{ Code="D09"; File="D09-小型爆炸强调气泡.png"; Description="A compact small explosion-shaped emphasis bubble with a few crisp pointed rays and a generous white center, no tail." },
    @{ Code="D10"; File="D10-大型尖刺无尾气泡.png"; Description="A large wide spiked bubble without a tail, designed for a collective shout, with evenly distributed dramatic spikes and a very large white interior." },

    @{ Code="E01"; File="E01-标准直角旁白框.png"; Description="A clean horizontal rectangular narration box with sharp 90-degree corners, a thin black outline and a large plain white interior." },
    @{ Code="E02"; File="E02-圆角旁白框.png"; Description="A clean horizontal rounded-rectangle narration box with gently rounded corners, a thin black outline and a large plain white interior." },
    @{ Code="E03"; File="E03-粗边说明框.png"; Description="A horizontal rectangular information box with sharp corners, a bold thick black outline and a large plain white interior." },
    @{ Code="E04"; File="E04-反白说明框结构.png"; Description="A strong regular horizontal information frame with a crisp double-line black outline and plain white interior, suitable for later inversion to a black panel with white lettering." },
    @{ Code="E05"; File="E05-细长时间提示框.png"; Description="A very slim elongated horizontal rectangular time-caption box, thin black outline, sharp corners and plain white interior." },
    @{ Code="E06"; File="E06-横向地点提示框.png"; Description="A wide horizontal location-caption box, moderately elongated rectangle with a clean black outline, sharp corners and plain white interior." },
    @{ Code="E07"; File="E07-科技系统提示框.png"; Description="A restrained futuristic system notification frame: regular horizontal rectangle with subtly clipped geometric corners, clean black outline and plain white interior." },
    @{ Code="E08"; File="E08-长句独白框.png"; Description="A tall vertical narration monologue box, significantly higher than wide, with a thin clean black outline, sharp corners and a large white interior for long text." },

    @{ Code="F01"; File="F01-电话锯齿对白-右尾.png"; Description="A telephone speech bubble with a wide oval center, small regular rhythmic zigzag teeth around the entire edge, and one clear tail extending to the right." },
    @{ Code="F02"; File="F02-电话锯齿对白-左尾.png"; Description="A telephone speech bubble with a wide oval center, small regular rhythmic zigzag teeth around the entire edge, and one clear tail extending to the left." },
    @{ Code="F03"; File="F03-矩形锯齿广播气泡.png"; Description="A broadcast announcement bubble with a horizontal rectangular center and regular sawtooth zigzag edges on all sides, no tail." },
    @{ Code="F04"; File="F04-机械对讲机声音框.png"; Description="A hard-edged near-rectangular intercom voice frame with stepped mechanical corners and a short angular tail, clean geometric black outline and white interior." },
    @{ Code="F05"; File="F05-电波屏幕外声音框.png"; Description="A television or off-screen electronic voice frame with a wide rounded rectangular center and a subtle regular waveform-like edge, no tail." },
    @{ Code="F06"; File="F06-机器人几何声音气泡.png"; Description="A robot voice bubble with a strong geometric polygonal outline, symmetric mechanical notches and a short angular tail, clean black outline and white interior." },

    @{ Code="G01"; File="G01-小型害羞气泡.png"; Description="A small gentle shy speech bubble, compact rounded oval with an especially soft smooth contour and a tiny discreet downward tail." },
    @{ Code="G02"; File="G02-下垂委屈气泡.png"; Description="A plaintive speech bubble with a slightly sagging lower contour, soft shallow wave edges and a small drooping tail, conveying a pitiful tone." },
    @{ Code="G03"; File="G03-压抑阴沉气泡.png"; Description="A subdued ominous speech bubble with a compressed low silhouette and a restrained mixture of soft curves and a few inward-leaning points, no decoration and no tail." },
    @{ Code="G04"; File="G04-扁长无语气泡.png"; Description="A very flat elongated horizontal speech bubble with a plain smooth contour and a tiny short tail, designed for a dry prolonged pause." },
    @{ Code="G05"; File="G05-花瓣撒娇气泡.png"; Description="A cute soft speech bubble with a rounded flower-petal-like scalloped edge and a small gentle tail, simple and clean rather than decorative." },

    @{ Code="H01"; File="H01-上下双联对白气泡.png"; Description="Two separate small rounded speech-bubble bodies stacked vertically and joined by a narrow connector, forming one unified two-part dialogue asset, with one small tail on the lower body." },
    @{ Code="H02"; File="H02-左右双联对白气泡.png"; Description="Two separate rounded speech-bubble bodies arranged side by side and joined by a narrow connector, forming one unified two-part dialogue asset, with one small outer tail." },
    @{ Code="H03"; File="H03-三联对白气泡.png"; Description="Three small rounded speech-bubble bodies connected in a clear descending chain, forming one unified three-part dialogue asset, with one small tail on the final body." },
    @{ Code="H04"; File="H04-多尾共语气泡.png"; Description="One large rounded speech bubble with three short distinct tails pointing in different directions, designed for several people speaking together." },
    @{ Code="H05"; File="H05-群体声讨论气泡.png"; Description="A compact irregular group-voice bubble made from several subtly merged rounded lobes with a few tiny outward tails, suitable for distant crowd discussion." }
)

$shared = @"
Use case: production asset for a mobile comic lettering editor.
Asset type: one isolated transparent PNG comic speech-bubble or narration-frame asset.
Primary request: {0}
Style and construction: professional clean Japanese manga lettering asset, pure black smooth outline, solid pure white fill inside the bubble, crisp high-resolution edges, balanced shape, generous empty interior for later user-added text.
Composition: exactly one complete connected asset centered on a 1024 by 1024 transparent canvas, comfortable transparent margin on every side, no cropping. Multi-lobed or multi-body shapes described as one asset must remain visibly connected and centered together.
Hard constraints: use a completely uniform pure white exterior background so it can be removed cleanly after generation; keep the requested bubble or frame enclosed by an unbroken black outline; no checkerboard; no gray halo; no shadow; no text; no letters; no punctuation; no people; no faces; no hands; no characters; no props; no icons; no extra decoration; no watermark; no interface elements; do not render an example page or comic panel. The only foreground subject is the black outline and pure white interior of the single requested asset.
"@

$selected = if ($Group -eq "all") { $items } else { $items | Where-Object { $_.Code.StartsWith($Group) } }
foreach ($item in $selected) {
    $target = Join-Path $outputRoot $item.File
    if (Test-Path -LiteralPath $target) {
        Write-Host "SKIP $($item.Code): already exists"
        continue
    }
    Write-Host "GENERATE $($item.Code) -> $($item.File)"
    $prompt = $shared -f $item.Description
    $temporary = Join-Path $outputRoot ".$($item.Code)-opaque.png"
    & python $generator --prompt $prompt --size 1024x1024 --quality high --background opaque --output-format png --output $temporary --timeout 300
    if ($LASTEXITCODE -ne 0) { throw "Generation failed for $($item.Code)" }
    & python $backgroundTool $temporary $target
    if ($LASTEXITCODE -ne 0) { throw "Transparency conversion failed for $($item.Code)" }
    Remove-Item -LiteralPath $temporary -Force
    Start-Sleep -Seconds 5
}
