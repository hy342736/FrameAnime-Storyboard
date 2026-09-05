const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const appPath = path.join(__dirname, "..", "web", "app.js");
const source = fs.readFileSync(appPath, "utf8").replace(/\nboot\(\);\s*$/, "");
const context = {
  console,
  setTimeout: () => 0,
  clearTimeout: () => {},
  window: {},
  document: {
    addEventListener: () => {},
    querySelector: () => ({}),
  },
  MutationObserver: class {
    observe() {}
  },
};
vm.createContext(context);
vm.runInContext(`${source}\n;globalThis.__test = {
  normalizeState,
  readableGenerationError,
  shotStatus,
  composePrompt,
  selectedGenerationReferences,
  generationCapabilityError,
  autoLetteringLayout,
  normalizeLetteringLayout,
  letteringPreviewItems,
  normalizePanelLayout,
  dynamicExpressionInstruction,
  isAgentMultiPanelPrompt,
  aspectRatioValues: ASPECT_RATIO_OPTIONS.map(item => item.value),
  setState: value => { state = value; },
  setReferences: value => { allReferences = value; },
  setBubblePacks: value => { bubblePacks = value; },
  setSettings: value => { settings = { ...settings, ...value }; },
  setStylePacks: value => { stylePacks = value; }
};`, context);

assert.match(context.__test.readableGenerationError("等待图片结果超时；页面可能仍在生成"), /超时/);
assert.doesNotMatch(context.__test.readableGenerationError("等待图片结果超时；页面可能仍在生成"), /登录状态已失效/);

assert.equal(context.__test.shotStatus({ status: "待制作", content: { lastImage: "/images/result.png" } }), "待确认");
assert.equal(context.__test.shotStatus({ status: "已确认", content: { lastImage: "/images/result.png" } }), "已确认");
assert.equal(context.__test.shotStatus({ status: "生成中", content: { lastImage: "" } }), "生成中");
assert.deepEqual(
  [...context.__test.aspectRatioValues],
  ["Auto", "1:1", "1:2", "9:16", "16:9", "21:9", "3:4", "4:5", "4:3", "3:2", "2:3"],
);

assert.equal(context.__test.normalizePanelLayout("split_vertical_2", []).beats.length, 2);
assert.equal(context.__test.normalizePanelLayout("progression_3", [{ visual: "起因" }]).beats.length, 3);
assert.match(context.__test.dynamicExpressionInstruction("action_peak"), /exact peak/i);

const shortLayout = context.__test.autoLetteringLayout({ text: "脸上怎么了？", position: "top-right" }, 0);
assert.ok(shortLayout.width <= 0.28, shortLayout);
assert.equal(shortLayout.x, 0.68);
assert.equal(shortLayout.y, 0.04);
assert.deepEqual(
  JSON.parse(JSON.stringify(context.__test.normalizeLetteringLayout({ x: 2, y: -1, width: 0.9, flip: true }))),
  { x: 0.52, y: 0, width: 0.48, flip: true, fontScale: 1, rotation: 0 },
);
assert.equal(context.__test.normalizeLetteringLayout({ width: 0.2, fontScale: 2 }).fontScale, 1.4);
assert.equal(context.__test.normalizeLetteringLayout({ width: 0.2, fontScale: "bad" }).fontScale, 1);

context.__test.setSettings({ generation_mode: "api", image_api_protocol: "images" });
assert.equal(context.__test.generationCapabilityError(1), "");
assert.equal(context.__test.generationCapabilityError(0), "");
context.__test.setSettings({ image_api_protocol: "responses" });
assert.equal(context.__test.generationCapabilityError(4), "");

const characters = [
  { id: "CHR-001", name: "莉亚", role: "守望者", faction: "灯塔", personality: "沉静", appearance: "银发蓝眼", costume: "蓝色长衣", signature: "星形耳坠" },
  { id: "CHR-002", name: "寒色", role: "旅人", faction: "列车", personality: "敏锐", appearance: "黑发金眼", costume: "白色短衣", signature: "铜色手环" },
];

const migrated = context.__test.normalizeState({
  shotId: "SHOT-001",
  characters,
  shots: [{ id: "SHOT-001", type: "Medium Shot", content: { selectedCharacter: "CHR-002" } }],
});
assert.deepEqual([...migrated.shots[0].content.selectedCharacters], ["CHR-002"]);
assert.equal("selectedCharacter" in migrated.shots[0].content, false);
assert.equal(migrated.shots[0].content.aspectRatio, "Auto");
assert.equal(migrated.shots[0].content.resolution, "Auto");

