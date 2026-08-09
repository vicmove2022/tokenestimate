const RANK_CDN = "https://cdn.jsdelivr.net/npm/js-tiktoken@1.0.21/dist/ranks";
const ENGINE_URL = "https://cdn.jsdelivr.net/npm/js-tiktoken@1.0.21/dist/lite.js";
const RANK_LOCAL = "./js/ranks/";
const ENGINE_LOCAL = "./js/ranks/lite.js";

// type: "exact" = real tiktoken tokenizer | "est" = rule-of-thumb estimate
// est.cjk  = tokens per Chinese character, est.ascii = characters per English token
// estimated prices: public list prices per 1M tokens (USD), Aug 2026 — user-editable in the UI
const MODELS = [
  // ---------- OpenAI (exact tiktoken) ----------
  { id: "gpt-5.5", label: "GPT-5.5", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 2.5, priceOut: 15.0, ctx: "200K", note: "" },
  { id: "gpt-5", label: "GPT-5", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 1.25, priceOut: 10.0, ctx: "400K", note: "" },
  { id: "gpt-5-mini", label: "GPT-5 mini", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 0.25, priceOut: 2.0, ctx: "400K", note: "" },
  { id: "gpt-5-nano", label: "GPT-5 nano", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 0.05, priceOut: 0.4, ctx: "400K", note: "" },
  { id: "gpt-4o", label: "GPT-4o", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 2.25, priceOut: 10.0, ctx: "128K", note: "" },
  { id: "gpt-4o-mini", label: "GPT-4o mini", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 0.15, priceOut: 0.6, ctx: "128K", note: "" },
  { id: "gpt-4.1", label: "GPT-4.1", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 2.0, priceOut: 8.0, ctx: "1M", note: "" },
  { id: "gpt-4.1-mini", label: "GPT-4.1 mini", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 0.4, priceOut: 1.6, ctx: "1M", note: "" },
  { id: "gpt-4.1-nano", label: "GPT-4.1 nano", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 0.1, priceOut: 0.4, ctx: "1M", note: "" },
  { id: "o3", label: "o3", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 2.0, priceOut: 8.0, ctx: "200K", note: "reasoning" },
  { id: "o4-mini", label: "o4-mini", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 1.1, priceOut: 4.4, ctx: "200K", note: "reasoning" },
  { id: "o3-mini", label: "o3-mini", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 1.1, priceOut: 4.4, ctx: "200K", note: "reasoning" },
  { id: "o1", label: "o1", group: "OpenAI", type: "exact", encoding: "o200k_base", priceIn: 15.0, priceOut: 60.0, ctx: "200K", note: "reasoning" },
  { id: "gpt-4-turbo", label: "GPT-4 Turbo", group: "OpenAI (legacy)", type: "exact", encoding: "cl100k_base", priceIn: 10.0, priceOut: 30.0, ctx: "128K", note: "" },
  { id: "gpt-4", label: "GPT-4", group: "OpenAI (legacy)", type: "exact", encoding: "cl100k_base", priceIn: 30.0, priceOut: 60.0, ctx: "8K", note: "" },
  { id: "gpt-3.5-turbo", label: "GPT-3.5 Turbo", group: "OpenAI (legacy)", type: "exact", encoding: "cl100k_base", priceIn: 0.5, priceOut: 1.5, ctx: "16K", note: "" },
  { id: "embedding-3-small", label: "text-embedding-3-small", group: "OpenAI embedding", type: "exact", encoding: "cl100k_base", priceIn: 0.02, priceOut: 0, ctx: "–", note: "" },
  { id: "embedding-3-large", label: "text-embedding-3-large", group: "OpenAI embedding", type: "exact", encoding: "cl100k_base", priceIn: 0.13, priceOut: 0, ctx: "–", note: "" },

  // ---------- Anthropic ----------
  { id: "claude-opus-5", label: "Claude Opus 5", group: "Anthropic Claude", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 5.0, priceOut: 25.0, ctx: "200K", note: "" },
  { id: "claude-sonnet-5", label: "Claude Sonnet 5", group: "Anthropic Claude", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 2.0, priceOut: 10.0, ctx: "200K", note: "intro pricing" },
  { id: "claude-haiku-4.5", label: "Claude Haiku 4.5", group: "Anthropic Claude", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 1.0, priceOut: 5.0, ctx: "200K", note: "" },
  { id: "claude-fable-5", label: "Claude Fable 5", group: "Anthropic Claude", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 10.0, priceOut: 50.0, ctx: "1M", note: "agentic" },
  { id: "claude-opus-4.6", label: "Claude Opus 4.6", group: "Anthropic Claude", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 5.0, priceOut: 25.0, ctx: "200K", note: "" },
  { id: "claude-sonnet-4.6", label: "Claude Sonnet 4.6", group: "Anthropic Claude", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 3.0, priceOut: 15.0, ctx: "200K", note: "" },

  // ---------- Google Gemini ----------
  { id: "gemini-3.1-pro", label: "Gemini 3.1 Pro", group: "Google Gemini", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 2.0, priceOut: 12.0, ctx: "2M", note: "≤200K ctx" },
  { id: "gemini-3.6-flash", label: "Gemini 3.6 Flash", group: "Google Gemini", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 1.5, priceOut: 7.5, ctx: "1M", note: "" },
  { id: "gemini-3.5-flash", label: "Gemini 3.5 Flash", group: "Google Gemini", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 1.5, priceOut: 9.0, ctx: "1M", note: "" },
  { id: "gemini-3-flash", label: "Gemini 3 Flash", group: "Google Gemini", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 0.5, priceOut: 3.0, ctx: "1M", note: "" },
  { id: "gemini-3.5-flash-lite", label: "Gemini 3.5 Flash-Lite", group: "Google Gemini", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 0.3, priceOut: 2.5, ctx: "1M", note: "" },
  { id: "gemini-2.5-pro", label: "Gemini 2.5 Pro", group: "Google Gemini", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 1.25, priceOut: 10.0, ctx: "2M", note: "" },
  { id: "gemini-2.5-flash", label: "Gemini 2.5 Flash", group: "Google Gemini", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 0.3, priceOut: 2.5, ctx: "1M", note: "" },
  { id: "gemini-2.5-flash-lite", label: "Gemini 2.5 Flash-Lite", group: "Google Gemini", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 0.1, priceOut: 0.4, ctx: "1M", note: "" },

  // ---------- US / EU others ----------
  { id: "grok-4.1", label: "Grok 4.1 (xAI)", group: "US & EU", type: "est", est: { cjk: 1.2, ascii: 4 }, priceIn: 0.2, priceOut: 1.0, ctx: "1M", note: "" },
  { id: "llama-4", label: "Llama 4 (Meta)", group: "US & EU", type: "est", est: { cjk: 1.0, ascii: 4 }, priceIn: 0.15, priceOut: 0.45, ctx: "1M", note: "open-weight" },
  { id: "mistral-large", label: "Mistral Large 3", group: "US & EU", type: "est", est: { cjk: 1.0, ascii: 4 }, priceIn: 2.0, priceOut: 6.0, ctx: "128K", note: "" },
  { id: "amazon-nova-pro", label: "Amazon Nova Pro", group: "US & EU", type: "est", est: { cjk: 1.0, ascii: 4 }, priceIn: 0.8, priceOut: 3.2, ctx: "300K", note: "" },

  // ---------- China ----------
  { id: "deepseek-v4-pro", label: "DeepSeek V4 Pro", group: "DeepSeek (深度求索)", type: "est", est: { cjk: 0.6, ascii: 3.3 }, priceIn: 0.44, priceOut: 0.87, ctx: "128K", note: "deepseek-chat" },
  { id: "deepseek-v4-flash", label: "DeepSeek V4 Flash", group: "DeepSeek (深度求索)", type: "est", est: { cjk: 0.6, ascii: 3.3 }, priceIn: 0.14, priceOut: 0.28, ctx: "400K", note: "" },
  { id: "deepseek-v3.2", label: "DeepSeek V3.2", group: "DeepSeek (深度求索)", type: "est", est: { cjk: 0.6, ascii: 3.3 }, priceIn: 0.35, priceOut: 0.42, ctx: "128K", note: "" },
  { id: "deepseek-r1", label: "DeepSeek R1", group: "DeepSeek (深度求索)", type: "est", est: { cjk: 0.6, ascii: 3.3 }, priceIn: 0.56, priceOut: 2.5, ctx: "64K", note: "reasoning" },

  { id: "qwen3-max", label: "Qwen3 Max (通义千问)", group: "Alibaba Qwen (阿里通义)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.78, priceOut: 3.9, ctx: "262K", note: "" },
  { id: "qwen3-plus", label: "Qwen3 Plus", group: "Alibaba Qwen (阿里通义)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.4, priceOut: 1.2, ctx: "128K", note: "" },
  { id: "qwen3-flash", label: "Qwen3 Flash", group: "Alibaba Qwen (阿里通义)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.15, priceOut: 1.5, ctx: "128K", note: "" },
  { id: "qwen3-coder", label: "Qwen3 Coder", group: "Alibaba Qwen (阿里通义)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.3, priceOut: 0.9, ctx: "128K", note: "coding" },

  { id: "glm-5", label: "GLM-5 (智谱)", group: "Zhipu GLM (智谱)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 1.0, priceOut: 3.2, ctx: "200K", note: "" },
  { id: "glm-5.1", label: "GLM-5.1", group: "Zhipu GLM (智谱)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.98, priceOut: 3.08, ctx: "200K", note: "" },
  { id: "glm-4.7", label: "GLM-4.7", group: "Zhipu GLM (智谱)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.5, priceOut: 2.2, ctx: "200K", note: "" },
  { id: "glm-4-flash", label: "GLM-4-Flash", group: "Zhipu GLM (智谱)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0, priceOut: 0, ctx: "128K", note: "free" },

  { id: "kimi-k2.6", label: "Kimi K2.6 (月之暗面)", group: "Moonshot Kimi (月之暗面)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 1.0, priceOut: 2.5, ctx: "256K", note: "tiered" },
  { id: "kimi-k2.5", label: "Kimi K2.5", group: "Moonshot Kimi (月之暗面)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.6, priceOut: 3.0, ctx: "128K", note: "" },
  { id: "kimi-k3", label: "Kimi K3", group: "Moonshot Kimi (月之暗面)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 7.0, priceOut: 14.0, ctx: "256K", note: "premium" },

  { id: "doubao-1.6-pro", label: "Doubao 1.6 Pro (豆包)", group: "ByteDance Doubao (火山引擎)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.11, priceOut: 0.45, ctx: "256K", note: "" },
  { id: "doubao-1.6-flash", label: "Doubao 1.6 Flash", group: "ByteDance Doubao (火山引擎)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.01, priceOut: 0.11, ctx: "128K", note: "cheapest" },
  { id: "doubao-1.6-lite", label: "Doubao 1.6 Lite", group: "ByteDance Doubao (火山引擎)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.02, priceOut: 0.04, ctx: "128K", note: "" },

  { id: "ernie-4.5", label: "ERNIE 4.5 (文心一言)", group: "Baidu ERNIE (百度)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.2, priceOut: 0.55, ctx: "128K", note: "" },
  { id: "ernie-x1", label: "ERNIE X1", group: "Baidu ERNIE (百度)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.006, priceOut: 0.02, ctx: "128K", note: "reasoning · ultra cheap" },

  { id: "hunyuan-2-pro", label: "Hunyuan 2 Pro (混元)", group: "Tencent Hunyuan (腾讯)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 1.0, priceOut: 4.0, ctx: "128K", note: "" },
  { id: "hunyuan-lite", label: "Hunyuan Lite", group: "Tencent Hunyuan (腾讯)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0, priceOut: 0, ctx: "32K", note: "free" },

  { id: "spark-max-x1", label: "Spark Max / X1 (讯飞星火)", group: "iFlytek Spark (讯飞星火)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.5, priceOut: 1.7, ctx: "128K", note: "" },
  { id: "spark-lite", label: "Spark Lite", group: "iFlytek Spark (讯飞星火)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0, priceOut: 0, ctx: "32K", note: "free" },

  { id: "minimax-2.5", label: "MiniMax M2.5", group: "MiniMax (稀宇科技)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.29, priceOut: 1.18, ctx: "197K", note: "agent" },
  { id: "yi-lightning", label: "Yi-Lightning (零一万物)", group: "01.AI (零一万物)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.4, priceOut: 1.2, ctx: "128K", note: "" },
  { id: "step-3", label: "Step-3 (阶跃星辰)", group: "StepFun (阶跃星辰)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.5, priceOut: 1.5, ctx: "128K", note: "" },
  { id: "sensetime-5.1", label: "SenseNova 5.1 (商汤)", group: "SenseTime (商汤)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.04, priceOut: 0.7, ctx: "128K", note: "" },
  { id: "baichuan-4", label: "Baichuan 4 (百川)", group: "Baichuan (百川智能)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 1.2, priceOut: 2.8, ctx: "128K", note: "" },
  { id: "skyclaw-1.0", label: "SkyClaw 1.0 (昆仑万维)", group: "Kunlun (昆仑万维)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.5, priceOut: 1.5, ctx: "1M", note: "agent" },
  { id: "mimo-v2.5-pro", label: "MiMo V2.5 Pro (小米)", group: "Xiaomi MiMo (小米)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.44, priceOut: 0.87, ctx: "1M", note: "" },
  { id: "mimo-v2.5", label: "MiMo V2.5", group: "Xiaomi MiMo (小米)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.14, priceOut: 0.28, ctx: "1M", note: "" },
  { id: "pangu-4.7", label: "PanGu 4.7 (盘古)", group: "Huawei PanGu (华为云)", type: "est", est: { cjk: 0.9, ascii: 3.8 }, priceIn: 0.5, priceOut: 1.5, ctx: "128K", note: "" },

  { id: "custom", label: "Custom (any model)", group: "Custom", type: "exact", encoding: "o200k_base", priceIn: 1.0, priceOut: 1.0, ctx: "–", note: "" }
];

const SAMPLE = `Tokens are how GPT models read text: nine English words usually cost about twelve tokens.

Token counting matters for AI developers because every API call is billed in tokens, not in characters or words. Most model pages quote per-million-token prices, and a difference of a few thousand tokens can change what a launch costs in production.

This calculator counts tokens exactly with the tiktoken tokenizer (what OpenAI uses on its servers) for OpenAI models, and gives a smart estimate for Claude, Gemini and Chinese models like DeepSeek, Qwen, GLM and Kimi. Paste any prompt, document or code — it works with mixed Chinese and English text too.`;

const state = {
  modelId: "gpt-4o",
  encoderMap: new Map(),
  pendingMap: new Map(),
  enginePromise: null,
  pricesEdited: false
};

const $ = (id) => document.getElementById(id);
const nf = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const usd = (v, digits) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: Math.max(digits, 2), maximumFractionDigits: Math.max(digits, 2) }).format(v);

function fmtUSD(v) {
  if (!isFinite(v)) return "—";
  if (v > 0 && v < 0.01) return "$" + (v * 1000).toFixed(3) + "k";
  return usd(v, v >= 100 ? 0 : 4);
}

function currentModel() {
  return MODELS.find((m) => m.id === state.modelId) || null;
}

function estimateTokens(text, est) {
  const cjk = (text.match(/[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/g) || []).length;
  const other = Math.max(0, text.length - cjk);
  return Math.ceil(cjk * est.cjk + other / est.ascii);
}

function ensureTokenizer() {
  if (!state.enginePromise) {
    state.enginePromise = import(ENGINE_LOCAL)
      .catch(() => import(ENGINE_URL))
      .then((m) => m.Tiktoken)
      .catch((err) => {
        state.enginePromise = null;
        throw err;
      });
  }
  return state.enginePromise;
}

async function getEncoder(name) {
  if (state.encoderMap.has(name)) return state.encoderMap.get(name);
  if (state.pendingMap.has(name)) return state.pendingMap.get(name);
  const task = (async () => {
    const Tiktoken = await ensureTokenizer();
    const storageKey = "tk-rank-" + name;
    let rankData = null;
    try { rankData = JSON.parse(localStorage.getItem(storageKey) || "null"); } catch (e) {}
    if (!rankData) {
      setStatus("info", "Loading " + name + " tokenizer data… (one-time download, cached after)");
      let mod;
      try {
        mod = await import(RANK_LOCAL + name + ".js");
      } catch (e) {
        mod = await import(RANK_CDN + "/" + name + ".js");
      }
      rankData = mod.default;
      try {
        for (const key of Object.keys(localStorage)) {
          if (key.startsWith("tk-rank-") && key !== storageKey) localStorage.removeItem(key);
        }
        localStorage.setItem(storageKey, JSON.stringify(rankData));
      } catch (e) {}
    }
    const enc = new Tiktoken(rankData);
    state.encoderMap.set(name, enc);
    return enc;
  })();
  state.pendingMap.set(name, task);
  try { return await task; } finally { state.pendingMap.delete(name); }
}

let statusTimer;
function setStatus(type, msg) {
  const el = $("status");
  el.className = "status-banner " + (type || "");
  el.textContent = msg || "";
  clearTimeout(statusTimer);
  if (msg) statusTimer = setTimeout(() => { el.className = "status-banner"; }, 9000);
}

function updateCharCount() {
  $("char-count").textContent = $("input-text").value.length.toLocaleString("en-US");
}

function syncPriceFields() {
  const model = currentModel();
  const pIn = $("price-in"), pOut = $("price-out");
  const disable = !!model && model.type === "est";
  pIn.disabled = disable;
  pOut.disabled = disable;
  if (disable) {
    pIn.placeholder = "estimated";
    pOut.placeholder = "estimated";
    if (!state.pricesEdited) { pIn.value = ""; pOut.value = ""; }
    $("price-note").textContent = "Estimate mode — model rates still applied.";
    return;
  }
  if (!state.pricesEdited) {
    pIn.value = model.priceIn == null ? "" : model.priceIn;
    pOut.value = model.priceOut == null ? "" : model.priceOut;
  }
  pIn.placeholder = "USD / 1M input";
  pOut.placeholder = "USD / 1M output";
  $("price-note").textContent = state.pricesEdited ? "Custom prices shown." : "";
}

function currentPrices() {
  const model = currentModel();
  const inRaw = parseFloat($("price-in").value);
  const outRaw = parseFloat($("price-out").value);
  let priceIn, priceOut;
  if (state.pricesEdited) {
    priceIn = isNaN(inRaw) ? null : inRaw;
    priceOut = isNaN(outRaw) ? null : outRaw;
  } else if (model) {
    priceIn = model.priceIn;
    priceOut = model.priceOut;
  }
  if (priceIn == null && priceOut == null) return null;
  if (priceIn == null) priceIn = 0;
  if (priceOut == null) priceOut = 0;
  return { in: priceIn, out: priceOut };
}

async function onModelChange() {
  state.modelId = $("model-select").value;
  state.pricesEdited = false;
  syncPriceFields();
  await renderCalc();
}

function onPriceChange() {
  state.pricesEdited = true;
  $("price-note").textContent = "Custom prices shown.";
  scheduleCalc(true);
}

function resetPrices() {
  state.pricesEdited = false;
  syncPriceFields();
  renderCalc();
}

let calcTimer = null;
function scheduleCalc(immediate) {
  clearTimeout(calcTimer);
  const delay = $("input-text").value.length > 400000 ? 900 : 300;
  calcTimer = setTimeout(renderCalc, immediate ? 10 : delay);
}

const animate = window.TokenMotion ? window.TokenMotion.animateNumber : null;
function setStat(el, val) {
  if (animate && val != null && typeof val === "number") animate(el, val);
  else { el.textContent = val === null ? "—" : String(val); delete el.dataset.motionFrom; }
}

async function renderCalc() {
  const seq = (state.calcSeq = (state.calcSeq || 0) + 1);
  const text = $("input-text").value;
  const bytes = new TextEncoder().encode(text).length;
  const chars = text.length;
  const words = (text.trim().match(/\S+/g) || []).length;
  const lines = text === "" ? 0 : text.split("\n").length;

  setStat($("chars-val"), chars);
  setStat($("words-val"), words);
  setStat($("lines-val"), lines);
  setStat($("bytes-val"), bytes);

  const model = currentModel();
  const encLabel = $("enc-label");
  let tokens = null;

  if (model.type === "est") {
    encLabel.textContent = "Estimate · " + model.est.cjk + " token/汉字 + " + (1 / model.est.ascii).toFixed(2) + " token/char";
    tokens = estimateTokens(text, model.est);
  } else if (model) {
    encLabel.textContent = model.encoding + " · exact tiktoken · " + (model.ctx !== "–" ? model.ctx + " context" : "embedding");
    $("results-title").classList.add("loading");
    try {
      const enc = await getEncoder(model.encoding);
      tokens = enc.encode(text, "all").length;
    } catch (err) {
      setStatus(null, "Tokenizer error: " + err.message);
      tokens = null;
    } finally {
      $("results-title").classList.remove("loading");
    }
  }

  if (seq !== state.calcSeq) return;
  if (tokens == null) {
    setStat($("tokens-val"), null);
    $("tokens-k").textContent = "";
    $("per-char").textContent = "—";
    $("cost-in").textContent = $("cost-out").textContent = $("cost-total").textContent = "—";
    return;
  }

  setStat($("tokens-val"), tokens);
  $("tokens-val").classList.remove("pulse");
  void $("tokens-val").offsetWidth;
  $("tokens-val").classList.add("pulse");
  $("tokens-k").textContent = "≈ " + compact(tokens) + " tokens";
  $("per-char").textContent = chars > 0 ? (tokens / chars).toFixed(3) : "0";

  const prices = currentPrices();
  if (!prices) {
    $("cost-in").textContent = $("cost-out").textContent = $("cost-total").textContent = "—";
    return;
  }
  const inCost = (tokens * prices.in) / 1e6;
  const outCost = (tokens * prices.out) / 1e6;
  $("cost-in").textContent = fmtUSD(inCost);
  $("cost-out").textContent = fmtUSD(outCost);
  $("cost-total").textContent = fmtUSD(inCost + outCost);
}

function compact(n) {
  if (n >= 1e6) return (n / 1e6).toFixed(2) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return String(n);
}

function copySummary() {
  const est = currentModel();
  const name = est ? est.label : $("model-select").value;
  const lines = [
    "Model: " + name,
    "Tokens: " + $("tokens-val").textContent,
    "Characters: " + $("chars-val").textContent,
    "Words: " + $("words-val").textContent,
    "Estimated cost: " + $("cost-total").textContent
  ];
  navigator.clipboard.writeText(lines.join("\n")).then(
    () => { $("copy-feedback").textContent = "Copied!"; setTimeout(() => { $("copy-feedback").textContent = ""; }, 1600); },
    () => { $("copy-feedback").textContent = "Press Ctrl+C to copy the numbers above."; }
  );
}

function onPaste(e) {
  if (e.target && e.target.closest("textarea, input, select")) return;
  const text = e.clipboardData && e.clipboardData.getData("text");
  if (text) {
    e.preventDefault();
    $("input-text").value = text;
    updateCharCount();
    scheduleCalc(true);
  }
}

function onDrop(e) {
  e.preventDefault();
  const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    $("input-text").value = String(reader.result || "");
    updateCharCount();
    scheduleCalc(true);
  };
  reader.readAsText(file);
}

function buildModelSelect() {
  const sel = $("model-select");
  const groups = {};
  for (const m of MODELS) (groups[m.group] = groups[m.group] || []).push(m);
  for (const [name, list] of Object.entries(groups)) {
    const og = document.createElement("optgroup");
    og.label = name;
    for (const m of list) {
      const opt = new Option(m.label + (m.note ? " — " + m.note : ""), m.id);
      if (m.priceIn === 0 && m.priceOut === 0) opt.title = "Free model";
      og.appendChild(opt);
    }
    sel.appendChild(og);
  }
  sel.value = state.modelId;
}

function buildModelTable() {
  const tbody = $("model-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  const money = (v) => (v === 0 ? "Free" : v == null ? "–" : "$" + v.toLocaleString("en-US", { maximumFractionDigits: 3 }));
  const groups = {};
  for (const m of MODELS) {
    if (m.id === "custom") continue;
    (groups[m.group] = groups[m.group] || []).push(m);
  }
  for (const [name, list] of Object.entries(groups)) {
    const head = document.createElement("tr");
    head.className = "group-row";
    head.innerHTML = "<td colspan='5'><strong>" + name + "</strong></td>";
    head.querySelector("td").style.paddingTop = "18px";
    tbody.appendChild(head);
    for (const m of list) {
      const outDisplay = m.priceOut === 0 && m.priceIn > 0 ? "–" : money(m.priceOut);
      const tr = document.createElement("tr");
      tr.innerHTML =
        "<td class='mono'>" + esc(m.label) + (m.note ? " <span class='tag'>" + esc(m.note) + "</span>" : "") + "</td>" +
        "<td>" + (m.type === "exact" ? "<span class='tag ok'>exact tiktoken</span>" : "<span class='tag'>estimate</span>") + "</td>" +
        "<td>" + m.ctx + "</td>" +
        "<td>" + money(m.priceIn) + "</td>" +
        "<td>" + outDisplay + "</td>";
      tbody.appendChild(tr);
    }
  }
}

const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 });
const money = (v) => (v === 0 ? "Free" : v == null ? "–" : "$" + fmt.format(v));
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function init() {
  buildModelSelect();
  buildModelTable();
  $("input-text").addEventListener("input", () => { updateCharCount(); scheduleCalc(); });
  $("model-select").addEventListener("change", onModelChange);
  $("btn-sample").addEventListener("click", () => {
    $("input-text").value = SAMPLE;
    updateCharCount();
    scheduleCalc(true);
  });
  $("btn-clear").addEventListener("click", () => {
    $("input-text").value = "";
    updateCharCount();
    scheduleCalc(true);
  });
  $("btn-copy").addEventListener("click", copySummary);
  $("price-in").addEventListener("input", onPriceChange);
  $("price-out").addEventListener("input", onPriceChange);
  $("btn-reset-prices").addEventListener("click", resetPrices);
  document.addEventListener("paste", onPaste);
  document.addEventListener("dragover", (e) => e.preventDefault());
  document.addEventListener("drop", onDrop);
  updateCharCount();
  syncPriceFields();
  scheduleCalc(true);
  setTimeout(() => ensureTokenizer().catch(() => {}), 500);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}