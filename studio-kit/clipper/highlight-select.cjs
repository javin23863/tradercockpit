'use strict';
/**
 * highlight-select.cjs — semantic highlight/moment selection for auto-clipping.
 *
 * Picks the genuinely clip-worthy moments from a long video instead of guessing with a plain regex
 * scorer: feed the transcript to an LLM and get back ranked [start,end] windows with a reason for each,
 * so the cuts are real hooks / payoffs / quotable lines. A deterministic regex fallback ALWAYS produces
 * output when no API key is set, so it works fully offline.
 *
 * White-label + dependency-free (no external lib imports) so it drops cleanly into any pipeline. Point it
 * at any OpenAI-compatible endpoint (DeepSeek / OpenAI / Ollama / LM Studio) via
 * env, or pass your own llmCall. Input: a Whisper .srt (or word-level .json). Output: clips.json [{start,end,score,reason,title}].
 *
 *   node highlight-select.cjs --srt transcript.srt --clips 6 --duration 30 --out clips.json
 *   env: LLM_BASE_URL (e.g. https://api.deepseek.com/v1 | http://localhost:11434/v1), LLM_API_KEY, LLM_MODEL
 *
 * As a module:  const { selectHighlights, parseSrt } = require('./highlight-select.cjs');
 */
const fs = require('fs');
const path = require('path');

// ---- transcript parsing -------------------------------------------------
function srtTimeToSec(t) {
  const m = /(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})/.exec(String(t || ''));
  if (!m) return 0;
  return (+m[1]) * 3600 + (+m[2]) * 60 + (+m[3]) + (+m[4]) / 1000;
}
function secToClock(s) {
  s = Math.max(0, Math.round(s * 1000) / 1000);
  const hh = Math.floor(s / 3600), mm = Math.floor((s % 3600) / 60), ss = (s % 60);
  return `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}:${ss.toFixed(3).padStart(6, '0')}`;
}
/** Parse SRT text into cues [{start,end,text}] (seconds). Tolerant of blank lines + CRLF. */
function parseSrt(srt) {
  const blocks = String(srt || '').replace(/\r/g, '').split(/\n\n+/);
  const cues = [];
  for (const b of blocks) {
    const lines = b.split('\n').filter(Boolean);
    const tl = lines.find(l => l.includes('-->'));
    if (!tl) continue;
    const [a, bb] = tl.split('-->');
    const text = lines.filter(l => l !== tl && !/^\d+$/.test(l.trim())).join(' ').trim();
    if (!text) continue;
    cues.push({ start: srtTimeToSec(a), end: srtTimeToSec(bb), text });
  }
  return cues;
}
/** Parse a Whisper word-level json ({segments:[{start,end,text}]} or {words:[...]}) into cues. */
function parseJson(obj) {
  if (obj && Array.isArray(obj.segments)) return obj.segments.map(s => ({ start: +s.start || 0, end: +s.end || 0, text: String(s.text || '').trim() })).filter(c => c.text);
  if (Array.isArray(obj)) return obj.map(s => ({ start: +s.start || 0, end: +s.end || 0, text: String(s.text || s.word || '').trim() })).filter(c => c.text);
  return [];
}

// ---- regex fallback (no LLM) --------------------------------------------
const HOOK_PATTERNS = [
  /\b(here'?s why|the secret|nobody tells you|stop doing|let me show you|wait until|watch this|the truth about|the reason|what if|how to|the biggest mistake|never|always|the trick)\b/i,
  /\?$/, /!$/,
  /\b(because|so that|which means|the point is|turns out|in fact|actually)\b/i,
];
function hookScore(text) {
  let s = 0;
  for (const re of HOOK_PATTERNS) if (re.test(text)) s += 1;
  const words = text.split(/\s+/).length;
  if (words >= 8 && words <= 60) s += 0.5;         // a completable thought
  return s;
}

// ---- LLM highlight selection --------------------------------------------
/** Build one OpenAI-compatible chat call from env, or return null if not configured. */
function envLlmCall() {
  const base = process.env.LLM_BASE_URL, key = process.env.LLM_API_KEY, model = process.env.LLM_MODEL;
  if (!base || !model) return null;
  return async (system, user) => {
    const res = await fetch(base.replace(/\/$/, '') + '/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(key ? { Authorization: 'Bearer ' + key } : {}) },
      body: JSON.stringify({ model, temperature: 0.2, response_format: { type: 'json_object' }, messages: [{ role: 'system', content: system }, { role: 'user', content: user }] }),
    });
    if (!res.ok) throw new Error('LLM HTTP ' + res.status);
    const j = await res.json();
    return j.choices?.[0]?.message?.content || '';
  };
}

