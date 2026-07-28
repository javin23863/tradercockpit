// stdin -> AIDetector.analyzeText -> stdout JSON. Local, added by TraderCockpit; not upstream.
// Vendored detector is CommonJS with no CLI of its own.
const chunks = [];
process.stdin.on('data', (c) => chunks.push(c));
process.stdin.on('end', () => {
  const text = Buffer.concat(chunks).toString('utf8');
  const mode = process.argv[2] || 'general';
  process.stdout.write(JSON.stringify(require('./detector/patterns.js').analyzeText(text, { contextMode: mode })));
});
