const http = require("http");
const fs = require("fs/promises");
const fss = require("fs");
const os = require("os");
const path = require("path");
const { URL } = require("url");

const workspaceRoot = path.resolve(__dirname, "..");
const publicRoot = path.resolve(__dirname, "public");
const port = Number(process.env.PORT || 8787);

const datasets = {
  practice10: {
    key: "practice10",
    label: "练习集 10 张",
    finalDataset: false,
    root: path.join(workspaceRoot, "datasets", "practice10"),
    urlPath: "/practice/"
  },
  formal300: {
    key: "formal300",
    label: "正式集 300 张",
    finalDataset: true,
    root: path.join(workspaceRoot, "datasets", "formal300"),
    urlPath: "/formal/"
  }
};

const jsonHeaders = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store"
};

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml; charset=utf-8"
};

let claimQueue = Promise.resolve();

function safeJoin(root, ...parts) {
  const resolvedRoot = path.resolve(root);
  const target = path.resolve(root, ...parts);
  const rootWithSep = resolvedRoot.endsWith(path.sep) ? resolvedRoot : resolvedRoot + path.sep;
  if (target !== resolvedRoot && !target.startsWith(rootWithSep)) {
    throw new Error(`Unsafe path outside root: ${target}`);
  }
  return target;
}

function stripBom(text) {
  return text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
}

function datasetFromRequest(requestUrl, pathname) {
  const requested = requestUrl.searchParams.get("dataset");
  if (datasets[requested]) return datasets[requested];
  if (pathname.startsWith("/practice")) return datasets.practice10;
  if (pathname.startsWith("/formal")) return datasets.formal300;
  return datasets.formal300;
}

function isSafeChartId(chartId) {
  return /^[A-Za-z0-9_.-]+$/.test(chartId || "");
}

function imageBasename(imagePath) {
  return String(imagePath || "").split(/[\\/]/).pop();
}

function scrubClientValue(value) {
  if (Array.isArray(value)) return value.map(scrubClientValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, scrubClientValue(item)]));
  }
  if (typeof value !== "string") return value;
  if (/^[A-Za-z]:[\\/]/.test(value)) return imageBasename(value);
  return value;
}