const migratedDirection = context.__test.normalizeState({
  shotId: "SHOT-001",
  characters,
  shots: [{ id: "SHOT-001", type: "Medium Shot", content: { selectedCharacters: ["CHR-001"], characterDirections: { "CHR-001": "画面左侧，右手持灯" } } }],
});
assert.equal(migratedDirection.shots[0].content.characterDirections["CHR-001"].position, "画面左侧，右手持灯");
assert.equal(migratedDirection.shots[0].content.characterDirections["CHR-001"].action, "");
assert.equal(migratedDirection.shots[0].content.characterDirections["CHR-001"].expression, "");

const imported = context.__test.normalizeState({
  shotId: "SHOT-001",
  characters,
  storyboardPreferences: { format: "vertical_comic", futurePreference: "keep-me" },
  sourceBatches: [{ batch_id: "BATCH-001", selected_text: "原文", futureBatchField: true }],
  storyboardChecklist: [{ kind: "character_reference", ownerId: "CHR-001", blocking: false }],
  futureProjectField: { version: 2 },
  shots: [{
    id: "SHOT-001",
    type: "Medium Shot",
    source: { batchId: "BATCH-001", anchor: "原文", adaptationKind: "direct", futureSourceField: 7 },
    postText: [{ kind: "dialogue", text: "你好", position: "top-right", style: "speech" }],
    textSafeAreas: ["top-right"],
    futureShotField: "keep-shot",
    content: { futureContentField: "keep-content" },
  }],
});
assert.equal(imported.futureProjectField.version, 2);
assert.equal(imported.storyboardPreferences.futurePreference, "keep-me");
assert.equal(imported.sourceBatches[0].futureBatchField, true);
assert.equal(imported.shots[0].futureShotField, "keep-shot");
assert.equal(imported.shots[0].source.futureSourceField, 7);
assert.equal(imported.shots[0].content.futureContentField, "keep-content");
assert.equal(imported.shots[0].postText[0].text, "你好");
assert.equal(imported.shots[0].postText[0].hidden, false);
assert.equal(imported.shots[0].postText[0].layout, null);
assert.deepEqual([...imported.shots[0].textSafeAreas], ["top-right"]);

const importedWithoutCharacters = context.__test.normalizeState({
  shotId: "SHOT-001",
  characters: [],
  shots: [{ id: "SHOT-001", type: "Wide Shot", content: {} }],
});
assert.deepEqual([...importedWithoutCharacters.characters], []);
assert.equal(importedWithoutCharacters.characterId, "");

context.__test.setBubblePacks([{
  id: "jp-clean-v1",
  semantic_defaults: { dialogue: "speech-right" },
  assets: [{ id: "speech-right", label: "对白", semantic_type: "dialogue", url: "bubble.png" }],
}]);
const letteringState = context.__test.normalizeState({
  shotId: "SHOT-001",
  shots: [{
    id: "SHOT-001",
    type: "Medium Shot",
    content: { lastImage: "/images/result.png" },
    postText: [
      { kind: "dialogue", text: "第一句", position: "top-right" },
      { kind: "dialogue", text: "第二句", position: "top-right" },
    ],
  }],
});
context.__test.setState(letteringState);
const previewItems = context.__test.letteringPreviewItems();
assert.equal(previewItems.length, 2);
assert.equal(previewItems[0].index, 0);
assert.equal(previewItems[1].index, 1);
assert.notEqual(previewItems[0].layout.y, previewItems[1].layout.y);

letteringState.shots[0].postText.push({
  elementType: "text",
  kind: "narration",
  text: "旁白",
  position: "top-left",
  layout: { x: 0.1, y: 0.1, width: 0.3, fontScale: 1, rotation: 0 },
});
context.__test.setState(context.__test.normalizeState(letteringState));
const textPreview = context.__test.letteringPreviewItems();
assert.equal(textPreview.length, 3);
assert.equal(textPreview[2].isText, true);

const content = migrated.shots[0].content;
content.selectedCharacters = ["CHR-001", "CHR-002"];
content.characterDirections = {
  "CHR-001": { position: "画面左侧，面向寒色", action: "右手持灯", expression: "克制悲伤，望向寒色" },
  "CHR-002": { position: "画面右侧，面向莉亚", action: "握住信封", expression: "惊讶，望向莉亚" },
};
content.action = "两人在站台擦肩后同时停下";
content.expression = "压抑、迟疑的整体氛围";
content.duration = "99 sec";
content.aspectRatio = "16:9";
content.resolution = "2K";
content.dynamicExpression = "action_peak";
content.panelLayout = "single";
content.prompt = "两人在站台擦肩后停下，镜头强调交接信封的瞬间。";
context.__test.setState(migrated);
context.__test.setReferences([
  { id: "ref-world", owner_type: "world", owner_id: "world-bible", reference_type: "world_impression", file_name: "world.png", note: "", enabled: true, is_primary: true, sort_order: 0 },
  { id: "ref-shot", owner_type: "shot", owner_id: "SHOT-001", reference_type: "composition", file_name: "shot.png", note: "", enabled: true, is_primary: true, sort_order: 0 },
  { id: "ref-char-2", owner_type: "character", owner_id: "CHR-002", reference_type: "character_design", file_name: "hanse.png", note: "", enabled: true, is_primary: true, sort_order: 0 },
  { id: "ref-char-1", owner_type: "character", owner_id: "CHR-001", reference_type: "character_design", file_name: "liya.png", note: "", enabled: true, is_primary: true, sort_order: 0 },
]);