/**
 * @param {object} opts {cues, clips=6, duration=30, minGap=6, llmCall}
 * @returns {Promise<Array<{start:number,end:number,score:number,reason:string,title:string}>>}
 */
async function selectHighlights(opts = {}) {
  const cues = opts.cues || [];
  const n = Math.max(1, opts.clips || 6);
  const dur = Math.max(5, opts.duration || 30);
  const minGap = opts.minGap != null ? opts.minGap : 6;
  const llmCall = opts.llmCall || envLlmCall();
  if (!cues.length) return [];

  if (llmCall) {
    try {
      const transcript = cues.map(c => `[${c.start.toFixed(1)}] ${c.text}`).join('\n').slice(0, 24000);
      const system = 'You are a viral short-form video editor. From a timestamped transcript, pick the most clip-worthy moments — strong hooks, payoffs, quotable/surprising lines, complete thoughts. Return ONLY JSON: {"clips":[{"start":<seconds>,"end":<seconds>,"score":<0-10>,"reason":"<why>","title":"<punchy 3-6 word title>"}]} — no prose.';
      const user = `Pick the ${n} best NON-OVERLAPPING moments, each about ${dur}s long (start at a natural sentence start). Transcript (start-seconds prefixed):\n\n${transcript}`;
      const raw = await llmCall(system, user);
      const m = /\{[\s\S]*\}/.exec(String(raw || ''));
      const parsed = m ? JSON.parse(m[0]) : JSON.parse(raw);
      let clips = (parsed.clips || parsed.moments || []).map(c => ({
        start: Math.max(0, +c.start || 0),
        end: +c.end > +c.start ? +c.end : (+c.start || 0) + dur,
        score: Math.max(0, Math.min(10, +c.score || 5)),
        reason: String(c.reason || '').slice(0, 200),
        title: String(c.title || '').slice(0, 80),
      })).filter(c => c.end > c.start);
      clips = dedupeByGap(clips.sort((a, b) => b.score - a.score), minGap).slice(0, n);
      if (clips.length) return clips.sort((a, b) => a.start - b.start);
    } catch (e) { /* fall through to regex fallback */ }
  }

  // regex fallback — always produces something
  const scored = cues.map(c => ({ start: c.start, end: Math.max(c.end, c.start + dur), score: hookScore(c.text), reason: 'hook/keyword match', title: c.text.split(/\s+/).slice(0, 6).join(' ') }))
    .filter(c => c.score > 0).sort((a, b) => b.score - a.score);
  const out = dedupeByGap(scored, minGap).slice(0, n);
  if (out.length < n) { // top up with evenly-spread cues so we always return n
    const step = Math.max(1, Math.floor(cues.length / n));
    for (let i = 0; i < cues.length && out.length < n; i += step) {
      const c = cues[i];
      if (!out.some(o => Math.abs(o.start - c.start) < minGap)) out.push({ start: c.start, end: c.start + dur, score: 0.1, reason: 'even spread', title: c.text.split(/\s+/).slice(0, 6).join(' ') });
    }
  }
  return out.sort((a, b) => a.start - b.start);
}
function dedupeByGap(clips, minGap) {
  const kept = [];
  for (const c of clips) if (!kept.some(k => Math.abs(k.start - c.start) < minGap)) kept.push(c);
  return kept;
}

module.exports = { selectHighlights, parseSrt, parseJson, hookScore, srtTimeToSec, secToClock };

// ---- CLI ----------------------------------------------------------------
if (require.main === module) {
  (async () => {
    const arg = (k, d) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : d; };
    const srtPath = arg('--srt'), jsonPath = arg('--json');
    if (!srtPath && !jsonPath) { console.log('usage: node highlight-select.cjs --srt t.srt [--clips 6] [--duration 30] [--out clips.json]\n  env for LLM: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL (OpenAI-compatible; else regex fallback)'); process.exit(0); }
    let cues = [];
    if (srtPath) cues = parseSrt(fs.readFileSync(srtPath, 'utf8'));
    else cues = parseJson(JSON.parse(fs.readFileSync(jsonPath, 'utf8')));
    const clips = await selectHighlights({ cues, clips: +arg('--clips', 6), duration: +arg('--duration', 30) });
    const out = arg('--out');
    const json = JSON.stringify(clips, null, 2);
    if (out) { fs.writeFileSync(out, json); console.log(`✓ ${clips.length} highlights → ${out} (${envLlmCall() ? 'LLM' : 'regex-fallback'})`); }
    else console.log(json);
  })().catch(e => { console.error(e.message); process.exit(1); });
}
