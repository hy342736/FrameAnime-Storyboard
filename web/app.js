const STORAGE_KEY = "frame-anime-desk-projects-v2";
const LEGACY_STORAGE_KEY = "frame-anime-desk-v1";
const NEGATIVE_PROMPT = "bad anatomy, bad hands, extra fingers, wrong face, wrong hairstyle, different character, low quality, blurry, bad composition, incorrect perspective";
const EMPTY_OPTIONAL_VALUES = new Set(["未定义身份", "未定义阵营", "待补充", "待补充外貌锁定", "待补充服装与标志元素"]);
const MULTI_PANEL_PROMPT_MARKERS = ["comic strip", "webtoon strip", "filmstrip layout", "manga page layout", "grid layout contact sheet"];

const SHOT_TYPE_OPTIONS = [
  { value: "Extreme Close Up", label: "大特写" },
  { value: "Close Up", label: "特写" },
  { value: "Medium Shot", label: "中景" },
  { value: "Full Shot", label: "全身" },
  { value: "Wide Shot", label: "远景" },
  { value: "Extreme Wide Shot", label: "大全景" },
];
const CAMERA_ANGLE_OPTIONS = [
  { value: "Eye Level", label: "平视" },
  { value: "Low Angle", label: "低机位" },
  { value: "High Angle", label: "高机位" },
  { value: "POV", label: "第一视角" },
  { value: "Over Shoulder", label: "肩后视角" },
];
const DYNAMIC_EXPRESSION_OPTIONS = [
  { value: "still", label: "静态定格" },
  { value: "action_peak", label: "动作瞬间" },
  { value: "speed_lines", label: "速度线" },
  { value: "motion_blur", label: "轻微运动模糊" },
  { value: "follow_composition", label: "追随构图" },
  { value: "impact_composition", label: "冲击构图" },
];
const PANEL_LAYOUT_OPTIONS = [
  { value: "single", label: "单格画面", count: 1 },
  { value: "split_vertical_2", label: "左右双格", count: 2 },
  { value: "split_horizontal_2", label: "上下双格", count: 2 },
  { value: "progression_3", label: "三格递进", count: 3 },
  { value: "main_with_inset", label: "主格 + 插入格", count: 2 },
];
const ASPECT_RATIO_OPTIONS = [
  { value: "Auto", label: "自动" },
  { value: "1:1", label: "1:1" },
  { value: "1:2", label: "1:2" },
  { value: "9:16", label: "9:16" },
  { value: "16:9", label: "16:9" },
  { value: "21:9", label: "21:9" },
  { value: "3:4", label: "3:4" },
  { value: "4:5", label: "4:5" },
  { value: "4:3", label: "4:3" },
  { value: "3:2", label: "3:2" },
  { value: "2:3", label: "2:3" },
];
const RESOLUTION_OPTIONS = [
  { value: "Auto", label: "自动" },
  { value: "1K", label: "1K / 1024px" },
  { value: "2K", label: "2K / 2048px" },
  { value: "4K", label: "4K / 4096px" },
];
const REFERENCE_TYPE_OPTIONS = [
  { value: "character_design", label: "角色设定" },
  { value: "hair_costume_palette", label: "发型 / 服装 / 配色" },
  { value: "expression", label: "表情" },
  { value: "pose", label: "姿势" },
  { value: "character_version", label: "角色版本" },
  { value: "world_impression", label: "世界整体印象" },
  { value: "architecture", label: "建筑与城市" },
  { value: "landscape", label: "地貌与自然" },
  { value: "interior", label: "室内环境" },
  { value: "map_landmark", label: "地图 / 地标" },
  { value: "palette_material", label: "色板与材质" },
  { value: "era_atmosphere", label: "时代氛围" },
  { value: "faction", label: "阵营与组织" },
  { value: "character_position", label: "角色位置" },
  { value: "draft_revision", label: "废稿修改" },
  { value: "action_pose", label: "动作姿势" },
  { value: "background_color", label: "背景颜色" },
  { value: "composition", label: "构图参考" },
  { value: "other", label: "其他" },
];
const STYLE_ANALYSIS_FIELDS = [
  { key: "linework", label: "线稿" },
  { key: "character_rendering", label: "人物塑造" },
  { key: "coloring", label: "上色" },
  { key: "background", label: "背景" },
  { key: "palette_lighting", label: "色彩与光影" },
  { key: "composition", label: "构图" },
  { key: "exclusions", label: "排除项" },
];
const BUBBLE_SEMANTIC_OPTIONS = [
  { value: "dialogue", label: "普通对白" },
  { value: "thought", label: "心理活动" },
  { value: "narration", label: "旁白" },
  { value: "shout", label: "喊叫 / 强调" },
  { value: "sfx", label: "拟声词" },
];
const TEXT_POSITION_OPTIONS = [
  { value: "top-left", label: "左上" }, { value: "top-right", label: "右上" },
  { value: "left", label: "左侧" }, { value: "right", label: "右侧" }, { value: "bottom", label: "底部" },
];

const LETTERING_POSITION_ANCHORS = {
  "top-left": [0.05, 0.04],
  "top-right": [0.68, 0.04],
  left: [0.05, 0.34],
  right: [0.68, 0.34],
  bottom: [0.38, 0.66],
};

function clamp(value, minimum, maximum) { return Math.min(maximum, Math.max(minimum, Number(value))); }
function automaticLetteringWidth(text = "") {
  const length = String(text).replace(/\s/g, "").length;
  return length <= 8 ? 0.24 : length <= 16 ? 0.30 : 0.36;
}
function normalizeLetteringLayout(value) {
  if (!value || typeof value !== "object") return null;
  const width = clamp(Number.isFinite(Number(value.width)) ? value.width : 0.24, 0.14, 0.48);
  return {
    x: clamp(Number.isFinite(Number(value.x)) ? value.x : 0.04, 0, 1 - width),
    y: clamp(Number.isFinite(Number(value.y)) ? value.y : 0.04, 0, 0.92),
    width,
    flip: Boolean(value.flip),
    fontScale: clamp(Number.isFinite(Number(value.fontScale)) ? value.fontScale : 1, 0.6, 1.4),
    rotation: clamp(Number.isFinite(Number(value.rotation)) ? value.rotation : 0, -180, 180),
  };
}
function autoLetteringLayout(block = {}, offset = 0) {
  const length = String(block.text || "").replace(/\s/g, "").length;
  const width = block.bubbleSemantic === "thought"
    ? (length <= 8 ? 0.22 : length <= 16 ? 0.24 : 0.30)
    : automaticLetteringWidth(block.text);
  const position = block.position || "top-right";
  const anchor = LETTERING_POSITION_ANCHORS[position] || LETTERING_POSITION_ANCHORS["top-right"];
  let x = anchor[0];
  if (["top-right", "right"].includes(position)) x = 1 - width - 0.08;
  if (position === "bottom") x = (1 - width) / 2;
  return normalizeLetteringLayout({ x, y: anchor[1] + offset * 0.12, width, flip: false });
}

const SHOT_CONTENT_KEYS = ["shotType", "cameraAngle", "dynamicExpression", "panelLayout", "panelBeats", "aspectRatio", "resolution", "selectedCharacter", "selectedCharacters", "characterDirections", "prompt", "scene", "action", "expression", "lighting", "style", "naiPositivePrompt", "naiNegativePrompt"];

function panelCount(layout) { return PANEL_LAYOUT_OPTIONS.find(item => item.value === layout)?.count || 1; }
function normalizePanelLayout(layout, beats) {
  const value = PANEL_LAYOUT_OPTIONS.some(item => item.value === layout) ? layout : "single";
  const source = Array.isArray(beats) ? beats : [];
  return {
    layout: value,
    beats: Array.from({ length: panelCount(value) }, (_, index) => ({
      label: String(source[index]?.label || `第 ${index + 1} 格`),
      visual: String(source[index]?.visual || ""),
    })),
  };
}

function blankShotContent(shot = {}) {
  return {
    shotId: shot.id || "",
    shotType: shot.type || "Wide Shot",
    cameraAngle: "Eye Level",
    dynamicExpression: "still",
    panelLayout: "single",
    panelBeats: [{ label: "第 1 格", visual: "" }],
    aspectRatio: "Auto",
    resolution: "Auto",
    selectedCharacters: [],
    characterDirections: {},
    prompt: "",
    scene: "",
    action: "",
    expression: "",
    lighting: "",
    style: "",
    naiPositivePrompt: "",
    naiNegativePrompt: "",
    stylePackOverride: "project",
    lastImage: "",
    generationHistory: [],
  };
}

function shotStatus(shot = {}) {
  const current = String(shot.status || "待制作");
  if (["生成中", "需重试"].includes(current)) return current;
  if (shot.content?.lastImage) return current === "已确认" ? "已确认" : "待确认";
  return "待制作";
}

function normalizeCharacterDirection(value) {
  if (typeof value === "string") return { position: value, action: "", expression: "", costume: "" };
  if (!value || typeof value !== "object") return { position: "", action: "", expression: "", costume: "" };
  return {
    position: typeof value.position === "string" ? value.position : "",
    action: typeof value.action === "string" ? value.action : "",
    expression: typeof value.expression === "string" ? value.expression : "",
    costume: typeof value.costume === "string" ? value.costume : "",
  };
}

function characterDirectionSummary(value) {
  const detail = normalizeCharacterDirection(value);
  return [detail.position, detail.action, detail.expression].filter(Boolean).join("；");
}

function normalizeShot(shot = {}) {
  const normalized = { ...shot };
  const content = shot.content && typeof shot.content === "object" ? shot.content : {};
  normalized.content = { ...blankShotContent(normalized), ...content };
  normalized.content.shotId = normalized.id || normalized.content.shotId || "";
  normalized.content.shotType = normalized.content.shotType || normalized.type || "Wide Shot";
  if (!normalized.content.dynamicExpression) {
    const legacyMove = String(content.cameraMove || "").toLowerCase();
    normalized.content.dynamicExpression = legacyMove.includes("track") || legacyMove.includes("drift") ? "follow_composition"
      : legacyMove.includes("handheld") ? "impact_composition" : "still";
  }
  const panels = normalizePanelLayout(normalized.content.panelLayout, normalized.content.panelBeats);
  normalized.content.panelLayout = panels.layout;
  normalized.content.panelBeats = panels.beats;
  delete normalized.content.mode;
  delete normalized.content.duration;
  delete normalized.content.cameraMove;
  normalized.content.generationHistory = Array.isArray(normalized.content.generationHistory) ? normalized.content.generationHistory : [];
  const layout = shot.layoutMeta || shot.layout_meta || {};
  normalized.layoutMeta = {
    ...layout,
    containerType: layout.containerType || layout.container_type || "single_panel",
    rowIndex: Number(layout.rowIndex || layout.row_index || 1),
    slotIndex: Number(layout.slotIndex || layout.slot_index || 1),
    gutterBottom: Number(layout.gutterBottom || layout.gutter_bottom || 0),
    borderStyle: layout.borderStyle || layout.border_style || "none",
    insetConfig: layout.insetConfig || layout.inset_config || null,
  };
  normalized.content.stylePackOverride = normalized.content.stylePackOverride || "project";
  normalized.status = shotStatus(normalized);
  const legacyCharacter = typeof normalized.content.selectedCharacter === "string" ? normalized.content.selectedCharacter : "";
  const selectedCharacters = Array.isArray(normalized.content.selectedCharacters)
    ? [...new Set(normalized.content.selectedCharacters.filter(id => typeof id === "string" && id))]
    : [];
  normalized.content.selectedCharacters = selectedCharacters.length ? selectedCharacters : (legacyCharacter ? [legacyCharacter] : []);
  normalized.content.characterDirections = normalized.content.characterDirections && typeof normalized.content.characterDirections === "object"
    ? Object.fromEntries(Object.entries(normalized.content.characterDirections).map(([id, value]) => [id, normalizeCharacterDirection(value)]))
    : {};
  normalized.postText = Array.isArray(shot.postText) ? shot.postText.map(block => ({
    ...block,
    elementType: block.elementType || "image",
    bubbleSemantic: block.bubbleSemantic || ({ speech: "dialogue", thought: "thought", caption: "narration", sfx: "sfx" }[block.style] || block.kind || "dialogue"),
    bubbleAssetId: block.bubbleAssetId || "",
    bubbleReferenceId: block.bubbleReferenceId || "",
    hidden: Boolean(block.hidden),
    layout: normalizeLetteringLayout(block.layout),
  })) : [];
  delete normalized.content.selectedCharacter;
  return normalized;
}

const defaultProjectState = () => ({
  activeView: "director",
  shotId: "SHOT-001",
  promptProfile: "natural",
  artDirection: {
    stylePackId: "",
    compiledPrompt: "",
    negativePrompt: "",
    styleAnalysis: Object.fromEntries(STYLE_ANALYSIS_FIELDS.map(field => [field.key, ""])),
    locked: true,
  },
  lettering: { bubblePackId: "jp-clean-v1", locked: true },
  world: {
    name: "星落纪元",
    era: "近未来的蒸汽与魔法并存时代",
    country: "雾港联邦",
    city: "旧车站与灯塔城",
    geography: "被潮汐和海雾包围的群岛，城市沿旧铁路和灯塔带展开。",
    technology: "铜制机械、蒸汽铁路与可储存记忆的灯塔技术并存。",
    magic: "记忆可以被装入灯火，但每次点亮都会消耗一段真实经历。",
    history: "七年前的潮汐战争让旧铁路停运，灯塔守望者成为唯一的记忆保管人。",
    factions: "雾港自治会、灯塔守望者、无眠商会三方争夺记忆灯火。",
    rules: "被灯火保存的记忆不能被复制；遗忘之后只能凭情绪残影找回。",
    conflict: "记忆可以被装进灯塔，但每次点亮都会失去一段真实经历。",
    weather: "深夜多雨，海雾在列车灯和铜制建筑之间形成柔软的光层。",
    time: "一天以灯塔换色计时，午夜是蓝灯切换为暖黄灯的时刻。",
    visual: "潮湿的旧金属、蓝色夜雾、暖黄人工光源",
    materials: "氧化铜、湿石、旧玻璃、深海蓝布料和被雨打亮的铁轨。",
  },
  characters: [
    { id: "CHR-001", name: "莉亚", role: "失忆的灯塔守望者", faction: "雾港自治会", personality: "安静、固执、对旧物有依恋", appearance: "银白长发，灰蓝色眼睛，纤细的成年少女体态", costume: "深海蓝长外套，铜色徽章，黑色短靴", signature: "左耳有一枚星形耳坠" },
  ],
  shots: [
    { id: "SHOT-001", type: "Medium Shot", title: "未寄出的信", desc: "莉亚在旧车站等候，列车灯光从雾中掠过。", status: "当前镜头", content: blankShotContent({ id: "SHOT-001", type: "Medium Shot" }) },
    { id: "SHOT-002", type: "Close Up", title: "灯塔记忆", desc: "信封上的蜡封裂开，倒映出一座正在熄灭的灯塔。", status: "待制作", content: blankShotContent({ id: "SHOT-002", type: "Close Up" }) },
  ],
});

let projects = [];
let currentProjectId = "";
let state = defaultProjectState();
let allReferences = [];
let stylePacks = [];
let bubblePacks = [];
let customStyleFormOpen = false;
let exportOptions = { format: "vertical_comic", include_lettering: true, width: 1080, gap: 24, frame_duration_seconds: 3 };
let exportInFlight = false;
let exportSelectionProjectId = "";
let selectedExportShotIds = new Set();
let finalRequestPreview = null;
let settings = { mirror_url: "", mirror_chat_url: "", image_dir: "data/generated", reference_dir: "data/references", headless: false, generation_timeout_seconds: 600, generation_mode: "mirror", image_api_name: "默认 API 节点", image_api_base_url: "", image_api_protocol: "responses", image_api_model: "gpt-image-1", image_api_prompt_profile: "auto", image_api_timeout_seconds: 240, has_image_api_key: false };
let sessionStatus = { started: false, context_open: false, page_open: false, page_url: "" };
let conversationBinding = { status: "unbound", project_id: "", url: "", title: "" };
let remoteSaveTimer = null;
let projectRefreshTimer = null;
let projectRefreshInFlight = false;
let remoteAvailable = false;
let draggedShotId = "";
let draggedReferenceId = "";
let generationSequence = 0;
const activeGenerations = new Map();
let letteringEditorIndex = -1;

