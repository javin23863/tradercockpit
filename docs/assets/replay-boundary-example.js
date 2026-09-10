(() => {
  const NS = "http://www.w3.org/2000/svg";
  const input = document.querySelector("[data-replay-cutoff]");
  const output = document.querySelector("[data-replay-output]");
  const safe = document.querySelector("[data-replay-safe]");
  const leaky = document.querySelector("[data-replay-leaky]");
  const safeSummary = document.querySelector("[data-replay-safe-summary]");
  const leakySummary = document.querySelector("[data-replay-leaky-summary]");
  if (!input || !output || !safe || !leaky || !safeSummary || !leakySummary) return;

  const bars = Array.from({ length: 24 }, (_, i) => {
    const open = 100 + Math.sin(i * 0.73) * 3.2 + i * 0.18;
    const close = open + Math.sin(i * 1.31 + 0.6) * 2.1;
    return { open, close, high: Math.max(open, close) + 0.8 + (i % 3) * 0.22, low: Math.min(open, close) - 0.7 - (i % 4) * 0.17 };
  });
  const make = (tag, attrs = {}) => { const node = document.createElementNS(NS, tag); for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value)); return node; };

  function draw(svg, cutoff, showFuture) {
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", "0 0 640 280");
    const min = Math.min(...bars.map((bar) => bar.low));
    const max = Math.max(...bars.map((bar) => bar.high));
    const y = (value) => 244 - ((value - min) / (max - min)) * 200;
    const step = 24.5;
    for (let row = 0; row < 5; row++) svg.appendChild(make("line", { x1: 26, y1: 44 + row * 50, x2: 614, y2: 44 + row * 50, class: "replay-grid-line" }));    bars.forEach((bar, i) => {
      if (!showFuture && i > cutoff) return;
      const x = 36 + i * step;
      const future = i > cutoff;
      const group = make("g", { class: future ? "replay-future" : "replay-visible" });
      group.appendChild(make("line", { x1: x, y1: y(bar.high), x2: x, y2: y(bar.low), class: "replay-candle-line" }));
      const top = Math.min(y(bar.open), y(bar.close));
      const height = Math.max(2, Math.abs(y(bar.open) - y(bar.close)));
      group.appendChild(make("rect", { x: x - 5, y: top, width: 10, height, rx: 1, class: bar.close >= bar.open ? "replay-candle-body" : "replay-candle-body replay-candle-down" }));
      svg.appendChild(group);
    });
    const cutoffX = 36 + cutoff * step + step / 2;
    svg.appendChild(make("line", { x1: cutoffX, y1: 26, x2: cutoffX, y2: 252, class: "replay-cutoff-line" }));
    const label = make("text", { x: Math.min(cutoffX + 8, 540), y: 22, class: "replay-cutoff-label" });
    label.textContent = `cutoff after bar ${cutoff + 1}`;
    svg.appendChild(label);
    svg.setAttribute("aria-label", showFuture
      ? `Invalid comparison: ${bars.length} synthetic OHLC bars shown, including ${bars.length - cutoff - 1} future bars after the replay cutoff.`
      : `Information-safe replay: ${cutoff + 1} synthetic OHLC bars shown and ${bars.length - cutoff - 1} future bars withheld.`);
  }

  function update() {
    const cutoff = Number(input.value);
    const hidden = bars.length - cutoff - 1;
    output.textContent = `Bar ${cutoff + 1} of ${bars.length}`;
    safeSummary.textContent = `${cutoff + 1} completed synthetic bars visible · ${hidden} future bars withheld.`;
    leakySummary.textContent = `${hidden} future bars remain visible here only to demonstrate an invalid replay boundary.`;
    draw(safe, cutoff, false);
    draw(leaky, cutoff, true);
  }
  input.addEventListener("input", update);
  update();
})();