function safeAnnotator(value) {
  const cleaned = String(value || "")
    .trim()
    .replace(/[<>:"/\\|?*\x00-\x1F]/g, "_")
    .replace(/\s+/g, "_");
  return cleaned || "";
}

function getAnnotator(requestUrl) {
  return safeAnnotator(requestUrl.searchParams.get("annotator") || "");
}

function timestampForFile() {
  return new Date().toISOString().replace(/[:.]/g, "-");
}

function clientIp(req) {
  const forwarded = req.headers["x-forwarded-for"];
  if (forwarded) return String(forwarded).split(",")[0].trim();
  return req.socket.remoteAddress || "";
}

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function readJsonFile(filePath, fallback = null) {
  try {
    return JSON.parse(stripBom(await fs.readFile(filePath, "utf8")));
  } catch (error) {
    if (error.code === "ENOENT") return fallback;
    throw error;
  }
}

async function readDatasetJson(dataset, relativePath, fallback = null) {
  return readJsonFile(safeJoin(dataset.root, relativePath), fallback);
}

async function readAnnotatorJson(dataset, annotator, relativePath, fallback = null) {
  if (!annotator) return fallback;
  return readDatasetJson(dataset, safeJoin("annotations", relativePath, annotator), fallback);
}

async function writeJsonFileAtomic(filePath, value) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const tmpPath = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  await fs.writeFile(tmpPath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  await fs.rename(tmpPath, filePath);
}

function withClaimLock(fn) {
  const run = claimQueue.then(fn, fn);
  claimQueue = run.catch(() => {});
  return run;
}

async function readClaims(dataset) {
  if (!dataset.finalDataset) return {};
  return readDatasetJson(dataset, "annotations/claims.json", {});
}

async function writeClaims(dataset, claims) {
  if (!dataset.finalDataset) return;
  await writeJsonFileAtomic(safeJoin(dataset.root, "annotations", "claims.json"), claims);
}

async function claimChart(dataset, chartId, annotator) {
  if (!dataset.finalDataset) return null;
  if (!annotator) {
    const error = new Error("正式标注请先填写标注人，再领取航图。");
    error.statusCode = 400;
    throw error;
  }
  return withClaimLock(async () => {
    const claims = await readClaims(dataset);
    const existing = claims[chartId];
    if (existing?.annotator && existing.annotator !== annotator) {
      const error = new Error(`这张图已由 ${existing.annotator} 领取，请换一张未领取的图，避免重复标注。`);
      error.statusCode = 409;
      error.claim = existing;
      throw error;
    }
    const now = new Date().toISOString();
    claims[chartId] = {
      chart_id: chartId,
      annotator,
      status: existing?.status === "submitted" ? "submitted" : "claimed",
      claimed_at: existing?.claimed_at || now,
      last_opened_at: now,
      last_saved_at: existing?.last_saved_at || ""
    };
    await writeClaims(dataset, claims);
    return claims[chartId];
  });
}

async function markSubmitted(dataset, chartId, annotator) {
  if (!dataset.finalDataset) return null;
  return withClaimLock(async () => {
    const claims = await readClaims(dataset);
    const now = new Date().toISOString();
    claims[chartId] = {
      ...(claims[chartId] || {}),
      chart_id: chartId,
      annotator,
      status: "submitted",
      last_saved_at: now
    };
    if (!claims[chartId].claimed_at) claims[chartId].claimed_at = now;
    await writeClaims(dataset, claims);
    return claims[chartId];
  });
}

async function submissionCount(dataset, chartId) {
  const folder = safeJoin(dataset.root, "annotations", "submissions", chartId);
  try {
    const entries = await fs.readdir(folder);
    return entries.filter((name) => name.toLowerCase().endsWith(".json")).length;
  } catch (error) {
    if (error.code === "ENOENT") return 0;
    throw error;
  }
}

async function loadCharts(dataset, annotator) {
  const manifest = await readDatasetJson(dataset, "manifest.json", []);
  const targets = await readDatasetJson(dataset, "targets/canonical_targets.json", []);
  const targetById = new Map(targets.map((item) => [item.chart_id, item]));
  const claims = await readClaims(dataset);

  return Promise.all(manifest.map(async (item) => {
    const chartId = item.chart_id;
    const target = targetById.get(chartId) || {};
    const prelabelPath = safeJoin(dataset.root, "prelabels", `${chartId}.json`);
    const claim = claims[chartId] || null;
    const mine = Boolean(annotator && claim?.annotator === annotator);
    const claimStatus = !dataset.finalDataset
      ? "practice"
      : !claim
        ? "unassigned"
        : mine
          ? claim.status || "claimed_by_me"
          : "claimed_by_other";
    const myAnnotationPath = annotator
      ? safeJoin(dataset.root, "annotations", "by_annotator", annotator, `${chartId}.json`)
      : "";
    const myDraftPath = annotator
      ? safeJoin(dataset.root, "annotations", "drafts", "by_annotator", annotator, `${chartId}.json`)
      : "";
    const draft = myDraftPath ? await readJsonFile(myDraftPath, null) : null;
    return scrubClientValue({
      ...item,
      dataset_key: dataset.key,
      final_dataset: dataset.finalDataset,
      image_file: imageBasename(item.image_file || item.image_path),
      has_prelabel: await fileExists(prelabelPath),
      has_my_annotation: myAnnotationPath ? await fileExists(myAnnotationPath) : false,
      has_my_draft: Boolean(draft),
      draft_saved_at: draft?.saved_at || draft?.updated_at || "",
      submission_count: await submissionCount(dataset, chartId),
      claim_status: claimStatus,
      claimed_by: claim?.annotator || "",
      claimed_at: claim?.claimed_at || "",
      last_saved_at: claim?.last_saved_at || "",
      target_leg_count: target.candidate_missed_approach_leg_count || 0,
      review_priority: item.needs_priority_review || item.sample_type === "anomaly" ? "high" : "normal"
    });
  }));
}

async function loadChartDetail(dataset, chartId, annotator) {
  if (!isSafeChartId(chartId)) {
    const error = new Error("Invalid chart_id");
    error.statusCode = 400;
    throw error;
  }

  const charts = await loadCharts(dataset, annotator);
  const manifestItem = charts.find((item) => item.chart_id === chartId);
  if (!manifestItem) {
    const error = new Error(`Unknown chart_id: ${chartId}`);
    error.statusCode = 404;
    throw error;
  }

  const claims = await readClaims(dataset);
  const claim = claims[chartId] || null;
  const targets = await readDatasetJson(dataset, "targets/canonical_targets.json", []);
  const target = targets.find((item) => item.chart_id === chartId) || null;
  const prelabel = await readDatasetJson(dataset, `prelabels/${chartId}.json`, null);
  const canonicalGt = await readDatasetJson(dataset, `targets/canonical_proxy_gt/${chartId}.json`, null);
  const annotation = annotator
    ? await readDatasetJson(dataset, `annotations/by_annotator/${annotator}/${chartId}.json`, null)
    : null;
  const draft = annotator
    ? await readDatasetJson(dataset, `annotations/drafts/by_annotator/${annotator}/${chartId}.json`, null)
    : null;

  return {
    dataset: {
      key: dataset.key,
      label: dataset.label,
      final_dataset: dataset.finalDataset,
      url_path: dataset.urlPath
    },
    manifest: scrubClientValue({
      ...manifestItem,
      claim_status: claim?.status || manifestItem.claim_status,
      claimed_by: claim?.annotator || manifestItem.claimed_by
    }),
    target: scrubClientValue(target),
    canonical_gt: scrubClientValue(canonicalGt),
    prelabel: scrubClientValue(prelabel),
    annotation: scrubClientValue(annotation),
    draft: scrubClientValue(draft),
    image_url: `/api/image?dataset=${encodeURIComponent(dataset.key)}&file=${encodeURIComponent(manifestItem.image_file)}`
  };
}

async function claimChartForRequest(requestUrl, dataset, chartId) {
  if (!isSafeChartId(chartId)) {
    const error = new Error("Invalid chart_id");
    error.statusCode = 400;
    throw error;
  }
  const annotator = getAnnotator(requestUrl);
  const claim = await claimChart(dataset, chartId, annotator || (dataset.finalDataset ? "" : "practice_user"));
  return {
    ok: true,
    dataset: dataset.key,
    chart_id: chartId,
    claim
  };
}

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, jsonHeaders);
  res.end(JSON.stringify(payload, null, 2));
}

