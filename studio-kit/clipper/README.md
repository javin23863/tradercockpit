# YouTube Auto-Clipper

Drop a YouTube URL or video file → get 6 subtitled short clips in `output/`.

## 3-step setup (one time)

1. **Install Node.js 16+** — https://nodejs.org (pick the LTS installer)
2. **Install the three tools** the clipper uses (all free + open source):
   - Windows:
     ```
     pip install yt-dlp openai-whisper
     choco install ffmpeg
     ```
     (If you don't have `pip`, install Python 3 first from python.org. If you don't have `choco`, download ffmpeg from ffmpeg.org and add the `bin/` folder to PATH.)
   - Mac:
     ```
     brew install yt-dlp ffmpeg
     pip3 install openai-whisper
     ```
   - Linux:
     ```
     sudo apt install ffmpeg python3-pip
     pip install yt-dlp openai-whisper
     ```
3. **Verify**: open this folder in a terminal and run `node check-deps.js` — should show three green checkmarks.

## How to use

### Option A — Just double-click `start.bat` (Windows)

It will check dependencies, then prompt you for a YouTube URL or local file path. Paste, press enter, walk away. Clips land in `output/`.

### Option B — Drop a video in the `input/` folder

Open `input/`, drop your `.mp4` (or `.mov` / `.mkv` / `.webm`) in there, double-click `start.bat`, press enter at the prompt. It'll pick up the video automatically.

### Option C — Command line

```bash
# YouTube URL
node clip.js https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Local file
node clip.js ./input/my-video.mp4

# Customize
node clip.js https://youtu.be/abc --clips 10 --duration 20 --mode hooks
```

## What you get

`output/` will contain:
```
transcript.srt                              ← full video transcript (SRT)
transcript.txt                              ← full video transcript (plain text)
manifest.json                               ← which timestamps each clip came from

clip-001-hook-1-stop-doing-this.mp4         ← with subtitles BURNED IN
clip-001-hook-1-stop-doing-this.srt         ← the matching SRT, as a separate file
clip-002-hook-2-the-secret-nobody.mp4
clip-002-hook-2-the-secret-nobody.srt
clip-003-hook-3-i-wish-i-knew-this.mp4
clip-003-hook-3-i-wish-i-knew-this.srt
clip-004-hook-4-watch-what-happens.mp4
clip-004-hook-4-watch-what-happens.srt
clip-005-hook-5-the-real-reason.mp4
clip-005-hook-5-the-real-reason.srt
clip-006-hook-6-this-changed-everything.mp4
clip-006-hook-6-this-changed-everything.srt
```

Every clip has subtitles **burned in** (Arial Bold, white text, black outline, bottom-center) AND the **matching `.srt` file** is saved next to it so you can edit, re-burn, or upload the captions separately (YouTube/Instagram/TikTok all accept `.srt`).

## Modes

| Mode | What it does |
|---|---|
| `hooks` (default) | Transcribes the whole video, picks the most attention-grabby sentences (questions, "here's why...", "I never...", strong-verb hooks) and centers a clip on each |
| `even` | Divides the video into N equally-spaced clips |
| `script` | You supply a JSON file with exact timestamps: `--script timestamps.json` |

Example `timestamps.json` for `--mode script`:
```json
{
  "segments": [
    { "start": 12,  "duration": 30, "label": "intro-hook" },
    { "start": 87,  "duration": 45, "label": "main-point" },
    { "start": 230, "duration": 20, "label": "punchline" }
  ]
}
```

## Just want the transcript? (no clipping)

```bash
node transcribe.js https://youtube.com/watch?v=...
```

Produces three files in `output/`:
- `transcript.srt` — SRT with timestamps
- `transcript.txt` — plain text
- `transcript.json` — structured cues

Or double-click `transcribe.bat`.

## All available flags

| Flag | Default | Notes |
|---|---|---|
| `--clips N` | 6 | Number of clips |
| `--duration S` | 30 | Seconds per clip |
| `--mode` | hooks | hooks / even / script |
| `--model` | small | Whisper model: tiny / base / small / medium / large-v3 |
| `--output` | ./output | Where the clips land |
| `--keep-source` | off | Keep the downloaded source video + raw SRT (debug) |

Bigger Whisper models = better transcription but slower:
- `tiny`   — ~30s for a 10-min video, OK accuracy
- `small`  — ~1.5min, good accuracy (recommended)
- `medium` — ~4min, very good
- `large-v3` — ~10min, excellent (overkill for most use)

## Optional: use OpenAI's Whisper API instead of local

If your machine is slow and you'd rather pay ~$0.006 per minute of audio for cloud transcription:

1. Copy `.env.example` to `.env`
2. Set `OPENAI_API_KEY=sk-...` and `USE_OPENAI_WHISPER=1`
3. Re-run `node clip.js` — it'll auto-route through the API

You still need ffmpeg and yt-dlp installed locally either way.

## Troubleshooting

| Problem | Fix |
|---|---|
| `node check-deps.js` shows `whisper: NOT FOUND` after install | Restart your terminal. Python sometimes needs a shell restart to expose `whisper` on PATH |
| `yt-dlp: command not found` | `pip install yt-dlp`; on Windows you may need to add Python's Scripts/ folder to PATH |
| `ffmpeg: command not found` after installing | Add the ffmpeg `bin/` folder to your system PATH and restart your terminal |
| Whisper takes forever | Use a smaller model (`--model tiny` or `--model base`), or switch to the OpenAI API (above) |
| Clip has no subtitles burned in | That segment may have been silent; try a different `--mode` or open `manifest.json` to see what got picked |
| Downloaded video is low quality | yt-dlp default is `bestvideo[height<=1080]+bestaudio`. Edit `clip.js` line ~85 to remove the height cap if you want 4K |

## License

MIT.
