const DATASET_CONFIG = {
  practice10: {
    key: "practice10",
    label: "练习集 10 张",
    finalDataset: false,
    storageKey: "shujuji_practice_annotator"
  },
  formal300: {
    key: "formal300",
    label: "正式集 300 张",
    finalDataset: true,
    storageKey: "shujuji_formal_annotator"
  }
};

function detectDatasetKey() {
  const params = new URLSearchParams(window.location.search);
  const explicit = params.get("dataset");
  if (DATASET_CONFIG[explicit]) return explicit;
  if (window.location.pathname.startsWith("/practice")) return "practice10";
  if (window.location.pathname.startsWith("/formal")) return "formal300";
  return "formal300";
}

const datasetKey = detectDatasetKey();
const datasetConfig = DATASET_CONFIG[datasetKey] || DATASET_CONFIG.formal300;
const ACCESS_TOKEN_STORAGE_KEY = "shujuji_access_token";

function initializeAccessToken() {
  const url = new URL(window.location.href);
  const token = url.searchParams.get("token");
  if (token) {
    sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
    url.searchParams.delete("token");
    window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`);
  }
}

initializeAccessToken();

function currentAccessToken() {
  return sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) || "";
}

const state = {
  charts: [],
  current: null,
  dataset: datasetConfig,
  regions: [],
  selectedRegionId: null,
  activeSaveMode: "final",
  drawMode: false,
  draft: null,
  drag: null,
  columnResize: null,
  layoutWidths: null,
  lastQuickAcceptSnapshot: null,
  zooms: {
    left: 1,
    center: 0.72,
    right: 1,
    workflow: 1
  }
};

const els = {
  layout: document.querySelector(".layout"),
  sidebarPanel: document.querySelector(".sidebar"),
  workspacePanel: document.querySelector(".workspace"),
  inspectorPanel: document.querySelector(".inspector"),
  workflowPanel: document.querySelector(".workflow-rail"),
  resizeHandles: document.querySelectorAll("[data-resize-handle]"),
  helpBtn: document.querySelector("#helpBtn"),
  helpOverlay: document.querySelector("#helpOverlay"),
  helpCloseBtn: document.querySelector("#helpCloseBtn"),
  fullTutorialBtn: document.querySelector("#fullTutorialBtn"),
  detailBoxTutorialBtn: document.querySelector("#detailBoxTutorialBtn"),
  saveDraftBtn: document.querySelector("#saveDraftBtn"),
  pageTitle: document.querySelector(".topbar h1"),
  datasetEyebrow: document.querySelector(".eyebrow"),
  sideTitle: document.querySelector(".side-title"),
  chartList: document.querySelector("#chartList"),
  chartFilter: document.querySelector("#chartFilter"),
  currentTitle: document.querySelector("#currentTitle"),
  currentMeta: document.querySelector("#currentMeta"),
  imageStage: document.querySelector("#imageStage"),
  chartImage: document.querySelector("#chartImage"),
  overlay: document.querySelector("#overlay"),
  drawBtn: document.querySelector("#drawBtn"),
  newRegionType: document.querySelector("#newRegionType"),
  newRegionTypeHint: document.querySelector("#newRegionTypeHint"),
  saveBtn: document.querySelector("#saveBtn"),
  workflowSummary: document.querySelector("#workflowSummary"),
  workflowNextList: document.querySelector("#workflowNextList"),
  quickAcceptBtn: document.querySelector("#quickAcceptBtn"),
  undoQuickAcceptBtn: document.querySelector("#undoQuickAcceptBtn"),
  nextPendingBtn: document.querySelector("#nextPendingBtn"),
  openTargetsBtn: document.querySelector("#openTargetsBtn"),
  workflowDraftBtn: document.querySelector("#workflowDraftBtn"),
  workflowSaveBtn: document.querySelector("#workflowSaveBtn"),
  annotatorInput: document.querySelector("#annotatorInput"),
  emptyRegion: document.querySelector("#emptyRegion"),
  regionForm: document.querySelector("#regionForm"),
  regionRoleHint: document.querySelector("#regionRoleHint"),
  regionIdInput: document.querySelector("#regionIdInput"),
  regionTypeInput: document.querySelector("#regionTypeInput"),
  labelInput: document.querySelector("#labelInput"),
  ocrInput: document.querySelector("#ocrInput"),
  bboxX: document.querySelector("#bboxX"),
  bboxY: document.querySelector("#bboxY"),
  bboxW: document.querySelector("#bboxW"),
  bboxH: document.querySelector("#bboxH"),
  reviewActionInput: document.querySelector("#reviewActionInput"),
  notesInput: document.querySelector("#notesInput"),
  deleteRegionBtn: document.querySelector("#deleteRegionBtn"),
  acceptFrameAndNextBtn: document.querySelector("#acceptFrameAndNextBtn"),
  markFrameUnsureBtn: document.querySelector("#markFrameUnsureBtn"),
  mappingList: document.querySelector("#mappingList"),
  targetPanel: document.querySelector("#targetPanel"),
  targetList: document.querySelector("#targetList"),
  canonicalSummary: document.querySelector("#canonicalSummary"),
  canonicalCompare: document.querySelector("#canonicalCompare"),
  annotationJsonPreview: document.querySelector("#annotationJsonPreview"),
  canonicalJsonPreview: document.querySelector("#canonicalJsonPreview"),
  leftZoomOut: document.querySelector("#leftZoomOut"),
  leftZoomIn: document.querySelector("#leftZoomIn"),
  leftZoomReset: document.querySelector("#leftZoomReset"),
  leftZoomValue: document.querySelector("#leftZoomValue"),
  centerZoomOut: document.querySelector("#centerZoomOut"),
  centerZoomIn: document.querySelector("#centerZoomIn"),
  centerZoomReset: document.querySelector("#centerZoomReset"),
  centerZoomValue: document.querySelector("#centerZoomValue"),
  rightZoomOut: document.querySelector("#rightZoomOut"),
  rightZoomIn: document.querySelector("#rightZoomIn"),
  rightZoomReset: document.querySelector("#rightZoomReset"),
  rightZoomValue: document.querySelector("#rightZoomValue"),
  workflowZoomOut: document.querySelector("#workflowZoomOut"),
  workflowZoomIn: document.querySelector("#workflowZoomIn"),
  workflowZoomReset: document.querySelector("#workflowZoomReset"),
  workflowZoomValue: document.querySelector("#workflowZoomValue"),
  toast: document.querySelector("#toast")
};

const zoomDefaults = {
  left: 1,
  center: 0.72,
  right: 1,
  workflow: 1
};

const zoomLimits = {
  left: { min: 0.65, max: 1.8, step: 0.1, wheelStep: 0.05 },
  center: { min: 0.35, max: 3, step: 0.1, wheelStep: 0.08 },
  right: { min: 0.65, max: 1.8, step: 0.1, wheelStep: 0.05 },
  workflow: { min: 0.65, max: 1.8, step: 0.1, wheelStep: 0.05 }
};

const panelAreas = ["left", "center", "right", "workflow"];

const panelMinWidths = {
  left: 180,
  center: 420,
  right: 280,
  workflow: 240
};

const panelWidthVars = {
  left: "--left-panel-width",
  center: "--center-panel-width",
  right: "--inspector-panel-width",
  workflow: "--workflow-panel-width"
};

const resizePairs = {
  "left-center": ["left", "center"],
  "center-inspector": ["center", "right"],
  "inspector-workflow": ["right", "workflow"]
};

const PR28_FIELDS = [
  "Q_terminator",
  "Q1_fix_ident",
  "Q2_altitude_constraint",
  "Q3_turn",
  "Q4_course_or_radial",
  "Q5_hold_params"
];

const FIELD_LABELS = {
  Q_terminator: "航段类型",
  Q1_fix_ident: "定位点 / 导航台",
  Q2_altitude_constraint: "高度限制",
  Q3_turn: "转弯方向 / 转弯证据",
  Q4_course_or_radial: "航向 / 径向 / 航迹",
  Q5_hold_params: "等待参数"
};

const LEG_TYPE_LABELS = {
  CA: "爬升到高度",
  CF: "飞向指定点",
  DF: "直飞定位点",
  FM: "从定位点飞出",
  HM: "等待航段",
  IF: "初始定位点",
  RF: "半径转弯",
  TF: "航迹到定位点",
  VI: "按航向拦截"
};

const REGION_TYPE_LABELS = {
  MISSED_APPROACH_TEXT: "上方复飞文字大框",
  PLAN_VIEW: "平面图复飞相关区域",
  MISSED_APPROACH_DETAIL_AREA: "下方复飞细节总框",
  FIX_TEXT: "定位点文字",
  FIX_SYMBOL: "定位点符号",
  MISSED_APPROACH_ICON: "复飞图标",
  MISSED_APPROACH_STEP_BOX: "复飞步骤格",
  ALTITUDE_TEXT: "高度文字",
  CLIMB_ARROW: "爬升箭头",
  HEADING_TEXT: "航向文字",
  NAVAID_TEXT: "导航台文字",
  PATH_SEGMENT: "路径/转弯线段",
  RADIAL_TEXT: "径向文字",
  TURN_PHRASE: "转弯文字",
  HOLDING_ARC: "等待弧线",
  HOLDING_PATTERN: "等待图形",
  TRACK_OR_RADIAL_TEXT: "航迹/径向文字",
  OUTBOUND_INBOUND_MARK: "出航/入航标记",
  HOLDING_TIME_TEXT: "等待时间",
  DME_DISTANCE_TEXT: "DME/距离文字"
};

function metaForRegionType(type) {
  const option = Array.from(els.newRegionType?.options || []).find((item) => item.value === type);
  const sourceFieldName = option?.dataset.field || "";
  const elementRole = option?.dataset.role || "";
  const annotationScope = sourceFieldName === "REGION_CONTEXT" ? "coarse_region" : "detail_element";
  const labelText = option?.textContent?.trim() || type;
  return {
    annotation_scope: annotationScope,
    element_role: elementRole,
    source_field_name: sourceFieldName === "REGION_CONTEXT" ? "" : sourceFieldName,
    label: labelText
  };
}

function updateNewRegionTypeHint() {
  if (!els.newRegionTypeHint || !els.newRegionType) return;
  const type = els.newRegionType.value;
  const meta = metaForRegionType(type);
  const scope = meta.annotation_scope === "coarse_region" ? "大框/区域证据" : "小框/字段证据";
  const field = meta.source_field_name || "区域上下文";
  els.newRegionTypeHint.innerHTML = `
    <strong>${escapeText(type)}</strong>
    <span>保存后对应：${escapeText(field)}</span>
    <span>${escapeText(scope)} · ${escapeText(meta.element_role || "-")}</span>
  `;
}

function clamp(value, min = 0, max = 1) {
  return Math.max(min, Math.min(max, value));
}

function escapeText(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function deepClone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

function unknownAnswer() {
  return { status: "unknown", value: null };
}

function answerKey(answer) {
  return JSON.stringify(answer ?? null);
}

function answerEqual(left, right) {
  return answerKey(left) === answerKey(right);
}

function isPresentAnswer(answer) {
  return answer?.status === "present";
}

function formatAnswer(answer) {
  if (!answer) return "unknown";
  if (answer.status !== "present") return answer.status || "unknown";
  if (answer.value === null || typeof answer.value === "undefined") return "present:null";
  if (typeof answer.value === "object") return JSON.stringify(answer.value);
  return String(answer.value);
}

function friendlyStatus(status) {
  const labels = {
    present: "需要图上证据",
    not_applicable: "本航图/本航段没有这个字段，无需画框",
    not_observable: "图上不可见，保留为空",
    unknown: "编码无法确定，先不要求人工框"
  };
  return labels[status] || status || "未知";
}

function friendlyFieldName(field) {
  return FIELD_LABELS[field] ? `${field} · ${FIELD_LABELS[field]}` : field || "字段";
}

function friendlyLegName(legOrMapping) {
  const legIndex = legOrMapping?.canonical_leg_index || canonicalLegIndexForMapping(legOrMapping) || "?";
  const legType = legOrMapping?.leg_type || "";
  const legTypeText = legType ? `${legType}${LEG_TYPE_LABELS[legType] ? `（${LEG_TYPE_LABELS[legType]}）` : ""}` : "未知类型";
  return `航段 ${legIndex} · ${legTypeText}`;
}

function friendlyRegionType(type) {
  return REGION_TYPE_LABELS[type] || type || "未知框类型";
}

function friendlyAnswerValue(answer, fallback = "") {
  if (!answer) return fallback || "未知";
  if (answer.status !== "present") return friendlyStatus(answer.status);
  const value = answer.value;
  if (value === null || typeof value === "undefined") return "空值";
  if (typeof value !== "object") return String(value);
  if ("altitude_ft" in value) {
    const desc = value.desc === "AT_OR_ABOVE" ? "不低于" : value.desc || "高度";
    const second = value.altitude_2_ft ? ` / ${value.altitude_2_ft} ft` : "";
    return `${desc} ${value.altitude_ft} ft${second}`;
  }
  if (value.type === "navaid_radial") {
    const dir = value.direction ? `，${value.direction}` : "";
    const chartRadial = formatChartDegree(value.radial_deg);
    return `${value.navaid || ""} R-${chartRadial}${dir}（424: ${value.radial_deg}°）`;
  }
  if (value.type === "course_deg") return `${formatChartDegree(value.course_deg)}°（424: ${value.course_deg}°）`;
  if ("inbound_course_deg" in value) {
    const parts = [];
    if (value.inbound_course_deg !== null) parts.push(`入航 ${formatChartDegree(value.inbound_course_deg)}°（424: ${value.inbound_course_deg}°）`);
    if (value.leg_time_min !== null) parts.push(`${value.leg_time_min} 分钟`);
    if (value.leg_distance_nm !== null) parts.push(`${value.leg_distance_nm} NM`);
    if (value.turn) parts.push(`${value.turn === "RIGHT" ? "右转" : value.turn}`);
    return parts.join("，") || JSON.stringify(value);
  }
  return JSON.stringify(value);
}

function formatChartDegree(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value ?? "");
  return String(Math.round(number)).padStart(3, "0");
}

function friendlyBasis(text) {
  const source = String(text || "");
  if (!source) return "";
  if (source.includes("generic candidate from CIFP424 target")) {
    return "候选来源：CIFP/424 复飞编码字段。请人工确认当前框能否在航图上证明这个字段；如果不能，请选择“不属于此框”或改挂到正确小框。";
  }
  if (source.includes("human must verify")) {
    return "操作提示：需要人工核对航图证据。";
  }
  if (source.includes("fine-grained")) {
    return "操作提示：如果这个大框太粗，请改用更精细的小框确认。";
  }
  if (source.includes("PDF text token")) return "候选来源：自动识别到的航图文字，请人工核对是否属于复飞字段。";
  if (source.includes("detected climb") || source.includes("cv_icon_component")) return "候选来源：自动识别到的复飞符号/图标，请人工核对。";
  if (source.includes("copied reviewed pilot10")) return "候选来源：从练习样本预标注迁移，请人工复核。";
  if (source.includes("MISSED_APPROACH_TEXT")) return "证据来源：上方复飞文字大框";
  if (source.includes("PLAN_VIEW")) return "证据来源：平面图复飞区域";
  if (source.includes("DETAIL") || source.includes("lower") || source.includes("profile")) return "证据来源：下方复飞细节框";
  if (source.includes("target panel") || source.includes("human-added")) return "证据来源：人工从候选字段挂接";
  return "候选来源：系统自动生成。请人工核对航图证据后再确认。";
}

function friendlyRegionNote(region) {
  if (!region) return "";
  if (region.region_type === "MISSED_APPROACH_TEXT") {
    return "这是上方复飞文字的大框。为了减少标注量，不需要把这段文字拆成很多小框；只要确认它确实覆盖完整复飞文字说明即可。";
  }
  if (region.region_type === "PLAN_VIEW") {
    return "这是平面图中与复飞有关的大区域。用于说明复飞路径、定位点、径向/航向、等待图形等上下文。";
  }
  if (region.region_type === "MISSED_APPROACH_DETAIL_AREA") {
    return "这是下方复飞细节总框。它只圈住复飞小表格/剖面复飞区域；里面的高度、箭头、fix、radial、holding 等仍要用小框单独确认。";
  }
  return `这是一个细节小框，应尽量贴紧一个可见符号或文字：${friendlyRegionType(region.region_type)}。`;
}

function canonicalAnswerAt(canonicalLegs, legIndex, field) {
  const leg = canonicalLegs.find((item) => item.leg_index === legIndex);
  return leg?.answers?.[field] || null;
}

function canonicalLegById(candidateLegId) {
  const target = state.current?.target;
  return (target?.candidate_legs || []).find((leg) => leg.candidate_leg_id === candidateLegId) || null;
}

function canonicalFieldForMapping(mapping) {
  if (mapping.expected_answer) return mapping.expected_answer;
  const leg = canonicalLegById(mapping.candidate_leg_id);
  const field = (leg?.target_fields || []).find((item) => (item.field_name || item.name) === mapping.field_name);
  return field?.expected_answer || null;
}

function canonicalLegIndexForMapping(mapping) {
  if (Number.isInteger(mapping.canonical_leg_index)) return mapping.canonical_leg_index;
  const leg = canonicalLegById(mapping.candidate_leg_id);
  if (Number.isInteger(leg?.canonical_leg_index)) return leg.canonical_leg_index;
  const match = String(mapping.candidate_leg_id || "").match(/__ma(\d+)$/);
  return match ? Number(match[1]) : null;
}

function buildAnnotationCanonicalJson() {
  const canonical = state.current?.canonical_gt;
  const target = state.current?.target;
  const chartId = state.current?.manifest?.chart_id || "";
  const procedure = canonical?.procedure || {
    airport: chartId.slice(0, 4),
    approach_ident: chartId.split("_")[1] || "",
    chart_name: state.current?.manifest?.procedure_key || ""
  };
  const canonicalLegs = canonical?.missed_approach?.legs || [];
  const targetLegs = target?.candidate_legs || [];
  const legCount = canonicalLegs.length || targetLegs.length;
  const legs = Array.from({ length: legCount }, (_, index) => ({
    leg_index: index + 1,
    answers: Object.fromEntries(PR28_FIELDS.map((field) => {
      const canonicalAnswer = canonicalAnswerAt(canonicalLegs, index + 1, field);
      // Non-present fields have no visual box to confirm. Keep their PR #28
      // status in the generated JSON and require box mapping only for present values.
      const initialAnswer = canonicalAnswer && (!isPresentAnswer(canonicalAnswer) || field === "Q_terminator")
        ? deepClone(canonicalAnswer)
        : unknownAnswer();
      return [field, initialAnswer];
    }))
  }));
  const acceptedMappings = [];

  state.regions.forEach((region) => {
    (region.candidate_mappings || []).forEach((mapping) => {
      if (mapping.human_decision !== "accepted") return;
      if (!PR28_FIELDS.includes(mapping.field_name)) return;
      const legIndex = canonicalLegIndexForMapping(mapping);
      const answer = mapping.human_answer || canonicalFieldForMapping(mapping);
      if (!legIndex || !answer || !legs[legIndex - 1]) return;
      legs[legIndex - 1].answers[mapping.field_name] = deepClone(answer);
      acceptedMappings.push(mapping);
    });
  });

  return {
    chart_id: chartId,
    procedure,
    missed_approach: {
      leg_count: { status: "present", value: legCount },
      legs
    }
  };
}

function flattenCanonicalAnswers(doc) {
  const rows = [];
  const legCount = doc?.missed_approach?.leg_count;
  rows.push({ key: "leg_count", answer: legCount });
  (doc?.missed_approach?.legs || []).forEach((leg) => {
    PR28_FIELDS.forEach((field) => {
      rows.push({
        key: `leg${leg.leg_index}.${field}`,
        leg_index: leg.leg_index,
        field,
        answer: leg.answers?.[field]
      });
    });
  });
  return rows;
}

function compareCanonicalJson(predicted, canonical) {
  const gtRows = flattenCanonicalAnswers(canonical);
  const predByKey = new Map(flattenCanonicalAnswers(predicted).map((row) => [row.key, row.answer]));
  let matched = 0;
  let observable = 0;
  let presentTotal = 0;
  let presentMatched = 0;
  let presentCovered = 0;
  let autoStatusTotal = 0;
  const rows = gtRows.map((row) => {
    const predictedAnswer = predByKey.get(row.key) || unknownAnswer();
    const isCovered = predictedAnswer.status !== "unknown";
    const isMatch = answerEqual(predictedAnswer, row.answer);
    const requiresBoxEvidence = row.key !== "leg_count" && row.field !== "Q_terminator" && isPresentAnswer(row.answer);
    const autoStatusField = row.key !== "leg_count" && (row.field === "Q_terminator" || !isPresentAnswer(row.answer));
    if (isCovered) observable += 1;
    if (isMatch) matched += 1;
    if (requiresBoxEvidence) {
      presentTotal += 1;
      if (isCovered) presentCovered += 1;
      if (isMatch) presentMatched += 1;
    }
    if (autoStatusField) autoStatusTotal += 1;
    return {
      ...row,
      predicted: predictedAnswer,
      match: isMatch,
      covered: isCovered,
      requiresBoxEvidence,
      autoStatusField
    };
  });
  return {
    total: gtRows.length,
    matched,
    covered: observable,
    present_total: presentTotal,
    present_matched: presentMatched,
    present_covered: presentCovered,
    auto_status_total: autoStatusTotal,
    full_alignment_rate: gtRows.length ? matched / gtRows.length : 0,
    overall_evidence_coverage: gtRows.length ? observable / gtRows.length : 0,
    present_alignment_rate: presentTotal ? presentMatched / presentTotal : 1,
    present_coverage: presentTotal ? presentCovered / presentTotal : 1,
    rows
  };
}

function currentAnnotator() {
  return (els.annotatorInput?.value || "").trim();
}

function apiUrl(path, params = {}) {
  const url = new URL(path, window.location.origin);
  url.searchParams.set("dataset", datasetKey);
  const token = currentAccessToken();
  if (token) url.searchParams.set("token", token);
  const annotator = params.annotator ?? currentAnnotator();
  if (annotator) url.searchParams.set("annotator", annotator);
  Object.entries(params).forEach(([key, value]) => {
    if (key !== "annotator" && value !== undefined && value !== null) {
      url.searchParams.set(key, value);
    }
  });
  return `${url.pathname}${url.search}`;
}

function withAccessToken(urlValue) {
  const token = currentAccessToken();
  if (!token || !urlValue) return urlValue;
  const url = new URL(urlValue, window.location.origin);
  url.searchParams.set("token", token);
  return `${url.pathname}${url.search}`;
}

async function parseResponseError(response) {
  const text = await response.text();
  try {
    const payload = JSON.parse(text);
    const error = new Error(payload.error || text || `HTTP ${response.status}`);
    error.status = response.status;
    error.payload = payload;
    return error;
  } catch {
    const error = new Error(text || `HTTP ${response.status}`);
    error.status = response.status;
    return error;
  }
}

async function getJson(url) {
  const headers = {};
  const token = currentAccessToken();
  if (token) headers["x-shujuji-token"] = token;
  const response = await fetch(url, { headers });
  if (!response.ok) throw await parseResponseError(response);
  return response.json();
}

async function postJson(url, payload) {
  const token = currentAccessToken();
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      ...(token ? { "x-shujuji-token": token } : {})
    },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw await parseResponseError(response);
  return response.json();
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.remove("hidden");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => els.toast.classList.add("hidden"), 2800);
}

function zoomText(value) {
  return `${Math.round(value * 100)}%`;
}

function updateZoomLabels() {
  if (els.leftZoomValue) els.leftZoomValue.textContent = zoomText(state.zooms.left);
  if (els.centerZoomValue) els.centerZoomValue.textContent = zoomText(state.zooms.center);
  if (els.rightZoomValue) els.rightZoomValue.textContent = zoomText(state.zooms.right);
  if (els.workflowZoomValue) els.workflowZoomValue.textContent = zoomText(state.zooms.workflow);
}

function applyPanelZooms() {
  document.documentElement.style.setProperty("--left-zoom", String(state.zooms.left));
  document.documentElement.style.setProperty("--right-zoom", String(state.zooms.right));
  document.documentElement.style.setProperty("--workflow-zoom", String(state.zooms.workflow));
  updateZoomLabels();
}

function applyImageZoom({ render = true } = {}) {
  if (!els.chartImage.naturalWidth) {
    updateZoomLabels();
    return;
  }
  els.chartImage.style.width = `${Math.round(els.chartImage.naturalWidth * state.zooms.center)}px`;
  els.chartImage.style.height = "auto";
  els.chartImage.style.maxWidth = "none";
  els.chartImage.style.maxHeight = "none";
  updateZoomLabels();
  if (render) window.requestAnimationFrame(renderOverlay);
}

function applyZooms({ render = true } = {}) {
  applyPanelZooms();
  applyImageZoom({ render });
}

function setPanelZoom(area, value) {
  const limit = zoomLimits[area];
  if (!limit) return;
  state.zooms[area] = Number(clamp(value, limit.min, limit.max).toFixed(2));
  applyZooms();
}

function adjustPanelZoom(area, direction) {
  const limit = zoomLimits[area];
  setPanelZoom(area, state.zooms[area] + limit.step * direction);
}

function resetPanelZoom(area) {
  setPanelZoom(area, zoomDefaults[area]);
}

function panelElement(area) {
  return {
    left: els.sidebarPanel,
    center: els.workspacePanel,
    right: els.inspectorPanel,
    workflow: els.workflowPanel
  }[area] || null;
}

function readPanelWidths() {
  return Object.fromEntries(panelAreas.map((area) => {
    const rect = panelElement(area)?.getBoundingClientRect();
    return [area, Math.round(rect?.width || panelMinWidths[area])];
  }));
}

function applyLayoutWidths(widths = state.layoutWidths) {
  if (!widths) return;
  panelAreas.forEach((area) => {
    const width = Number(widths[area]);
    if (Number.isFinite(width)) {
      document.documentElement.style.setProperty(panelWidthVars[area], `${Math.round(width)}px`);
    }
  });
  window.requestAnimationFrame(renderOverlay);
}

function beginColumnResize(event) {
  const pair = resizePairs[event.currentTarget?.dataset.resizeHandle];
  if (!pair) return;
  const widths = readPanelWidths();
  state.layoutWidths = widths;
  applyLayoutWidths(widths);
  state.columnResize = {
    pair,
    startX: event.clientX,
    startWidths: widths,
    handle: event.currentTarget
  };
  els.layout?.classList.add("resizing");
  event.currentTarget.classList.add("dragging");
  event.currentTarget.setPointerCapture?.(event.pointerId);
  event.preventDefault();
}

function updateColumnResize(event) {
  if (!state.columnResize) return;
  const { pair, startX, startWidths } = state.columnResize;
  const [before, after] = pair;
  const total = startWidths[before] + startWidths[after];
  const minBefore = Math.min(panelMinWidths[before], total * 0.45);
  const minAfter = Math.min(panelMinWidths[after], total * 0.45);
  const maxBefore = Math.max(minBefore, total - minAfter);
  const beforeWidth = clamp(startWidths[before] + event.clientX - startX, minBefore, maxBefore);
  const nextWidths = {
    ...startWidths,
    [before]: beforeWidth,
    [after]: total - beforeWidth
  };
  state.layoutWidths = nextWidths;
  applyLayoutWidths(nextWidths);
}

function endColumnResize() {
  if (!state.columnResize) return;
  state.columnResize.handle?.classList.remove("dragging");
  els.layout?.classList.remove("resizing");
  state.columnResize = null;
}

function bindCtrlWheelZoom() {
  [
    ["left", els.sidebarPanel],
    ["center", els.workspacePanel],
    ["right", els.inspectorPanel],
    ["workflow", els.workflowPanel]
  ].forEach(([area, element]) => {
    if (!element) return;
    element.addEventListener("wheel", (event) => {
      if (!event.ctrlKey) return;
      event.preventDefault();
      const limit = zoomLimits[area];
      const direction = event.deltaY < 0 ? 1 : -1;
      setPanelZoom(area, state.zooms[area] + direction * (limit.wheelStep || limit.step));
    }, { passive: false });
  });
}

function openHelp() {
  els.helpOverlay?.classList.remove("hidden");
  document.body.classList.add("help-open");
}

function closeHelp() {
  els.helpOverlay?.classList.add("hidden");
  document.body.classList.remove("help-open");
}

function makeRegionId(chartId, index) {
  return `${chartId}_r${String(index + 1).padStart(3, "0")}`;
}

function normalizeRegion(region, index) {
  const sourceId = region.region_id || region.final_region_id || region.source_region_id || makeRegionId(state.current.manifest.chart_id, index);
  return {
    region_id: sourceId,
    source_region_id: region.source_region_id || sourceId,
    region_type: region.region_type || "MISSED_APPROACH_TEXT",
    bbox: {
      x_center: Number(region.bbox?.x_center ?? 0.5),
      y_center: Number(region.bbox?.y_center ?? 0.5),
      width: Number(region.bbox?.width ?? 0.25),
      height: Number(region.bbox?.height ?? 0.12)
    },
    label: region.label || "",
    ocr_text: region.ocr_text || "",
    confidence: region.confidence ?? null,
    annotation_scope: region.annotation_scope || "",
    element_role: region.element_role || "",
    expected_visual_value: region.expected_visual_value || "",
    step_id: region.step_id || "",
    parent_step_region_id: region.parent_step_region_id || "",
    source_candidate_leg_id: region.source_candidate_leg_id || "",
    source_leg_type: region.source_leg_type || "",
    source_field_name: region.source_field_name || "",
    is_formal_annotation_candidate: Boolean(region.is_formal_annotation_candidate),
    candidate_mappings: region.candidate_mappings || region.candidate_mappings_reviewed || region.accepted_mappings || [],
    needs_human_decision: region.needs_human_decision ?? true,
    human_review: {
      review_action: region.review_action || region.human_review?.review_action || "pending",
      adjusted_bbox: region.human_review?.adjusted_bbox || null,
      final_region_type: region.human_review?.final_region_type || region.region_type || "",
      notes: region.notes || region.human_review?.notes || ""
    }
  };
}

function selectedRegion() {
  return state.regions.find((region) => region.region_id === state.selectedRegionId) || null;
}

function mappingIsPending(mapping) {
  return !mapping.human_decision || mapping.human_decision === "pending";
}

function regionHasPendingMappings(region) {
  return Boolean(region?.candidate_mappings?.some(mappingIsPending));
}

function selectRegionById(regionId) {
  state.selectedRegionId = regionId;
  renderOverlay();
  renderRegionForm();
  renderTargets();
}

function findNextPendingRegionId(afterRegionId = state.selectedRegionId) {
  if (!state.regions.length) return null;
  const startIndex = Math.max(0, state.regions.findIndex((region) => region.region_id === afterRegionId));
  for (let offset = 1; offset <= state.regions.length; offset += 1) {
    const region = state.regions[(startIndex + offset) % state.regions.length];
    if (regionHasPendingMappings(region)) return region.region_id;
  }
  return null;
}

function acceptPendingMappings(region) {
  if (!region) return 0;
  let changed = 0;
  (region.candidate_mappings || []).forEach((mapping) => {
    if (mappingIsPending(mapping)) {
      mapping.human_decision = "accepted";
      changed += 1;
    }
  });
  if (changed) region.human_review.review_action = "accept";
  return changed;
}

function acceptCurrentAndAdvance() {
  const region = selectedRegion();
  const changed = acceptPendingMappings(region);
  const nextRegionId = findNextPendingRegionId(region?.region_id);
  if (nextRegionId) {
    selectRegionById(nextRegionId);
    showToast(`已确认当前框 ${changed} 条候选，并跳到下一个待确认框。`);
  } else {
    renderRegionForm();
    renderTargets();
    renderCanonicalPanel();
    showToast(`已确认当前框 ${changed} 条候选；本图暂无待确认框。`);
  }
}

function setUndoQuickAcceptEnabled(enabled) {
  if (els.undoQuickAcceptBtn) {
    els.undoQuickAcceptBtn.disabled = !enabled;
  }
}

function acceptAllChartPendingMappings() {
  const snapshot = [];
  const changedRegions = new Set();
  state.regions.forEach((region) => {
    const previousReviewAction = region.human_review?.review_action;
    (region.candidate_mappings || []).forEach((mapping) => {
      if (!mappingIsPending(mapping)) return;
      snapshot.push({
        region,
        mapping,
        previousDecision: mapping.human_decision,
        previousReviewAction
      });
      mapping.human_decision = "accepted";
      changedRegions.add(region);
    });
  });
  changedRegions.forEach((region) => {
    region.human_review.review_action = "accept";
  });
  state.lastQuickAcceptSnapshot = snapshot.length ? snapshot : null;
  setUndoQuickAcceptEnabled(Boolean(state.lastQuickAcceptSnapshot));
  renderOverlay();
  renderRegionForm();
  renderTargets();
  renderCanonicalPanel();
  const message = snapshot.length
    ? `已快速确认本图已有候选 ${snapshot.length} 条；误点可先点“撤销快速确认”。`
    : "当前没有待快速确认的候选。";
  showToast(message);
}

function undoQuickAccept() {
  const snapshot = state.lastQuickAcceptSnapshot;
  if (!snapshot?.length) {
    showToast("没有可撤销的快速确认。");
    return;
  }
  snapshot.forEach(({ region, mapping, previousDecision, previousReviewAction }) => {
    if (previousDecision === undefined) {
      delete mapping.human_decision;
    } else {
      mapping.human_decision = previousDecision;
    }
    if (region?.human_review) region.human_review.review_action = previousReviewAction || "pending";
  });
  state.lastQuickAcceptSnapshot = null;
  setUndoQuickAcceptEnabled(false);
  renderOverlay();
  renderRegionForm();
  renderTargets();
  renderCanonicalPanel();
  showToast("已撤销上次快速确认；保存前不会写入那次批量确认。");
}

function markCurrentFrameUnsure() {
  const region = selectedRegion();
  if (!region) return;
  (region.candidate_mappings || []).forEach((mapping) => {
    if (mappingIsPending(mapping)) mapping.human_decision = "needs_discussion";
  });
  region.human_review.review_action = "pending";
  region.human_review.notes = region.human_review.notes || "不确定，需要复核。";
  renderRegionForm();
  renderTargets();
  renderCanonicalPanel();
  showToast("已把当前框标记为不确定。");
}

function openTargetPanel() {
  if (!els.targetPanel) return;
  els.targetPanel.open = true;
  els.targetPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function fieldAcceptedForLeg(leg, field) {
  const legId = leg?.candidate_leg_id || "";
  const fieldName = field.field_name || field.name || "";
  return state.regions.some((region) => (region.candidate_mappings || []).some((mapping) => {
    return mapping.human_decision === "accepted"
      && mapping.candidate_leg_id === legId
      && mapping.field_name === fieldName;
  }));
}

function renderWorkflowPanel(comparison, pendingCount, attentionRows) {
  if (!els.workflowSummary || !els.workflowNextList) return;
  const remaining = attentionRows.length;
  const coverage = Math.round((comparison?.present_coverage || 0) * 100);
  let nextText = "可以保存";
  if (pendingCount > 0) {
    nextText = "先快速确认已有候选";
  } else if (remaining > 0) {
    nextText = `补 ${remaining} 个缺证字段`;
  }
  els.workflowSummary.innerHTML = `
    <div class="workflow-metric">
      <strong>${coverage}%</strong>
      <span>证据覆盖</span>
    </div>
    <div class="workflow-metric">
      <strong>${pendingCount}</strong>
      <span>待确认候选</span>
    </div>
    <div class="workflow-metric">
      <strong>${remaining}</strong>
      <span>缺证字段</span>
    </div>
    <div class="workflow-next">
      <b>下一步：</b>${escapeText(nextText)}
    </div>
    <p class="metric-note">这里统计的是人工证据覆盖/对齐，不代表独立 OCR 或 LLM 抽取正确率。</p>
  `;

  els.workflowNextList.innerHTML = "";
  if (!remaining) {
    els.workflowNextList.innerHTML = '<p class="empty">当前没有缺证的 present 字段。确认图上没有明显错误后即可保存。</p>';
    return;
  }
  const title = document.createElement("strong");
  title.textContent = "需要优先补证据的字段";
  els.workflowNextList.appendChild(title);
  attentionRows.slice(0, 5).forEach((row) => {
    const item = document.createElement("div");
    item.className = "workflow-missing-row";
    item.innerHTML = `
      <span>${escapeText(`航段 ${row.leg_index} · ${friendlyFieldName(row.field)}`)}</span>
      <b>${escapeText(friendlyAnswerValue(row.answer))}</b>
      <button type="button">去候选字段处理</button>
    `;
    item.querySelector("button").addEventListener("click", openTargetPanel);
    els.workflowNextList.appendChild(item);
  });
}

function renderChartList() {
  const query = els.chartFilter.value.trim().toLowerCase();
  els.chartList.innerHTML = "";
  state.charts
    .filter((chart) => {
      const text = `${chart.chart_id} ${chart.sample_type} ${chart.priority_reason || ""} ${chart.claim_status || ""} ${chart.claimed_by || ""}`.toLowerCase();
      return !query || text.includes(query);
    })
    .forEach((chart) => {
      const card = document.createElement("div");
      const claimedByOther = datasetConfig.finalDataset && chart.claim_status === "claimed_by_other";
      const canClaim = datasetConfig.finalDataset
        && chart.claim_status === "unassigned"
        && currentAnnotator();
      const claimLabel = !datasetConfig.finalDataset
        ? "practice"
        : chart.claim_status === "unassigned"
          ? "未领取"
          : chart.claim_status === "submitted"
            ? "我已提交"
            : chart.claim_status === "claimed" || chart.claim_status === "claimed_by_me"
              ? "我已领取"
              : `已被 ${chart.claimed_by || "他人"} 领取`;
      card.className = `chart-card ${state.current?.manifest?.chart_id === chart.chart_id ? "active" : ""} ${claimedByOther ? "disabled" : ""}`;
      card.title = claimedByOther ? "这张图已被其他标注人领取，请选择未领取的图。" : "点击打开这张图；正式标注请在左栏点“领取”。";
      card.innerHTML = `
        <button class="chart-open" type="button" ${claimedByOther ? "disabled" : ""}>
          <strong>${escapeText(chart.chart_id)}</strong>
          <span class="muted">${escapeText(chart.procedure_key || "")}</span>
        </button>
        ${datasetConfig.finalDataset ? `<button class="claim-card-btn" type="button" ${canClaim ? "" : "disabled"}>${chart.claim_status === "unassigned" ? "领取" : claimLabel}</button>` : ""}
        <div class="badge-row">
          <span class="badge ${chart.sample_type === "anomaly" ? "hot" : ""}">${escapeText(chart.sample_type)}</span>
          <span class="badge">legs ${chart.target_leg_count}</span>
          <span class="badge ${claimedByOther ? "hot" : ""}">${escapeText(claimLabel)}</span>
          ${chart.has_prelabel ? '<span class="badge">prelabel</span>' : ""}
          ${chart.has_my_draft ? '<span class="badge">鏆傚瓨</span>' : ""}
          ${chart.has_my_annotation ? '<span class="badge hot">我的保存</span>' : ""}
          ${chart.submission_count ? `<span class="badge">提交 ${escapeText(chart.submission_count)}</span>` : ""}
        </div>
      `;
      card.querySelector(".chart-open")?.addEventListener("click", () => loadChart(chart.chart_id).catch((error) => showToast(error.message)));
      card.querySelector(".claim-card-btn")?.addEventListener("click", (event) => {
        event.stopPropagation();
        claimChartFromList(chart.chart_id).catch((error) => showToast(error.message));
      });
      els.chartList.appendChild(card);
    });
}

function updateClaimButton() {
  renderChartList();
}

async function claimChartFromList(chartId) {
  if (datasetConfig.finalDataset && !currentAnnotator()) {
    showToast("请先填写标注人，再领取航图。");
    els.annotatorInput?.focus();
    return;
  }
  const result = await postJson(apiUrl(`/api/claims/${encodeURIComponent(chartId)}`), {});
  const claim = result.claim || {};
  const chart = state.charts.find((item) => item.chart_id === chartId);
  if (chart) {
    chart.claim_status = claim.status || "claimed";
    chart.claimed_by = claim.annotator || currentAnnotator();
    chart.claimed_at = claim.claimed_at || "";
  }
  if (state.current?.manifest?.chart_id === chartId) {
    state.current.manifest.claim_status = claim.status || "claimed";
    state.current.manifest.claimed_by = claim.annotator || currentAnnotator();
    state.current.manifest.claimed_at = claim.claimed_at || "";
    const claimText = state.current.manifest.claimed_by ? ` · 领取人 ${state.current.manifest.claimed_by}` : "";
    if (els.currentMeta) {
      els.currentMeta.textContent = ` ${state.current.manifest.sample_type || ""} · ${state.current.manifest.priority_reason || ""}${claimText}`;
    }
  }
  renderChartList();
  showToast(`已领取：${chartId}`);
}

async function loadChart(chartId) {
  if (datasetConfig.finalDataset && !currentAnnotator()) {
    showToast("正式标注请先填写右上角“标注人”，再在左栏点击航图的“领取”。");
    els.annotatorInput?.focus();
    return;
  }
  state.current = await getJson(apiUrl("/api/chart", { chart_id: chartId }));
  state.dataset = state.current.dataset || datasetConfig;
  const sourceRegions = state.current.draft?.regions || state.current.annotation?.regions || state.current.prelabel?.regions || [];
  state.regions = sourceRegions.map(normalizeRegion);
  state.selectedRegionId = state.regions[0]?.region_id || null;
  state.lastQuickAcceptSnapshot = null;
  setUndoQuickAcceptEnabled(false);

  els.currentTitle.textContent = chartId;
  const claimText = state.current.manifest.claimed_by ? ` · 领取人 ${state.current.manifest.claimed_by}` : "";
  els.currentMeta.textContent = ` ${state.current.manifest.sample_type || ""} · ${state.current.manifest.priority_reason || ""}${claimText}`;
  els.overlay.style.width = "1px";
  els.overlay.style.height = "1px";
  els.chartImage.onload = () => {
    applyImageZoom({ render: false });
    renderOverlay();
  };
  els.chartImage.src = withAccessToken(state.current.image_url);

  renderChartList();
  renderOverlay();
  renderRegionForm();
  renderTargets();
  renderCanonicalPanel();
  updateClaimButton();
}

function getStageSize() {
  const rect = els.chartImage.getBoundingClientRect();
  return {
    width: rect.width || 1,
    height: rect.height || 1
  };
}

function syncOverlayToImage(size = getStageSize()) {
  // Keep overlay coordinates tied to the rendered image, not the wrapper.
  // Browser zoom can make the image smaller than the stage and otherwise
  // creates apparent bbox drift.
  els.overlay.style.width = `${size.width}px`;
  els.overlay.style.height = `${size.height}px`;
  els.overlay.setAttribute("width", String(size.width));
  els.overlay.setAttribute("height", String(size.height));
}

function normalizedPoint(event) {
  const rect = els.overlay.getBoundingClientRect();
  return {
    x: clamp((event.clientX - rect.left) / Math.max(rect.width, 1)),
    y: clamp((event.clientY - rect.top) / Math.max(rect.height, 1))
  };
}

function bboxToPixels(bbox) {
  const size = getStageSize();
  return {
    x: (bbox.x_center - bbox.width / 2) * size.width,
    y: (bbox.y_center - bbox.height / 2) * size.height,
    width: bbox.width * size.width,
    height: bbox.height * size.height
  };
}

function roundUnit(value) {
  return Number(clamp(value).toFixed(4));
}

function bboxEdges(bbox) {
  const width = clamp(Number(bbox.width) || 0.001, 0.001, 1);
  const height = clamp(Number(bbox.height) || 0.001, 0.001, 1);
  const xCenter = clamp(Number(bbox.x_center) || 0.5, width / 2, 1 - width / 2);
  const yCenter = clamp(Number(bbox.y_center) || 0.5, height / 2, 1 - height / 2);
  return {
    left: clamp(xCenter - width / 2),
    right: clamp(xCenter + width / 2),
    top: clamp(yCenter - height / 2),
    bottom: clamp(yCenter + height / 2)
  };
}

function bboxFromEdges(left, top, right, bottom) {
  const safeLeft = clamp(Math.min(left, right));
  const safeRight = clamp(Math.max(left, right));
  const safeTop = clamp(Math.min(top, bottom));
  const safeBottom = clamp(Math.max(top, bottom));
  return {
    x_center: roundUnit((safeLeft + safeRight) / 2),
    y_center: roundUnit((safeTop + safeBottom) / 2),
    width: roundUnit(Math.max(0.001, safeRight - safeLeft)),
    height: roundUnit(Math.max(0.001, safeBottom - safeTop))
  };
}

function boxHandleForPoint(point, bbox) {
  const size = getStageSize();
  const edges = bboxEdges(bbox);
  const width = Math.max(0.001, edges.right - edges.left);
  const height = Math.max(0.001, edges.bottom - edges.top);
  const thresholdX = Math.min(10 / Math.max(size.width, 1), width / 3);
  const thresholdY = Math.min(10 / Math.max(size.height, 1), height / 3);
  const nearLeft = Math.abs(point.x - edges.left) <= thresholdX;
  const nearRight = Math.abs(point.x - edges.right) <= thresholdX;
  const nearTop = Math.abs(point.y - edges.top) <= thresholdY;
  const nearBottom = Math.abs(point.y - edges.bottom) <= thresholdY;
  if (nearTop && nearLeft) return "nw";
  if (nearTop && nearRight) return "ne";
  if (nearBottom && nearLeft) return "sw";
  if (nearBottom && nearRight) return "se";
  if (nearTop) return "n";
  if (nearBottom) return "s";
  if (nearLeft) return "w";
  if (nearRight) return "e";
  return "move";
}

function cursorForBoxHandle(handle) {
  return {
    n: "ns-resize",
    s: "ns-resize",
    e: "ew-resize",
    w: "ew-resize",
    ne: "nesw-resize",
    sw: "nesw-resize",
    nw: "nwse-resize",
    se: "nwse-resize",
    move: "move"
  }[handle] || "default";
}

function resetOverlayCursor() {
  if (!els.overlay) return;
  els.overlay.style.cursor = state.drawMode ? "crosshair" : "default";
}

function markRegionAdjusted(region) {
  if (!region.human_review) region.human_review = {};
  region.human_review.adjusted_bbox = { ...region.bbox };
  if (!region.human_review.review_action || region.human_review.review_action === "pending") {
    region.human_review.review_action = "adjust";
  }
}

function resizedBbox(startBbox, mode, dx, dy) {
  const minWidth = 0.004;
  const minHeight = 0.004;
  let { left, right, top, bottom } = bboxEdges(startBbox);
  if (mode.includes("w")) left += dx;
  if (mode.includes("e")) right += dx;
  if (mode.includes("n")) top += dy;
  if (mode.includes("s")) bottom += dy;

  if (right - left < minWidth) {
    if (mode.includes("w")) left = right - minWidth;
    else right = left + minWidth;
  }
  if (bottom - top < minHeight) {
    if (mode.includes("n")) top = bottom - minHeight;
    else bottom = top + minHeight;
  }

  left = clamp(left);
  right = clamp(right);
  top = clamp(top);
  bottom = clamp(bottom);

  if (right - left < minWidth) {
    if (mode.includes("w")) left = Math.max(0, right - minWidth);
    else right = Math.min(1, left + minWidth);
  }
  if (bottom - top < minHeight) {
    if (mode.includes("n")) top = Math.max(0, bottom - minHeight);
    else bottom = Math.min(1, top + minHeight);
  }

  return bboxFromEdges(left, top, right, bottom);
}

function movedBbox(startBbox, dx, dy) {
  const width = clamp(Number(startBbox.width) || 0.001, 0.001, 1);
  const height = clamp(Number(startBbox.height) || 0.001, 0.001, 1);
  return {
    x_center: roundUnit(clamp((Number(startBbox.x_center) || 0.5) + dx, width / 2, 1 - width / 2)),
    y_center: roundUnit(clamp((Number(startBbox.y_center) || 0.5) + dy, height / 2, 1 - height / 2)),
    width: roundUnit(width),
    height: roundUnit(height)
  };
}

function updateDraggedRegionBox(point) {
  if (!state.drag || state.drag.type !== "region-box") return false;
  const region = state.regions.find((item) => item.region_id === state.drag.regionId);
  if (!region) return false;
  const dx = point.x - state.drag.startPoint.x;
  const dy = point.y - state.drag.startPoint.y;
  region.bbox = state.drag.mode === "move"
    ? movedBbox(state.drag.startBbox, dx, dy)
    : resizedBbox(state.drag.startBbox, state.drag.mode, dx, dy);
  markRegionAdjusted(region);
  return true;
}

function regionClassName(regionType) {
  return `region-${String(regionType || "").toLowerCase().replace(/_/g, "-")}`;
}

function renderOverlay() {
  const size = getStageSize();
  syncOverlayToImage(size);
  els.overlay.setAttribute("viewBox", `0 0 ${size.width} ${size.height}`);
  els.overlay.innerHTML = "";

  state.regions.forEach((region) => {
    const box = bboxToPixels(region.bbox);
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", box.x);
    rect.setAttribute("y", box.y);
    rect.setAttribute("width", box.width);
    rect.setAttribute("height", box.height);
    rect.classList.add("box");
    rect.classList.add(regionClassName(region.region_type));
    if (region.region_id === state.selectedRegionId) rect.classList.add("selected");
    if (state.drag?.type === "region-box" && state.drag.regionId === region.region_id) {
      rect.style.cursor = cursorForBoxHandle(state.drag.mode);
    }
    rect.addEventListener("pointerdown", (event) => {
      if (state.drawMode) return;
      event.stopPropagation();
      event.preventDefault();
      state.selectedRegionId = region.region_id;
      const point = normalizedPoint(event);
      const mode = boxHandleForPoint(point, region.bbox);
      state.drag = {
        type: "region-box",
        regionId: region.region_id,
        mode,
        startPoint: point,
        startBbox: { ...region.bbox }
      };
      els.overlay.style.cursor = cursorForBoxHandle(mode);
      rect.style.cursor = cursorForBoxHandle(mode);
      renderOverlay();
      renderRegionForm();
      renderTargets();
    });
    rect.addEventListener("pointermove", (event) => {
      if (state.drawMode || state.drag) return;
      const cursor = cursorForBoxHandle(boxHandleForPoint(normalizedPoint(event), region.bbox));
      els.overlay.style.cursor = cursor;
      rect.style.cursor = cursor;
    });
    rect.addEventListener("pointerleave", () => {
      if (!state.drag) resetOverlayCursor();
    });
    els.overlay.appendChild(rect);

    if (region.region_id === state.selectedRegionId) {
      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", Math.max(4, box.x + 4));
      label.setAttribute("y", Math.max(14, box.y + 14));
      label.classList.add("box-label");
      label.textContent = region.region_type;
      els.overlay.appendChild(label);
    }
  });

  if (state.draft) {
    const box = bboxToPixels(state.draft);
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", box.x);
    rect.setAttribute("y", box.y);
    rect.setAttribute("width", box.width);
    rect.setAttribute("height", box.height);
    rect.classList.add("draft-box");
    els.overlay.appendChild(rect);
  }
}

function renderRegionForm() {
  const region = selectedRegion();
  els.emptyRegion.classList.toggle("hidden", Boolean(region));
  els.regionForm.classList.toggle("hidden", !region);

  if (!region) {
    els.mappingList.innerHTML = '<p class="empty">选中一个框后，会显示对应字段候选。</p>';
    return;
  }

  if (els.regionRoleHint) {
    els.regionRoleHint.innerHTML = `
      <strong>${escapeText(friendlyRegionType(region.region_type))}</strong>
      <p>${escapeText(friendlyRegionNote(region))}</p>
    `;
  }
  els.regionIdInput.value = region.region_id;
  els.regionIdInput.readOnly = true;
  els.regionTypeInput.value = region.region_type;
  els.regionTypeInput.readOnly = true;
  els.labelInput.value = friendlyRegionType(region.region_type);
  els.ocrInput.value = region.ocr_text;
  els.bboxX.value = region.bbox.x_center.toFixed(3);
  els.bboxY.value = region.bbox.y_center.toFixed(3);
  els.bboxW.value = region.bbox.width.toFixed(3);
  els.bboxH.value = region.bbox.height.toFixed(3);
  els.reviewActionInput.value = region.human_review.review_action || "pending";
  const note = region.human_review.notes || "";
  els.notesInput.value = /[\u4e00-\u9fff]/.test(note) ? note : friendlyRegionNote(region);
  renderMappingsV2(region);
}

function renderMappings(region) {
  els.mappingList.innerHTML = "";
  if (!region.candidate_mappings.length) {
    els.mappingList.innerHTML = '<p class="empty">当前框还没有字段映射。可以从下方候选目标字段挂接。</p>';
    return;
  }

  region.candidate_mappings.forEach((mapping, index) => {
    const item = document.createElement("div");
    item.className = "mapping-item";
    item.innerHTML = `
      <strong>${escapeText(mapping.candidate_leg_id || "procedure")} ${mapping.leg_type ? `(${escapeText(mapping.leg_type)})` : ""}.${escapeText(mapping.field_name || "")}</strong>
      <div class="muted">expected: ${escapeText(mapping.expected_value)}</div>
      <select data-index="${index}">
        <option value="pending">pending</option>
        <option value="accepted">accepted</option>
        <option value="rejected">rejected</option>
        <option value="changed">changed</option>
        <option value="needs_discussion">needs_discussion</option>
      </select>
      <button data-remove="${index}">移除映射</button>
    `;
    const select = item.querySelector("select");
    select.value = mapping.human_decision || "pending";
    select.addEventListener("change", () => {
      mapping.human_decision = select.value;
    });
    item.querySelector("button").addEventListener("click", () => {
      region.candidate_mappings.splice(index, 1);
      renderMappings(region);
    });
    els.mappingList.appendChild(item);
  });
}

function renderMappingsV2(region) {
  els.mappingList.innerHTML = "";
  if (!region.candidate_mappings.length) {
    els.mappingList.innerHTML = '<p class="empty">当前框还没有对应到任何 PR #28 字段。先在下方“候选目标字段”里找应该由这个框证明的字段，再点“挂到当前框”。</p>';
    renderCanonicalPanel();
    return;
  }

  const actions = document.createElement("div");
  actions.className = "mapping-actions";
  actions.innerHTML = `
    <button data-action="accept-all">确认下面全部对应</button>
    <button data-action="accept-next">确认本框并跳下一个</button>
    <button data-action="pending-all">全部暂不确认</button>
    <p class="hint">如果这个框确实包含下面列出的所有信息，可以一次确认；不确定时逐条确认更稳。</p>
  `;
  actions.querySelector('[data-action="accept-all"]').addEventListener("click", () => {
    acceptPendingMappings(region);
    renderRegionForm();
    renderTargets();
    renderCanonicalPanel();
  });
  actions.querySelector('[data-action="accept-next"]').addEventListener("click", acceptCurrentAndAdvance);
  actions.querySelector('[data-action="pending-all"]').addEventListener("click", () => {
    region.candidate_mappings.forEach((mapping) => {
      mapping.human_decision = "pending";
    });
    renderRegionForm();
    renderTargets();
    renderCanonicalPanel();
  });
  els.mappingList.appendChild(actions);

  region.candidate_mappings.forEach((mapping, index) => {
    const item = document.createElement("div");
    const decision = mapping.human_decision || "pending";
    const decisionLabel = {
      accepted: "已确认",
      rejected: "不属于此框",
      pending: "待确认",
      changed: "需改值",
      needs_discussion: "不确定"
    }[decision] || decision;
    item.className = `mapping-item decision-${decision}`;
    const canonicalAnswer = mapping.human_answer || canonicalFieldForMapping(mapping);
    item.innerHTML = `
      <div class="mapping-head">
        <strong>${escapeText(friendlyLegName(mapping))}</strong>
        <span>${escapeText(decisionLabel)}</span>
      </div>
      <div><b>字段：</b>${escapeText(friendlyFieldName(mapping.field_name))}</div>
      <div><b>应看到：</b>${escapeText(friendlyAnswerValue(canonicalAnswer, mapping.expected_value))}</div>
      <div class="mapping-actions mapping-actions-compact">
        <button data-decision="accepted">确认对应</button>
        <button data-decision="rejected">不属于此框</button>
        <button data-decision="needs_discussion">不确定</button>
        <button data-remove="${index}">移除</button>
      </div>
    `;
    item.querySelectorAll("[data-decision]").forEach((button) => {
      button.addEventListener("click", () => {
        mapping.human_decision = button.dataset.decision;
        renderMappingsV2(region);
        renderTargets();
        renderCanonicalPanel();
      });
    });
    item.querySelector("[data-remove]").addEventListener("click", () => {
      region.candidate_mappings.splice(index, 1);
      renderMappingsV2(region);
      renderTargets();
      renderCanonicalPanel();
    });
    els.mappingList.appendChild(item);
  });
  renderCanonicalPanel();
}

function renderCanonicalPanel() {
  if (!els.canonicalSummary || !els.canonicalCompare) return;
  const canonical = state.current?.canonical_gt;
  if (!canonical) {
    els.canonicalSummary.innerHTML = '<p class="empty">当前航图没有 CIFP canonical JSON，无法做 PR #28 对比。</p>';
    els.canonicalCompare.innerHTML = "";
    if (els.workflowSummary) els.workflowSummary.innerHTML = '<p class="empty">当前航图没有可对齐的 canonical JSON。</p>';
    if (els.workflowNextList) els.workflowNextList.innerHTML = "";
    if (els.annotationJsonPreview) els.annotationJsonPreview.textContent = "";
    if (els.canonicalJsonPreview) els.canonicalJsonPreview.textContent = "";
    return;
  }

  const predicted = buildAnnotationCanonicalJson();
  const comparison = compareCanonicalJson(predicted, canonical);
  const acceptedCount = state.regions.reduce(
    (sum, item) => sum + (item.candidate_mappings || []).filter((mapping) => mapping.human_decision === "accepted").length,
    0
  );
  const pendingCount = state.regions.reduce(
    (sum, item) => sum + (item.candidate_mappings || []).filter((mapping) => !mapping.human_decision || mapping.human_decision === "pending").length,
    0
  );
  const allAttentionRows = comparison.rows
    .filter((row) => row.requiresBoxEvidence && !row.match)
    .sort((left, right) => Number(left.covered) - Number(right.covered));
  renderWorkflowPanel(comparison, pendingCount, allAttentionRows);
  const attentionRows = allAttentionRows.slice(0, 12);

  els.canonicalSummary.innerHTML = `
    <div class="score-grid">
      <div><strong>${comparison.present_matched}/${comparison.present_total}</strong><span>present 证据对齐</span></div>
      <div><strong>${Math.round(comparison.present_coverage * 100)}%</strong><span>present 证据覆盖</span></div>
      <div><strong>${comparison.matched}/${comparison.total}</strong><span>完整 JSON 对齐</span></div>
      <div><strong>${comparison.auto_status_total}</strong><span>自动状态字段</span></div>
      <div><strong>${acceptedCount}</strong><span>accepted 映射</span></div>
      <div><strong>${pendingCount}</strong><span>pending 映射</span></div>
    </div>
    <p class="hint">这里是与 424 canonical 目标的证据对齐视图，不是独立模型抽取正确率；日常操作优先看“简化操作区”。</p>
  `;

  els.canonicalCompare.innerHTML = "";
  const taskTitle = document.createElement("div");
  taskTitle.className = "compare-section-title";
  taskTitle.textContent = attentionRows.length
    ? "优先检查：未覆盖或不对齐的 present 字段"
    : "present 字段已全部有证据对齐";
  els.canonicalCompare.appendChild(taskTitle);

  attentionRows.forEach((row) => {
    const item = document.createElement("div");
    item.className = `compare-row ${row.match ? "match" : row.covered ? "mismatch" : "missing"}`;
    item.innerHTML = `
      <strong>${escapeText(row.key)}</strong>
      <span>${row.match ? "match" : row.covered ? "mismatch" : "missing"}</span>
      <small>人工：${escapeText(formatAnswer(row.predicted))}</small>
      <small>CIFP：${escapeText(formatAnswer(row.answer))}</small>
    `;
    item.title = `人工: ${JSON.stringify(row.predicted)}\nCIFP: ${JSON.stringify(row.answer)}`;
    els.canonicalCompare.appendChild(item);
  });

  const allTitle = document.createElement("div");
  allTitle.className = "compare-section-title";
  allTitle.textContent = "完整字段对比预览";
  els.canonicalCompare.appendChild(allTitle);

  comparison.rows.slice(0, 24).forEach((row) => {
    const item = document.createElement("div");
    item.className = `compare-row ${row.match ? "match" : row.covered ? "mismatch" : "missing"} ${row.autoStatusField ? "auto-status" : ""}`;
    item.innerHTML = `
      <strong>${escapeText(row.key)}</strong>
      <span>${row.autoStatusField && row.match ? "无需画框 · match" : row.match ? "match" : row.covered ? "mismatch" : "missing"}</span>
    `;
    item.title = `人工: ${JSON.stringify(row.predicted)}\nCIFP: ${JSON.stringify(row.answer)}`;
    els.canonicalCompare.appendChild(item);
  });

  const more = document.createElement("p");
  more.className = "hint";
  more.textContent = "完整内容见下方两个 JSON 预览；保存时会把人工框生成 JSON 和 PR #28 证据对齐摘要一起写入标注文件。";
  els.canonicalCompare.appendChild(more);

  if (els.annotationJsonPreview) {
    els.annotationJsonPreview.textContent = JSON.stringify(predicted, null, 2);
  }
  if (els.canonicalJsonPreview) {
    els.canonicalJsonPreview.textContent = JSON.stringify(canonical, null, 2);
  }
}

function targetFieldButton(target, leg, field) {
  const item = document.createElement("div");
  item.className = "target-item";
  const legId = leg?.candidate_leg_id || "procedure";
  const legType = leg?.leg_type || "";
  const fieldName = field.field_name || field.name;
  const expectedValue = field.expected_value ?? field.value ?? "";
  const answer = field.expected_answer || null;
  const region = selectedRegion();
  const alreadyLinked = Boolean(region?.candidate_mappings?.some((mapping) => {
    return mapping.candidate_leg_id === legId && mapping.field_name === fieldName;
  }));
  item.innerHTML = `
    <strong>${escapeText(friendlyFieldName(fieldName))}</strong>
    <div class="muted">${escapeText(friendlyLegName({ candidate_leg_id: legId, canonical_leg_index: leg?.canonical_leg_index, leg_type: legType }))}</div>
    <div><b>应在图上找到：</b>${escapeText(friendlyAnswerValue(answer, expectedValue))}</div>
    <div class="target-actions">
      ${alreadyLinked
        ? '<button data-action="accept-existing">已挂，直接确认</button><button data-action="unlink-existing">取消挂接</button>'
        : '<button data-action="link">挂到当前框</button><button data-action="link-accept">挂并确认</button>'
      }
    </div>
  `;
  item.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => {
    const activeRegion = selectedRegion();
    if (!activeRegion) {
      showToast("先选中或新增一个框，再挂字段。");
      return;
    }
    if (button.dataset.action === "accept-existing") {
      (activeRegion.candidate_mappings || []).forEach((mapping) => {
        if (mapping.candidate_leg_id === legId && mapping.field_name === fieldName) {
          mapping.human_decision = "accepted";
        }
      });
      activeRegion.human_review.review_action = "accept";
      renderMappingsV2(activeRegion);
      renderTargets();
      renderCanonicalPanel();
      showToast("已确认当前框里的这个字段。");
      return;
    }
    if (button.dataset.action === "unlink-existing") {
      activeRegion.candidate_mappings = (activeRegion.candidate_mappings || []).filter((mapping) => {
        return !(mapping.candidate_leg_id === legId && mapping.field_name === fieldName);
      });
      renderMappingsV2(activeRegion);
      renderTargets();
      renderCanonicalPanel();
      showToast("已取消当前框和这个字段的挂接。");
      return;
    }
    const shouldAccept = button.dataset.action === "link-accept";
    activeRegion.candidate_mappings.push({
      candidate_leg_id: leg?.candidate_leg_id || "",
      canonical_leg_index: leg?.canonical_leg_index || null,
      leg_type: leg?.leg_type || "",
      field_name: fieldName,
      expected_value: expectedValue,
      expected_answer: field.expected_answer || null,
      match_basis: "human-added from target panel",
      confidence: null,
      human_decision: shouldAccept ? "accepted" : "pending",
      human_notes: ""
    });
    if (shouldAccept) activeRegion.human_review.review_action = "accept";
    renderMappingsV2(activeRegion);
    renderTargets();
    renderCanonicalPanel();
    showToast(shouldAccept ? "已挂到当前框并确认。" : "已加入当前框的候选映射。");
  }));
  return item;
}

function renderTargets() {
  const target = state.current?.target;
  els.targetList.innerHTML = "";
  if (!target) {
    els.targetList.innerHTML = '<p class="empty">当前样本没有 target 文件记录。</p>';
    return;
  }

  const summary = document.createElement("div");
  summary.className = "target-item";
  summary.innerHTML = `
    <strong>当前航图的 424 复飞候选</strong>
    <div class="muted">主 transition：${escapeText(target.main_transition_candidate || "")}；候选复飞航段：${escapeText(target.candidate_missed_approach_leg_count || 0)} 个</div>
    <p class="hint">下面默认只列出需要人工框确认的 present 字段；本航图没有的字段放在“无需画框字段”里自动处理。</p>
    ${target.anomaly_note ? `<div class="badge hot">${escapeText(target.anomaly_note)}</div>` : ""}
  `;
  els.targetList.appendChild(summary);

  (target.candidate_legs || []).forEach((leg) => {
    const fields = leg.target_fields || [];
    const visualFields = fields.filter((field) => {
      return field.field_name !== "Q_terminator" && field.expected_answer?.status === "present";
    });
    const openVisualFields = visualFields.filter((field) => !fieldAcceptedForLeg(leg, field));
    const completedVisualFields = visualFields.filter((field) => fieldAcceptedForLeg(leg, field));
    const autoFields = fields.filter((field) => !visualFields.includes(field));
    const title = document.createElement("div");
    title.className = "target-leg";
    title.textContent = `${friendlyLegName(leg)} · 待处理 ${openVisualFields.length} 项 / 已完成 ${completedVisualFields.length} 项`;
    els.targetList.appendChild(title);
    if (!openVisualFields.length) {
      const empty = document.createElement("p");
      empty.className = "empty compact-empty";
      empty.textContent = visualFields.length
        ? "这个航段的可视字段已经确认完成。"
        : "这个航段没有需要单独画框确认的可视字段。";
      els.targetList.appendChild(empty);
    }
    openVisualFields.forEach((field) => {
      els.targetList.appendChild(targetFieldButton(target, leg, field));
    });
    if (completedVisualFields.length) {
      const details = document.createElement("details");
      details.className = "auto-fields completed-fields";
      details.innerHTML = `<summary>已完成字段 ${completedVisualFields.length} 项</summary>`;
      completedVisualFields.forEach((field) => {
        const row = document.createElement("div");
        row.className = "auto-field-row";
        row.innerHTML = `
          <strong>${escapeText(friendlyFieldName(field.field_name || field.name))}</strong>
          <span>${escapeText(friendlyAnswerValue(field.expected_answer, field.expected_value || ""))}</span>
        `;
        details.appendChild(row);
      });
      els.targetList.appendChild(details);
    }
    if (autoFields.length) {
      const details = document.createElement("details");
      details.className = "auto-fields";
      details.innerHTML = `<summary>无需画框字段 / 自动状态 ${autoFields.length} 项</summary>`;
      autoFields.forEach((field) => {
        const answer = field.expected_answer || null;
        const row = document.createElement("div");
        row.className = "auto-field-row";
        row.innerHTML = `
          <strong>${escapeText(friendlyFieldName(field.field_name || field.name))}</strong>
          <span>${escapeText(friendlyAnswerValue(answer, field.expected_value || ""))}</span>
        `;
        details.appendChild(row);
      });
      els.targetList.appendChild(details);
    }
  });
}

function updateSelectedFromForm() {
  const region = selectedRegion();
  if (!region) return;
  region.region_id = els.regionIdInput.value.trim() || region.region_id;
  state.selectedRegionId = region.region_id;
  region.region_type = els.regionTypeInput.value.trim() || "MISSED_APPROACH_TEXT";
  const meta = metaForRegionType(region.region_type);
  region.annotation_scope = meta.annotation_scope || region.annotation_scope;
  region.element_role = meta.element_role || region.element_role;
  region.source_field_name = meta.source_field_name;
  region.label = els.labelInput.value;
  region.ocr_text = els.ocrInput.value;
  region.bbox.x_center = clamp(Number(els.bboxX.value));
  region.bbox.y_center = clamp(Number(els.bboxY.value));
  region.bbox.width = clamp(Number(els.bboxW.value), 0.001, 1);
  region.bbox.height = clamp(Number(els.bboxH.value), 0.001, 1);
  region.human_review.review_action = els.reviewActionInput.value;
  region.human_review.notes = els.notesInput.value;
  renderOverlay();
}

function addRegion(type, bbox) {
  if (!state.current) {
    showToast("请先选择一张航图。");
    return;
  }
  const meta = metaForRegionType(type);
  const region = normalizeRegion({
    region_id: makeRegionId(state.current.manifest.chart_id, state.regions.length),
    region_type: type,
    bbox,
    label: meta.label,
    annotation_scope: meta.annotation_scope,
    element_role: meta.element_role,
    source_field_name: meta.source_field_name,
    candidate_mappings: [],
    human_review: { review_action: "pending" }
  }, state.regions.length);
  state.regions.push(region);
  state.selectedRegionId = region.region_id;
  renderOverlay();
  renderRegionForm();
  renderTargets();
}

function buildAnnotationPayload(mode = "final") {
  const chartId = state.current.manifest.chart_id;
  const annotationPr28 = buildAnnotationCanonicalJson();
  const comparison = state.current.canonical_gt
    ? compareCanonicalJson(annotationPr28, state.current.canonical_gt)
    : null;
  const reviewStatus = mode === "draft" ? "draft_saved" : "pilot_reviewed";
  return {
    chart_id: chartId,
    dataset_key: state.current?.dataset?.key || datasetKey,
    dataset_label: state.current?.dataset?.label || datasetConfig.label,
    image_path: state.current.manifest.image_file || "",
    annotator: currentAnnotator() || (datasetConfig.finalDataset ? "" : "practice_user"),
    review_status: reviewStatus,
    save_mode: mode,
    source_prelabel_file: `prelabels/${chartId}.json`,
    canonical_targets_file: "targets/canonical_targets.json",
    canonical_proxy_gt_combined_file: "targets/canonical_proxy_gt_combined.json",
    canonical_proxy_gt_file: state.current.target?.canonical_proxy_gt_file || `targets/canonical_proxy_gt/${chartId}.json`,
    regions: state.regions.map((region) => {
      const accepted = region.candidate_mappings.filter((mapping) => mapping.human_decision === "accepted");
      const rejected = region.candidate_mappings.filter((mapping) => mapping.human_decision === "rejected");
      return {
        final_region_id: region.region_id,
        source_region_id: region.source_region_id || region.region_id,
        region_type: region.region_type,
        bbox: region.bbox,
        label: region.label,
        ocr_text: region.ocr_text,
        annotation_scope: region.annotation_scope || "",
        element_role: region.element_role || "",
        expected_visual_value: region.expected_visual_value || "",
        step_id: region.step_id || "",
        parent_step_region_id: region.parent_step_region_id || "",
        source_candidate_leg_id: region.source_candidate_leg_id || "",
        source_leg_type: region.source_leg_type || "",
        source_field_name: region.source_field_name || "",
        is_formal_annotation_candidate: region.is_formal_annotation_candidate || false,
        accepted_mappings: accepted.map((mapping) => ({
          candidate_leg_id: mapping.candidate_leg_id || "",
          canonical_leg_index: canonicalLegIndexForMapping(mapping),
          leg_type: mapping.leg_type || "",
          field_name: mapping.field_name || "",
          final_value: mapping.expected_value ?? null,
          canonical_answer: mapping.human_answer || canonicalFieldForMapping(mapping) || null,
          evidence_role: "supports_field",
          human_confidence: "medium",
          notes: mapping.human_notes || mapping.match_basis || ""
        })),
        rejected_mappings: rejected.map((mapping) => ({
          candidate_leg_id: mapping.candidate_leg_id || "",
          leg_type: mapping.leg_type || "",
          field_name: mapping.field_name || "",
          reason: mapping.human_notes || "rejected during platform review"
        })),
        candidate_mappings_reviewed: region.candidate_mappings,
        review_action: region.human_review.review_action || "pending",
        needs_discussion: region.candidate_mappings.some((mapping) => mapping.human_decision === "needs_discussion"),
        notes: region.human_review.notes || ""
      };
    }),
    unresolved_targets: [],
    annotation_pr28_json: annotationPr28,
    canonical_gt_file: state.current.target?.canonical_proxy_gt_file || `targets/canonical_proxy_gt/${chartId}.json`,
    pr28_comparison_summary: comparison
      ? {
          metric_scope: "manual_evidence_alignment_against_cifp424_canonical_not_independent_extraction_accuracy",
          canonical_answer_source: "CIFP/424 canonical target",
          total: comparison.total,
          matched: comparison.matched,
          covered: comparison.covered,
          present_total: comparison.present_total,
          present_matched: comparison.present_matched,
          present_covered: comparison.present_covered,
          auto_status_total: comparison.auto_status_total,
          full_alignment_rate: comparison.full_alignment_rate,
          overall_evidence_coverage: comparison.overall_evidence_coverage,
          present_alignment_rate: comparison.present_alignment_rate,
          present_evidence_coverage: comparison.present_coverage
        }
      : null,
    sample_notes: mode === "draft"
      ? "Draft saved from local annotation platform."
      : "Saved from local annotation platform."
  };
}

async function saveCurrentWork(mode = "final") {
  if (!state.current) {
    showToast("请先选择一张航图。");
    return;
  }
  updateSelectedFromForm();
  const chartId = state.current.manifest.chart_id;
  if (datasetConfig.finalDataset && !currentAnnotator()) {
    showToast("正式标注必须先填写标注人，否则保存会和别人混在一起。");
    els.annotatorInput?.focus();
    return;
  }
  if (datasetConfig.finalDataset) {
    const claimedBy = state.current.manifest.claimed_by || "";
    const claimStatus = state.current.manifest.claim_status || "unassigned";
    if (claimedBy !== currentAnnotator() || !["claimed", "claimed_by_me", "submitted"].includes(claimStatus)) {
      showToast("请先在左栏点击这张图的“领取”，领取成功后再保存。");
      updateClaimButton();
      return;
    }
  }

  const payload = buildAnnotationPayload(mode);
  const endpoint = mode === "draft"
    ? `/api/drafts/${encodeURIComponent(chartId)}`
    : `/api/annotations/${encodeURIComponent(chartId)}`;
  const result = await postJson(apiUrl(endpoint), payload);
  const chart = state.charts.find((item) => item.chart_id === chartId);

  if (mode === "draft") {
    showToast("\u5df2\u6682\u5b58\u3002");
    state.current.draft = payload;
    if (chart) {
      chart.has_my_draft = true;
      chart.draft_saved_at = payload.saved_at || new Date().toISOString();
    }
  } else {
    showToast("\u5df2\u4fdd\u5b58\u3002");
    if (datasetConfig.finalDataset) {
      state.current.manifest.claim_status = "submitted";
      state.current.manifest.claimed_by = currentAnnotator();
    }
    state.current.annotation = payload;
    if (chart) {
      chart.has_my_annotation = true;
      chart.claim_status = datasetConfig.finalDataset ? "submitted" : "practice";
      chart.claimed_by = currentAnnotator();
      chart.submission_count = Number(chart.submission_count || 0) + 1;
    }
  }

  updateClaimButton();
  renderChartList();
}

async function saveDraft() {
  return saveCurrentWork("draft");
}

async function saveAnnotation() {
  return saveCurrentWork("final");
}

function ensureSaveButtons() {
  if (!els.saveDraftBtn && els.saveBtn?.parentElement) {
    const button = document.createElement("button");
    button.id = "saveDraftBtn";
    button.type = "button";
    button.textContent = "暂存";
    els.saveBtn.parentElement.insertBefore(button, els.saveBtn);
    els.saveDraftBtn = button;
  }

  if (!els.workflowDraftBtn && els.workflowSaveBtn?.parentElement) {
    const button = document.createElement("button");
    button.id = "workflowDraftBtn";
    button.type = "button";
    button.textContent = "暂存当前检查状态";
    els.workflowSaveBtn.parentElement.insertBefore(button, els.workflowSaveBtn);
    els.workflowDraftBtn = button;
  }
}

function bindEvents() {
  els.chartFilter.addEventListener("input", renderChartList);
  els.annotatorInput?.addEventListener("input", () => {
    localStorage.setItem(datasetConfig.storageKey, currentAnnotator());
  });
  els.annotatorInput?.addEventListener("change", () => {
    state.current = null;
    state.regions = [];
    state.selectedRegionId = null;
    if (els.currentTitle) els.currentTitle.textContent = "请选择航图";
    if (els.currentMeta) els.currentMeta.textContent = "";
    renderOverlay();
    renderRegionForm();
    renderTargets();
    renderCanonicalPanel();
    updateClaimButton();
    refreshCharts().catch((error) => showToast(error.message));
  });
  if (els.newRegionType) {
    els.newRegionType.addEventListener("change", updateNewRegionTypeHint);
  }
  [
    ["left", els.leftZoomOut, -1],
    ["left", els.leftZoomIn, 1],
    ["center", els.centerZoomOut, -1],
    ["center", els.centerZoomIn, 1],
    ["right", els.rightZoomOut, -1],
    ["right", els.rightZoomIn, 1],
    ["workflow", els.workflowZoomOut, -1],
    ["workflow", els.workflowZoomIn, 1]
  ].forEach(([area, button, direction]) => {
    if (button) button.addEventListener("click", () => adjustPanelZoom(area, direction));
  });
  [
    ["left", els.leftZoomReset],
    ["center", els.centerZoomReset],
    ["right", els.rightZoomReset],
    ["workflow", els.workflowZoomReset]
  ].forEach(([area, button]) => {
    if (button) button.addEventListener("click", () => resetPanelZoom(area));
  });
  bindCtrlWheelZoom();
  els.resizeHandles.forEach((handle) => handle.addEventListener("pointerdown", beginColumnResize));
  window.addEventListener("pointermove", updateColumnResize);
  els.helpBtn?.addEventListener("click", openHelp);
  els.helpCloseBtn?.addEventListener("click", closeHelp);
  els.fullTutorialBtn?.addEventListener("click", () => {
    window.open("/tutorial/", "_blank", "noopener");
  });
  els.detailBoxTutorialBtn?.addEventListener("click", () => {
    window.open("/detail-box-tutorial/", "_blank", "noopener");
  });
  els.helpOverlay?.addEventListener("click", (event) => {
    if (event.target === els.helpOverlay) closeHelp();
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !els.helpOverlay?.classList.contains("hidden")) {
      closeHelp();
    }
  });
  els.drawBtn.addEventListener("click", () => {
    state.drawMode = !state.drawMode;
    els.drawBtn.classList.toggle("primary", state.drawMode);
    resetOverlayCursor();
    els.drawBtn.textContent = state.drawMode ? "正在框选" : "框选新增";
  });
  els.saveDraftBtn?.addEventListener("click", () => saveDraft().catch((error) => showToast(error.message)));
  els.saveBtn.addEventListener("click", () => saveAnnotation().catch((error) => showToast(error.message)));
  els.workflowDraftBtn?.addEventListener("click", () => saveDraft().catch((error) => showToast(error.message)));
  els.workflowSaveBtn?.addEventListener("click", () => saveAnnotation().catch((error) => showToast(error.message)));
  els.quickAcceptBtn?.addEventListener("click", acceptAllChartPendingMappings);
  els.undoQuickAcceptBtn?.addEventListener("click", undoQuickAccept);
  els.nextPendingBtn?.addEventListener("click", () => {
    const nextRegionId = findNextPendingRegionId();
    if (nextRegionId) {
      selectRegionById(nextRegionId);
      showToast("已跳到下一个待确认框。");
    } else {
      showToast("没有待确认框了，可以检查缺证字段或保存。");
    }
  });
  els.openTargetsBtn?.addEventListener("click", openTargetPanel);
  els.acceptFrameAndNextBtn?.addEventListener("click", acceptCurrentAndAdvance);
  els.markFrameUnsureBtn?.addEventListener("click", markCurrentFrameUnsure);
  els.deleteRegionBtn.addEventListener("click", () => {
    state.regions = state.regions.filter((region) => region.region_id !== state.selectedRegionId);
    state.selectedRegionId = state.regions[0]?.region_id || null;
    renderOverlay();
    renderRegionForm();
    renderTargets();
    renderCanonicalPanel();
  });

  [
    els.regionIdInput,
    els.regionTypeInput,
    els.labelInput,
    els.ocrInput,
    els.bboxX,
    els.bboxY,
    els.bboxW,
    els.bboxH,
    els.reviewActionInput,
    els.notesInput
  ].forEach((input) => input.addEventListener("input", updateSelectedFromForm));

  els.overlay.addEventListener("pointerdown", (event) => {
    if (!state.drawMode || !state.current) return;
    const point = normalizedPoint(event);
    state.draft = {
      x_center: point.x,
      y_center: point.y,
      width: 0.001,
      height: 0.001,
      startX: point.x,
      startY: point.y
    };
    renderOverlay();
  });

  els.overlay.addEventListener("pointermove", (event) => {
    if (state.draft) {
      const point = normalizedPoint(event);
      const x1 = state.draft.startX;
      const y1 = state.draft.startY;
      state.draft.x_center = (x1 + point.x) / 2;
      state.draft.y_center = (y1 + point.y) / 2;
      state.draft.width = Math.abs(point.x - x1);
      state.draft.height = Math.abs(point.y - y1);
      renderOverlay();
      return;
    }

    if (state.drag?.type === "region-box") {
      const point = normalizedPoint(event);
      if (updateDraggedRegionBox(point)) {
        els.overlay.style.cursor = cursorForBoxHandle(state.drag.mode);
        renderOverlay();
        renderRegionForm();
      }
    }
  });

  window.addEventListener("pointerup", () => {
    endColumnResize();
    const finishedBoxDrag = state.drag?.type === "region-box";
    if (state.draft) {
      const draft = state.draft;
      state.draft = null;
      if (draft.width > 0.01 && draft.height > 0.01) {
        addRegion(els.newRegionType.value, {
          x_center: draft.x_center,
          y_center: draft.y_center,
          width: draft.width,
          height: draft.height
        });
      } else {
        renderOverlay();
      }
    }
    state.drag = null;
    resetOverlayCursor();
    if (finishedBoxDrag) {
      renderOverlay();
      renderRegionForm();
    }
  });

  window.addEventListener("resize", renderOverlay);
  if ("ResizeObserver" in window) {
    const imageResizeObserver = new ResizeObserver(() => renderOverlay());
    imageResizeObserver.observe(els.chartImage);
  }
}

function setupDatasetUi() {
  ensureSaveButtons();
  document.title = `${datasetConfig.label} - Missed Approach 标注校准平台`;
  if (els.pageTitle) {
    els.pageTitle.textContent = `${datasetConfig.label} · 自动预标注校准平台`;
  }
  if (els.datasetEyebrow) {
    els.datasetEyebrow.textContent = datasetConfig.finalDataset
      ? "FAA Missed Approach Formal 300"
      : "FAA Missed Approach Practice 10";
  }
  if (els.sideTitle) {
    els.sideTitle.textContent = datasetConfig.finalDataset ? "300 张正式航图" : "10 张练习航图";
  }
  const storedAnnotator = localStorage.getItem(datasetConfig.storageKey) || "";
  if (els.annotatorInput && !els.annotatorInput.value) {
    els.annotatorInput.value = storedAnnotator;
    els.annotatorInput.placeholder = datasetConfig.finalDataset ? "标注人（正式必填）" : "标注人（练习可选）";
  }
}

async function refreshCharts() {
  const data = await getJson(apiUrl("/api/charts"));
  state.dataset = data.dataset || datasetConfig;
  state.charts = data.charts || [];
  renderChartList();
}

function firstOpenableChart() {
  if (!state.charts.length) return null;
  if (!datasetConfig.finalDataset) return state.charts[0];
  return state.charts.find((chart) => chart.claim_status === "claimed" || chart.claim_status === "submitted")
    || state.charts.find((chart) => chart.claim_status === "unassigned")
    || null;
}

async function init() {
  setupDatasetUi();
  bindEvents();
  updateNewRegionTypeHint();
  updateClaimButton();
  applyZooms({ render: false });
  await refreshCharts();
  const first = firstOpenableChart();
  if (first && (!datasetConfig.finalDataset || currentAnnotator())) {
    await loadChart(first.chart_id);
  } else if (datasetConfig.finalDataset) {
    showToast("正式标注请先填写标注人，然后从左侧选择未领取航图。");
  }
}

init().catch((error) => showToast(error.message));