function clone(value) { return JSON.parse(JSON.stringify(value)); }
function esc(value = "") { return String(value).replace(/[&<>'"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[c])); }
function optionalText(value) { const text = String(value ?? "").trim(); return EMPTY_OPTIONAL_VALUES.has(text) ? "" : text; }
function containsCjk(value) { return /[\u3400-\u9fff]/.test(String(value || "")); }
function isNaiProject() { return state.promptProfile === "nai"; }
function optionalLine(label, value) { const text = optionalText(value); return text ? `[${label}] ${text}` : ""; }
function icon(name) { return `<i data-lucide="${name}"></i>`; }
function refreshIcons() { if (window.lucide) window.lucide.createIcons(); }
function toast(message, options = {}) {
  const { kind = "info", actionLabel = "", action = null, duration = 3600, key = "" } = options;
  if (key && document.querySelector(`[data-toast-key="${CSS.escape(key)}"]`)) return;
  const node = document.createElement("div");
  node.className = `toast ${kind === "error" ? "toast-error" : ""}`.trim();
  if (key) node.dataset.toastKey = key;
  node.setAttribute("role", kind === "error" ? "alert" : "status");
  const copy = document.createElement("span");
  copy.className = "toast-message";
  copy.textContent = message;
  node.appendChild(copy);
  if (action && actionLabel) {
    const retry = document.createElement("button");
    retry.className = "toast-action";
    retry.type = "button";
    retry.textContent = actionLabel;
    retry.addEventListener("click", () => {
      node.remove();
      Promise.resolve(action()).catch(error => toast(error.message, { kind: "error", duration: 0 }));
    });
    node.appendChild(retry);
  }
  const close = document.createElement("button");
  close.className = "toast-close";
  close.type = "button";
  close.title = "关闭提醒";
  close.setAttribute("aria-label", "关闭提醒");
  close.textContent = "×";
  close.addEventListener("click", () => node.remove());
  node.appendChild(close);
  document.querySelector("#toastRegion").appendChild(node);
  if (duration > 0) setTimeout(() => node.remove(), duration);
}
function readableGenerationError(message) {
  const value = String(message || "生成请求失败");
  if (/超时|timeout/i.test(value)) return "等待镜像站生成结果超时；页面可能仍在生成，当前登录状态未被判定为失效。";
  if (/something went wrong|help\.openai\.com/i.test(value)) return "镜像站返回了服务错误，图片没有成功生成。请检查登录状态后重试。";
  if (/登录|login/i.test(value)) return "镜像站登录状态已失效，请先打开镜像站完成登录，再重试生成。";
  return `生图失败：${value}`;
}
function generationCapabilityError(referenceCount) {
  // Images protocol degrades to text-only generation. The backend keeps the
  // compiled style/character prompt and reports which image files were omitted.
  return "";
}
function clearGenerationNotice(shotId) { document.querySelector(`[data-toast-key="generation-${CSS.escape(shotId)}"]`)?.remove(); }
function generationError(message, shotId) { toast(readableGenerationError(message), { kind: "error", actionLabel: "重试", action: () => generate(shotId), duration: 0, key: `generation-${shotId}` }); }
function readLocal(key) { try { return JSON.parse(localStorage.getItem(key) || "null"); } catch { return null; } }
function saveLocal() { localStorage.setItem(STORAGE_KEY, JSON.stringify({ currentProjectId, projects })); }
function setSaveStatus(status, message) {
  const node = document.querySelector("#saveStatus");
  const copy = document.querySelector("#saveStatusText");
  if (!node || !copy) return;
  node.dataset.saveState = status;
  copy.textContent = message;
}
function getProject() { return projects.find(item => item.id === currentProjectId) || projects[0]; }
function getShot() { return state.shots.find(item => item.id === state.shotId) || state.shots[0]; }
function currentShotContent() { const shot = getShot(); if (!shot) return blankShotContent(); if (!shot.content) shot.content = blankShotContent(shot); return shot.content; }
function selectedCharacterIds() { return currentShotContent().selectedCharacters || []; }
function getSelectedCharacters() { const ids = selectedCharacterIds(); return ids.map(id => state.characters.find(item => item.id === id)).filter(Boolean); }
function getCharacter() { return state.characters.find(item => item.id === state.characterId) || getSelectedCharacters()[0] || state.characters[0]; }
function syncProjectUrl() {
  if (!currentProjectId || !window.history?.replaceState) return;
  const url = new URL(window.location.href);
  url.searchParams.set("project_id", currentProjectId);
  window.history.replaceState(null, "", url);
}

function normalizeState(raw = {}) {
  const base = defaultProjectState();
  const result = {
    ...base,
    ...raw,
    world: { ...base.world, ...(raw.world || {}) },
    artDirection: {
      ...base.artDirection,
      ...(raw.artDirection || {}),
      styleAnalysis: { ...base.artDirection.styleAnalysis, ...((raw.artDirection || {}).styleAnalysis || {}) },
    },
    lettering: { ...base.lettering, ...(raw.lettering || {}) },
  };
  result.promptProfile = raw.promptProfile === "nai" ? "nai" : "natural";
  result.characters = Array.isArray(raw.characters) ? raw.characters : base.characters;
  result.shots = Array.isArray(raw.shots) && raw.shots.length ? raw.shots : base.shots;
  if (!result.shots.some(item => item.id === result.shotId)) result.shotId = result.shots[0]?.id || "";
  const legacyShotId = raw.shotId || result.shotId;
  const legacyContent = {};
  SHOT_CONTENT_KEYS.forEach(key => {
    if (Object.prototype.hasOwnProperty.call(raw, key)) legacyContent[key] = raw[key];
  });
  if (Object.prototype.hasOwnProperty.call(raw, "lastImage")) legacyContent.lastImage = raw.lastImage;
  if (Object.prototype.hasOwnProperty.call(raw, "generationHistory")) legacyContent.generationHistory = raw.generationHistory;
  result.shots = result.shots.map(shot => {
    const normalized = normalizeShot(shot);
    if (!shot.content && shot.id === legacyShotId) normalized.content = { ...normalized.content, ...legacyContent };
    if (!normalized.content.selectedCharacters.length && normalized.content.selectedCharacter) normalized.content.selectedCharacters = [normalized.content.selectedCharacter];
    normalized.content.selectedCharacters = normalized.content.selectedCharacters.filter(id => result.characters.some(character => character.id === id));
    delete normalized.content.selectedCharacter;
    normalized.content.shotId = normalized.id;
    normalized.content.shotType = normalized.content.shotType || normalized.type || "Wide Shot";
    normalized.content.generationHistory = Array.isArray(normalized.content.generationHistory) ? normalized.content.generationHistory : [];
    return normalized;
  });
  if (!result.characterId || !result.characters.some(item => item.id === result.characterId)) result.characterId = result.shots.find(item => item.id === result.shotId)?.content.selectedCharacters?.[0] || result.characters[0]?.id || "";
  SHOT_CONTENT_KEYS.forEach(key => { delete result[key]; });
  delete result.lastImage;
  delete result.generationHistory;
  return result;
}

async function readResponse(response) { const raw = await response.text(); try { return raw ? JSON.parse(raw) : {}; } catch { return { detail: raw || `请求失败（HTTP ${response.status}）` }; } }
async function api(path, options = {}) { const response = await fetch(path, options); const data = await readResponse(response); if (!response.ok) throw new Error(data.detail || `请求失败（HTTP ${response.status}）`); return data; }

function projectStateForCache() { return projects.map(item => ({ ...item, state: item.id === currentProjectId ? clone(state) : item.state })); }
function saveState() {
  setSaveStatus("saving", "正在保存...");
  try {
    const project = getProject();
    if (project) project.state = clone(state);
    projects = projectStateForCache();
    saveLocal();
  } catch {
    setSaveStatus("error", "保存失败，请重试");
    return;
  }
  clearTimeout(remoteSaveTimer);
  if (!remoteAvailable || !currentProjectId || currentProjectId.startsWith("local-")) {
    setSaveStatus("local", "已保存到本机");
    return;
  }
  remoteSaveTimer = setTimeout(() => saveProjectRemote(), 350);
}
async function saveProjectRemote() {
  clearTimeout(remoteSaveTimer);
  if (!remoteAvailable || !currentProjectId || currentProjectId.startsWith("local-")) {
    setSaveStatus("local", "已保存到本机");
    return true;
  }
  try {
    const project = getProject();
    const response = await fetch(`/api/projects/${encodeURIComponent(currentProjectId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ state, expected_revision: project?.revision || 1 }),
    });
    const updated = await readResponse(response);
    if (response.status === 409) {
      setSaveStatus("error", "项目已更新，请刷新");
      toast("项目已在其他窗口更新。当前页面没有覆盖新内容，请刷新后继续编辑。", { kind: "error", duration: 10000, key: `project-conflict-${currentProjectId}` });
      return false;
    }
    if (!response.ok) throw new Error(updated.detail || `保存失败（HTTP ${response.status}）`);
    const index = projects.findIndex(item => item.id === currentProjectId);
    if (index >= 0) projects[index] = { ...projects[index], ...updated, state: clone(state) };
    saveLocal();
    setSaveStatus("saved", "已保存");
    return true;
  } catch {
    remoteAvailable = false;
    document.querySelector("#connectionText").textContent = "本地缓存";
    setSaveStatus("error", "保存失败，本机副本已保留");
    return false;
  }
}
async function refreshCurrentProjectRevision() {
  if (!remoteAvailable || !currentProjectId || currentProjectId.startsWith("local-")) return;
  try {
    const detail = await api(`/api/projects/${encodeURIComponent(currentProjectId)}`);
    const index = projects.findIndex(item => item.id === currentProjectId);
    if (index >= 0) projects[index] = { ...projects[index], revision: detail.revision, updated_at: detail.updated_at };
    saveLocal();
  } catch { /* The next state save will surface a concrete conflict or connection error. */ }
}
async function reloadCurrentProjectFromRemote() {
  if (!remoteAvailable || !currentProjectId || currentProjectId.startsWith("local-")) return;
  clearTimeout(remoteSaveTimer);
  const detail = await api(`/api/projects/${encodeURIComponent(currentProjectId)}`);
  const index = projects.findIndex(item => item.id === currentProjectId);
  if (index >= 0) projects[index] = detail;
  state = normalizeState(detail.state);
  await loadReferences();
  saveLocal();
  render();
  setSaveStatus("saved", "已载入最新版本");
  toast("已载入 Skill 更新后的项目内容");
}
async function checkForProjectUpdates() {
  if (!remoteAvailable || projectRefreshInFlight || document.hidden) return;
  projectRefreshInFlight = true;
  try {
    const remoteProjects = await api("/api/projects");
    const knownById = new Map(projects.map(item => [item.id, item]));
    const newProjects = remoteProjects.filter(item => !knownById.has(item.id));
    for (const item of remoteProjects) {
      const known = knownById.get(item.id);
      if (!known) {
        projects.push(item);
        continue;
      }
      if (item.id === currentProjectId && Number(item.revision) > Number(known.revision || 0)) {
        toast("当前项目已由 Skill 更新，页面没有覆盖你的编辑。", {
          actionLabel: "重新载入",
          action: reloadCurrentProjectFromRemote,
          duration: 10000,
          key: `project-revision-${item.id}`,
        });
      } else if (item.id !== currentProjectId) {
        Object.assign(known, item);
      }
    }
    if (newProjects.length) {
      saveLocal();
      render();
      const target = newProjects[newProjects.length - 1];
      const label = newProjects.length === 1 ? target.name : `${target.name} 等 ${newProjects.length} 个项目`;
      toast(`检测到 Skill 新建的项目：${label}`, {
        actionLabel: "查看项目",
        action: () => switchProject(target.id),
        duration: 10000,
        key: `new-project-${newProjects.map(item => item.id).join("-")}`,
      });
    }
  } catch {
    // A normal save or explicit action will surface persistent connection failures.
  } finally {
    projectRefreshInFlight = false;
  }
}
function startProjectUpdateChecks() {
  clearInterval(projectRefreshTimer);
  projectRefreshTimer = setInterval(checkForProjectUpdates, 5000);
}
async function loadReferences() { if (!remoteAvailable || !currentProjectId || currentProjectId.startsWith("local-")) { allReferences = []; return; } try { allReferences = await api(`/api/projects/${encodeURIComponent(currentProjectId)}/references`); } catch { allReferences = []; } }
async function loadConversationBinding() { if (!remoteAvailable || !currentProjectId || currentProjectId.startsWith("local-")) { conversationBinding = { status: "unbound", project_id: currentProjectId, url: "", title: "" }; return; } try { conversationBinding = await api(`/api/projects/${encodeURIComponent(currentProjectId)}/conversation`); } catch { conversationBinding = { status: "error", project_id: currentProjectId, url: "", title: "" }; } }
async function loadArtLibraries() {
  if (!remoteAvailable) { stylePacks = []; bubblePacks = []; return; }
  try { stylePacks = await api("/api/style-packs"); } catch { stylePacks = []; }
  try { bubblePacks = await api("/api/bubble-packs"); } catch { bubblePacks = []; }
}

async function boot() {
  const requestedProjectId = new URLSearchParams(window.location.search).get("project_id") || "";
  const cache = readLocal(STORAGE_KEY) || {};
  const legacy = readLocal(LEGACY_STORAGE_KEY);
  projects = Array.isArray(cache.projects) ? cache.projects : [];
  currentProjectId = cache.currentProjectId || projects[0]?.id || "";
  if (requestedProjectId && projects.some(item => item.id === requestedProjectId)) currentProjectId = requestedProjectId;
  if (!projects.length && legacy) { projects = [{ id: "local-migration", name: "星落纪元 / 零号机", description: "从旧版工作区迁移", state: normalizeState(legacy) }]; currentProjectId = projects[0].id; }
  state = normalizeState(projects.find(item => item.id === currentProjectId)?.state || {});
  try {
    const remoteProjects = await api("/api/projects"); remoteAvailable = true;
    let availableProjects = remoteProjects;
    let migrationTargetId = "";
    const pendingMigration = projects.find(item => item.id === "local-migration")?.state;
    if (pendingMigration && remoteProjects.length) {
      const imported = await api("/api/projects", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: "迁移：星落纪元 / 零号机", description: "从旧版本地工作区迁移", state: pendingMigration }) });
      availableProjects = [...remoteProjects, imported];
      migrationTargetId = imported.id;
      localStorage.removeItem(LEGACY_STORAGE_KEY);
    }
    if (!availableProjects.length) {
      const seed = projects.find(item => item.id === currentProjectId)?.state || normalizeState(legacy || {});
      const created = await api("/api/projects", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: projects[0]?.name || "星落纪元 / 零号机", description: "个人动画制作工作台", state: seed }) });
      projects = [created]; currentProjectId = created.id; state = normalizeState(created.state); localStorage.removeItem(LEGACY_STORAGE_KEY);
    } else {
      projects = await Promise.all(availableProjects.map(item => api(`/api/projects/${encodeURIComponent(item.id)}`))); const preferred = migrationTargetId || (requestedProjectId && projects.some(item => item.id === requestedProjectId) ? requestedProjectId : (projects.some(item => item.id === currentProjectId) ? currentProjectId : projects[0].id)); currentProjectId = preferred; const detail = projects.find(item => item.id === currentProjectId) || projects[0]; state = normalizeState(detail.state);
    }
    await loadReferences(); await loadConversationBinding(); await loadArtLibraries(); settings = await api("/api/settings");
    try { sessionStatus = await api("/api/session/status"); } catch { sessionStatus = { started: false, context_open: false, page_open: false, page_url: "" }; }
  } catch (error) {
    remoteAvailable = false;
    if (!projects.length) { projects = [{ id: "local-first", name: "星落纪元 / 零号机", description: "本地缓存项目", state: clone(state) }]; currentProjectId = projects[0].id; }
    toast(`后端存储暂不可用，已使用本地缓存：${error.message}`);
  }
  saveLocal(); syncProjectUrl(); render();
  startProjectUpdateChecks();
  if (requestedProjectId && requestedProjectId !== currentProjectId) toast("深链接中的项目不存在，已保留当前项目", { kind: "error" });
}

function optionMarkup(options, selected) { return options.map(option => `<option value="${esc(option.value)}" ${option.value === selected ? "selected" : ""}>${esc(option.label)}</option>`).join(""); }
function field(label, key, value, type = "input", options = [], extra = "") { let control; if (type === "select") control = `<select data-field="${esc(key)}" ${extra}>${optionMarkup(options, value)}</select>`; else if (type === "textarea") control = `<textarea data-field="${esc(key)}" ${extra}>${esc(value)}</textarea>`; else control = `<input data-field="${esc(key)}" value="${esc(value)}" ${extra} />`; return `<div class="field"><label>${esc(label)}</label>${control}</div>`; }
function labelFor(options, value) { return options.find(item => item.value === value)?.label || value; }
function referenceLabel(value) { return REFERENCE_TYPE_OPTIONS.find(item => item.value === value)?.label || "其他"; }
function referencesFor(ownerType, ownerId) { return allReferences.filter(item => item.owner_type === ownerType && item.owner_id === ownerId).sort((a, b) => a.sort_order - b.sort_order); }
function referenceThumb(reference, compact = false) { return `<div class="reference-thumb ${compact ? "compact" : ""}"><img src="${esc(reference.url)}" alt="${esc(reference.file_name)}" loading="lazy" /></div>`; }

function characterSelector(content) {
  const selected = new Set(content.selectedCharacters || []);
  const characters = getSelectedCharacters();
  const choices = state.characters.map(character => `<label class="character-choice ${selected.has(character.id) ? "is-selected" : ""}"><input type="checkbox" data-character-toggle="${esc(character.id)}" ${selected.has(character.id) ? "checked" : ""} /><span class="character-choice-mark">${selected.has(character.id) ? icon("check") : ""}</span><span><strong>${esc(character.name)}</strong><small>${esc(character.id)} · ${esc(character.role)}</small></span></label>`).join("");
  const bindings = characters.map((character, index) => {
    const detail = normalizeCharacterDirection(content.characterDirections?.[character.id]);
    const detailField = (key, label, value, placeholder) => `<label class="binding-detail binding-${key}"><span>${label}</span><input data-character-id="${esc(character.id)}" data-character-detail="${key}" value="${esc(value)}" placeholder="${placeholder}" aria-label="${esc(character.name)}的${label}" /></label>`;
    const examples = isNaiProject()
      ? ["frame left, facing character 02", "holding a lantern, standing still", "restrained sadness, looking at character 02"]
      : ["例如：画面左侧，面向角色 02", "例如：右手持灯，身体停下", "例如：克制悲伤，望向角色 02"];
    return `<div class="character-binding"><span class="binding-index">${String(index + 1).padStart(2, "0")}</span><div class="binding-identity"><strong>${esc(character.name)}</strong><small>${esc(character.id)}</small></div>${detailField("costume", "当前服装", detail.costume, character.costume || "填写本场唯一服装")}${detailField("position", "位置与朝向", detail.position, examples[0])}${detailField("action", "独立动作", detail.action, examples[1])}${detailField("expression", "表情与视线", detail.expression, examples[2])}</div>`;
  }).join("");
  return `${field("画面比例", "aspectRatio", content.aspectRatio, "select", ASPECT_RATIO_OPTIONS)}${field("输出分辨率", "resolution", content.resolution, "select", RESOLUTION_OPTIONS)}<div class="field character-selector-field"><label>入镜角色 <span>${characters.length} 人</span></label><div class="character-picker" role="group" aria-label="选择当前镜头中的角色">${choices || `<div class="character-picker-empty">请先在角色库创建角色</div>`}</div>${characters.length ? `<div class="character-bindings"><div class="binding-heading"><span>逐角色画面约束</span><small>每个角色分别锁定位置、动作、表情与视线</small></div>${bindings}</div>` : ""}</div>`;
}

function naiPromptStats(value) {
  const text = String(value || "").trim();
  return { characters: text.length, tags: text ? text.split(/[,，;；\n]+/).filter(item => item.trim()).length : 0 };
}

function naiDirectorPromptPanel(content) {
  const positive = naiPromptStats(content.naiPositivePrompt);
  const negative = naiPromptStats(content.naiNegativePrompt);
  const hasChinese = containsCjk(content.naiPositivePrompt) || containsCjk(content.naiNegativePrompt);
  const status = hasChinese ? "检测到中文，请让 Agent 转换为英文 NAI 标签" : (positive.tags ? "英文标签已就绪" : "等待 Agent 写入英文标签");
  return `<section class="nai-director-workbench" data-nai-language-state="${hasChinese ? "invalid" : "ready"}"><div class="nai-workbench-status"><div>${icon(hasChinese ? "languages" : "badge-check")}<span><strong>NAI 标签项目</strong><small>${esc(status)}</small></span></div><div class="nai-status-count"><span>正面 <strong>${positive.tags}</strong> tags</span><span>负面 <strong>${negative.tags}</strong> tags</span></div></div><div class="nai-prompt-tabs"><section class="nai-prompt-pane is-positive"><header><div><span>POSITIVE PROMPT</span><h2>正面提示词</h2></div><strong>${positive.characters} 字符</strong></header><textarea data-field="naiPositivePrompt" rows="10" spellcheck="false" placeholder="1girl, adult woman, short black hair, medium shot, eye level, modern Japanese home, cinematic lighting">${esc(content.naiPositivePrompt)}</textarea></section><section class="nai-prompt-pane is-negative"><header><div><span>NEGATIVE PROMPT</span><h2>负面提示词</h2></div><strong>${negative.characters} 字符</strong></header><textarea data-field="naiNegativePrompt" rows="6" spellcheck="false" placeholder="bad anatomy, bad hands, extra fingers, duplicate person, text, watermark">${esc(content.naiNegativePrompt)}</textarea></section></div><details class="nai-ingredients"><summary>${icon("list-filter")}镜头标签素材 <span>由 Agent 写入英文，供核对和重新编译</span></summary><div class="field-grid shot-language-grid">${field("场景 / 时间", "scene", content.scene, "textarea", [], `rows="2" placeholder="modern Japanese home, entryway, evening"`)}${field("角色互动与共同事件", "action", content.action, "textarea", [], `rows="2" placeholder="homecoming confrontation, avoiding eye contact"`)}${field("整体情绪氛围", "expression", content.expression, "textarea", [], `rows="2" placeholder="tense atmosphere, restrained shock"`)}${field("光影设计", "lighting", content.lighting, "textarea", [], `rows="2" placeholder="cool interior light, warm sunset outside"`)}${field("画面风格", "style", content.style, "textarea", [], `rows="2" placeholder="clean lineart, flat color, cel shading"`)}</div></details></section>`;
}

function referenceCards(ownerType, ownerId) {
  const refs = referencesFor(ownerType, ownerId);
  if (!refs.length) return `<div class="reference-empty">还没有参考图。上传后可在这里预览、排序和控制是否参与生成。</div>`;
  return `<div class="reference-grid">${refs.map((reference, index) => `<article class="reference-card ${reference.enabled ? "is-enabled" : "is-disabled"}" draggable="true" data-reference-id="${esc(reference.id)}">${referenceThumb(reference)}<div class="reference-card-body"><div class="reference-card-top"><span class="reference-index">${String(index + 1).padStart(2, "0")}</span><strong>${esc(reference.file_name)}</strong><label class="switch-label" title="是否参与生成"><input type="checkbox" data-ref-toggle="${esc(reference.id)}" ${reference.enabled ? "checked" : ""} /><span class="switch"></span></label></div><div class="reference-badges">${reference.is_primary ? "主参考" : ""}</div><select class="reference-type" data-ref-type="${esc(reference.id)}">${optionMarkup(REFERENCE_TYPE_OPTIONS, reference.reference_type)}</select><input class="reference-note" data-ref-note="${esc(reference.id)}" value="${esc(reference.note || "")}" placeholder="添加参考说明" /><div class="reference-actions"><button class="icon-button" data-ref-move="up" data-ref-id="${esc(reference.id)}" title="上移优先级">${icon("arrow-up")}</button><button class="icon-button" data-ref-move="down" data-ref-id="${esc(reference.id)}" title="下移优先级">${icon("arrow-down")}</button><button class="icon-button" data-ref-primary="${esc(reference.id)}" title="设为主参考">${icon("star")}</button><label class="icon-button" title="替换参考图">${icon("replace")}<input class="visually-hidden" type="file" accept="image/*" data-replace-reference="${esc(reference.id)}" /></label><button class="icon-button danger" data-delete-ref="${esc(reference.id)}" title="删除参考图">${icon("trash-2")}</button></div></div></article>`).join("")}</div>`;
}

function referencePanel(ownerType, ownerId, title = "参考图板", description = "选择的图片会保存在当前项目中") {
  const formId = `reference-form-${ownerType}-${ownerId}`.replace(/[^A-Za-z0-9_-]/g, "-");
  const defaultType = ownerType === "shot" ? "composition" : ownerType === "world" ? "world_impression" : "character_design";
  return `<section class="panel reference-panel" data-reference-owner="${esc(ownerType)}" data-reference-owner-id="${esc(ownerId)}"><div class="panel-header"><div><div class="panel-title">${icon("images")} ${esc(title)}</div><p class="panel-subtitle">${esc(description)}</p></div><span class="panel-label">${String(referencesFor(ownerType, ownerId).length).padStart(2, "0")} FILES</span></div><div class="reference-upload-bar" id="${esc(formId)}"><label class="file-picker">${icon("upload")}<span>选择参考图</span><input class="visually-hidden" id="${esc(formId)}-files" type="file" accept="image/*" multiple /></label><select id="${esc(formId)}-type">${optionMarkup(REFERENCE_TYPE_OPTIONS, defaultType)}</select><input id="${esc(formId)}-note" placeholder="本批参考图说明（可选）" /><button class="button button-secondary" data-upload-reference="${esc(formId)}" data-owner-type="${esc(ownerType)}" data-owner-id="${esc(ownerId)}">${icon("plus")}上传到当前项目</button></div><div class="reference-list">${referenceCards(ownerType, ownerId)}</div></section>`;
}

function selectedGenerationReferences() {
  const ids = [];
  const enabled = refs => refs.filter(item => item.enabled).sort((a, b) => Number(b.is_primary) - Number(a.is_primary) || a.sort_order - b.sort_order);
  const add = refs => refs.forEach(item => { if (!ids.includes(item.id) && ids.length < 6) ids.push(item.id); });
  const characterGroups = getSelectedCharacters().map(character => enabled(referencesFor("character", character.id)));
  characterGroups.forEach(refs => add(refs.slice(0, 1)));
  add(enabled(referencesFor("shot", state.shotId)));
  add(enabled(referencesFor("world", "world-bible")));
  characterGroups.forEach(refs => add(refs.slice(1)));
  return ids.map(id => allReferences.find(item => item.id === id)).filter(Boolean);
}

function storyboardContractPanel(shot) {
  const source = shot?.source || {};
  const postText = Array.isArray(shot?.postText) ? shot.postText : [];
  const safeAreas = Array.isArray(shot?.textSafeAreas) ? shot.textSafeAreas : [];
  const selectedIds = new Set(shot?.content?.selectedCharacters || []);
  const relevantOwners = new Set([shot?.id, "world-bible", ...selectedIds]);
  const checklist = (state.storyboardChecklist || []).filter(item => !item.ownerId || relevantOwners.has(item.ownerId));
  const reminders = [...checklist.map(item => item.message).filter(Boolean)];
  state.characters.filter(character => selectedIds.has(character.id)).forEach(character => {
    (character.needsUserInput || []).forEach(message => reminders.push(`${character.name}：${message}`));
    if ((character.referenceRequests || []).length && !referencesFor("character", character.id).length) {
      character.referenceRequests.forEach(message => reminders.push(`${character.name}：${message}`));
    }
  });
  const uniqueReminders = [...new Set(reminders)];
  const warnings = Array.isArray(shot?.warnings) ? shot.warnings : [];
  const batch = (state.sourceBatches || []).find(item => item.batch_id === source.batchId);
  const adaptationLabels = { direct: "直接呈现", visualized: "叙事视觉化", agent_bridge: "衔接补充" };
  const kindLabels = { dialogue: "对白", narration: "旁白", sfx: "音效" };
  const positionLabels = { "top-left": "左上", "top-right": "右上", left: "左侧", right: "右侧", bottom: "底部" };
  const bubblePack = selectedBubblePack();
  let textRows = postText.length
    ? postText.map((item, index) => {
        const assetOptions = letteringAssetOptions(item, true);
        const customLayout = normalizeLetteringLayout(item.layout);
        const layoutSummary = customLayout
          ? `<div class="post-layout-summary">${icon("move-diagonal-2")}<span>自定义排版</span><strong>水平 ${Math.round(customLayout.x * 100)}% · 垂直 ${Math.round(customLayout.y * 100)}% · 大小 ${Math.round(customLayout.width * 100)}%</strong></div>`
          : "";
        return `<li class="post-text-editor-item ${item.hidden ? "is-hidden" : ""}"><div class="post-text-meta"><select data-post-semantic="${index}" aria-label="气泡语义">${optionMarkup(BUBBLE_SEMANTIC_OPTIONS, item.bubbleSemantic || "dialogue")}</select><select data-post-position="${index}" aria-label="文字位置">${optionMarkup(TEXT_POSITION_OPTIONS, item.position || "top-right")}</select><select data-post-bubble="${index}" aria-label="气泡样式">${assetOptions}</select></div><textarea data-post-text="${index}" rows="2" maxlength="200" aria-label="后期文字">${esc(item.text)}</textarea>${layoutSummary}<div class="post-text-footer"><small>${item.hidden ? "不导出" : esc(kindLabels[item.kind] || item.bubbleSemantic || item.kind || "文字")}</small><button class="text-button post-layout-button" data-edit-lettering="${index}" ${shot?.content?.lastImage ? "" : "disabled"}>${icon("move")}排字</button><span class="${String(item.text || "").length > 30 ? "is-long" : ""}">${String(item.text || "").length}/30</span><button class="icon-button danger" data-delete-post-text="${index}" title="删除后期文字">${icon("trash-2")}</button></div></li>`;
      }).join("")
    : `<li class="contract-empty">当前镜头没有后期文字</li>`;
  textRows += `<li class="post-text-add"><button class="text-button" id="addPostTextButton">${icon("plus")}添加后期文字</button></li>`;
  const reminderRows = uniqueReminders.length
    ? uniqueReminders.map(message => `<li>${icon("circle-alert")}<span>${esc(message)}</span></li>`).join("")
    : `<li class="contract-empty">当前镜头没有待补充项目</li>`;
  const warningRows = warnings.map(message => `<li>${icon("triangle-alert")}<span>${esc(message)}</span></li>`).join("");
  return `<section class="panel storyboard-contract-panel"><div class="panel-header"><div><div class="panel-title">${icon("notebook-tabs")}分镜来源与后期文字</div><p class="panel-subtitle">用于核对改编依据和排版留白，不会自动触发生图</p></div><span class="panel-label">${esc(source.batchId || "手动镜头")}</span></div><div class="storyboard-contract-grid"><section><div class="contract-heading"><span>原文锚点</span><em>${esc(adaptationLabels[source.adaptationKind] || source.adaptationKind || "未标注")}</em></div><blockquote>${source.anchor ? esc(source.anchor) : "当前镜头没有导入来源记录"}</blockquote>${batch ? `<p class="contract-batch">${esc(batch.source_title || batch.source_file || batch.batch_id)} · ${Number(batch.char_count || 0)} 字</p>` : ""}</section><section><div class="contract-heading"><span>后期文字</span><em>${postText.length} 项</em></div><ul class="post-text-list">${textRows}</ul><div class="safe-area-row"><span>文字安全区</span><strong>${safeAreas.length ? safeAreas.map(value => esc(positionLabels[value] || value)).join("、") : "未设置"}</strong></div></section><section class="contract-reminders"><div class="contract-heading"><span>完善清单</span><em>提示，不阻断生成</em></div><ul>${reminderRows}${warningRows}</ul></section></div></section>`;
}

function layoutSummary(shot) {
  const layout = shot?.layoutMeta || {};
  const row = Number(layout.rowIndex || 1);
  const slot = Number(layout.slotIndex || 1);
  const border = { none: "无边框", solid_black_2px: "黑边", solid_white_2px: "白边", broken_panel: "破格边" }[layout.borderStyle] || "无边框";
  return `第 ${row} 行 / 槽位 ${slot} · ${border}`;
}

function panelBeatEditor(content) {
  return '<p class="prompt-authoring-note">多格漫画由 Agent 写入最终英文提示词；软件不决定格数或布局。</p>';
}

function projectConversationStrip() {
  if (settings.generation_mode === "api") return "";
  const bound = conversationBinding.status === "bound" && conversationBinding.url;
  const pending = conversationBinding.status === "pending";
  const status = bound ? "已绑定" : pending ? "等待首次生成" : conversationBinding.status === "error" ? "状态不可用" : "未绑定";
  const title = bound ? (conversationBinding.title || getProject()?.name || "项目对话") : pending ? "新聊天已打开，首次生成后自动记录对话" : "首次生成会自动创建并绑定独立对话";
  const actions = bound
    ? `<button class="text-button" id="openProjectConversationButton">${icon("external-link")}打开对话</button><button class="text-button" id="newProjectConversationButton">${icon("message-square-plus")}新建对话</button><button class="text-button danger-text" id="unbindProjectConversationButton">解除绑定</button>`
    : `<button class="text-button" id="bindCurrentConversationButton">${icon("link")}绑定当前对话</button><button class="text-button" id="newProjectConversationButton">${icon("message-square-plus")}新建项目对话</button>`;
  return `<section class="conversation-strip" data-conversation-status="${esc(conversationBinding.status || "unbound")}"><div class="conversation-strip-icon">${icon(bound ? "messages-square" : "message-square-dashed")}</div><div class="conversation-strip-copy"><span>镜像站项目对话 · ${esc(status)}</span><strong>${esc(title)}</strong></div><div class="conversation-strip-actions">${actions}</div></section>`;
}

function directorView() {
  const shot = getShot();
  const content = currentShotContent();
  const characters = getSelectedCharacters(); const generationRefs = selectedGenerationReferences();
  const stylePack = effectiveShotStylePack(content);
  const styleReferenceTotal = packReferenceCount(stylePack);
  const isGenerating = shotStatus(shot) === "生成中";
  const latestGeneration = content.generationHistory?.[0];
  const origin = latestGeneration?.generationChannel
    ? `${latestGeneration.generationChannel}${latestGeneration.generationModel ? ` · ${latestGeneration.generationModel}` : ""}`
    : latestGeneration?.generationMode
      ? `升级前记录：${latestGeneration.generationMode === "api" ? "API 节点" : "镜像站浏览器"}`
      : "";
  const image = content.lastImage ? `<img src="${esc(content.lastImage)}" alt="${esc(state.shotId)} 生成结果" />${origin ? `<div class="generation-origin">${icon("route")}${esc(origin)}</div>` : ""}${shotStatus(shot) !== "已确认" ? `<button class="button preview-confirm" id="confirmShotButton">${icon("check")}确认采用</button>` : `<div class="preview-confirmed">${icon("badge-check")}已确认</div>`}` : `<div class="image-empty">${icon("image-plus")}<span>生成后的镜头会出现在这里</span></div>`;
  const shotRail = state.shots.map((item, index) => `<button class="shot-rail-item ${item.id === state.shotId ? "active" : ""}" data-shot-id="${esc(item.id)}" draggable="true"><span class="rail-number">${String(index + 1).padStart(2, "0")}</span><span class="rail-copy"><strong>${esc(item.title)}</strong><small>${esc(item.type)} · ${esc(shotStatus(item))}</small></span><span class="rail-mark"></span></button>`).join("");
  const channelLabel = settings.generation_mode === "api" ? `API：${settings.image_api_name || "自定义节点"}` : "镜像站浏览器";
  const progress = Math.round(state.shots.filter(item => ["待确认", "已确认"].includes(shotStatus(item))).length / Math.max(1, state.shots.length) * 100);
  const naiMode = isNaiProject();
  const headingTitle = naiMode ? "NAI 镜头导演台" : "镜头导演台";
  const headingCopy = naiMode ? `编辑当前镜头最终发送的英文标签，完成 <strong>${esc(state.shotId)}</strong>。` : `锁定角色、构图与光影，完成 <strong>${esc(state.shotId)}</strong> 的画面调度。`;
  const promptWorkspace = naiMode
    ? naiDirectorPromptPanel(content)
    : `<div class="prompt-field">${field("镜头意图", "prompt", content.prompt, "textarea", [], `rows="4"`)}</div><hr class="section-rule" /><div class="form-section-title"><h2>画面语言</h2><span>SHOT LANGUAGE</span></div><div class="field-grid shot-language-grid">${field("场景 / 时间", "scene", content.scene, "textarea", [], `rows="2"`)}${field("角色互动与共同事件", "action", content.action, "textarea", [], `rows="2"`)}${field("整体情绪氛围", "expression", content.expression, "textarea", [], `rows="2"`)}${field("光影设计", "lighting", content.lighting, "textarea", [], `rows="2"`)}${field("艺术风格", "style", content.style, "textarea", [], `rows="2"`)}</div>`;
  const referenceSummary = naiMode ? "NAI 纯文本请求 · 参考图仅供工作台核对" : `画风 ${styleReferenceTotal} 张 · 项目参考 ${generationRefs.length} 张`;
  const styleSummary = naiMode ? "仅合并英文画风标签；画风参考图不上传" : `${styleReferenceTotal} 张画风参考图将随本次请求发送`;
  return `<section class="page-heading"><div><div class="heading-index">${naiMode ? "NAI TAG DIRECTOR / 01" : "DIRECTOR'S DESK / 01"}</div><h1>${headingTitle}</h1><p>${headingCopy}</p></div><div class="heading-readout"><span>项目类型</span><strong>${naiMode ? "NAI 英文标签" : esc(channelLabel)}</strong><em>${isGenerating ? "执行中" : "已就绪"}</em></div><button class="button button-primary" id="generateButton" ${isGenerating ? "disabled" : ""}>${icon(isGenerating ? "loader-circle" : "sparkles")}${isGenerating ? "生成中..." : "生成当前镜头"}</button></section>${projectConversationStrip()}<section class="shot-rail" aria-label="镜头时间轴"><div class="rail-header"><span>${icon("film")}镜头胶片带</span><small>${String(state.shots.length).padStart(2, "0")} 个镜头 · 连续性已锁定</small></div><div class="rail-track">${shotRail}<button class="rail-add" id="addShotFromRail" title="添加镜头">${icon("plus")}</button></div></section><div class="director-layout"><section class="panel editor-panel ${naiMode ? "is-nai-editor" : ""}"><div class="panel-header"><div class="panel-title">${icon(naiMode ? "tags" : "crosshair")}${naiMode ? "NAI 生成画板" : "镜头规划"}</div><span class="panel-label">STATIC COMIC</span></div><div class="editor-body"><div class="field-grid shot-basics">${field("镜头编号", "shotId", shot?.id || state.shotId, "input", [], "readonly")}${field("景别", "shotType", content.shotType, "select", SHOT_TYPE_OPTIONS)}${field("摄影机角度", "cameraAngle", content.cameraAngle, "select", CAMERA_ANGLE_OPTIONS)}${field("动态表现", "dynamicExpression", content.dynamicExpression, "select", DYNAMIC_EXPRESSION_OPTIONS)}${characterSelector(content)}</div>${panelBeatEditor(content)}<div class="shot-style-control"><div class="field"><label>当前镜头画风</label><select id="shotStylePackSelect">${shotStyleOptions(content)}</select></div><div class="shot-style-summary"><strong>${esc(stylePack?.display_name || "不使用画风参考")}</strong><span>${styleSummary}</span></div></div>${promptWorkspace}<details class="final-request-preview"><summary>${icon("file-search")}本次最终请求</summary><pre>${esc(naiMode ? content.naiPositivePrompt : composePrompt())}</pre></details><div class="editor-footer"><div class="auto-note">${icon("shield-check")}${referenceSummary}</div><button class="button button-primary" id="generateButtonBottom" ${isGenerating ? "disabled" : ""}>${icon(isGenerating ? "loader-circle" : "arrow-up-right")}${isGenerating ? "生成中..." : `发送到${esc(channelLabel)}`}</button></div></div></section><aside class="side-stack"><section class="panel preview-panel"><div class="panel-header"><div class="panel-title">${icon("scan-search")}当前预览</div><span class="panel-label">${esc(state.shotId)}</span></div><div class="image-result" id="imageResult">${image}</div></section><section class="panel continuity-panel"><div class="panel-header"><div class="panel-title">${icon("fingerprint")}连续性上下文</div><span class="panel-label">${characters.length} LOCKED</span></div><div class="context-list">${characters.length ? characters.map(character => `<div class="context-row"><div class="avatar">${esc(character.name.slice(0, 1))}</div><div><strong>${esc(character.name)} / ${esc(character.id)}</strong><span>${esc(characterDirectionSummary(content.characterDirections?.[character.id]) || character.appearance)}</span></div><button class="row-action" data-manage-character="${esc(character.id)}" data-view-jump="characters">编辑</button></div>`).join("") : `<div class="empty-context">尚未选择入镜角色。请在镜头规划中勾选。</div>`}<div class="context-row"><div class="avatar">WB</div><div><strong>${esc(state.world.name)}</strong><span>${esc(state.world.visual)}</span></div><button class="row-action" data-view-jump="world">查看</button></div></div></section><section class="panel progress-panel"><div class="progress-meta"><span>制作进度</span><span>${progress}%</span></div><div class="progress-line"><span style="width:${progress}%"></span></div><div class="progress-meta progress-meta-last"><span>生图上下文</span><span>${naiMode ? "英文标签 · 纯文本" : `画风 ${styleReferenceTotal} · 项目参考 ${generationRefs.length} / 10`}</span></div></section><section class="panel queue-panel"><div class="panel-header"><div class="panel-title">${icon("list-video")}镜头队列</div><button class="text-button" data-view-jump="storyboard">查看全部</button></div><div class="context-list">${state.shots.slice(0, 3).map(item => `<div class="context-row"><div class="avatar mono">${esc(item.id.split("-")[1])}</div><div><strong>${esc(item.title)}</strong><span>${esc(item.type)} · ${esc(shotStatus(item))}</span></div></div>`).join("")}</div></section></aside></div>${storyboardContractPanel(shot)}${referencePanel("shot", state.shotId, "当前镜头参考板", naiMode ? "NAI 项目中参考图用于人工核对，不随纯文本请求上传" : "角色位置、废稿修改、动作、背景颜色和构图参考")}${letteringLayoutEditor()}`;
}

function charactersView() {
  const selected = getCharacter();
  return `<section class="page-heading"><div><div class="heading-index">CHARACTER BIBLE / 02</div><h1>角色库。</h1><p>每个角色都是一组不可随意漂移的视觉约束。</p></div><button class="button button-primary" id="newCharacterButton">${icon("user-plus")}创建角色</button></section><div id="characterFormSlot"></div><div class="library-grid">${state.characters.map(character => { const refs = referencesFor("character", character.id); const inShot = selectedCharacterIds().includes(character.id); const summary = [optionalText(character.role), optionalText(character.faction)].filter(Boolean).join(" · "); const tags = [optionalText(character.appearance).split("，")[0], optionalText(character.signature)].filter(Boolean); return `<article class="library-card ${selected?.id === character.id ? "is-selected" : ""}" data-edit-character="${esc(character.id)}" tabindex="0" role="button" aria-label="编辑角色 ${esc(character.name)}"><div class="card-code">${esc(character.id)} / DNA LOCK</div><span class="card-edit-mark" title="编辑角色资料">${icon("pencil")}</span>${refs[0] ? referenceThumb(refs[0], true) : ""}<h3>${esc(character.name)}</h3><p>${esc(summary || "尚未填写身份信息")}</p>${tags.length ? `<div class="tag-row">${tags.map(tag => `<span class="tag">${esc(tag)}</span>`).join("")}</div>` : ""}<div class="card-actions"><button class="text-button" data-use-character="${esc(character.id)}">${inShot ? "移出当前镜头" : "加入当前镜头"}</button><button class="text-button" data-manage-character="${esc(character.id)}">${refs.length ? `${refs.length} 张参考图` : "管理参考图"}</button><button class="text-button danger-text" data-delete-character="${esc(character.id)}">删除</button></div></article>`; }).join("")}</div>${selected ? referencePanel("character", selected.id, `角色参考板 / ${selected.name}`, "用正面设定、发型服装、表情和姿势维持角色一致性") : ""}`;
}

function characterForm(character = null) {
  const editing = Boolean(character);
  const roleFaction = character ? [optionalText(character.role), optionalText(character.faction)].filter(Boolean).join(" / ") : "";
  const costumeSignature = character ? [optionalText(character.costume), optionalText(character.signature)].filter(Boolean).join("；") : "";
  return `<div class="library-form" data-editing-character-id="${esc(character?.id || "")}" data-original-role-faction="${esc(roleFaction)}" data-original-costume-signature="${esc(costumeSignature)}"><div class="library-form-heading"><div><span>${editing ? `EDITING / ${esc(character.id)}` : "NEW CHARACTER"}</span><h3>${editing ? `设置角色：${esc(character.name)}` : "创建角色 / CHARACTER DNA"}</h3></div>${editing ? `<button class="icon-button" id="closeCharacterEditorButton" title="关闭角色设置">${icon("x")}</button>` : ""}</div><div class="field-grid"><div class="field"><label>角色名称</label><input id="newCharacterName" value="${esc(character?.name || "")}" placeholder="例如：莉亚" /></div><div class="field"><label>身份 / 阵营</label><input id="newCharacterRole" value="${esc(roleFaction)}" placeholder="例如：灯塔守望者 / 雾港自治会" /></div><div class="field wide"><label>性格与动机</label><textarea id="newCharacterPersonality" rows="2" placeholder="性格、目标、行为习惯">${esc(character?.personality || "")}</textarea></div><div class="field wide"><label>外貌锁定</label><textarea id="newCharacterAppearance" rows="2" placeholder="发色、眼睛、脸型、身体比例">${esc(character?.appearance || "")}</textarea></div><div class="field wide"><label>服装与标志元素</label><textarea id="newCharacterCostume" rows="2" placeholder="服装、道具、代表色、发饰">${esc(costumeSignature)}</textarea></div><div class="field wide"><label>${editing ? "新增参考图（可多选）" : "首次参考图（可多选）"}</label><input id="newCharacterReferences" type="file" accept="image/*" multiple /></div></div><div class="editor-footer"><button class="button button-secondary" id="cancelCharacterButton">取消</button><button class="button button-primary" id="saveCharacterButton">${icon("save")}${editing ? "更新角色" : "保存角色并上传参考图"}</button></div></div>`;
}

const WORLD_FIELDS = [["世界名称", "name"], ["时代背景", "era"], ["国家 / 区域", "country"], ["城市 / 地点", "city"], ["地理环境", "geography"], ["科技水平", "technology"], ["魔法体系", "magic"], ["历史事件", "history"], ["组织与阵营", "factions"], ["禁忌规则", "rules"], ["核心冲突", "conflict"], ["天气规律", "weather"], ["时间规律", "time"], ["视觉色彩", "visual"], ["材质与环境", "materials"]];
function worldView() { return `<section class="page-heading"><div><div class="heading-index">WORLD BIBLE / 03</div><h1>世界观。</h1><p>让每一张图都发生在同一个世界里。</p></div><button class="button button-primary" id="saveWorldButton">${icon("save")}保存世界观</button></section><div class="world-layout"><section class="panel world-sheet"><div class="world-fields">${WORLD_FIELDS.map(([label, key]) => field(label, `world.${key}`, state.world[key], ["name", "era", "country", "city"].includes(key) ? "input" : "textarea", [], ["name", "era", "country", "city"].includes(key) ? "" : "rows=\"3\"" )).join("")}</div></section><section class="world-summary"><section class="panel"><div class="panel-header"><div class="panel-title">${icon("book-open")}WORLD BIBLE</div><span class="panel-label">ACTIVE</span></div><div class="world-sheet"><div class="world-section"><h3>世界与时代</h3><p>${esc(state.world.name)} · ${esc(state.world.era)}</p></div><div class="world-section"><h3>地点与环境</h3><p>${esc(state.world.country)} / ${esc(state.world.city)}
${esc(state.world.geography)}
${esc(state.world.weather)}</p></div><div class="world-section"><h3>规则与冲突</h3><p>${esc(state.world.conflict)}
${esc(state.world.rules)}</p></div><div class="world-section"><h3>视觉约束</h3><p>${esc(state.world.visual)}
${esc(state.world.materials)}</p></div></div></section>${referencePanel("world", "world-bible", "世界观参考板", "世界主视觉、建筑、地貌、地图、色板和时代氛围会作为镜头上下文")}</section></div>`; }

function selectedStylePack() { return stylePacks.find(pack => pack.id === state.artDirection.stylePackId) || null; }
function effectiveShotStylePack(content = currentShotContent()) {
  if (content.stylePackOverride === "none") return null;
  if (content.stylePackOverride && content.stylePackOverride !== "project") {
    return stylePacks.find(pack => pack.id === content.stylePackOverride) || null;
  }
  return state.artDirection.locked ? selectedStylePack() : null;
}
function shotStyleOptions(content) {
  const values = [
    { value: "project", label: `跟随项目画风${selectedStylePack() ? ` · ${selectedStylePack().display_name}` : " · 未设置"}` },
    { value: "none", label: "不使用项目画风" },
    ...stylePacks.map(pack => ({ value: pack.id, label: `${pack.display_name}${pack.source === "custom" ? " · 自定义" : ""}` })),
  ];
  return values.map(item => `<option value="${esc(item.value)}" ${content.stylePackOverride === item.value ? "selected" : ""}>${esc(item.label)}</option>`).join("");
}
function selectedBubblePack() { return bubblePacks.find(pack => pack.id === state.lettering.bubblePackId) || bubblePacks[0] || null; }
function letteringReferences() { return referencesFor("lettering", "bubble-library"); }
function letteringAssetValue(block) { return block.bubbleReferenceId ? `reference:${block.bubbleReferenceId}` : block.bubbleAssetId || ""; }
function letteringAssetOptions(block, includeAuto = false) {
  const selected = letteringAssetValue(block);
  const builtIn = (selectedBubblePack()?.assets || []).map(asset => `<option value="${esc(asset.id)}" ${asset.id === selected ? "selected" : ""}>${esc(asset.label)}</option>`);
  const custom = letteringReferences().map(reference => {
    const value = `reference:${reference.id}`;
    return `<option value="${esc(value)}" ${value === selected ? "selected" : ""}>自定义 · ${esc(reference.file_name)}</option>`;
  });
  return [includeAuto ? `<option value="" ${selected ? "" : "selected"}>按语义自动</option>` : "", ...builtIn, ...custom].join("");
}
function setLetteringAsset(block, value) {
  if (!block) return;
  if (value.startsWith("reference:")) {
    block.bubbleReferenceId = value.slice("reference:".length);
    block.bubbleAssetId = "";
  } else {
    block.bubbleReferenceId = "";
    block.bubbleAssetId = value;
  }
}
function letteringAsset(block) {
  if (block.bubbleReferenceId) {
    const reference = letteringReferences().find(item => item.id === block.bubbleReferenceId);
    if (reference) return { id: reference.id, label: reference.file_name, semantic_type: "dialogue", url: reference.url, referenceId: reference.id };
  }
  const pack = selectedBubblePack();
  if (!pack) return null;
  const assetId = block.bubbleAssetId || pack.semantic_defaults?.[block.bubbleSemantic || block.kind || "dialogue"] || "";
  return pack.assets?.find(asset => asset.id === assetId) || pack.assets?.[0] || null;
}
function letteringLayoutFor(block, index) {
  if (block.layout) return normalizeLetteringLayout(block.layout);
  const preceding = (getShot()?.postText || []).slice(0, index).filter(item => !item.hidden && item.position === block.position).length;
  return autoLetteringLayout(block, preceding);
}
function letteringPreviewItems(shot = getShot()) {
  return (shot?.postText || []).map((block, index) => {
    const isText = block.elementType === "text";
    const asset = letteringAsset(block);
    if (!isText && !asset) return null;
    return { block, index, asset, isText, layout: letteringLayoutFor(block, index) };
  }).filter(Boolean);
}
function letteringLayoutEditor() {
  const shot = getShot();
  const block = shot?.postText?.[letteringEditorIndex];
  const imageUrl = shot?.content?.lastImage;
  if (!block || !imageUrl) return "";
  const pack = selectedBubblePack();
  const isText = block.elementType === "text";
  const asset = letteringAsset(block);
  if (!isText && (!pack || !asset)) return "";
  const layout = letteringLayoutFor(block, letteringEditorIndex);
  const assetOptions = letteringAssetOptions(block);
  const presets = TEXT_POSITION_OPTIONS.map(item => `<button type="button" class="proof-preset ${block.position === item.value && !block.layout ? "is-active" : ""}" data-lettering-preset="${esc(item.value)}">${esc(item.label)}</button>`).join("");
  const bubbles = letteringPreviewItems(shot).map(item => {
    const selected = item.index === letteringEditorIndex;
    const itemBlock = item.block;
    if (item.isText) return `<div class="proof-bubble proof-text-element ${itemBlock.hidden ? "is-hidden" : ""} ${selected ? "is-active" : ""}" ${selected ? 'id="letteringProofBubble"' : ""} data-lettering-index="${item.index}" data-semantic="${esc(itemBlock.bubbleSemantic || "narration")}" style="left:${item.layout.x * 100}%;top:${item.layout.y * 100}%;width:${item.layout.width * 100}%;--lettering-font-scale:${item.layout.fontScale};--lettering-rotation:${item.layout.rotation}deg"><span>${esc(itemBlock.text || "文字")}</span>${selected ? `<button type="button" class="proof-resize-handle" data-lettering-resize title="拖动调整大小" aria-label="拖动调整大小">${icon("move-diagonal-2")}</button>` : ""}</div>`;
    return `<div class="proof-bubble ${itemBlock.hidden ? "is-hidden" : ""} ${selected ? "is-active" : ""}" ${selected ? 'id="letteringProofBubble"' : ""} data-lettering-index="${item.index}" data-semantic="${esc(itemBlock.bubbleSemantic || itemBlock.kind || "dialogue")}" data-asset-semantic="${esc(item.asset.semantic_type || "dialogue")}" style="left:${item.layout.x * 100}%;top:${item.layout.y * 100}%;width:${item.layout.width * 100}%;--lettering-font-scale:${item.layout.fontScale};--lettering-rotation:${item.layout.rotation}deg"><img src="${esc(item.asset.url)}" alt="" style="transform:scaleX(${item.layout.flip ? -1 : 1})" /><span>${esc(itemBlock.text || "文字")}</span>${selected ? `<button type="button" class="proof-resize-handle" data-lettering-resize title="拖动调整大小" aria-label="拖动调整气泡大小">${icon("move-diagonal-2")}</button>` : ""}</div>`;
  }).join("");
  return `<div class="lettering-proof-overlay" role="dialog" aria-modal="true" aria-labelledby="letteringProofTitle"><section class="lettering-proof-shell"><header class="lettering-proof-header"><div><span>LETTERING PROOF / ${esc(shot.id)}</span><h2 id="letteringProofTitle">可视化排字</h2></div><div class="proof-header-actions"><span>${block.hidden ? "当前不导出" : "将合成到成品"}</span><button class="icon-button" id="closeLetteringEditorButton" title="关闭排字编辑器">${icon("x")}</button></div></header><div class="lettering-proof-workspace"><section class="proof-stage"><div class="proof-stage-label"><span>${icon("move")}拖动气泡调整位置，点击切换编辑对象</span><strong>${Math.round(layout.width * 100)}% 画宽</strong></div><div class="proof-frame-wrap"><div class="proof-frame" id="letteringProofFrame"><img class="proof-shot" src="${esc(imageUrl)}" alt="${esc(shot.title)} 排字预览" />${bubbles}</div></div></section><aside class="proof-controls"><section><div class="proof-control-heading"><span>ADD</span><strong>添加自定义素材</strong></div><label class="proof-bubble-dropzone" id="letteringBubbleDropzone">${icon("image-plus")}<span><strong>拖入透明气泡</strong><small>PNG 或 WebP，也可点击选择</small></span><input class="visually-hidden" id="letteringBubbleUploadInput" type="file" accept="image/png,image/webp" /></label></section><section><div class="proof-control-heading"><span>CONTENT</span><strong>文字与样式</strong></div><label class="proof-field"><span>后期文字</span><textarea id="letteringTextInput" rows="3" maxlength="200">${esc(block.text || "")}</textarea></label><label class="proof-field"><span>气泡样式</span><select id="letteringAssetSelect">${assetOptions}</select></label></section><section><div class="proof-control-heading"><span>POSITION</span><strong>快速位置</strong></div><div class="proof-presets">${presets}</div><label class="proof-range"><span>水平位置 <output id="letteringXOutput">${Math.round(layout.x * 100)}%</output></span><input id="letteringXRange" type="range" min="0" max="${Math.round((1 - layout.width) * 100)}" value="${Math.round(layout.x * 100)}" /></label><label class="proof-range"><span>垂直位置 <output id="letteringYOutput">${Math.round(layout.y * 100)}%</output></span><input id="letteringYRange" type="range" min="0" max="92" value="${Math.round(layout.y * 100)}" /></label><label class="proof-range"><span>气泡大小 <output id="letteringWidthOutput">${Math.round(layout.width * 100)}%</output></span><input id="letteringWidthRange" type="range" min="14" max="48" value="${Math.round(layout.width * 100)}" /></label><label class="proof-range"><span>文字大小 <output id="letteringFontSizeOutput">${Math.round(layout.fontScale * 100)}%</output></span><input id="letteringFontSizeRange" type="range" min="60" max="140" value="${Math.round(layout.fontScale * 100)}" /></label><label class="proof-range"><span>旋转角度 <output id="letteringRotationOutput">${Math.round(layout.rotation)}°</output></span><input id="letteringRotationRange" type="range" min="-180" max="180" value="${Math.round(layout.rotation)}" /></label></section><section class="proof-switches"><label><input id="letteringFlipToggle" type="checkbox" ${layout.flip ? "checked" : ""} /><span class="switch"></span><span>水平翻转尾巴</span></label><label class="proof-hide-toggle"><input id="letteringHiddenToggle" type="checkbox" ${block.hidden ? "checked" : ""} /><span class="switch"></span><span>此条不导出</span></label></section><div class="proof-actions"><button class="button button-secondary" id="deleteLetteringElementButton">${icon("trash-2")}删除当前元素</button><button class="button button-secondary" id="resetLetteringLayoutButton">${icon("rotate-ccw")}恢复自动排版</button><button class="button button-primary" id="closeLetteringEditorDoneButton">${icon("check")}完成排字</button></div></aside></div></section></div>`;
}
function packReferenceCount(pack) { return pack ? [pack.references?.primary, ...(pack.references?.auxiliary || [])].filter(item => item?.enabled !== false).length : 0; }

function styleReferenceRail(pack) {
  if (!pack) return `<div class="style-reference-empty">选择画风后显示随生图请求发送的参考图。</div>`;
  const references = [pack.references.primary, ...(pack.references.auxiliary || [])];
  return `<div class="style-reference-rail">${references.map((reference, index) => `<figure class="style-reference-frame ${index === 0 ? "is-primary" : ""}"><img src="${esc(reference.url)}" alt="${esc(reference.label)}" loading="lazy" /><figcaption><span>${index === 0 ? "PRIMARY" : `AUX ${index}`}</span><strong>${esc(reference.label)}</strong></figcaption></figure>`).join("")}</div>`;
}

function customStyleForm() {
  if (!customStyleFormOpen) return "";
  const analysisFields = STYLE_ANALYSIS_FIELDS.map(item => `<div class="field"><label>${esc(item.label)}</label><textarea data-new-style-analysis="${esc(item.key)}" rows="2"></textarea></div>`).join("");
  return `<section class="panel custom-style-form"><div class="panel-header"><div><div class="panel-title">${icon("palette")}新建自定义画风</div><p class="panel-subtitle">1 张主参考图，可选 0–3 张辅助参考图</p></div><button class="icon-button" id="closeCustomStyleButton" title="关闭">${icon("x")}</button></div><div class="custom-style-body"><div class="field-grid"><div class="field"><label>画风名称</label><input id="customStyleName" maxlength="80" /></div><div class="field wide"><label>简短说明</label><input id="customStyleDescription" maxlength="500" /></div></div><div class="custom-upload-grid"><label class="style-file-slot is-required">${icon("image-plus")}<span>主参考图</span><small>必填</small><input id="customStylePrimary" type="file" accept="image/png,image/jpeg,image/webp" /></label><label class="style-file-slot">${icon("images")}<span>辅助参考图</span><small>最多 3 张</small><input id="customStyleAuxiliary" type="file" accept="image/png,image/jpeg,image/webp" multiple /></label></div><div class="style-analysis-grid">${analysisFields}</div><div class="field"><label>合成画风提示词</label><textarea id="customStylePrompt" rows="4"></textarea></div><div class="field"><label>排除提示词</label><textarea id="customStyleNegative" rows="3"></textarea></div><div class="editor-footer"><span class="auto-note">${icon("bot")}Agent 可通过本机接口写入分析，文字仍可编辑</span><button class="button button-primary" id="createCustomStyleButton">${icon("plus")}创建画风</button></div></div></section>`;
}

function styleView() {
  const pack = selectedStylePack();
  const analysis = state.artDirection.styleAnalysis || {};
  const presets = [`<button class="style-pack-tile ${!pack ? "is-selected" : ""}" data-select-style=""><span class="style-pack-none">${icon("ban")}</span><strong>不使用项目画风</strong><small>仅使用镜头描述</small></button>`, ...stylePacks.map(item => `<button class="style-pack-tile ${item.id === pack?.id ? "is-selected" : ""}" data-select-style="${esc(item.id)}"><img src="${esc(item.references.primary.url)}" alt="" loading="lazy" /><span class="style-source">${item.source === "custom" ? "CUSTOM" : "BUILT-IN"}</span><strong>${esc(item.display_name)}</strong><small>${packReferenceCount(item)} 张参考图</small></button>`)].join("");
  const analysisFields = STYLE_ANALYSIS_FIELDS.map(item => `<div class="field"><label>${esc(item.label)}</label><textarea data-art-analysis="${esc(item.key)}" rows="3" ${!pack ? "disabled" : ""}>${esc(analysis[item.key] || "")}</textarea></div>`).join("");
  const bubblePack = selectedBubblePack();
  const bubbleTiles = bubblePack ? bubblePack.assets.map(asset => `<button class="bubble-sample" data-bubble-preview="${esc(asset.id)}" title="${esc(asset.label)}"><img src="${esc(asset.url)}" alt="${esc(asset.label)}" loading="lazy" /><span>${esc(asset.label)}</span></button>`).join("") : `<div class="style-reference-empty">未发现可用气泡包</div>`;
  const customActions = pack?.editable ? `<button class="button button-secondary" id="saveCustomStyleButton">${icon("save")}更新文本</button><label class="button button-secondary style-file-button">${icon("image")}新主图<input class="visually-hidden" id="replaceCustomStylePrimary" type="file" accept="image/png,image/jpeg,image/webp" /></label><label class="button button-secondary style-file-button">${icon("images")}新辅助图<input class="visually-hidden" id="replaceCustomStyleAuxiliary" type="file" accept="image/png,image/jpeg,image/webp" multiple /></label><button class="button button-secondary" id="replaceCustomStyleAssetsButton">${icon("replace")}提交图片</button><button class="icon-button danger" id="deleteCustomStyleButton" title="删除自定义画风">${icon("trash-2")}</button>` : "";
  return `<section class="page-heading"><div><div class="heading-index">ART DIRECTION / 04</div><h1>艺术指导</h1><p>项目画风会锁定提示词，并将参考图随每个镜头发送。</p></div><label class="setting-toggle art-lock"><input type="checkbox" id="styleLockToggle" ${state.artDirection.locked ? "checked" : ""} /><span class="switch"></span><span>锁定项目画风</span></label><button class="button button-primary" id="openCustomStyleButton">${icon("plus")}自定义画风</button></section>${customStyleForm()}<div class="style-workspace"><section class="style-preset-band"><div class="style-section-heading"><div><span>STYLE PACKS</span><h2>画风样片</h2></div><strong>${stylePacks.length} 个可用画风</strong></div><div class="style-pack-strip">${presets}</div></section><section class="panel style-editor"><div class="panel-header"><div><div class="panel-title">${icon("swatch-book")}${esc(pack?.display_name || "未选择画风")}</div><p class="panel-subtitle">${esc(pack?.description || "当前项目不会附加画风参考图")}</p></div><span class="panel-label">${pack ? `${packReferenceCount(pack)} REFERENCES` : "NO STYLE"}</span></div>${styleReferenceRail(pack)}<div class="style-editor-body"><div class="style-analysis-grid">${analysisFields}</div><div class="field"><label>项目画风提示词</label><textarea data-art-prompt rows="5" ${!pack ? "disabled" : ""}>${esc(state.artDirection.compiledPrompt || "")}</textarea></div><div class="field"><label>排除提示词</label><textarea data-art-negative rows="4" ${!pack ? "disabled" : ""}>${esc(state.artDirection.negativePrompt || "")}</textarea></div><div class="editor-footer"><div class="style-editor-actions"><button class="button button-secondary" id="resetStylePresetButton" ${!pack ? "disabled" : ""}>${icon("rotate-ccw")}恢复预设</button>${customActions}</div><span class="auto-note">${icon("shield-check")}气泡与后期文字不会发送给生图模型</span></div></div></section><section class="panel lettering-editor"><div class="panel-header"><div><div class="panel-title">${icon("message-circle-more")}后期气泡</div><p class="panel-subtitle">${esc(bubblePack?.description || "项目气泡配置")}</p></div><select id="bubblePackSelect">${bubblePacks.map(item => `<option value="${esc(item.id)}" ${item.id === bubblePack?.id ? "selected" : ""}>${esc(item.display_name)}</option>`).join("")}</select></div><div class="bubble-sample-strip">${bubbleTiles}</div></section></div>`;
}

function applyStylePack(packId) {
  const pack = stylePacks.find(item => item.id === packId);
  state.artDirection = pack ? {
    stylePackId: pack.id,
    compiledPrompt: pack.compiled_prompt || "",
    negativePrompt: pack.negative_prompt || "",
    styleAnalysis: clone(pack.style_analysis || {}),
    locked: state.artDirection.locked !== false,
  } : { ...defaultProjectState().artDirection, locked: state.artDirection.locked !== false };
  saveState(); render();
}

async function createCustomStyle() {
  const name = document.querySelector("#customStyleName")?.value.trim();
  const primary = document.querySelector("#customStylePrimary")?.files?.[0];
  const auxiliary = [...(document.querySelector("#customStyleAuxiliary")?.files || [])];
  const prompt = document.querySelector("#customStylePrompt")?.value.trim();
  if (!name) return toast("请填写画风名称", { kind: "error" });
  if (!primary) return toast("自定义画风需要 1 张主参考图", { kind: "error" });
  if (auxiliary.length > 3) return toast("辅助参考图最多 3 张", { kind: "error" });
  if (!prompt) return toast("请填写合成画风提示词", { kind: "error" });
  const form = new FormData();
  form.append("display_name", name);
  form.append("description", document.querySelector("#customStyleDescription")?.value.trim() || "");
  form.append("compiled_prompt", prompt);
  form.append("negative_prompt", document.querySelector("#customStyleNegative")?.value.trim() || "");
  form.append("style_analysis", JSON.stringify(Object.fromEntries(STYLE_ANALYSIS_FIELDS.map(item => [item.key, document.querySelector(`[data-new-style-analysis="${item.key}"]`)?.value.trim() || ""]))));
  form.append("primary", primary);
  auxiliary.forEach(file => form.append("auxiliary", file));
  try {
    const pack = await api("/api/style-packs/custom", { method: "POST", body: form });
    await loadArtLibraries(); customStyleFormOpen = false; applyStylePack(pack.id); toast(`已创建画风：${pack.display_name}`);
  } catch (error) { toast(error.message, { kind: "error" }); }
}

async function saveCustomStyle() {
  const pack = selectedStylePack();
  if (!pack?.editable) return;
  try {
    const updated = await api(`/api/style-packs/${encodeURIComponent(pack.id)}/custom`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ style_analysis: state.artDirection.styleAnalysis, compiled_prompt: state.artDirection.compiledPrompt, negative_prompt: state.artDirection.negativePrompt }),
    });
    await loadArtLibraries(); applyStylePack(updated.id); toast("自定义画风文本已更新");
  } catch (error) { toast(error.message, { kind: "error" }); }
}

async function replaceCustomStyleAssets() {
  const pack = selectedStylePack();
  if (!pack?.editable) return;
  const primary = document.querySelector("#replaceCustomStylePrimary")?.files?.[0];
  const auxiliary = [...(document.querySelector("#replaceCustomStyleAuxiliary")?.files || [])];
  if (!primary && !auxiliary.length) return toast("请选择新的主图或辅助图", { kind: "error" });
  if (auxiliary.length > 3) return toast("辅助参考图最多 3 张", { kind: "error" });
  const form = new FormData();
  if (primary) form.append("primary", primary);
  auxiliary.forEach(file => form.append("auxiliary", file));
  if (auxiliary.length) form.append("replace_auxiliary", "true");
  try {
    await api(`/api/style-packs/${encodeURIComponent(pack.id)}/custom/assets`, { method: "PUT", body: form });
    await loadArtLibraries(); render(); toast("自定义画风参考图已更新");
  } catch (error) { toast(error.message, { kind: "error" }); }
}

async function deleteCustomStyle() {
  const pack = selectedStylePack();
  if (!pack?.editable || !confirm(`删除自定义画风“${pack.display_name}”？此操作无法撤销。`)) return;
  try {
    await api(`/api/style-packs/${encodeURIComponent(pack.id)}/custom`, { method: "DELETE" });
    state.artDirection = defaultProjectState().artDirection; await loadArtLibraries(); saveState(); render(); toast("自定义画风已删除");
  } catch (error) { toast(error.message, { kind: "error" }); }
}

function storyboardView() { return `<section class="page-heading"><div><div class="heading-index">STORYBOARD / 05</div><h1>分镜板</h1><p>拖动镜头改变顺序；镜头编号保持稳定，方便连续性追踪。</p></div><button class="button button-primary" id="addShotButton">${icon("plus")}添加镜头</button></section><div class="storyboard-track">${state.shots.map((shot, index) => `<article class="shot-card" draggable="true" tabindex="0" data-shot-id="${esc(shot.id)}"><div class="shot-card-top"><span>${esc(shot.id)}</span><span>${esc(shotStatus(shot))}</span></div><div class="shot-frame">${shot.content?.lastImage ? `<img src="${esc(shot.content.lastImage)}" alt="${esc(shot.title)} 镜头画面" loading="lazy" />` : `<div class="shot-frame-empty">${icon("image")}<span>等待镜头画面</span></div>`}</div><div class="shot-card-body"><div class="shot-card-order"><span>顺序 ${String(index + 1).padStart(2, "0")}</span><div><button class="icon-button" data-move-shot="up" data-shot-id="${esc(shot.id)}" title="上移镜头" ${index === 0 ? "disabled" : ""}>${icon("chevron-up")}</button><button class="icon-button" data-move-shot="down" data-shot-id="${esc(shot.id)}" title="下移镜头" ${index === state.shots.length - 1 ? "disabled" : ""}>${icon("chevron-down")}</button></div></div><h3>${esc(shot.title)}</h3><p>${esc(shot.desc)}</p><div class="shot-spec"><span>${esc(labelFor(SHOT_TYPE_OPTIONS, shot.type))}</span><span>·</span><span>${esc(shot.content?.aspectRatio || "Auto")}</span></div><div class="shot-layout-badge">${icon("panels-top-left")}${esc(layoutSummary(shot))}</div><button class="text-button" data-load-shot="${esc(shot.id)}">载入导演台</button></div></article>`).join("")}<article class="shot-card add-card"><button id="addShotButtonCard">${icon("plus-circle")}添加下一个镜头</button></article></div>`; }

function ensureExportShotSelection() {
  if (exportSelectionProjectId === currentProjectId) return;
  exportSelectionProjectId = currentProjectId;
  selectedExportShotIds = new Set(
    state.shots.filter(shot => shot.content?.lastImage).map(shot => shot.id),
  );
}

function selectedExportShots() {
  return state.shots.filter(
    shot => shot.content?.lastImage && selectedExportShotIds.has(shot.id),
  );
}

function refreshExportSelectionUi() {
  const selected = selectedExportShots();
  const available = state.shots.filter(shot => shot.content?.lastImage);
  document.querySelectorAll(".export-shot").forEach(row => {
    const checkbox = row.querySelector("[data-export-shot-id]");
    if (!checkbox) return;
    const checked = selectedExportShotIds.has(checkbox.dataset.exportShotId);
    checkbox.checked = checked;
    row.classList.toggle("is-selected", checked);
    const status = row.querySelector(".export-shot-copy span");
    if (status && row.classList.contains("is-ready")) status.textContent = `${checkbox.dataset.exportShotId} · ${checked ? "已选择导出" : "未选择"}`;
  });
  const readiness = document.querySelector(".export-readiness");
  if (readiness) readiness.querySelector("strong").textContent = `${selected.length}/${available.length}`;
  const status = document.querySelector(".export-status");
  if (status) status.querySelector("span").textContent = selected.length ? `将按分镜顺序导出已勾选的 ${selected.length} 个镜头。` : "请至少勾选一个已有成图的镜头。";
  const button = document.querySelector("#exportButton");
  if (button) {
    button.disabled = selected.length === 0 || !remoteAvailable || currentProjectId.startsWith("local-") || exportInFlight;
    const label = button.querySelector("[data-export-button-label]");
    if (label) label.textContent = `导出 ${selected.length} 个镜头`;
  }
}

function exportView() {
  ensureExportShotSelection();
  const formats = [
    { value: "png_bundle", icon: "files", label: "分镜 PNG", meta: "ZIP / 每格一张" },
    { value: "vertical_comic", icon: "panels-top-left", label: "竖版长图", meta: "PNG / 连续阅读" },
    { value: "pdf", icon: "file-text", label: "PDF", meta: "每格一页" },
    { value: "video", icon: "clapperboard", label: "推漫视频", meta: "MP4 / 无音轨" },
  ];
  const available = state.shots.filter(shot => shot.content?.lastImage);
  const selected = selectedExportShots();
  const backendUnavailable = !remoteAvailable || currentProjectId.startsWith("local-");
  const blocked = selected.length === 0 || backendUnavailable || exportInFlight;
  const blockReason = backendUnavailable
    ? "当前项目仅在浏览器缓存中，请连接桌面后端后导出。"
    : selected.length === 0
      ? "请至少勾选一个已有成图的镜头。"
      : `将按分镜顺序导出已勾选的 ${selected.length} 个镜头。`;
  const film = state.shots.map((shot, index) => {
    const image = shot.content?.lastImage;
    const checked = image && selectedExportShotIds.has(shot.id);
    return `<article class="export-shot ${image ? "is-ready" : "is-missing"} ${checked ? "is-selected" : ""}"><span class="export-shot-index">${String(index + 1).padStart(2, "0")}</span><div class="export-shot-thumb">${image ? `<img src="${esc(image)}" alt="" loading="lazy" />` : icon("image-off")}</div><div class="export-shot-copy"><strong>${esc(shot.title || shot.id)}</strong><span>${esc(shot.id)} · ${image ? (checked ? "已选择导出" : "未选择") : "缺少成图"}</span></div><label class="export-shot-check" title="${image ? "选择该镜头" : "该镜头没有成图"}"><input type="checkbox" data-export-shot-id="${esc(shot.id)}" ${checked ? "checked" : ""} ${image ? "" : "disabled"} /><span>${image ? icon("check") : icon("alert-triangle")}</span></label></article>`;
  }).join("");
  const exportButtonContent = exportInFlight
    ? `${icon("loader-circle")}<span data-export-button-label>正在整理文件...</span>`
    : `${icon("download")}<span data-export-button-label>导出 ${selected.length} 个镜头</span>`;
  return `<section class="page-heading"><div><div class="heading-index"></div><h1>导出</h1><p>勾选本次需要交付的镜头；文字与气泡仅在此处合成。</p></div><div class="export-readiness"><strong>${selected.length}/${available.length}</strong><span>已选择 / 有成图</span></div></section><div class="export-workspace"><section class="export-film"><header><div><span>SEQUENCE</span><h2>镜头顺序</h2></div><div class="export-selection-actions"><button class="text-button" type="button" data-export-select="all">全选有成图</button><button class="text-button" type="button" data-export-select="none">清空</button></div></header><div class="export-film-list">${film || `<div class="export-empty">当前项目没有镜头</div>`}</div></section><aside class="export-controls"><div class="export-control-heading"><span>OUTPUT</span><h2>交付设置</h2></div><div class="export-format-grid" role="group" aria-label="导出格式">${formats.map(format => `<button type="button" class="export-format ${exportOptions.format === format.value ? "is-selected" : ""}" data-export-format="${format.value}">${icon(format.icon)}<span><strong>${format.label}</strong><small>${format.meta}</small></span></button>`).join("")}</div><div class="export-fields"><label class="export-toggle"><input type="checkbox" id="exportLettering" ${exportOptions.include_lettering ? "checked" : ""} /><span class="switch"></span><span><strong>合成后期文字</strong><small>使用当前气泡包，不发送给生图模型</small></span></label><div class="field ${exportOptions.format === "video" ? "is-muted" : ""}"><label>${exportOptions.format === "video" ? "视频画布（固定 1080×1920）" : "输出宽度"}</label><select id="exportWidth" ${exportOptions.format === "video" ? "disabled" : ""}><option value="720" ${exportOptions.width === 720 ? "selected" : ""}>720 px</option><option value="1080" ${exportOptions.width === 1080 ? "selected" : ""}>1080 px</option><option value="1440" ${exportOptions.width === 1440 ? "selected" : ""}>1440 px</option><option value="2160" ${exportOptions.width === 2160 ? "selected" : ""}>2160 px</option></select></div><div class="field ${exportOptions.format === "vertical_comic" ? "" : "is-muted"}"><label>格间距</label><input id="exportGap" type="number" min="0" max="160" value="${exportOptions.gap}" ${exportOptions.format === "vertical_comic" ? "" : "disabled"} /></div><div class="field ${exportOptions.format === "video" ? "" : "is-muted"}"><label>每格停留</label><div class="input-suffix"><input id="exportDuration" type="number" min="1" max="10" step="0.5" value="${exportOptions.frame_duration_seconds}" ${exportOptions.format === "video" ? "" : "disabled"} /><span>秒</span></div></div></div><div class="export-status ${blocked ? "is-blocked" : ""}">${selected.length ? icon("shield-check") : icon("alert-circle")}<span>${esc(blockReason)}</span></div><button class="button button-primary export-submit" id="exportButton" ${blocked ? "disabled" : ""}>${exportButtonContent}</button></aside></div>`;
}

function settingsView() {
  const mirrorActive = settings.generation_mode !== "api";
  const naiProfile = isNaiProject();
  const projectProfilePanel = `<section class="project-profile-setting"><div class="form-section-title"><div><h2>当前项目的提示词类型</h2><p>创建后由 Skill 按此类型编写角色、世界观与镜头字段；其他项目不受影响。</p></div><span>PROJECT CONTRACT</span></div><div class="profile-switch" role="group" aria-label="当前项目提示词类型"><button type="button" class="profile-option ${naiProfile ? "" : "active"}" data-project-prompt-profile="natural">${icon("message-square-text")}<span><strong>GPT 自然语言</strong><small>保存并发送完整的自然语言指导</small></span></button><button type="button" class="profile-option ${naiProfile ? "active" : ""}" data-project-prompt-profile="nai">${icon("tags")}<span><strong>NAI 英文标签</strong><small>生图字段保存为英文并分离正负提示词</small></span></button></div><p class="settings-note ${naiProfile ? "nai-language-notice" : ""}">${naiProfile ? "NAI 项目中，原文、项目名、镜头标题和后期对白可以使用中文；角色外观、世界观视觉字段、艺术指导和镜头提示词必须使用英文。" : "GPT 项目保留自然语言工作流，可用中文或英文写视觉指导。"}</p></section><hr class="section-rule" />`;
  let modePanel = mirrorActive
    ? `<div class="channel-fields"><div class="field-grid"><div class="field"><label>镜像站网址</label><input data-setting="mirror_url" value="${esc(settings.mirror_url || "")}" placeholder="https://example.com" /></div><div class="field"><label>聊天页面网址（可选）</label><input data-setting="mirror_chat_url" value="${esc(settings.mirror_chat_url || "")}" placeholder="留空则使用镜像站网址" /></div><div class="field"><label>生图超时（秒）</label><input data-setting="generation_timeout_seconds" type="number" min="10" max="3600" value="${esc(settings.generation_timeout_seconds)}" /></div><label class="setting-toggle"><input type="checkbox" data-setting="headless" ${settings.headless ? "checked" : ""} /><span class="switch"></span><span>后台运行浏览器</span></label></div><div class="settings-actions"><button class="button button-secondary" id="testConnectionButton">${icon("plug")}测试镜像站连接</button></div></div>`
    : `<div class="channel-fields"><div class="field-grid"><div class="field"><label>节点名称</label><input data-setting="image_api_name" value="${esc(settings.image_api_name || "")}" placeholder="例如：我的生图节点" /></div><div class="field"><label>接口协议</label><select data-setting="image_api_protocol"><option value="images" ${settings.image_api_protocol === "images" ? "selected" : ""}>Images / 仅文字</option><option value="responses" ${settings.image_api_protocol === "responses" ? "selected" : ""}>Responses / 支持参考图</option></select></div><div class="field wide"><label>API 地址</label><input data-setting="image_api_base_url" value="${esc(settings.image_api_base_url || "")}" placeholder="https://api.example.com/v1" /></div><div class="field"><label>生图模型</label><input data-setting="image_api_model" value="${esc(settings.image_api_model || "")}" placeholder="gpt-image-1" /></div><div class="field"><label>提示词格式</label><select data-setting="image_api_prompt_profile"><option value="auto" ${settings.image_api_prompt_profile === "auto" ? "selected" : ""}>自动识别</option><option value="natural" ${settings.image_api_prompt_profile === "natural" ? "selected" : ""}>GPT 自然语言</option><option value="nai" ${settings.image_api_prompt_profile === "nai" ? "selected" : ""}>NAI 标签</option></select></div><div class="field"><label>API 超时（秒）</label><input data-setting="image_api_timeout_seconds" type="number" min="10" max="3600" value="${esc(settings.image_api_timeout_seconds)}" /></div><div class="field wide api-key-field"><label>API Key <span class="key-state ${settings.has_image_api_key ? "is-ready" : ""}">${settings.has_image_api_key ? "已配置" : "未配置"}</span></label><div class="key-input-row"><input data-secret-setting="image_api_key" type="password" value="" autocomplete="new-password" placeholder="${settings.has_image_api_key ? "留空保留现有 Key，输入则替换" : "sk-..."}" /><button class="icon-button" id="toggleApiKeyButton" type="button" title="显示或隐藏 API Key">${icon("eye")}</button><button class="text-button danger-text" id="clearApiKeyButton" type="button">清除 Key</button></div></div></div><p class="settings-note">自动模式会为 NAI 使用标签式提示词，为 GPT-image 保留自然语言。Images 模式保留画风和角色的文字设定，但不上传任何参考图片；Responses 模式可发送参考图。</p><div class="settings-actions"><button class="button button-secondary" id="testImageApiButton">${icon("plug-zap")}测试 API 连接</button><span class="settings-status">${esc(settings.image_api_name || "API 节点")} · ${esc(settings.image_api_model || "未选模型")}</span></div></div>`;
  return `<section class="page-heading"><div><div class="heading-index">WORKSPACE SETTINGS / 05</div><h1>设置。</h1><p>选择生成通道，配置本机连接与保存位置。</p></div><button class="button button-primary" id="saveSettingsButton">${icon("save")}保存设置</button></section><div class="settings-layout"><section class="panel settings-panel"><div class="panel-header"><div class="panel-title">${icon("route")}生成通道</div><span class="panel-label">${mirrorActive ? "MIRROR" : "API"}</span></div><div class="settings-body"><div class="channel-switch" role="group" aria-label="选择生成通道"><button type="button" class="channel-option ${mirrorActive ? "active" : ""}" data-generation-mode="mirror">${icon("monitor-up")}<span><strong>镜像站浏览器</strong><small>复用登录会话</small></span></button><button type="button" class="channel-option ${!mirrorActive ? "active" : ""}" data-generation-mode="api">${icon("server-cog")}<span><strong>API 节点</strong><small>OpenAI 兼容接口</small></span></button></div>${modePanel}<hr class="section-rule" /><div class="form-section-title"><h2>本机文件</h2><span>LOCAL STORAGE</span></div><div class="field-grid"><div class="field wide"><label>图片保存目录</label><input data-setting="image_dir" value="${esc(settings.image_dir || "")}" placeholder="例如：D:\\AnimeDesk\\generated" /></div><div class="field wide"><label>参考图保存目录</label><input data-setting="reference_dir" value="${esc(settings.reference_dir || "")}" placeholder="例如：D:\\AnimeDesk\\references" /></div></div><p class="settings-note">保存目录使用本机绝对路径。新的生成和上传会使用当前目录。</p><div class="settings-actions"><span class="settings-status">${remoteAvailable ? "后端存储已连接" : "当前使用本地缓存"}</span></div></div></section><aside class="panel settings-help"><div class="panel-header"><div class="panel-title">${icon("shield-check")}本地安全边界</div></div><div class="settings-body"><ul><li>API Key 只保存在本机 <span class="mono">data/settings.json</span>，网页不会读回密钥正文。</li><li>留空 API Key 并保存会保留现有密钥。</li><li>登录状态只保存在浏览器配置目录。</li><li>开源前请排除 <span class="mono">.env</span>、<span class="mono">data/</span>和 <span class="mono">.browser-profile/</span>。</li></ul></div></aside></div>`;
}

function render() {
  const previousRailScroll = document.querySelector(".rail-track")?.scrollLeft || 0;
  document.body.dataset.activeView = state.activeView;
  const project = getProject(); const viewTitles = { director: "导演台", characters: "角色库", world: "世界观", style: "艺术指导", storyboard: "分镜板", export: "导出", settings: "设置" };
  document.querySelector("#breadcrumbTitle").textContent = viewTitles[state.activeView] || "导演台"; document.querySelector("#projectName").textContent = project?.name || "未命名项目"; document.querySelector("#projectIndex").textContent = `PROJECT ${String(Math.max(1, projects.findIndex(item => item.id === currentProjectId) + 1)).padStart(2, "0")}`; document.querySelector("#projectSelect").innerHTML = projects.map(item => `<option value="${esc(item.id)}" ${item.id === currentProjectId ? "selected" : ""}>${esc(item.name)}</option>`).join(""); document.querySelectorAll(".nav-item").forEach(item => item.classList.toggle("active", item.dataset.view === state.activeView));
  document.querySelector("#projectIndex").textContent = `项目 ${String(Math.max(1, projects.findIndex(item => item.id === currentProjectId) + 1)).padStart(2, "0")}`;
  document.querySelector("#overviewCharacterCount").textContent = String(state.characters.length);
  document.querySelector("#overviewShotCount").textContent = String(state.shots.length);
  document.querySelector("#overviewReferenceCount").textContent = String(allReferences.filter(item => item.owner_type !== "lettering").length);
  const content = document.querySelector("#appContent"); content.innerHTML = state.activeView === "director" ? directorView() : state.activeView === "characters" ? charactersView() : state.activeView === "world" ? worldView() : state.activeView === "style" ? styleView() : state.activeView === "storyboard" ? storyboardView() : state.activeView === "export" ? exportView() : settingsView(); document.querySelector("#connectionText").textContent = remoteAvailable ? (settings.generation_mode === "api" ? "API 待命" : "镜像站待命") : "本地缓存"; refreshIcons();
  if (state.activeView === "settings") content.querySelector(".heading-index").textContent = "WORKSPACE SETTINGS / 07";
  const nextRail = document.querySelector(".rail-track");
  if (nextRail) nextRail.scrollLeft = previousRailScroll;
}

function exportFilename(disposition, fallback) {
  const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (encoded) { try { return decodeURIComponent(encoded[1]); } catch {} }
  const plain = disposition.match(/filename="?([^";]+)"?/i);
  return plain?.[1] || fallback;
}
async function downloadProjectExport() {
  if (exportInFlight) return;
  exportInFlight = true;
  render();
  try {
    const response = await fetch(`/api/projects/${encodeURIComponent(currentProjectId)}/exports`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...exportOptions,
        shot_ids: selectedExportShots().map(shot => shot.id),
      }),
    });
    if (!response.ok) {
      const data = await readResponse(response);
      throw new Error(typeof data.detail === "string" ? data.detail : "导出失败，请检查镜头状态");
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = exportFilename(response.headers.get("Content-Disposition") || "", "FrameAnimeDesk-export");
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast("导出文件已保存");
  } catch (error) {
    toast(error.message, { kind: "error", duration: 0 });
  } finally {
    exportInFlight = false;
    render();
  }
}

function updatePath(key, value) { if (key.startsWith("world.")) state.world[key.slice(6)] = value; else if (SHOT_CONTENT_KEYS.includes(key) && key !== "shotId") { const shot = getShot(); if (shot) { shot.content[key] = value; if (key === "shotType") shot.type = value; } } else if (key !== "shotId") state[key] = value; saveState(); }
function referenceMapping(reference, index) {
  if (reference.owner_type === "character") {
    const character = state.characters.find(item => item.id === reference.owner_id);
    return `Reference Image ${index + 1} = CHARACTER ${character ? `${character.id} / ${character.name}` : reference.owner_id}; ${referenceLabel(reference.reference_type)}; ${reference.note || reference.file_name}`;
  }
  if (reference.owner_type === "world") return `Reference Image ${index + 1} = WORLD / ENVIRONMENT; ${referenceLabel(reference.reference_type)}; ${reference.note || reference.file_name}`;
  return `Reference Image ${index + 1} = SHOT COMPOSITION / POSITION; ${referenceLabel(reference.reference_type)}; ${reference.note || reference.file_name}`;
}

function aspectRatioInstruction(value) {
  return value && value !== "Auto" ? `${value} aspect ratio; compose natively for this frame without cropping` : "automatic aspect ratio based on the shot intent";
}

function resolutionInstruction(value, aspectRatio) {
  const longEdge = { "1K": 1024, "2K": 2048, "4K": 4096 }[value];
  if (!longEdge) return "automatic native output resolution supported by the image model";
  const match = /^(\d+):(\d+)$/.exec(aspectRatio || "");
  if (!match) return `${value} native output resolution; target approximately ${longEdge}px on the long edge; do not upscale or interpolate a smaller image`;
  const ratioWidth = Number(match[1]);
  const ratioHeight = Number(match[2]);
  const width = ratioWidth >= ratioHeight ? longEdge : Math.round(longEdge * ratioWidth / ratioHeight);
  const height = ratioHeight >= ratioWidth ? longEdge : Math.round(longEdge * ratioHeight / ratioWidth);
  return `${value} native output resolution; target approximately ${width}x${height}px; do not upscale or interpolate a smaller image`;
}

function dynamicExpressionInstruction(value) {
  return {
    still: "Hold one quiet, readable instant with stable silhouettes; no speed lines or motion blur.",
    action_peak: "Freeze the exact peak of the action, with a clear weight shift, readable limb direction, and visible cause-and-effect contact.",
    speed_lines: "Use controlled directional speed lines behind the moving subject while keeping faces, hands, costume, and the key prop sharp.",
    motion_blur: "Use restrained motion blur only on the moving limb, hair tips, or prop; keep identity, facial expression, and the action endpoint sharp.",
    follow_composition: "Build a directional follow composition with the subject entering available space and the background lines reinforcing the movement path.",
    impact_composition: "Use an impact composition with strong foreground scale, compressed depth, and one dominant contact or reaction point.",
  }[value] || "Hold one clear, readable comic moment.";
}

function isAgentMultiPanelPrompt(value) {
  const prompt = String(value || "").toLowerCase();
  return MULTI_PANEL_PROMPT_MARKERS.some(marker => prompt.includes(marker));
}

function composePrompt() {
  const content = currentShotContent();
  if (isAgentMultiPanelPrompt(content.prompt)) return String(content.prompt || "").trim();
  const shot = getShot();
  const characters = getSelectedCharacters();
  const refs = selectedGenerationReferences();
  const characterBlocks = characters.map((character, index) => {
    const direction = normalizeCharacterDirection(content.characterDirections?.[character.id]);
    const identity = [
      optionalText(character.role) ? `role: ${optionalText(character.role)}` : "",
      optionalText(character.faction) ? `faction: ${optionalText(character.faction)}` : "",
      optionalText(character.personality) ? `personality: ${optionalText(character.personality)}` : "",
    ].filter(Boolean).join("; ");
    const costume = [optionalText(direction.costume) || optionalText(character.costume), optionalText(character.signature) ? `signature: ${optionalText(character.signature)}` : ""].filter(Boolean).join("; ");
    return [
      `[Character ${index + 1}: ${character.id} / ${character.name}]`,
      identity ? `Identity: ${identity}` : "",
      optionalText(character.appearance) ? `Appearance lock: ${optionalText(character.appearance)}` : "",
      costume ? `Costume lock: ${costume}` : "",
      optionalText(direction.position) ? `Position and orientation: ${optionalText(direction.position)}` : "",
      optionalText(direction.action) ? `Individual action: ${optionalText(direction.action)}` : "",
      optionalText(direction.expression) ? `Expression and eye line: ${optionalText(direction.expression)}` : "",
    ].filter(Boolean).join("\n");
  }).join("\n");
  const referenceLines = refs.map(referenceMapping);
  return [
    "(masterpiece), (best quality), (high quality anime illustration), consistent character design",
    characters.length ? `[Characters in Frame] ${characters.length}; ${characters.map(character => `${character.id}=${character.name}`).join(", ")}` : "",
    characterBlocks,
    characters.length > 1 ? "[Identity Separation] Keep every listed character as a distinct person. Never merge faces, hair, costumes, body features, names, actions, or reference-image identities between characters." : "",
    optionalLine("Interaction and shared event", content.action),
    optionalLine("Overall mood", content.expression),
    optionalLine("Scene / time", content.scene),
    `[Camera] ${content.shotType}, ${content.cameraAngle}`,
    `[Dynamic Expression] ${labelFor(DYNAMIC_EXPRESSION_OPTIONS, content.dynamicExpression)}. ${dynamicExpressionInstruction(content.dynamicExpression)}`,
    `[Output Format] ${aspectRatioInstruction(content.aspectRatio)}; ${resolutionInstruction(content.resolution, content.aspectRatio)}`,
    optionalLine("Lighting", content.lighting),
    optionalLine("Style", content.style),
    optionalLine("Shot Intent", content.prompt),
    referenceLines.length ? `[Reference Image Mapping]\n${referenceLines.join("\n")}` : "",
    referenceLines.length ? "[Reference Rule] Match each reference image only to its explicitly mapped character or scene purpose. Do not transfer one character's visual traits to another character." : "",
    characters.length ? "[Continuity] same face, same hairstyle, same eye color, same body proportion, consistent character design for each character ID" : "",
    `[Negative Prompt] ${NEGATIVE_PROMPT}`,
  ].filter(Boolean).join("\n");
}

function generationRequestPayload() {
  const content = currentShotContent();
  const naiMode = isNaiProject();
  const refs = selectedGenerationReferences();
  const characters = getSelectedCharacters();
  return {
    prompt: naiMode ? String(content.naiPositivePrompt || "").trim() : composePrompt(),
    negative_prompt: naiMode ? String(content.naiNegativePrompt || "").trim() : "",
    project_id: currentProjectId,
    shot_id: getShot()?.id || "",
    reference_ids: refs.map(item => item.id),
    selected_character_ids: characters.map(item => item.id),
    aspect_ratio: content.aspectRatio,
    resolution: content.resolution,
    style_pack_override: content.stylePackOverride === "project" ? "" : content.stylePackOverride,
  };
}

function enhanceFinalRequestPreview() {
  const details = document.querySelector(".final-request-preview");
  if (!details || details.dataset.enhanced === "true") return;
  details.dataset.enhanced = "true";
  details.innerHTML = `<summary>${icon("file-search")}本次最终请求</summary><div class="final-request-toolbar"><button class="text-button" id="refreshFinalRequestButton">${icon("refresh-cw")}按实际通道编译</button><span>${finalRequestPreview ? `${esc(finalRequestPreview.size)} · ${esc(finalRequestPreview.style_pack_id || "无项目画风")}` : "点击后显示实际发送内容"}</span></div><pre>${esc(finalRequestPreview ? `[POSITIVE PROMPT]\n${finalRequestPreview.positive_prompt}${finalRequestPreview.negative_prompt ? `\n\n[NEGATIVE PROMPT]\n${finalRequestPreview.negative_prompt}` : ""}` : "尚未编译")}</pre>`;
}

async function refreshFinalRequestPreview() {
  try {
    const response = await fetch("/api/generate/preview", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(generationRequestPayload()) });
    const data = await readResponse(response);
    if (!response.ok) throw new Error(data.detail || "最终请求编译失败");
    finalRequestPreview = data;
    render();
    document.querySelector(".final-request-preview")?.setAttribute("open", "");
  } catch (error) { toast(error.message, { kind: "error", duration: 0 }); }
}

async function generate(requestedShotId = "") {
  if (requestedShotId && requestedShotId !== state.shotId) {
    state.shotId = requestedShotId;
    render();
  }
  const projectId = currentProjectId;
  const shot = getShot();
  if (!shot) return;
  const shotId = shot.id;
  const requestKey = `${projectId}:${shotId}`;
  if (activeGenerations.has(requestKey)) return;
  const content = shot.content;
  const refs = selectedGenerationReferences();
  const characters = getSelectedCharacters();
  const naiMode = isNaiProject();
  const prompt = naiMode ? String(content.naiPositivePrompt || "").trim() : composePrompt();
  const negativePrompt = naiMode ? String(content.naiNegativePrompt || "").trim() : "";
  if (naiMode && !prompt) return toast("NAI 项目需要先填写英文正面提示词", { kind: "error", duration: 0 });
  if (naiMode && !negativePrompt) return toast("NAI 项目需要先填写英文负面提示词", { kind: "error", duration: 0 });
  if (naiMode && (containsCjk(prompt) || containsCjk(negativePrompt))) return toast("NAI 正负提示词中仍有中文，已阻止请求以避免浪费额度", { kind: "error", duration: 0 });
  const stylePackOverride = content.stylePackOverride === "project" ? "" : content.stylePackOverride;
  const styleReferenceCount = packReferenceCount(effectiveShotStylePack(content));
  const capabilityError = generationCapabilityError(naiMode ? 0 : refs.length + styleReferenceCount);
  if (capabilityError) return toast(capabilityError, { kind: "error", duration: 0 });
  const requestId = ++generationSequence;
  activeGenerations.set(requestKey, requestId);
  clearGenerationNotice(shotId);
  shot.status = "生成中";
  saveState();
  render();
  document.querySelector("#connectionText").textContent = "正在生成";
  try {
    const response = await fetch("/api/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(generationRequestPayload()) });
    const data = await readResponse(response);
    if (!response.ok) throw new Error(data.detail || "生图代理返回错误");
    if (activeGenerations.get(requestKey) !== requestId) return;
    content.lastImage = data.url;
    content.generationHistory.unshift({ id: `${Date.now()}`, requestId, shotId, url: data.url, createdAt: new Date().toISOString(), prompt: content.prompt, generationMode: data.generation_mode, generationChannel: data.generation_channel, generationModel: data.generation_model, aspectRatio: content.aspectRatio, resolution: content.resolution, characterIds: characters.map(item => item.id), referenceIds: refs.map(item => item.id), stylePackId: data.style_pack_id || "" });
    content.generationHistory = content.generationHistory.slice(0, 30);
    shot.status = "待确认";
    if (data.generation_mode === "mirror") await loadConversationBinding();
    saveState();
    render();
    clearGenerationNotice(shotId);
    if (data.generation_warning) toast(`结果核验提示：${data.generation_warning}`, { actionLabel: "重试", action: () => generate(shotId), duration: 0, key: `generation-${shotId}` });
    else toast(data.reference_warning || `镜头已通过 ${data.generation_channel || (data.generation_mode === "api" ? "API" : "镜像站")} 生成${data.generation_model ? ` · ${data.generation_model}` : ""}`);
  } catch (error) {
    if (activeGenerations.get(requestKey) !== requestId) return;
    shot.status = content.lastImage ? "待确认" : "需重试";
    saveState();
    generationError(error.message, shotId);
    document.querySelector("#connectionText").textContent = "生成错误";
  } finally {
    if (activeGenerations.get(requestKey) === requestId) activeGenerations.delete(requestKey);
    if (currentProjectId === projectId) render();
  }
}

async function generateFromUi() {
  try {
    await generate();
  } catch (error) {
    const shotId = getShot()?.id || "current";
    generationError(error?.message || String(error), shotId);
    const connection = document.querySelector("#connectionText");
    if (connection) connection.textContent = "生成错误";
  }
}

let loginInFlight = false;
async function openLogin() { if (loginInFlight) return; loginInFlight = true; try { const data = await api("/api/session/login", { method: "POST" }); toast(`浏览器已打开，请完成登录（${data.url}）`); document.querySelector("#connectionText").textContent = "等待登录"; await refreshSessionStatus(); } catch (error) { toast(error.message); } finally { loginInFlight = false; } }
async function bindCurrentConversation() { try { conversationBinding = await api(`/api/projects/${encodeURIComponent(currentProjectId)}/conversation/bind-current`, { method: "POST" }); render(); toast("当前镜像站对话已绑定到项目"); } catch (error) { toast(error.message, { kind: "error" }); } }
async function startNewProjectConversation() { try { conversationBinding = await api(`/api/projects/${encodeURIComponent(currentProjectId)}/conversation/new`, { method: "POST" }); render(); toast("新聊天已打开；首次生成后会自动完成绑定"); } catch (error) { toast(error.message, { kind: "error" }); } }
async function openProjectConversation() { try { conversationBinding = await api(`/api/projects/${encodeURIComponent(currentProjectId)}/conversation/open`, { method: "POST" }); toast("已打开当前项目对应的镜像站对话"); } catch (error) { toast(error.message, { kind: "error" }); } }
async function unbindProjectConversation() { if (!confirm("解除当前项目与镜像站对话的绑定？已有聊天不会被删除。")) return; try { conversationBinding = await api(`/api/projects/${encodeURIComponent(currentProjectId)}/conversation`, { method: "DELETE" }); render(); toast("已解除对话绑定"); } catch (error) { toast(error.message, { kind: "error" }); } }
function showCharacterForm(characterId = "", scrollToForm = false) {
  const character = characterId ? state.characters.find(item => item.id === characterId) : null;
  const slot = document.querySelector("#characterFormSlot");
  if (!slot) return;
  slot.innerHTML = characterForm(character);
  refreshIcons();
  // Establish a predictable editing focus. In particular, never let the
  // appearance textarea inherit an accidental full-selection from a rerender.
  requestAnimationFrame(() => {
    const name = slot.querySelector("#newCharacterName");
    if (name) {
      name.focus();
      name.setSelectionRange(name.value.length, name.value.length);
    }
    if (scrollToForm) slot.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}
function openCharacterEditor(characterId) { const character = state.characters.find(item => item.id === characterId); if (!character) return; state.characterId = characterId; saveState(); render(); showCharacterForm(characterId, true); }
async function saveCharacter() {
  const form = document.querySelector("[data-editing-character-id]");
  const name = document.querySelector("#newCharacterName")?.value.trim();
  if (!name) return toast("请先填写角色名称");

  const editingId = form?.dataset.editingCharacterId || "";
  let character = editingId ? state.characters.find(item => item.id === editingId) : null;
  if (editingId && !character) return toast("角色不存在，请刷新页面", { kind: "error" });

  const roleInput = document.querySelector("#newCharacterRole").value.trim();
  const costumeInput = document.querySelector("#newCharacterCostume").value.trim();
  const roleFaction = roleInput.split(/\s*[\/／]\s*/, 2);
  const unchangedRole = character && roleInput === form.dataset.originalRoleFaction;
  const unchangedCostume = character && costumeInput === form.dataset.originalCostumeSignature;
  const values = {
    name,
    role: unchangedRole ? character.role : (roleFaction[0] || ""),
    faction: unchangedRole ? character.faction : (roleFaction[1] || ""),
    personality: document.querySelector("#newCharacterPersonality").value.trim(),
    appearance: document.querySelector("#newCharacterAppearance").value.trim(),
    costume: unchangedCostume ? character.costume : costumeInput,
    signature: unchangedCostume ? character.signature : "",
  };
  const files = [...(document.querySelector("#newCharacterReferences")?.files || [])];

  if (character) {
    Object.assign(character, values);
    state.characterId = character.id;
    saveState();
    render();
    showCharacterForm(character.id);
    toast("角色设置已更新");
  } else {
    const ids = state.characters.map(item => Number(String(item.id).split("-")[1])).filter(Number.isFinite);
    const next = Math.max(0, ...ids) + 1;
    character = { id: `CHR-${String(next).padStart(3, "0")}`, ...values };
    state.characters.push(character);
    state.characterId = character.id;
    currentShotContent().selectedCharacters.push(character.id);
    saveState();
    render();
    toast("角色 DNA 已保存并加入当前镜头");
  }
  if (files.length) await uploadFiles(files, "character", character.id, "character_design", editingId ? "编辑角色时上传的参考图" : "创建时上传的角色参考图");
}
function addShot() { const ids = state.shots.map(item => Number(String(item.id).split("-")[1])).filter(Number.isFinite); const next = Math.max(0, ...ids) + 1; const id = `SHOT-${String(next).padStart(3, "0")}`; const type = "Wide Shot"; state.shots.push({ id, type, title: "新镜头", desc: "待补充镜头意图与动作。", status: "待制作", content: blankShotContent({ id, type }) }); saveState(); render(); toast("已添加镜头，内容待填写"); }
function moveShot(shotId, direction) { const from = state.shots.findIndex(item => item.id === shotId); const to = from + direction; if (from < 0 || to < 0 || to >= state.shots.length) return; [state.shots[from], state.shots[to]] = [state.shots[to], state.shots[from]]; saveState(); render(); }
function toggleShotCharacter(characterId, enabled) {
  const content = currentShotContent();
  const selected = new Set(content.selectedCharacters || []);
  if (enabled) selected.add(characterId); else selected.delete(characterId);
  content.selectedCharacters = [...selected];
  if (!enabled && content.characterDirections) delete content.characterDirections[characterId];
  saveState();
  render();
}

async function uploadFiles(files, ownerType, ownerId, referenceType, note, formButton = null) { if (!remoteAvailable || currentProjectId.startsWith("local-")) return toast("后端存储未连接，当前只能使用本地项目缓存；请先启动服务"); if (!files.length) return toast("请先选择图片"); if (formButton) formButton.disabled = true; try { for (const file of files) { const form = new FormData(); form.append("file", file); form.append("owner_type", ownerType); form.append("owner_id", ownerId); form.append("reference_type", referenceType); form.append("note", note || ""); await api(`/api/projects/${encodeURIComponent(currentProjectId)}/references`, { method: "POST", body: form }); } await loadReferences(); await refreshCurrentProjectRevision(); render(); toast(`已上传 ${files.length} 张参考图`); } catch (error) { toast(error.message); } finally { if (formButton) formButton.disabled = false; } }
async function uploadReferenceFromForm(button) { const form = document.querySelector(`#${CSS.escape(button.dataset.uploadReference)}`); const files = [...(form?.querySelector("input[type=file]")?.files || [])]; const referenceType = form?.querySelector("select")?.value || "other"; const note = form?.querySelector("input:not([type=file])")?.value || ""; await uploadFiles(files, button.dataset.ownerType, button.dataset.ownerId, referenceType, note, button); }
async function updateReference(referenceId, values, rerender = false) { try { const updated = await api(`/api/references/${encodeURIComponent(referenceId)}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(values) }); allReferences = allReferences.map(item => item.id === referenceId ? updated : item); await refreshCurrentProjectRevision(); if (rerender) render(); } catch (error) { toast(error.message); } }
async function moveReference(referenceId, direction) { const current = allReferences.find(item => item.id === referenceId); if (!current) return; const siblings = referencesFor(current.owner_type, current.owner_id); const from = siblings.findIndex(item => item.id === referenceId); const to = from + direction; if (from < 0 || to < 0 || to >= siblings.length) return; [siblings[from], siblings[to]] = [siblings[to], siblings[from]]; for (let index = 0; index < siblings.length; index += 1) await updateReference(siblings[index].id, { sort_order: index }); await loadReferences(); render(); }
async function replaceReference(referenceId, file) { if (!file) return; const form = new FormData(); form.append("file", file); try { await api(`/api/references/${encodeURIComponent(referenceId)}/replace`, { method: "POST", body: form }); await loadReferences(); await refreshCurrentProjectRevision(); render(); toast("参考图已替换"); } catch (error) { toast(error.message); } }
async function deleteReference(referenceId) { if (!confirm("删除这张参考图？")) return; try { await api(`/api/references/${encodeURIComponent(referenceId)}`, { method: "DELETE" }); allReferences = allReferences.filter(item => item.id !== referenceId); await refreshCurrentProjectRevision(); render(); toast("参考图已删除"); } catch (error) { toast(error.message); } }

async function createProject() {
  const name = window.prompt("新项目名称", "未命名动画项目");
  if (!name?.trim()) return;
  const profileInput = window.prompt("请输入项目提示词路线：GPT 或 NAI\n\nGPT：自然语言生图模型\nNAI：英文标签式二次元模型", state.promptProfile === "nai" ? "NAI" : "GPT");
  if (profileInput === null) return;
  const normalizedProfile = profileInput.trim().toLowerCase();
  if (!["gpt", "natural", "nai"].includes(normalizedProfile)) return toast("请输入 GPT 或 NAI", { kind: "error" });
  const seed = defaultProjectState();
  seed.promptProfile = normalizedProfile === "nai" ? "nai" : "natural";
  seed.world = Object.fromEntries(Object.keys(seed.world).map(key => [key, ""]));
  seed.characters = [];
  seed.shots = [{ id: "SHOT-001", type: "Medium Shot", title: "新镜头", desc: "", status: "待制作", content: blankShotContent({ id: "SHOT-001", type: "Medium Shot" }) }];
  seed.shotId = "SHOT-001";
  try {
    const created = remoteAvailable
      ? await api("/api/projects", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: name.trim(), description: "个人动画制作项目", state: seed }) })
      : { id: `local-${Date.now()}`, name: name.trim(), description: "本地缓存项目", revision: 1, state: seed };
    await saveProjectRemote();
    projects.push(created);
    currentProjectId = created.id;
    state = normalizeState(created.state);
    allReferences = [];
    conversationBinding = { status: "unbound", project_id: created.id, url: "", title: "" };
    saveLocal();
    syncProjectUrl();
    render();
    toast(`已创建 ${seed.promptProfile === "nai" ? "NAI" : "GPT"} 项目：${created.name}`);
  } catch (error) { toast(error.message); }
}
async function switchProject(projectId) { if (!projectId || projectId === currentProjectId) return; const saved = await saveProjectRemote(); if (!saved) { render(); return; } currentProjectId = projectId; const cached = projects.find(item => item.id === projectId); try { if (remoteAvailable && !projectId.startsWith("local-")) { const detail = await api(`/api/projects/${encodeURIComponent(projectId)}`); state = normalizeState(detail.state); projects = projects.map(item => item.id === projectId ? detail : item); } else state = normalizeState(cached?.state || {}); await loadReferences(); await loadConversationBinding(); saveLocal(); syncProjectUrl(); render(); toast(`已切换到项目：${cached?.name || "未命名项目"}`); } catch (error) { toast(error.message); } }
async function renameProject() { const project = getProject(); const name = window.prompt("重命名当前项目", project?.name || ""); if (!name?.trim() || !project) return; try { const updated = remoteAvailable && !project.id.startsWith("local-") ? await api(`/api/projects/${encodeURIComponent(project.id)}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: name.trim() }) }) : { ...project, name: name.trim() }; projects = projects.map(item => item.id === project.id ? { ...item, ...updated } : item); saveLocal(); render(); toast("项目名称已更新"); } catch (error) { toast(error.message); } }
async function deleteCurrentProject() { if (projects.length <= 1) return toast("至少保留一个项目"); const project = getProject(); if (!project || !confirm(`删除项目“${project.name}”及其参考图？`)) return; try { if (remoteAvailable && !project.id.startsWith("local-")) await api(`/api/projects/${encodeURIComponent(project.id)}`, { method: "DELETE" }); projects = projects.filter(item => item.id !== project.id); currentProjectId = projects[0].id; state = normalizeState(projects[0].state || {}); await loadReferences(); await loadConversationBinding(); saveLocal(); render(); toast("项目已删除"); } catch (error) { toast(error.message); } }
function collectSettingsPatch() {
  const values = { generation_mode: settings.generation_mode };
  document.querySelectorAll("[data-setting]").forEach(element => { values[element.dataset.setting] = element.type === "checkbox" ? element.checked : element.value; });
  document.querySelectorAll("[data-secret-setting]").forEach(element => { if (element.value.trim()) values[element.dataset.secretSetting] = element.value.trim(); });
  for (const key of ["generation_timeout_seconds", "image_api_timeout_seconds"]) if (key in values) values[key] = Number(values[key]);
  return values;
}
async function persistSettings(extra = {}, rerender = true) { settings = await api("/api/settings", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...collectSettingsPatch(), ...extra }) }); if (rerender) render(); return settings; }
async function saveSettings() { try { await persistSettings(); toast("设置已保存"); } catch (error) { toast(error.message, { kind: "error" }); } }
async function switchGenerationMode(mode) { if (mode === settings.generation_mode) return; try { await persistSettings({ generation_mode: mode }); toast(mode === "api" ? "已切换到 API 节点" : "已切换到镜像站模式"); } catch (error) { toast(error.message, { kind: "error" }); } }
function switchProjectPromptProfile(profile) {
  if (!["natural", "nai"].includes(profile) || profile === state.promptProfile) return;
  toast("项目提示词路线在创建后已锁定。请新建项目并选择另一条路线。", { kind: "error", duration: 0 });
}
async function clearApiKey() { if (!confirm("清除当前 API Key？")) return; try { await persistSettings({ clear_image_api_key: true }); toast("API Key 已清除"); } catch (error) { toast(error.message, { kind: "error" }); } }
async function testConnection() { const button = document.querySelector("#testConnectionButton"); if (button) button.disabled = true; try { const data = await api("/api/settings/test-connection", { method: "POST" }); toast(`${data.message}：${data.url}`); } catch (error) { toast(error.message); } finally { if (button) button.disabled = false; } }
async function testImageApi() { const button = document.querySelector("#testImageApiButton"); if (button) button.disabled = true; try { await persistSettings({}, false); const data = await api("/api/settings/test-image-api", { method: "POST" }); settings = await api("/api/settings"); render(); toast(data.message); } catch (error) { toast(error.message, { kind: "error" }); if (button) button.disabled = false; } }
function sessionStatusLabel() { if (!sessionStatus.started) return "浏览器会话尚未启动"; if (!sessionStatus.page_open) return "浏览器已启动，尚无页面"; return `浏览器页面：${sessionStatus.page_url || "已打开"}`; }
async function refreshSessionStatus() { try { sessionStatus = await api("/api/session/status"); const node = document.querySelector("#sessionStatusText"); if (node) node.textContent = sessionStatusLabel(); } catch (error) { toast(error.message); } }
async function validateDirectories() { const node = document.querySelector("#directoryStatusText"); try { const result = await api("/api/settings/validate-directories", { method: "POST" }); if (node) node.textContent = result.valid ? "图片和参考图目录可写" : "目录不可用，请检查路径"; toast(result.valid ? "目录验证通过" : "目录验证失败"); } catch (error) { if (node) node.textContent = "目录验证失败"; toast(error.message); } }
function projectProfilePanelMarkup() {
  const naiProfile = isNaiProject();
  return `<section class="project-profile-setting"><div class="form-section-title"><div><h2>当前项目提示词路线</h2><p>这是已锁定的项目契约，Skill 会在创建、续接和修订时始终继承它。</p></div><span>LOCKED CONTRACT</span></div><div class="profile-switch" role="group" aria-label="当前项目提示词路线"><button type="button" class="profile-option ${naiProfile ? "" : "active"}" data-project-prompt-profile="natural" ${naiProfile ? "" : "disabled"}>${icon("message-square-text")}<span><strong>GPT 自然语言</strong><small>完整指令式描述</small></span></button><button type="button" class="profile-option ${naiProfile ? "active" : ""}" data-project-prompt-profile="nai" ${naiProfile ? "disabled" : ""}>${icon("tags")}<span><strong>NAI 英文标签</strong><small>英文正面与负面提示词</small></span></button></div><p class="settings-note ${naiProfile ? "nai-language-notice" : ""}">${naiProfile ? "原文、标题和后期对白可以使用中文；所有会进入生图上下文的字段必须使用英文。" : "角色、世界观、艺术指导和镜头可使用中文或英文自然语言。"}</p></section><hr class="section-rule" />`;
}
function enhanceSettingsView() {
  if (state.activeView !== "settings") return;
  const body = document.querySelector(".settings-panel .settings-body");
  if (body && !body.querySelector(".project-profile-setting")) {
    body.insertAdjacentHTML("afterbegin", projectProfilePanelMarkup());
  }
  const actions = document.querySelector(".settings-actions");
  if (!actions || document.querySelector("#validateDirectoriesButton")) { refreshIcons(); return; }
  const validate = document.createElement("button");
  validate.id = "validateDirectoriesButton";
  validate.className = "button button-secondary";
  validate.innerHTML = `${icon("folder-check")}验证目录`;
  actions.insertBefore(validate, actions.querySelector(".settings-status"));
  const refresh = document.createElement("button");
  refresh.id = "refreshSessionButton";
  refresh.className = "button button-secondary";
  refresh.innerHTML = `${icon("refresh-cw")}刷新会话`;
  actions.insertBefore(refresh, actions.querySelector(".settings-status"));
  const session = document.createElement("span");
  session.id = "sessionStatusText";
  session.className = "settings-status";
  session.textContent = sessionStatusLabel();
  actions.appendChild(session);
  const directory = document.createElement("span");
  directory.id = "directoryStatusText";
  directory.className = "settings-status";
  directory.textContent = "目录尚未验证";
  actions.appendChild(directory);
  refreshIcons();
}

