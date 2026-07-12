#!/usr/bin/env node
/**
 * arsenal-fetch.cjs — populate the assets/ library with real CC0 (public-domain) assets.
 *
 * Source: Poly Haven (CC0 — free for any use, no attribution required). HDRIs, PBR textures,
 * and 3D props that feed BOTH the Unreal cinematic pipeline and the Three/Hyperframes renderer.
 *
 * Idempotent: skips anything already on disk. Binaries are .gitignored; this script + the
 * generated _INDEX-assets.json are the committed catalog. Re-run with bigger --counts to scale
 * toward the 10GB library.
 *
 * Usage:
 *   node arsenal-fetch.cjs                 # default batch
 *   node arsenal-fetch.cjs --hdris 12 --textures 10 --models 10 --res 2k
 */
const fs = require('fs');
const cp = require('child_process');
const path = require('path');

const ARSENAL = __dirname + '/arsenal';
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const N_HDRI = +arg('hdris', 8);
const N_TEX = +arg('textures', 6);
const N_MODEL = +arg('models', 8);
const RES = arg('res', '2k');

const curl = (url) => cp.execSync(`curl -sL --max-time 40 "${url}"`, { maxBuffer: 1 << 26 }).toString();
const curlJSON = (url) => JSON.parse(curl(url));
const download = (url, dest) => {
  if (fs.existsSync(dest) && fs.statSync(dest).size > 0) return 'skip';
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  cp.execSync(`curl -sL --max-time 180 "${url}" -o "${dest}"`);
  return (fs.statSync(dest).size / 1048576).toFixed(2) + 'MB';
};

const index = { source: 'Poly Haven (CC0)', generated_by: 'arsenal-fetch.cjs', res: RES, hdris: [], textures: [], models: [] };

// ---- selection: pull the API catalog and pick a relevant, diverse spread ----
function pick(type, want, matchTags) {
  const all = curlJSON(`https://api.polyhaven.com/assets?type=${type}`);
  const ids = Object.keys(all);
  const scored = ids.map(id => {
    const a = all[id];
    const tags = ((a.categories || []).concat(a.tags || [])).join(' ').toLowerCase();
    const hit = matchTags.filter(t => tags.includes(t)).length;
    return { id, hit, name: a.name || id };
  }).filter(x => x.hit > 0).sort((a, b) => b.hit - a.hit);
  return scored.slice(0, want);
}

// ---------- HDRIs (lighting + reflections; used by Unreal SkyLight + Three IBL) ----------
console.log(`\n== HDRIs (${N_HDRI}) ==`);
try {
  const sel = pick('hdris', N_HDRI, ['studio', 'indoor', 'sunset', 'night', 'office', 'urban', 'skies']);
  for (const s of sel) {
    const files = curlJSON(`https://api.polyhaven.com/files/${s.id}`);
    const node = files.hdri && files.hdri[RES] && files.hdri[RES].hdr;
    if (!node) { console.log(`  - ${s.id} (no ${RES} hdr)`); continue; }
    const dest = `${ARSENAL}/three-hyperframes/hdris/${s.id}_${RES}.hdr`;
    const r = download(node.url, dest);
    index.hdris.push({ id: s.id, file: path.relative(ARSENAL, dest), tags: s.hit });
    console.log(`  + ${s.id} ${r}`);
  }
} catch (e) { console.log('  HDRI batch error:', e.message); }

// ---------- PBR textures (surface realism) ----------
console.log(`\n== Textures (${N_TEX}) ==`);
try {
  const sel = pick('textures', N_TEX, ['wood', 'concrete', 'metal', 'fabric', 'brick', 'stone', 'plaster', 'floor', 'marble', 'tiles']);
  const MAPS = ['Diffuse', 'nor_gl', 'Rough', 'AO', 'Displacement', 'Metal'];
  for (const s of sel) {
    const files = curlJSON(`https://api.polyhaven.com/files/${s.id}`);
    const dir = `${ARSENAL}/stock/textures/${s.id}`;
    let got = [];
    for (const m of MAPS) {
      const node = files[m] && files[m][RES] && (files[m][RES].jpg || files[m][RES].png);
      if (!node) continue;
      const ext = node.url.split('.').pop();
      download(node.url, `${dir}/${s.id}_${m}_${RES}.${ext}`);
      got.push(m);
    }
    index.textures.push({ id: s.id, maps: got, dir: path.relative(ARSENAL, dir) });
    console.log(`  + ${s.id} [${got.join(',')}]`);
  }
} catch (e) { console.log('  Texture batch error:', e.message); }

// ---------- 3D prop models (glTF, auto-material on import) ----------
console.log(`\n== Models (${N_MODEL}) ==`);
try {
  // curated office/tech/set-dressing props (relevant to "guy at a computer" narrative scenes)
  const wanted = ['classic_laptop', 'desk_lamp_arm_01', 'WoodenTable_02', 'WoodenChair_01',
    'CoffeeTable_01', 'Rockingchair_01', 'wooden_picture_frame_01', 'potted_plant_01',
    'office_chair_01', 'cardboard_box_01', 'ceramic_vase_01', 'books_set_01'];
  let count = 0;
  for (const id of wanted) {
    if (count >= N_MODEL) break;
    let files;
    try { files = curlJSON(`https://api.polyhaven.com/files/${id}`); } catch { console.log(`  - ${id} (404)`); continue; }
    const g = files.gltf && files.gltf[RES] && files.gltf[RES].gltf;
    if (!g) { console.log(`  - ${id} (no ${RES} gltf)`); continue; }
    const dir = `${ARSENAL}/unreal/environments/props/${id}`;
    download(g.url, `${dir}/${path.basename(g.url)}`);
    for (const rel of Object.keys(g.include || {})) download(g.include[rel].url, path.join(dir, rel));
    index.models.push({ id, dir: path.relative(ARSENAL, dir), gltf: path.basename(g.url) });
    console.log(`  + ${id}`);
    count++;
  }
} catch (e) { console.log('  Model batch error:', e.message); }

fs.writeFileSync(`${ARSENAL}/_INDEX-assets.json`, JSON.stringify(index, null, 2));
const total = index.hdris.length + index.textures.length + index.models.length;
console.log(`\nDONE — ${index.hdris.length} HDRIs, ${index.textures.length} textures, ${index.models.length} models (${total} assets). Catalog: arsenal/_INDEX-assets.json`);
