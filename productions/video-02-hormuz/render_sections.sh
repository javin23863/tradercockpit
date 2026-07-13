#!/usr/bin/env bash
# Render the video-02 chart/card sections one at a time, each in its own
# timeboxed subprocess with chrome cleanup between — immunizes against the
# between-section / chrome-launch hang that wedged the all-in-one run. GPU
# compositing (MG3D_GPU=1) ~0.15s/frame; a section is ~1000 frames (~2.5min),
# 420s timeout gives margin even under battery contention. Skips existing.
set -u
cd "C:/Users/MSI/Desktop/OpenMontage-Skill" || exit 1
export MG3D_GPU=1
VIS="productions/video-02-hormuz/visuals"
LOG="productions/video-02-hormuz/build/render-sections.log"
: > "$LOG"

kill_chrome() {
  powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { (\$_.Name -eq 'chrome.exe' -and \$_.CommandLine -match 'puppeteer') -or (\$_.Name -eq 'node.exe' -and \$_.CommandLine -match 'html3d') } | ForEach-Object { try { Stop-Process -Id \$_.ProcessId -Force -ErrorAction Stop } catch {} }" >/dev/null 2>&1
}

# card 07 + 09 are '<NN>-card.mp4'; charts 04/06/08 are '<NN>-chart.mp4'
# Timeout sized for the CONTENDED rate (~1.7s/frame while the mes-m1-cat1 battery
# shares the box); a section is ~1000 frames -> ~1700s, so 2400s completes with
# margin. Uncontended (GPU alone) a section is ~150s and finishes long before.
#
# LESSON (2026-07-13): heavy fragment shaders (tc-card.html bg=bulb, a power-8
# Mandelbulb raymarcher) trip the Windows GPU TDR watchdog under MG3D_GPU=1 —
# chrome's GPU process dies deterministically mid-render (~frame 720 for 09).
# Sections using bg=bulb must render WITHOUT MG3D_GPU (swiftshader, ~7s/frame
# but TDR-immune). 09 is excluded from the GPU loop below for that reason.
declare -A SUFFIX=( [07]=card [09]=card [04]=chart [06]=chart [08]=chart )
for NN in 07 04 06 08; do
  OUT="$VIS/${NN}-${SUFFIX[$NN]}.mp4"
  if [ -f "$OUT" ]; then echo "[skip] ${NN}-${SUFFIX[$NN]}.mp4 exists" | tee -a "$LOG"; continue; fi
  echo "[render] section $NN starting $(date +%H:%M:%S)" | tee -a "$LOG"
  timeout 2400 python tools/visuals/render_visuals_v02.py --only "$NN" >> "$LOG" 2>&1
  rc=$?
  kill_chrome
  if [ -f "$OUT" ]; then
    echo "[done] section $NN -> $(basename "$OUT") $(date +%H:%M:%S)" | tee -a "$LOG"
  else
    echo "[FAIL] section $NN rc=$rc (no output) $(date +%H:%M:%S)" | tee -a "$LOG"
  fi
done
# 09 (bg=bulb) on software rendering — see TDR note above
if [ ! -f "$VIS/09-card.mp4" ]; then
  echo "[render] section 09 (software, TDR-safe) starting $(date +%H:%M:%S)" | tee -a "$LOG"
  env -u MG3D_GPU timeout 9000 python tools/visuals/render_visuals_v02.py --only 09 >> "$LOG" 2>&1
  kill_chrome
fi

n=$(ls "$VIS"/{04-chart,06-chart,08-chart,07-card,09-card}.mp4 2>/dev/null | wc -l)
echo "[complete] $n/5 chart+card sections present $(date +%H:%M:%S)" | tee -a "$LOG"