function enhanceNaiLanguageNotice() {
  if (!isNaiProject() || !["characters", "world", "style"].includes(state.activeView)) return;
  const content = document.querySelector("#appContent");
  const heading = content?.querySelector(".page-heading");
  if (!heading || content.querySelector(".nai-page-language-notice")) return;
  const copy = state.activeView === "characters"
    ? "角色名称可用中文；身份、性格、外貌、服装与标志元素请用英文编写，它们会进入 NAI 生图上下文。"
    : state.activeView === "world"
      ? "世界观页的字段都可能进入 NAI 生图上下文，请使用简洁英文。原文与后期对白仍可使用中文。"
      : "画风分析、正面画风提示词和排除提示词请使用英文。NAI 纯文本请求不会上传画风参考图。";
  heading.insertAdjacentHTML("afterend", `<div class="nai-page-language-notice">${icon("languages")}<span><strong>NAI 项目·英文生图字段</strong><small>${copy}</small></span></div>`);
  refreshIcons();
}

function currentLetteringBlock() { return getShot()?.postText?.[letteringEditorIndex] || null; }
function enhanceLetteringControls() {
  const dropzone = document.querySelector("#letteringBubbleDropzone");
  if (!dropzone) return;
  const title = dropzone.querySelector("strong");
  if (title) title.textContent = "拖入图片";
  const subtitle = dropzone.querySelector("small");
  if (subtitle) subtitle.textContent = "PNG 或 WebP，也可点击选择";
  if (!document.querySelector("#addLetteringTextButton")) {
    dropzone.insertAdjacentHTML("afterend", `<button type="button" class="proof-text-dropzone" id="addLetteringTextButton" draggable="true">${icon("type")}<span><strong>拖入文本框</strong><small>点击添加，或拖到画面指定位置</small></span></button>`);
    refreshIcons();
  }
  const block = currentLetteringBlock();
  const assetSelect = document.querySelector("#letteringAssetSelect");
  if (assetSelect) {
    const field = assetSelect.closest(".proof-field");
    if (field) field.hidden = block?.elementType === "text";
  }
}
function ensureCustomLetteringLayout() {
  const block = currentLetteringBlock();
  if (!block) return null;
  block.layout = letteringLayoutFor(block, letteringEditorIndex);
  return block.layout;
}
function syncLetteringProof() {
  const block = currentLetteringBlock();
  const bubbles = document.querySelectorAll(".proof-bubble[data-lettering-index]");
  const selectedBubble = document.querySelector("#letteringProofBubble");
  if (!block || !selectedBubble) return;
  const layout = letteringLayoutFor(block, letteringEditorIndex);
  bubbles.forEach(node => {
    const index = Number(node.dataset.letteringIndex);
    const item = getShot()?.postText?.[index];
    if (!item) return;
    const itemLayout = letteringLayoutFor(item, index);
    node.style.left = `${itemLayout.x * 100}%`;
    node.style.top = `${itemLayout.y * 100}%`;
    node.style.width = `${itemLayout.width * 100}%`;
    node.style.setProperty("--lettering-font-scale", itemLayout.fontScale);
    node.style.setProperty("--lettering-rotation", `${itemLayout.rotation}deg`);
    node.classList.toggle("is-hidden", Boolean(item.hidden));
    node.classList.toggle("is-active", index === letteringEditorIndex);
    const image = node.querySelector("img");
    if (image) image.style.transform = `scaleX(${itemLayout.flip ? -1 : 1})`;
    const text = node.querySelector("span");
    if (text) text.textContent = item.text || "文字";
  });
  const values = { letteringX: layout.x, letteringY: layout.y, letteringWidth: layout.width, letteringFontSize: layout.fontScale, letteringRotation: layout.rotation };
  Object.entries(values).forEach(([name, value]) => {
    const input = document.querySelector(`#${name}Range`);
    const output = document.querySelector(`#${name}Output`);
    if (input) input.value = String(Math.round(value * 100));
    if (output) output.textContent = name === "letteringRotation" ? `${Math.round(value)}°` : `${Math.round(value * 100)}%`;
  });
  const xRange = document.querySelector("#letteringXRange");
  if (xRange) xRange.max = String(Math.round((1 - layout.width) * 100));
}
function beginLetteringPointerEdit(event, resize, targetBubble = null) {
  const frame = document.querySelector("#letteringProofFrame");
  const bubble = targetBubble || document.querySelector("#letteringProofBubble");
  const block = currentLetteringBlock();
  if (!frame || !bubble || !block || block.hidden) return;
  event.preventDefault();
  const origin = { ...ensureCustomLetteringLayout() };
  const startX = event.clientX;
  const startY = event.clientY;
  const frameRect = frame.getBoundingClientRect();
  const move = pointerEvent => {
    if (resize) {
      const width = clamp(origin.width + (pointerEvent.clientX - startX) / frameRect.width, 0.14, 0.48);
      block.layout = normalizeLetteringLayout({ ...origin, width, x: clamp(origin.x, 0, 1 - width) });
    } else {
      block.layout = normalizeLetteringLayout({
        ...origin,
        x: clamp(origin.x + (pointerEvent.clientX - startX) / frameRect.width, 0, 1 - origin.width),
        y: clamp(origin.y + (pointerEvent.clientY - startY) / frameRect.height, 0, 0.92),
      });
    }
    syncLetteringProof();
  };
  const finish = () => {
    window.removeEventListener("pointermove", move);
    window.removeEventListener("pointerup", finish);
    saveState();
  };
  window.addEventListener("pointermove", move);
  window.addEventListener("pointerup", finish, { once: true });
}