const references = context.__test.selectedGenerationReferences();
assert.deepEqual([...references].map(item => item.id), ["ref-char-1", "ref-char-2", "ref-shot", "ref-world"]);

const prompt = context.__test.composePrompt();
assert.match(prompt, /Character 1: CHR-001 \/ 莉亚/);
assert.match(prompt, /Character 2: CHR-002 \/ 寒色/);
assert.match(prompt, /Position and orientation: 画面左侧，面向寒色/);
assert.match(prompt, /Individual action: 右手持灯/);
assert.match(prompt, /Expression and eye line: 克制悲伤，望向寒色/);
assert.match(prompt, /Position and orientation: 画面右侧，面向莉亚/);
assert.match(prompt, /Individual action: 握住信封/);
assert.match(prompt, /Expression and eye line: 惊讶，望向莉亚/);
assert.match(prompt, /\[Interaction and shared event\] 两人在站台擦肩后同时停下/);
assert.match(prompt, /\[Overall mood\] 压抑、迟疑的整体氛围/);
assert.doesNotMatch(prompt, /99 sec/);
assert.match(prompt, /Reference Image 1 = CHARACTER CHR-001 \/ 莉亚/);
assert.match(prompt, /Reference Image 2 = CHARACTER CHR-002 \/ 寒色/);
assert.match(prompt, /Reference Image 3 = SHOT COMPOSITION \/ POSITION/);
assert.match(prompt, /Reference Image 4 = WORLD \/ ENVIRONMENT/);
assert.match(prompt, /16:9 aspect ratio/);
assert.match(prompt, /2K native output resolution; target approximately 2048x1152px/);
assert.match(prompt, /\[Shot Intent\] 两人在站台擦肩后停下/);
assert.doesNotMatch(prompt, /\[Panel Contract\]/);
assert.match(prompt, /\[Dynamic Expression\][\s\S]*exact peak/i);
assert.doesNotMatch(prompt, /\[World name\]|\[History\]|\[Factions\]|\[Magic system\]/);

const agentMultiPanelPrompt = "A 2-panel split comic strip, side-by-side split composition, clean white borders between panels, featuring the same character across all panels: a young woman with silver hair, blue coat, star earring. Panel 1 (left): medium shot, she raises a lantern. Panel 2 (right): close-up, she passes an envelope. Clean 2D anime line art, clean panels, no text, no gibberish speech bubbles, no logo, no watermark, --ar 16:9";
content.prompt = agentMultiPanelPrompt;
assert.equal(context.__test.isAgentMultiPanelPrompt(agentMultiPanelPrompt), true);
assert.equal(context.__test.composePrompt(), agentMultiPanelPrompt);
assert.doesNotMatch(context.__test.composePrompt(), /\[Dynamic Expression\]|\[Negative Prompt\]|\[PROJECT ART DIRECTION\]/);

content.action = "";
content.expression = "";
content.lighting = "";
content.style = "";
content.prompt = "";
content.characterDirections["CHR-002"] = { position: "", action: "", expression: "" };
migrated.characters[1].faction = "未定义阵营";
migrated.characters[1].personality = "待补充";
migrated.world.magic = "";
migrated.world.history = "";
const optionalPrompt = context.__test.composePrompt();
assert.doesNotMatch(optionalPrompt, /\[Interaction and shared event\]/);
assert.doesNotMatch(optionalPrompt, /\[Overall mood\]/);
assert.doesNotMatch(optionalPrompt, /\[Lighting\]/);
assert.doesNotMatch(optionalPrompt, /\[Style\]/);
assert.doesNotMatch(optionalPrompt, /\[Shot Intent\]/);
assert.doesNotMatch(optionalPrompt, /\[Magic system\]/);
assert.doesNotMatch(optionalPrompt, /\[History\]/);
assert.doesNotMatch(optionalPrompt, /未定义阵营|待补充|no separate action specified|follow the overall mood/);

console.log("frontend multi-character state tests passed");
