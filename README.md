# 🎸 Guitar Extractor

**Made by Hai Guriel**

Isolate the guitar from any song. Built-in player with A/B loop, tempo control, and UVR de-reverb / de-crowd. PySide6 + Demucs + audio-separator.

![Main interface](docs/screenshots/01_main_interface.png)

---

## What it does

Feed it a **YouTube link** or a **local audio file**. It runs Demucs' 6-stem model
(`htdemucs_6s`) and gives you back:

- `<song>_guitar.wav` — the isolated guitar track, great for transcribing or learning a riff.
- `<song>_no_guitar.wav` — everything else (drums + bass + vocals + piano + other), perfect as a backing track to jam over.

Then it drops you into a built-in player with A/B/C switching, a scrubbable timeline,
**loop A–B** for drilling a tough passage, and a **tempo slider (0.5×–1.5×)** to slow
a solo down and pick it apart.

---

## Features

- 🎯 One-click extraction: guitar + no-guitar backing track
- 🎧 **Built-in player** with instant A/B between the isolated guitar and the backing
- 🔁 **Loop A–B** — set two points, loop the section for practising
- ⏩ **Tempo control** — slow a solo to 0.5× without leaving the app
- ✂️ **Time range** — process only part of a song (saves a lot of time)
- 🎸 **Solo Time mode** — mark the windows where the guitar plays and get a single mix where the guitar only appears inside those windows (the band still plays throughout)
- 🚀 GPU acceleration auto-detected (CUDA)
- 🌍 English / Hebrew UI with RTL layout switching
- ⌨️ Keyboard shortcuts — `Space` play/pause, `Ctrl+Enter` start extract, `Esc` cancel

![Player and progress after extraction](docs/screenshots/02_player_and_progress.png)

---

## Quick start

1. Install **Python 3.10+** (tick *Add Python to PATH* in the installer).
2. Install **FFmpeg**:
   ```powershell
   winget install Gyan.FFmpeg
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   — or double-click `install_dependencies.bat`.
4. Run:
   ```bash
   python main.py
   ```
   — or double-click `run.bat`.

First run will download the Demucs `htdemucs_6s` weights (~350 MB) once.

---

## Pipeline steps

| # | Tool                  | What it does                                                       |
|---|-----------------------|--------------------------------------------------------------------|
| 1 | yt-dlp                | Downloads audio from YouTube (skipped if you uploaded a local file)|
| 2 | ffmpeg                | Converts to 44.1 kHz stereo WAV; trims to your time range if set   |
| 3 | Demucs `htdemucs_6s`  | Splits into drums, bass, vocals, piano, other, **guitar**          |
| 4 | ffmpeg                | Copies the guitar stem; sums the other 5 into the backing track    |
| 5 | UVR (`audio-separator`) | *Optional* — de-reverb / de-crowd each output track              |

Output lands in `<export_folder>/final_result/`. With both UVR boxes ticked you'll
also get `_dry.wav`, `_reverb_echo.wav`, `_clean.wav`, and `_crowd.wav` variants
for every track. The reverb-echo and crowd files are the *isolated residuals* —
exactly what got removed — so they can be layered back in selectively.

**Solo Time** replaces step 4 with a single masked mix — the full band keeps playing,
but the guitar only fades in during the segments you specified.

### Optional UVR models

Place these in [resources/models/](resources/models/) (or `resources/`) to enable the
*Cleanup* options:

- `UVR-DeEcho-DeReverb.pth` — for *Remove reverb / echo*
- `UVR-MDX-NET_Crowd_HQ_1.onnx` — for *Remove crowd noise*

The GUI shows live status under the checkboxes if either model or the
`audio-separator` package is missing.

---

## Requirements

| Component | Minimum                         |
|-----------|---------------------------------|
| OS        | Windows 10 / 11                 |
| Python    | 3.10+                           |
| RAM       | 8 GB (16 GB recommended)        |
| GPU       | Optional — 4+ GB CUDA is 5–10× faster |
| Disk      | ~3 GB for model weights + working space |

---

## Shortcuts

| Key             | Action                |
|-----------------|-----------------------|
| `Ctrl + Enter`  | Start extraction      |
| `Space`         | Play / pause the result |
| `Esc`           | Cancel a running job  |

---

## Troubleshooting

| Problem                      | Fix                                                                                              |
|-----------------------------|--------------------------------------------------------------------------------------------------|
| "yt-dlp not found"           | `pip install -U yt-dlp`                                                                          |
| "ffmpeg not found"           | `winget install Gyan.FFmpeg` (then restart your terminal)                                        |
| Demucs crashes / slow        | Run with CPU only (default); close other apps; ensure ~4 GB free RAM                             |
| Hebrew text looks off        | Switch to English via the header button; Hebrew needs a system font that covers Hebrew glyphs   |

---

## License

For personal use. Made by Hai Guriel. Not affiliated with YouTube, Demucs, or FFmpeg.
