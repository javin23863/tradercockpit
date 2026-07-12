# ffmpeg — the Assembly Step

**What it is:** ffmpeg is the universal video swiss-army knife — the tool that assembles all the loose pieces into one finished reel.

## Why it's in the pipeline / what job it does

Everything upstream produces *parts*: rendered frames (still images), a voiceover audio track, and a list of word timings for captions. None of those is a video yet. ffmpeg is the glue that turns those separate pieces into a single, polished MP4 you can post. Specifically, it:

- **Encodes** the rendered frames into an MP4.
- **Stitches scenes together** with smooth crossfades between them (the `xfade` transition).
- **Lays the voiceover** under the visuals so audio and picture line up.
- **Burns in word-timed captions** directly onto the video (`drawtext`), so the words appear exactly when they're spoken.
- **Extracts frames** back out as stills — handy for a quick quality check that a scene looks right.

Think of it as the final station on the line: parts go in, one finished reel comes out.

## Where it lives

ffmpeg is a free, standalone program you install once on your machine — it's the shared assembly utility every render flows through. Get it from [ffmpeg.org/download.html](https://ffmpeg.org/download.html) (or a package manager: `winget install ffmpeg`, `brew install ffmpeg`, `apt install ffmpeg`). Confirm it's on your PATH:

```
ffmpeg -version
```

If that prints a version, the pipeline can find it. Otherwise note the full path to the binary (for example `C:\ffmpeg\bin\ffmpeg.exe` on Windows, or `/usr/local/bin/ffmpeg` on macOS/Linux) and add its folder to your PATH.

## How to use it

You generally don't type ffmpeg commands by hand — the pipeline does it for you. But here's the one real gotcha worth knowing, because it bit us:

When captions are burned in via a `-filter_complex_script`, the caption **font file must be a *relative* path**. A Windows drive-letter path (anything with a `C:\` in it) breaks ffmpeg's filtergraph parser — the colon confuses it. The fix we use: keep a copy of the font named `_capfont.ttf` **in the working directory**, and run ffmpeg **from that directory** so it can find the font by its short, relative name. Do that and captions render cleanly every time.

**Complements:** pairs with the frame renderers (which produce the images it encodes) and the voiceover/caption-timing tools (which produce the audio and word timings it lays in and burns on).
