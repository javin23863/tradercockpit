'use strict';
/**
 * llm.cjs — the studio's bring-your-own-LLM shim (dependency-free, native fetch).
 *
 * The generators (generate-shot-pack / diagnose-generation / qa-attention-gate / build-video-skills)
 * call this. If you point it at any OpenAI-compatible endpoint it AUTO-RUNS your model; if you set
 * nothing, the generators fall back to PASTE-MODE (they save the fully-assembled pro prompt so you can
 * paste it into ChatGPT / Claude / any LLM). So the tools always produce value, and light up the moment
 * you add a key.
 *
 * Configure it with EITHER:
 *   - LLM_BASE_URL + LLM_MODEL   (+ LLM_API_KEY if the endpoint needs one)   ← any OpenAI-compatible API
 *   - OPENAI_API_KEY             (base defaults to https://api.openai.com/v1, model to gpt-4o-mini)
 *   - a local Ollama            (base defaults to http://localhost:11434/v1) — set LLM_MODEL to your pulled model
 *
 * Exports: callLLM(system, user, opts) -> string   ·   llmConfigured() -> boolean
 */

const fs = require('fs');
const path = require('path');

// Optional, zero-dependency .env loader: pull LLM_* / OPENAI_API_KEY from a .env in the generators dir,
// the pipeline dir, or the kit root, without overriding anything already set in the real environment.
function loadEnvFrom(file) {
  try {
    if (!fs.existsSync(file)) return;
    for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
      const t = line.trim();
      if (!t || t.startsWith('#')) continue;
      const i = t.indexOf('=');
      if (i < 0) continue;
      const k = t.slice(0, i).trim();
      const v = t.slice(i + 1).trim().replace(/^["']|["']$/g, '');
      if (k && process.env[k] === undefined) process.env[k] = v;
    }
  } catch (_) { /* best-effort */ }
}
for (const p of [
  path.join(__dirname, '.env'),
  path.join(__dirname, '..', '.env'),
  path.join(__dirname, '..', '..', '.env'),
]) loadEnvFrom(p);

// Resolve the effective {base, key, model} from the environment.
function cfg() {
  const key = process.env.LLM_API_KEY || process.env.OPENAI_API_KEY || '';
  let base = (process.env.LLM_BASE_URL || '').trim();
  let model = (process.env.LLM_MODEL || '').trim();
  if (!base && process.env.OPENAI_API_KEY) {
    base = 'https://api.openai.com/v1';
    if (!model) model = 'gpt-4o-mini';
  }
  if (!base && (process.env.OLLAMA_BASE_URL || process.env.OLLAMA_MODEL)) {
    base = process.env.OLLAMA_BASE_URL || 'http://localhost:11434/v1';
  }
  if (!model && process.env.OLLAMA_MODEL) model = process.env.OLLAMA_MODEL.trim();
  const isLocal = /localhost|127\.0\.0\.1|:11434|host\.docker\.internal/i.test(base);
  const configured = !!(base && model && (key || isLocal));
  return { base, key, model, isLocal, configured };
}

/** True when an LLM is reachable from the current environment (so a caller can auto-run instead of paste-mode). */
function llmConfigured() {
  return cfg().configured;
}

/**
 * Call the configured OpenAI-compatible chat endpoint. Throws an error tagged `LLM_NOT_CONFIGURED`
 * when nothing is set (so callers can fall back to PASTE-MODE), and a normal error on transport/HTTP failure.
 * @param {string} system  system prompt
 * @param {string} user    user prompt (the fully-assembled generation prompt)
 * @param {object} [opts]  { temperature=0.5, maxTokens, timeoutMs=180000, jsonMode }
 * @returns {Promise<string>} the model's text
 */
async function callLLM(system, user, opts = {}) {
  const c = cfg();
  if (!c.configured) {
    const e = new Error('LLM_NOT_CONFIGURED');
    e.code = 'LLM_NOT_CONFIGURED';
    throw e;
  }
  const body = {
    model: c.model,
    temperature: opts.temperature != null ? opts.temperature : 0.5,
    messages: [
      { role: 'system', content: String(system || '') },
      { role: 'user', content: String(user || '') },
    ],
  };
  if (opts.maxTokens) body.max_tokens = opts.maxTokens;
  if (opts.jsonMode) body.response_format = { type: 'json_object' };
  const res = await fetch(c.base.replace(/\/+$/, '') + '/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(c.key ? { Authorization: 'Bearer ' + c.key } : {}) },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(opts.timeoutMs || 180000),
  });
  if (!res.ok) {
    let detail = '';
    try { detail = (await res.text()).slice(0, 300); } catch (_) { /* ignore */ }
    throw new Error('LLM HTTP ' + res.status + (detail ? ' — ' + detail : ''));
  }
  const j = await res.json();
  return (j && j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || '';
}

/** The standard paste-mode notice, given the path the ready-to-run prompt was saved to. */
function notConfiguredMessage(savedPath) {
  return 'No LLM configured (set LLM_BASE_URL/LLM_API_KEY/LLM_MODEL, or OPENAI_API_KEY, or run Ollama). '
    + 'Your ready-to-run prompt is saved at ' + savedPath
    + ' — paste it into ChatGPT / Claude / any LLM to generate.';
}

module.exports = { callLLM, llmConfigured, notConfiguredMessage, cfg };