function sendHtml(res, statusCode, html) {
  res.writeHead(statusCode, {
    "content-type": "text/html; charset=utf-8",
    "cache-control": "no-store"
  });
  res.end(html);
}

async function sendTextFile(res, filePath, contentType = "text/plain; charset=utf-8") {
  const text = await fs.readFile(filePath, "utf8");
  res.writeHead(200, {
    "content-type": contentType,
    "cache-control": "no-store"
  });
  res.end(text);
}

function sendRedirect(res, location) {
  res.writeHead(302, { location });
  res.end();
}

function sendError(res, error) {
  const statusCode = error.statusCode || 500;
  sendJson(res, statusCode, {
    error: error.message || "Internal server error",
    claim: error.claim || null
  });
}

async function readRequestBody(req) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > 20 * 1024 * 1024) {
      const error = new Error("Request body too large");
      error.statusCode = 413;
      throw error;
    }
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

async function serveStatic(res, pathname) {
  const cleanPath = pathname === "/" ? "index.html" : pathname.replace(/^\/+/, "");
  const filePath = safeJoin(publicRoot, cleanPath);
  const stat = await fs.stat(filePath);
  if (!stat.isFile()) {
    const error = new Error("Not found");
    error.statusCode = 404;
    throw error;
  }
  const ext = path.extname(filePath).toLowerCase();
  res.writeHead(200, {
    "content-type": mimeTypes[ext] || "application/octet-stream",
    "cache-control": ext === ".html" ? "no-store" : "public, max-age=60"
  });
  fss.createReadStream(filePath).pipe(res);
}