function addLetteringElement(assetId, point = null, referenceId = "") {
  const shot = getShot();
  const pack = selectedBubblePack();
  const reference = referenceId ? letteringReferences().find(item => item.id === referenceId) : null;
  const asset = reference
    ? { id: reference.id, semantic_type: "dialogue" }
    : pack?.assets?.find(item => item.id === assetId);
  if (!shot || !asset) return;
  const block = {
    elementType: "image",
    kind: asset.semantic_type === "sfx" ? "sfx" : "dialogue",
    text: asset.semantic_type === "sfx" ? "拟声词" : "输入文字",
    position: "top-right",
    style: "speech",
    bubbleSemantic: asset.semantic_type || "dialogue",
    bubbleAssetId: reference ? "" : asset.id,
    bubbleReferenceId: reference?.id || "",
    layout: normalizeLetteringLayout({ x: point?.x ?? 0.58, y: point?.y ?? 0.08, width: 0.28, rotation: 0 }),
  };
  shot.postText = [...(shot.postText || []), block];
  letteringEditorIndex = shot.postText.length - 1;
  saveState();
  render();
}

function addLetteringTextElement(point = null) {
  const shot = getShot();
  if (!shot) return;
  const block = {
    elementType: "text",
    kind: "narration",
    text: "输入文字",
    position: "top-left",
    style: "text",
    bubbleSemantic: "narration",
    bubbleAssetId: "",
    bubbleReferenceId: "",
    layout: normalizeLetteringLayout({ x: point?.x ?? 0.12, y: point?.y ?? 0.12, width: 0.32, rotation: 0 }),
  };
  shot.postText = [...(shot.postText || []), block];
  letteringEditorIndex = shot.postText.length - 1;
  saveState();
  render();
}

