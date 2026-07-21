#!/usr/bin/env node
// Deterministic input gate for the thumbnail renderer. The first palette colour
// is the background; every remaining colour must reach WCAG AA against it.
const fs = require("fs");

const DEFAULT_SPEC = {
  eyebrow: "BRENT CRUDE",
  num: "$120?",
  phrase: "The *Hormuz* Toll",
  dir: "",
  sub: "",
  palette: ["#08030a", "#F5E8EA", "#FF1744"],
  logoCorner: "bottom-right",
};

function wordCount(text) {
  return String(text || "").replace(/\*/g, "").trim().split(/\s+/).filter(Boolean).length;
}

function paletteColours(palette) {
  const values = Array.isArray(palette) ? palette : String(palette || "").split(",");
  return [...new Set(values.map(v => String(v).trim().toUpperCase()).filter(Boolean))];
}

function rgb(hex) {
  const value = String(hex).trim();
  const match = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(value);
  if (!match) throw new Error(`invalid palette colour: ${hex}`);
  const full = match[1].length === 3 ? [...match[1]].map(c => c + c).join("") : match[1];
  return [0, 2, 4].map(i => parseInt(full.slice(i, i + 2), 16));
}

function relativeLuminance(hex) {
  const linear = rgb(hex).map(value => {
    const channel = value / 255;
    return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}

function contrastRatio(a, b) {
  const [light, dark] = [relativeLuminance(a), relativeLuminance(b)].sort((x, y) => y - x);
  return (light + 0.05) / (dark + 0.05);
}

function checkThumbnailSpec(input) {
  const spec = {...DEFAULT_SPEC, ...input};
  const title = `${spec.num || ""} ${spec.phrase || ""}`.replace(/\*/g, "").trim();
  const colours = paletteColours(spec.palette);
  const hardFail = [];
  const words = wordCount(title);
  if (words > 5) hardFail.push(`thumbnail title has ${words} words; maximum is 5`);
  if (!/^[+\-]?[$€£¥]?\d/.test(title)) hardFail.push("thumbnail title must lead with a number");
  if (colours.length < 2 || colours.length > 3) {
    hardFail.push(`thumbnail palette has ${colours.length} colours; expected 2-3`);
  }
  let ratios = [];
  try {
    ratios = colours.slice(1).map(colour => ({
      foreground: colour,
      background: colours[0],
      ratio: contrastRatio(colour, colours[0]),
    }));
    for (const item of ratios) {
      if (item.ratio < 4.5) {
        hardFail.push(`${item.foreground} on ${item.background} contrast ${item.ratio.toFixed(2)}:1; minimum is 4.5:1`);
      }
    }
  } catch (error) {
    hardFail.push(error.message);
  }
  if (spec.logoCorner !== "bottom-right") {
    hardFail.push("thumbnail logo corner must be bottom-right");
  }
  return {
    status: hardFail.length ? "BLOCK" : "PASS",
    title,
    wordCount: words,
    palette: colours,
    colourCount: colours.length,
    contrast: ratios.map(item => ({...item, ratio: Number(item.ratio.toFixed(4))})),
    logoCorner: "bottom-right",
    hardFail,
    doesNotProve: [
      "rendered PNG text or colours; this gate validates renderer inputs, not OCR or sampled pixels",
      "mobile-size legibility, subject dominance, or aesthetic quality",
    ],
    spec: {...spec, palette: colours},
  };
}

function selftest() {
  const close = (actual, expected, epsilon = 1e-6) => Math.abs(actual - expected) < epsilon;
  assert(close(contrastRatio("#000000", "#FFFFFF"), 21), "black/white must be 21:1");
  assert(close(contrastRatio("#777777", "#FFFFFF"), 4.4780894536), "WCAG #777/white vector");
  assert(close(contrastRatio("#FF0000", "#000000"), 5.252), "WCAG red/black vector");
  assert(wordCount("$85 Don't Trade the Siren") === 5, "five-word title");
  assert(wordCount("$85 This Title Has Six Words") === 6, "six-word title");
  assert(paletteColours(["#000", "#fff", "#FFF"]).length === 2, "deduplicate colours");
  assert(paletteColours("#000,#fff,#f00").length === 3, "three-colour palette");
  assert(checkThumbnailSpec({num: "$85", phrase: "Don't Trade the *Siren*"}).status === "PASS", "valid spec");
  assert(checkThumbnailSpec({num: "$85", phrase: "This Title Has Six Words"}).status === "BLOCK", "word gate");
  assert(checkThumbnailSpec({palette: ["#000", "#fff", "#f00", "#0f0"]}).status === "BLOCK", "colour gate");
  assert(checkThumbnailSpec({num: "Oil", phrase: "At $85"}).status === "BLOCK", "number-first gate");
  assert(checkThumbnailSpec({palette: ["#FFFFFF", "#777777"]}).status === "BLOCK", "contrast gate");
  assert(checkThumbnailSpec({logoCorner: "top-left"}).status === "BLOCK", "fixed-corner gate");
  console.log("thumbnail rules self-test: 13/13 PASS");
  console.log("contrast vectors: black/white=21.0000, #777/white=4.4781, red/black=5.2520");
}

function assert(ok, message) {
  if (!ok) throw new Error(`self-test failed: ${message}`);
}

if (require.main === module) {
  if (process.argv.includes("--selftest")) {
    selftest();
  } else {
    const index = process.argv.indexOf("--json");
    if (index < 0 || !process.argv[index + 1]) throw new Error("usage: check_thumbnail.cjs --json spec.json | --selftest");
    const result = checkThumbnailSpec(JSON.parse(fs.readFileSync(process.argv[index + 1], "utf8")));
    console.log(JSON.stringify(result, null, 2));
    process.exitCode = result.status === "PASS" ? 0 : 1;
  }
}

module.exports = {DEFAULT_SPEC, checkThumbnailSpec, contrastRatio, paletteColours, wordCount};