function landingHtml() {
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>复飞航图标注平台入口</title>
  <style>
    body{margin:0;font-family:"Microsoft YaHei",sans-serif;background:#f6efe1;color:#10241f}
    main{max-width:980px;margin:8vh auto;padding:32px}
    .card{background:#fffaf0;border:1px solid #dfceb0;border-radius:24px;padding:28px;margin:18px 0;box-shadow:0 18px 50px rgba(26,55,46,.12)}
    a{display:inline-block;margin:10px 10px 0 0;padding:14px 22px;border-radius:14px;background:#176f5b;color:white;text-decoration:none;font-weight:700}
    .secondary{background:#efe4cf;color:#10241f}
    code{background:#efe4cf;padding:2px 6px;border-radius:6px}
  </style>
</head>
<body>
  <main>
    <p>FAA MISSED APPROACH DATASET</p>
    <h1>复飞航图多人协同标注入口</h1>
    <section class="card">
      <h2>练习网页：10 张</h2>
      <p>用于新手熟悉流程，保存结果不进入正式 300 张数据集。</p>
      <a href="/practice/">进入练习标注</a>
    </section>
    <section class="card">
      <h2>正式网页：300 张</h2>
      <p>正式入口会按“标注人领取航图”防止重复。进入后请先填写右上角标注人，再领取未分配航图。</p>
      <a href="/formal/">进入正式标注</a>
    </section>
    <section class="card">
      <h2>局域网使用</h2>
      <p>在项目的 <code>tools/shujuji_annotation</code> 目录运行 <code>启动标注平台.bat</code>，其他同学访问 <code>http://主机IP:${port}/formal/</code>。</p>
      <a class="secondary" href="/README.md">查看说明</a>
    </section>
  </main>
</body>
</html>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function tutorialHtml(options = {}) {
  const manualPath = safeJoin(workspaceRoot, "docs", options.fileName || "正式标注操作手册_步骤与字段对应.md");
  const markdown = stripBom(await fs.readFile(manualPath, "utf8"));
  const title = options.title || "正式标注操作手册：步骤、框类型、字段对应";
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)}</title>
  <style>
    body{margin:0;background:#f6efe1;color:#10241f;font-family:"Microsoft YaHei","Noto Sans SC",sans-serif}
    header{position:sticky;top:0;z-index:2;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 28px;border-bottom:1px solid #dfceb0;background:rgba(255,250,240,.96);box-shadow:0 10px 30px rgba(26,55,46,.08)}
    h1{margin:0;font-size:22px}
    button{border:1px solid #d8ccb7;border-radius:12px;padding:10px 16px;background:#176f5b;color:white;font-size:16px;font-weight:700;cursor:pointer}
    main{max-width:1120px;margin:24px auto;padding:0 24px 48px}
    pre{white-space:pre-wrap;word-break:break-word;line-height:1.72;margin:0;padding:26px;border:1px solid #dfceb0;border-radius:22px;background:#fffaf0;box-shadow:0 18px 50px rgba(26,55,46,.12);font-family:"Microsoft YaHei","Noto Sans SC",sans-serif;font-size:16px}
  </style>
</head>
<body>
  <header>
    <h1>${escapeHtml(title)}</h1>
    <button type="button" onclick="window.close()">关闭</button>
  </header>
  <main>
    <pre>${escapeHtml(markdown)}</pre>
  </main>
</body>
</html>`;
}

async function saveAnnotation(req, requestUrl, dataset, chartId) {
  if (!isSafeChartId(chartId)) {
    const error = new Error("Invalid chart_id");
    error.statusCode = 400;
    throw error;
  }
  const payload = JSON.parse(stripBom(await readRequestBody(req)));
  const annotator = safeAnnotator(payload.annotator || getAnnotator(requestUrl) || (dataset.finalDataset ? "" : "practice_user"));
  if (dataset.finalDataset && !annotator) {
    const error = new Error("正式标注必须先填写标注人。");
    error.statusCode = 400;
    throw error;
  }

  if (dataset.finalDataset) {
    const claims = await readClaims(dataset);
    const claim = claims[chartId];
    if (claim?.annotator && claim.annotator !== annotator) {
      const error = new Error(`这张图已由 ${claim.annotator} 领取，不能用 ${annotator} 保存，避免重复覆盖。`);
      error.statusCode = 409;
      throw error;
    }
    if (!claim) {
      const error = new Error("请先点击“领取当前图”，领取成功后再保存，避免多人重复标注同一张图。");
      error.statusCode = 409;
      throw error;
    }
  }

  const savedAt = new Date().toISOString();
  const submissionName = `${timestampForFile()}__${annotator}.json`;
  const enrichedPayload = {
    ...payload,
    chart_id: chartId,
    dataset_key: dataset.key,
    final_dataset: dataset.finalDataset,
    annotator,
    saved_at: savedAt,
    saved_by: "shujuji_annotation_platform",
    saved_from_ip: clientIp(req)
  };

  const currentPath = safeJoin(dataset.root, "annotations", "by_annotator", annotator, `${chartId}.json`);
  const submissionPath = safeJoin(dataset.root, "annotations", "submissions", chartId, submissionName);
  await writeJsonFileAtomic(currentPath, enrichedPayload);
  await writeJsonFileAtomic(submissionPath, enrichedPayload);
  await markSubmitted(dataset, chartId, annotator);

  return {
    ok: true,
    dataset: dataset.key,
    chart_id: chartId,
    annotator,
    saved_at: savedAt
  };
}

async function saveDraft(req, requestUrl, dataset, chartId) {
  if (!isSafeChartId(chartId)) {
    const error = new Error("Invalid chart_id");
    error.statusCode = 400;
    throw error;
  }

  const payload = JSON.parse(stripBom(await readRequestBody(req)));
  const annotator = safeAnnotator(payload.annotator || getAnnotator(requestUrl) || (dataset.finalDataset ? "" : "practice_user"));
  if (dataset.finalDataset && !annotator) {
    const error = new Error("姝ｅ紡鏍囨敞蹇呴』鍏堝～鍐欐爣娉ㄤ汉銆?");
    error.statusCode = 400;
    throw error;
  }

  if (dataset.finalDataset) {
    const claims = await readClaims(dataset);
    const claim = claims[chartId];
    if (claim?.annotator && claim.annotator !== annotator) {
      const error = new Error(`杩欏紶鍥惧凡鐢?${claim.annotator} 棰嗗彇锛屼笉鑳界敤 ${annotator} 鏆傚瓨銆?`);
      error.statusCode = 409;
      throw error;
    }
    if (!claim) {
      const error = new Error("璇峰厛棰嗗彇褰撳墠鑸浘锛屽啀杩涜鏆傚瓨銆?");
      error.statusCode = 409;
      throw error;
    }
  }

  const savedAt = new Date().toISOString();
  const snapshotName = `${timestampForFile()}__${annotator}.json`;
  const enrichedPayload = {
    ...payload,
    chart_id: chartId,
    dataset_key: dataset.key,
    final_dataset: dataset.finalDataset,
    annotator,
    review_status: payload.review_status || "draft_saved",
    saved_at: savedAt,
    saved_by: "shujuji_annotation_platform_draft",
    saved_from_ip: clientIp(req)
  };

  const currentPath = safeJoin(dataset.root, "annotations", "drafts", "by_annotator", annotator, `${chartId}.json`);
  const snapshotPath = safeJoin(dataset.root, "annotations", "drafts", "snapshots", chartId, snapshotName);
  await writeJsonFileAtomic(currentPath, enrichedPayload);
  await writeJsonFileAtomic(snapshotPath, enrichedPayload);

  return {
    ok: true,
    dataset: dataset.key,
    chart_id: chartId,
    annotator,
    saved_at: savedAt
  };
}

async function route(req, res) {
  const requestUrl = new URL(req.url, `http://${req.headers.host || "127.0.0.1"}`);
  const pathname = decodeURIComponent(requestUrl.pathname);
  const dataset = datasetFromRequest(requestUrl, pathname);
  const annotator = getAnnotator(requestUrl);

  if (req.method === "GET" && pathname === "/") {
    sendHtml(res, 200, landingHtml());
    return;
  }

  if (req.method === "GET" && pathname === "/README.md") {
    await sendTextFile(res, safeJoin(workspaceRoot, "README.md"), "text/markdown; charset=utf-8");
    return;
  }

  if (req.method === "GET" && pathname === "/tutorial") {
    sendRedirect(res, "/tutorial/");
    return;
  }

  if (req.method === "GET" && pathname === "/tutorial/") {
    sendHtml(res, 200, await tutorialHtml());
    return;
  }

  if (req.method === "GET" && pathname === "/detail-box-tutorial") {
    sendRedirect(res, "/detail-box-tutorial/");
    return;
  }

  if (req.method === "GET" && pathname === "/detail-box-tutorial/") {
    sendHtml(res, 200, await tutorialHtml({
      fileName: "下方复飞框读法教程.md",
      title: "下方复飞框读法教程"
    }));
    return;
  }

  if (req.method === "GET" && pathname === "/practice") {
    sendRedirect(res, "/practice/");
    return;
  }

  if (req.method === "GET" && pathname === "/formal") {
    sendRedirect(res, "/formal/");
    return;
  }

  if (req.method === "GET" && (pathname === "/practice/" || pathname === "/formal/")) {
    await serveStatic(res, "/index.html");
    return;
  }

  if (req.method === "GET" && pathname === "/api/charts") {
    sendJson(res, 200, {
      dataset: {
        key: dataset.key,
        label: dataset.label,
        final_dataset: dataset.finalDataset,
        url_path: dataset.urlPath
      },
      charts: await loadCharts(dataset, annotator)
    });
    return;
  }

  if (req.method === "GET" && pathname === "/api/chart") {
    sendJson(res, 200, await loadChartDetail(dataset, requestUrl.searchParams.get("chart_id"), annotator));
    return;
  }

  if (req.method === "POST" && pathname.startsWith("/api/claims/")) {
    const chartId = pathname.split("/").pop();
    sendJson(res, 200, await claimChartForRequest(requestUrl, dataset, chartId));
    return;
  }

  if (req.method === "GET" && pathname === "/api/image") {
    const file = requestUrl.searchParams.get("file");
    if (!/^[A-Za-z0-9_. -]+\.(png|jpg|jpeg)$/i.test(file || "")) {
      const error = new Error("Invalid image file");
      error.statusCode = 400;
      throw error;
    }
    const filePath = safeJoin(dataset.root, "images", imageBasename(file));
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      "content-type": mimeTypes[ext] || "application/octet-stream",
      "cache-control": "public, max-age=300"
    });
    fss.createReadStream(filePath).pipe(res);
    return;
  }

  if (req.method === "POST" && pathname.startsWith("/api/annotations/")) {
    const chartId = pathname.split("/").pop();
    sendJson(res, 200, await saveAnnotation(req, requestUrl, dataset, chartId));
    return;
  }

  if (req.method === "POST" && pathname.startsWith("/api/drafts/")) {
    const chartId = pathname.split("/").pop();
    sendJson(res, 200, await saveDraft(req, requestUrl, dataset, chartId));
    return;
  }

  if (req.method === "GET") {
    await serveStatic(res, pathname);
    return;
  }

  const error = new Error("Method not allowed");
  error.statusCode = 405;
  throw error;
}

const server = http.createServer((req, res) => {
  route(req, res).catch((error) => sendError(res, error));
});

server.listen(port, "0.0.0.0", () => {
  console.log(`Annotation platform running on 0.0.0.0:${port}`);
  console.log(`Local practice: http://127.0.0.1:${port}/practice/`);
  console.log(`Local formal:   http://127.0.0.1:${port}/formal/`);
  Object.values(os.networkInterfaces())
    .flat()
    .filter((item) => item && item.family === "IPv4" && !item.internal)
    .forEach((item) => {
      console.log(`LAN practice:   http://${item.address}:${port}/practice/`);
      console.log(`LAN formal:     http://${item.address}:${port}/formal/`);
    });
  console.log(`Workspace root: ${workspaceRoot}`);
});