async function uploadLetteringBubble(file, point = null) {
  if (!file) return;
  if (!remoteAvailable || currentProjectId.startsWith("local-")) return toast("后端存储未连接，无法保存自定义气泡", { kind: "error" });
  const allowed = ["image/png", "image/webp"];
  if (!allowed.includes(file.type)) return toast("自定义气泡仅支持 PNG 或 WebP", { kind: "error" });
  const form = new FormData();
  form.append("file", file);
  form.append("owner_type", "lettering");
  form.append("owner_id", "bubble-library");
  form.append("reference_type", "other");
  form.append("note", "自定义透明气泡");
  form.append("enabled", "false");
  try {
    const reference = await api(`/api/projects/${encodeURIComponent(currentProjectId)}/references`, { method: "POST", body: form });
    allReferences = [...allReferences.filter(item => item.id !== reference.id), reference];
    await refreshCurrentProjectRevision();
    addLetteringElement("", point, reference.id);
    toast(`已添加气泡素材：${reference.file_name}`);
  } catch (error) {
    toast(error.message, { kind: "error" });
  }
}

document.addEventListener("click", event => {
  if (event.target.closest("#refreshFinalRequestButton")) return refreshFinalRequestPreview();
  const nav = event.target.closest(".nav-item[data-view]"); if (nav) { state.activeView = nav.dataset.view; saveState(); render(); return; }
  const jump = event.target.closest("[data-view-jump]"); if (jump) { const managed = jump.closest("[data-manage-character]"); if (managed) state.characterId = managed.dataset.manageCharacter; state.activeView = jump.dataset.viewJump; saveState(); render(); return; }
  const styleChoice = event.target.closest("[data-select-style]"); if (styleChoice) return applyStylePack(styleChoice.dataset.selectStyle);
  if (event.target.closest("#openCustomStyleButton")) { customStyleFormOpen = true; render(); return; }
  if (event.target.closest("#closeCustomStyleButton")) { customStyleFormOpen = false; render(); return; }
  if (event.target.closest("#createCustomStyleButton")) return createCustomStyle();
  if (event.target.closest("#resetStylePresetButton")) return applyStylePack(state.artDirection.stylePackId);
  if (event.target.closest("#saveCustomStyleButton")) return saveCustomStyle();
  if (event.target.closest("#replaceCustomStyleAssetsButton")) return replaceCustomStyleAssets();
  if (event.target.closest("#deleteCustomStyleButton")) return deleteCustomStyle();
  if (event.target.closest("#addPostTextButton")) { const shot = getShot(); if (shot) { shot.postText = [...(shot.postText || []), { kind: "dialogue", text: "", position: "top-right", style: "speech", bubbleSemantic: "dialogue", bubbleAssetId: "" }]; saveState(); render(); } return; }
  if (event.target.closest("#addLetteringTextButton")) { addLetteringTextElement(); return; }
  const editLettering = event.target.closest("[data-edit-lettering]"); if (editLettering) { if (!getShot()?.content?.lastImage) return toast("请先生成镜头画面，再进行可视化排字"); letteringEditorIndex = Number(editLettering.dataset.editLettering); render(); return; }
  if (event.target.closest("#closeLetteringEditorButton") || event.target.closest("#closeLetteringEditorDoneButton")) { letteringEditorIndex = -1; render(); return; }
  if (event.target === document.querySelector(".lettering-proof-overlay")) { letteringEditorIndex = -1; render(); return; }
  const letteringPreset = event.target.closest("[data-lettering-preset]"); if (letteringPreset) { const block = currentLetteringBlock(); if (block) { block.position = letteringPreset.dataset.letteringPreset; block.layout = null; saveState(); render(); } return; }
  if (event.target.closest("#resetLetteringLayoutButton")) { const block = currentLetteringBlock(); if (block) { block.layout = null; block.hidden = false; saveState(); render(); } return; }
  if (event.target.closest("#deleteLetteringElementButton")) { const shot = getShot(); if (shot?.postText?.length) { shot.postText.splice(letteringEditorIndex, 1); letteringEditorIndex = Math.min(letteringEditorIndex, shot.postText.length - 1); saveState(); render(); } return; }
  const deletePostText = event.target.closest("[data-delete-post-text]"); if (deletePostText) { const shot = getShot(); if (shot) { shot.postText.splice(Number(deletePostText.dataset.deletePostText), 1); saveState(); render(); } return; }
  const generationMode = event.target.closest("[data-generation-mode]"); if (generationMode) return switchGenerationMode(generationMode.dataset.generationMode);
  const projectPromptProfile = event.target.closest("[data-project-prompt-profile]"); if (projectPromptProfile) return switchProjectPromptProfile(projectPromptProfile.dataset.projectPromptProfile);
  const exportSelection = event.target.closest("[data-export-select]"); if (exportSelection) { selectedExportShotIds = exportSelection.dataset.exportSelect === "all" ? new Set(state.shots.filter(shot => shot.content?.lastImage).map(shot => shot.id)) : new Set(); render(); return; }
  const exportFormat = event.target.closest("[data-export-format]"); if (exportFormat) { exportOptions.format = exportFormat.dataset.exportFormat; if (exportOptions.format === "video") exportOptions.width = 1080; render(); return; }
  if (event.target.closest("#exportButton")) return downloadProjectExport();
  if (event.target.closest("#toggleApiKeyButton")) { const input = document.querySelector('[data-secret-setting="image_api_key"]'); const button = event.target.closest("#toggleApiKeyButton"); if (input) { input.type = input.type === "password" ? "text" : "password"; button.innerHTML = input.type === "password" ? icon("eye") : icon("eye-off"); refreshIcons(); } return; }
  if (event.target.closest("#clearApiKeyButton")) return clearApiKey();
  if (event.target.closest("#testImageApiButton")) return testImageApi();
  if (event.target.closest("#confirmShotButton")) { const shot = getShot(); if (shot?.content?.lastImage) { shot.status = "已确认"; saveState(); render(); toast(`${shot.id} 已确认为最终画面`); } return; }
  if (event.target.closest("#bindCurrentConversationButton")) return bindCurrentConversation();
  if (event.target.closest("#newProjectConversationButton")) return startNewProjectConversation();
  if (event.target.closest("#openProjectConversationButton")) return openProjectConversation();
  if (event.target.closest("#unbindProjectConversationButton")) return unbindProjectConversation();
  if (event.target.closest("#loginButton")) return openLogin(); if (event.target.closest("#generateButton") || event.target.closest("#generateButtonBottom")) return generateFromUi(); if (event.target.closest("#newCharacterButton")) return showCharacterForm("", true); if (event.target.closest("#cancelCharacterButton") || event.target.closest("#closeCharacterEditorButton")) { document.querySelector("#characterFormSlot").innerHTML = ""; return; } if (event.target.closest("#saveCharacterButton")) return saveCharacter(); if (event.target.closest("#addShotButton") || event.target.closest("#addShotButtonCard") || event.target.closest("#addShotFromRail")) return addShot(); if (event.target.closest("#saveWorldButton")) { saveState(); toast("World Bible 已保存"); return; } if (event.target.closest("#saveSettingsButton")) return saveSettings(); if (event.target.closest("#testConnectionButton")) return testConnection(); if (event.target.closest("#newProjectButton")) return createProject(); if (event.target.closest("#renameProjectButton")) return renameProject(); if (event.target.closest("#deleteProjectButton")) return deleteCurrentProject();
  const uploadButton = event.target.closest("[data-upload-reference]"); if (uploadButton) return uploadReferenceFromForm(uploadButton); const moveRef = event.target.closest("[data-ref-move]"); if (moveRef) return moveReference(moveRef.dataset.refId, moveRef.dataset.refMove === "up" ? -1 : 1); const primaryRef = event.target.closest("[data-ref-primary]"); if (primaryRef) return updateReference(primaryRef.dataset.refPrimary, { is_primary: true }, true); const deleteRef = event.target.closest("[data-delete-ref]"); if (deleteRef) return deleteReference(deleteRef.dataset.deleteRef); const loadShot = event.target.closest("[data-load-shot]"); if (loadShot) { state.shotId = loadShot.dataset.loadShot; state.activeView = "director"; saveState(); render(); toast(`${state.shotId} 已载入导演台`); return; } const shotSelect = event.target.closest("[data-shot-id]"); if (shotSelect && !event.target.closest("[data-move-shot]")) { state.shotId = shotSelect.dataset.shotId; saveState(); render(); toast(`${state.shotId} 已载入导演台`); return; } const useCharacter = event.target.closest("[data-use-character]"); if (useCharacter) { const id = useCharacter.dataset.useCharacter; const isSelected = selectedCharacterIds().includes(id); if (!isSelected && selectedCharacterIds().length >= 6) return toast("单个镜头最多锁定 6 个角色"); toggleShotCharacter(id, !isSelected); state.characterId = id; state.activeView = "director"; saveState(); render(); toast(isSelected ? "角色已移出当前镜头" : "角色已加入当前镜头"); return; } const manageCharacter = event.target.closest("[data-manage-character]"); if (manageCharacter) { state.characterId = manageCharacter.dataset.manageCharacter; state.activeView = "characters"; saveState(); render(); return; } const deleteCharacter = event.target.closest("[data-delete-character]"); if (deleteCharacter) { if (state.characters.length === 1) return toast("至少保留一个角色"); const id = deleteCharacter.dataset.deleteCharacter; state.characters = state.characters.filter(item => item.id !== id); state.shots.forEach(shot => { shot.content.selectedCharacters = (shot.content.selectedCharacters || []).filter(characterId => characterId !== id); if (shot.content.characterDirections) delete shot.content.characterDirections[id]; }); if (state.characterId === id) state.characterId = state.characters[0]?.id || ""; saveState(); render(); return; } const editCharacter = event.target.closest("[data-edit-character]"); if (editCharacter && !event.target.closest("button, a, input, select, textarea, label")) return openCharacterEditor(editCharacter.dataset.editCharacter); const move = event.target.closest("[data-move-shot]"); if (move) return moveShot(move.dataset.shotId, move.dataset.moveShot === "up" ? -1 : 1); if (event.target.closest("#resetButton")) { if (confirm("清除当前项目中的角色、世界观和分镜数据？")) { state = defaultProjectState(); saveState(); render(); toast("当前项目已重置"); } }
});

