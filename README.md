# 🎸 Guitar Extractor
**Made by Hai Guriel**

☕ [Support me on Ko-fi](https://ko-fi.com/haiguriel)

A Windows desktop application that downloads audio from YouTube, runs Demucs stem separation, and exports the **`other`** stem plus a mix of **drums + bass + vocals** (everything except `other`).

---

## ✨ Features

- 🎯 **One-click export** of the Demucs `other` stem plus a full mix without it
- 🌍 **English / Hebrew** UI with true RTL layout switching
- 🚀 **GPU acceleration** auto-detected (CUDA)
- 🎛️ **5 output formats**: WAV, MP3, M4A, WebM, Opus
- 🛠️ **Dependency checker** with auto-install
- 📄 **Full logs** saved to export folder
- 🖥️ **Dark modern UI** with smooth design

---

## 🗂️ File Structure

```
guitar_extractor/
├── main.py                    ← Entry point
├── run.bat                    ← Windows launcher
├── install_dependencies.bat   ← Dependency installer
├── requirements.txt
├── gui/
│   ├── main_window.py         ← Main window assembly
│   ├── card_performance.py    ← Card 1: Input & controls
│   ├── card_debug.py          ← Card 2: Logs & progress
│   ├── dep_dialog.py          ← Dependency check dialog
│   └── styles.py              ← Dark theme stylesheet
├── pipeline/
│   ├── worker.py              ← Background pipeline thread
│   └── dep_checker.py         ← Dependency check thread
└── utils/
    ├── translations.py        ← English + Hebrew strings
    ├── settings.py            ← JSON settings + recent files
    └── helpers.py             ← Filename sanitization, GPU detection, etc.
```

---

## 🚀 Quick Start

### 1. Install Python
Download Python 3.10+ from [python.org](https://www.python.org/downloads/)  
✅ Check **"Add Python to PATH"** during installation.

### 2. Install dependencies
Double-click `install_dependencies.bat`  
— or run manually:
```bash
pip install PySide6 yt-dlp demucs soundfile deepfilternet
```

### 3. Install ffmpeg
```bash
winget install Gyan.FFmpeg
```
Or download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

### 4. Run the app
Double-click `run.bat`  
— or:
```bash
python main.py
```

---

## 🎛️ Pipeline Steps

| Step | Tool | What Happens |
|------|------|-------------|
| 1 | yt-dlp | Downloads audio from YouTube |
| 2 | ffmpeg | Converts to WAV if needed |
| 3 | Demucs htdemucs | Separates: vocals, drums, bass, **other** |
| 4 | ffmpeg | Exports `other` as its own file; mixes drums + bass + vocals |

Output is saved to:  
`<export_folder>/final_result/`  
- `<song_name>_other.wav` — the Demucs **other** stem (guitars, keys, etc. in that bin)  
- `<song_name>_everything_but_other.wav` — sum of **drums + bass + vocals** (the rest of the mix)

## ⚙️ Requirements

| Component | Minimum |
|-----------|---------|
| OS | Windows 10/11 |
| Python | 3.10+ |
| RAM | 8 GB (16 GB recommended) |
| VRAM (optional) | 4+ GB NVIDIA GPU for CUDA |
| Disk | ~3 GB for model weights + working space |

---

## 🌍 Languages

Toggle between **English** and **Hebrew** using the flag button in the top-right corner.  
The full UI mirrors for true RTL layout in Hebrew.

---

## 🛠️ Troubleshooting

| Issue | Fix |
|-------|-----|
| "yt-dlp not found" | Run `pip install yt-dlp` |
| "ffmpeg not found" | Install ffmpeg and add to PATH |
| Demucs crashes | Ensure at least 8GB RAM free; try CPU mode |
| Slow processing | Normal on CPU — GPU (NVIDIA CUDA) is 5-10x faster |
| DeepFilterNet skipped | Install with `pip install deepfilternet`; non-fatal |

---

---

## ☕ Support

If you find this tool useful, consider supporting its development:

[![Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/haiguriel)

---

## 📄 License
Made by Hai Guriel. For personal use.