document.addEventListener("click", event => {
  if (event.target.closest("#validateDirectoriesButton")) return validateDirectories();
  if (event.target.closest("#refreshSessionButton")) return refreshSessionStatus();
});

document.addEventListener("change", event => {
  const layoutField = event.target.closest("[data-layout-field]"); if (layoutField) { const shot = getShot(); if (shot) { const key = layoutField.dataset.layoutField; shot.layoutMeta[key] = ["rowIndex", "slotIndex", "gutterBottom"].includes(key) ? Number(layoutField.value) : layoutField.value; saveState(); } return; }
  const shotStyle = event.target.closest("#shotStylePackSelect"); if (shotStyle) { currentShotContent().stylePackOverride = shotStyle.value; saveState(); render(); return; }
  const exportShot = event.target.closest("[data-export-shot-id]"); if (exportShot) { if (exportShot.checked) selectedExportShotIds.add(exportShot.dataset.exportShotId); else selectedExportShotIds.delete(exportShot.dataset.exportShotId); refreshExportSelectionUi(); return; }
  if (event.target.closest("#exportLettering")) { exportOptions.include_lettering = event.target.checked; return; }
  if (event.target.closest("#exportWidth")) { exportOptions.width = Number(event.target.value); return; }
  if (event.target.closest("#exportGap")) { exportOptions.gap = Number(event.target.value); return; }
  if (event.target.closest("#exportDuration")) { exportOptions.frame_duration_seconds = Number(event.target.value); return; }
  const styleLock = event.target.closest("#styleLockToggle"); if (styleLock) { state.artDirection.locked = styleLock.checked; saveState(); return; }
  const bubblePack = event.target.closest("#bubblePackSelect"); if (bubblePack) { state.lettering.bubblePackId = bubblePack.value; saveState(); render(); return; }
  const semantic = event.target.closest("[data-post-semantic]"); if (semantic) { const block = getShot()?.postText?.[Number(semantic.dataset.postSemantic)]; if (block) { block.bubbleSemantic = semantic.value; block.bubbleAssetId = ""; block.bubbleReferenceId = ""; saveState(); render(); } return; }
  const position = event.target.closest("[data-post-position]"); if (position) { const block = getShot()?.postText?.[Number(position.dataset.postPosition)]; if (block) { block.position = position.value; block.layout = null; const shot = getShot(); if (!shot.textSafeAreas?.includes(position.value)) shot.textSafeAreas = [...(shot.textSafeAreas || []), position.value]; saveState(); render(); } return; }
  const bubble = event.target.closest("[data-post-bubble]"); if (bubble) { const block = getShot()?.postText?.[Number(bubble.dataset.postBubble)]; if (block) { setLetteringAsset(block, bubble.value); saveState(); } return; }
  const letteringAssetSelect = event.target.closest("#letteringAssetSelect"); if (letteringAssetSelect) { const block = currentLetteringBlock(); if (block) { setLetteringAsset(block, letteringAssetSelect.value); saveState(); render(); } return; }
  const letteringUpload = event.target.closest("#letteringBubbleUploadInput"); if (letteringUpload) { const file = letteringUpload.files?.[0]; if (file) uploadLetteringBubble(file); return; }
  const letteringFlip = event.target.closest("#letteringFlipToggle"); if (letteringFlip) { const layout = ensureCustomLetteringLayout(); if (layout) { layout.flip = letteringFlip.checked; saveState(); syncLetteringProof(); } return; }
  const letteringHidden = event.target.closest("#letteringHiddenToggle"); if (letteringHidden) { const block = currentLetteringBlock(); if (block) { block.hidden = letteringHidden.checked; saveState(); render(); } return; }
  const characterToggle = event.target.closest("[data-character-toggle]"); if (characterToggle) { if (characterToggle.checked && selectedCharacterIds().length >= 6) { characterToggle.checked = false; return toast("单个镜头最多锁定 6 个角色"); } return toggleShotCharacter(characterToggle.dataset.characterToggle, characterToggle.checked); } const fieldElement = event.target.closest("[data-field]"); if (fieldElement) { updatePath(fieldElement.dataset.field, fieldElement.value); if (fieldElement.dataset.field === "shotType") { const shot = getShot(); if (shot) shot.type = fieldElement.value; } return; } const projectSelect = event.target.closest("#projectSelect"); if (projectSelect) return switchProject(projectSelect.value); const toggle = event.target.closest("[data-ref-toggle]"); if (toggle) return updateReference(toggle.dataset.refToggle, { enabled: toggle.checked }, true); const type = event.target.closest("[data-ref-type]"); if (type) return updateReference(type.dataset.refType, { reference_type: type.value }); const replace = event.target.closest("[data-replace-reference]"); if (replace) return replaceReference(replace.dataset.replaceReference, replace.files[0]);
});
document.addEventListener("blur", event => { const note = event.target.closest("[data-ref-note]"); if (note) updateReference(note.dataset.refNote, { note: note.value }); }, true);
document.addEventListener("input", event => {
  const layoutField = event.target.closest("[data-layout-field]"); if (layoutField) { const shot = getShot(); if (shot) { const key = layoutField.dataset.layoutField; shot.layoutMeta[key] = ["rowIndex", "slotIndex", "gutterBottom"].includes(key) ? Number(layoutField.value) : layoutField.value; saveState(); } return; }
  const artAnalysis = event.target.closest("[data-art-analysis]"); if (artAnalysis) { state.artDirection.styleAnalysis[artAnalysis.dataset.artAnalysis] = artAnalysis.value; saveState(); return; }
  const artPrompt = event.target.closest("[data-art-prompt]"); if (artPrompt) { state.artDirection.compiledPrompt = artPrompt.value; saveState(); return; }
  const artNegative = event.target.closest("[data-art-negative]"); if (artNegative) { state.artDirection.negativePrompt = artNegative.value; saveState(); return; }
  const postText = event.target.closest("[data-post-text]"); if (postText) { const block = getShot()?.postText?.[Number(postText.dataset.postText)]; if (block) { block.text = postText.value; const counter = postText.closest(".post-text-editor-item")?.querySelector(".post-text-footer span"); if (counter) { counter.textContent = `${postText.value.length}/30`; counter.classList.toggle("is-long", postText.value.length > 30); } saveState(); } return; }
  const letteringText = event.target.closest("#letteringTextInput"); if (letteringText) { const block = currentLetteringBlock(); if (block) { block.text = letteringText.value; saveState(); syncLetteringProof(); } return; }
  const letteringRange = event.target.closest("#letteringXRange, #letteringYRange, #letteringWidthRange, #letteringFontSizeRange, #letteringRotationRange"); if (letteringRange) { const layout = ensureCustomLetteringLayout(); if (layout) { if (letteringRange.id === "letteringXRange") layout.x = Number(letteringRange.value) / 100; if (letteringRange.id === "letteringYRange") layout.y = Number(letteringRange.value) / 100; if (letteringRange.id === "letteringWidthRange") layout.width = Number(letteringRange.value) / 100; if (letteringRange.id === "letteringFontSizeRange") layout.fontScale = Number(letteringRange.value) / 100; if (letteringRange.id === "letteringRotationRange") layout.rotation = Number(letteringRange.value); const normalized = normalizeLetteringLayout(layout); currentLetteringBlock().layout = normalized; saveState(); syncLetteringProof(); } return; }
  const detail = event.target.closest("[data-character-detail]"); if (detail) { const content = currentShotContent(); const characterId = detail.dataset.characterId; content.characterDirections[characterId] = normalizeCharacterDirection(content.characterDirections[characterId]); content.characterDirections[characterId][detail.dataset.characterDetail] = detail.value; saveState(); return; } const fieldElement = event.target.closest("[data-field]"); if (fieldElement) updatePath(fieldElement.dataset.field, fieldElement.value);
});
document.addEventListener("keydown", event => { if (event.key === "Escape" && letteringEditorIndex >= 0) { letteringEditorIndex = -1; render(); return; } const characterCard = event.target.closest("[data-edit-character]"); if (characterCard && event.target === characterCard && ["Enter", " "].includes(event.key)) { event.preventDefault(); openCharacterEditor(characterCard.dataset.editCharacter); return; } const card = event.target.closest("[data-shot-id][tabindex]"); if (!card) return; if (event.key === "ArrowUp") { event.preventDefault(); moveShot(card.dataset.shotId, -1); } if (event.key === "ArrowDown") { event.preventDefault(); moveShot(card.dataset.shotId, 1); } });
document.addEventListener("pointerdown", event => { const bubble = event.target.closest(".proof-bubble[data-lettering-index]"); if (!bubble) return; const index = Number(bubble.dataset.letteringIndex); if (index !== letteringEditorIndex) { letteringEditorIndex = index; render(); return; } const resize = event.target.closest("[data-lettering-resize]"); return beginLetteringPointerEdit(event, Boolean(resize), bubble); });
document.addEventListener("dragstart", event => { const shot = event.target.closest("[data-shot-id]"); const reference = event.target.closest("[data-reference-id]"); const textTool = event.target.closest("#addLetteringTextButton"); if (shot) { draggedShotId = shot.dataset.shotId; shot.classList.add("is-dragging"); } if (reference) { draggedReferenceId = reference.dataset.referenceId; reference.classList.add("is-dragging"); } if (textTool) event.dataTransfer?.setData("text/frame-lettering-text", "text"); });
document.addEventListener("dragend", event => { event.target.closest("[data-shot-id]")?.classList.remove("is-dragging"); event.target.closest("[data-reference-id]")?.classList.remove("is-dragging"); draggedShotId = ""; draggedReferenceId = ""; });
document.addEventListener("dragover", event => { if ((event.target.closest("#letteringProofFrame") || event.target.closest("#letteringBubbleDropzone")) && (event.dataTransfer?.types?.includes("Files") || event.dataTransfer?.types?.includes("text/frame-lettering-text"))) event.preventDefault(); });
document.addEventListener("drop", event => {
  const frame = event.target.closest("#letteringProofFrame");
  const dropzone = event.target.closest("#letteringBubbleDropzone");
  const textTool = event.dataTransfer?.types?.includes("text/frame-lettering-text");
  if (frame && textTool) {
    event.preventDefault();
    const rect = frame.getBoundingClientRect();
    addLetteringTextElement({ x: clamp((event.clientX - rect.left) / rect.width - 0.16, 0, 0.68), y: clamp((event.clientY - rect.top) / rect.height - 0.06, 0, 0.86) });
    return;
  }
  const file = [...(event.dataTransfer?.files || [])].find(item => ["image/png", "image/webp"].includes(item.type));
  if ((!frame && !dropzone) || !file) return;
  event.preventDefault();
  const rect = frame?.getBoundingClientRect();
  const point = rect ? { x: clamp((event.clientX - rect.left) / rect.width - 0.14, 0, 0.72), y: clamp((event.clientY - rect.top) / rect.height - 0.08, 0, 0.82) } : null;
  uploadLetteringBubble(file, point);
});
document.addEventListener("dragover", event => { if (event.target.closest("[data-shot-id]") || event.target.closest("[data-reference-id]")) event.preventDefault(); });
document.addEventListener("drop", event => { event.preventDefault(); const targetShot = event.target.closest("[data-shot-id]"); if (draggedShotId && targetShot && draggedShotId !== targetShot.dataset.shotId) { const from = state.shots.findIndex(item => item.id === draggedShotId); const to = state.shots.findIndex(item => item.id === targetShot.dataset.shotId); if (from >= 0 && to >= 0) { const [item] = state.shots.splice(from, 1); state.shots.splice(to, 0, item); saveState(); render(); toast("镜头顺序已保存"); } } const targetReference = event.target.closest("[data-reference-id]"); if (draggedReferenceId && targetReference && draggedReferenceId !== targetReference.dataset.referenceId) { const dragged = allReferences.find(item => item.id === draggedReferenceId); const siblings = referencesFor(dragged.owner_type, dragged.owner_id); const from = siblings.findIndex(item => item.id === draggedReferenceId); const to = siblings.findIndex(item => item.id === targetReference.dataset.referenceId); if (from >= 0 && to >= 0) { const [item] = siblings.splice(from, 1); siblings.splice(to, 0, item); Promise.all(siblings.map((ref, index) => updateReference(ref.id, { sort_order: index }))).then(() => loadReferences().then(render)); } } });

const appContentObserver = new MutationObserver(() => { enhanceSettingsView(); enhanceNaiLanguageNotice(); enhanceFinalRequestPreview(); enhanceLetteringControls(); });
appContentObserver.observe(document.querySelector("#appContent"), { childList: true });
window.addEventListener?.("focus", checkForProjectUpdates);
document.addEventListener("visibilitychange", () => { if (!document.hidden) checkForProjectUpdates(); });

boot();
