"""
Pipeline Worker - runs the full extraction pipeline in a background thread.
Emits signals for progress, logs, ETA, and completion.
"""
import os
import re
import sys
import subprocess
import shutil
import time
from pathlib import Path

import PySide6.QtCore

from utils.helpers import sanitize_cli_filename, detect_gpu, ensure_dir, clean_temp_files, split_audio_segments, apply_gain_match, smart_blend

CROWD_MODEL_PATH = r"C:\Users\haig0\AppData\Local\Programs\Ultimate Vocal Remover\models\MDX_Net_Models\UVR-MDX-NET_Crowd_HQ_1.onnx"
REVERB_MODEL_PATH = r"C:\Users\haig0\AppData\Local\Programs\Ultimate Vocal Remover\models\VR_Models\UVR-DeEcho-DeReverb.pth"


def run_onnx_model(input_wav: str, model_path: str, output_wav: str) -> str:
    """
    Run ONNX model on mono 44.1k audio in overlap-add chunks.
    """
    import librosa
    import numpy as np
    import onnxruntime as ort
    import soundfile as sf

    providers = ["CPUExecutionProvider"]
    try:
        import torch
        if torch.cuda.is_available():
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    except Exception:
        pass

    audio, _sr = librosa.load(input_wav, sr=44100, mono=True)
    audio = audio.astype(np.float32, copy=False)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0:
        audio = audio / peak

    session = ort.InferenceSession(model_path, providers=providers)
    input_name = session.get_inputs()[0].name

    chunk = 10 * 44100
    overlap = 2 * 44100
    step = chunk - overlap
    win = np.hanning(chunk).astype(np.float32)
    out = np.zeros(len(audio), dtype=np.float32)
    weight = np.zeros(len(audio), dtype=np.float32)

    for start in range(0, max(len(audio), 1), step):
        end = min(start + chunk, len(audio))
        piece = audio[start:end]
        if len(piece) < chunk:
            piece = np.pad(piece, (0, chunk - len(piece)))

        inp = piece.astype(np.float32)
        input_dims = len(session.get_inputs()[0].shape)
        if input_dims == 3:
            model_input = inp[None, None, :]
        elif input_dims == 2:
            model_input = inp[None, :]
        else:
            model_input = inp

        pred = session.run(None, {input_name: model_input})[0]
        pred = np.asarray(pred, dtype=np.float32).reshape(-1)[:chunk]

        take = end - start
        out[start:end] += pred[:take] * win[:take]
        weight[start:end] += win[:take]

        if end >= len(audio):
            break

    weight[weight == 0] = 1.0
    out = out / weight
    max_abs = float(np.max(np.abs(out))) if out.size else 0.0
    if max_abs > 1.0:
        out = out / max_abs
    if peak > 0:
        out = out * peak

    sf.write(output_wav, out, 44100)
    return output_wav


class PipelineWorker(PySide6.QtCore.QThread):
    """
    Runs the extraction pipeline:
    1. Download or prepare audio (yt-dlp / copy file)
    2. Convert to WAV if needed (ffmpeg)
    3. Full stem separation (Demucs htdemucs_6s: drums, bass, vocals, other, piano, guitar)
    4. Export ``guitar`` stem and a mix of everything but guitar
    """

    # Signals
    progress = PySide6.QtCore.Signal(int)           # 0-100
    eta_update = PySide6.QtCore.Signal(str)         # human-readable ETA string
    log = PySide6.QtCore.Signal(str)                # log message
    status = PySide6.QtCore.Signal(str)             # short status line
    step_changed = PySide6.QtCore.Signal(int, int)  # current_step, total_steps
    pipeline_finished = PySide6.QtCore.Signal(str)  # output file path
    error = PySide6.QtCore.Signal(str, str)         # error message, suggested fix

    TOTAL_STEPS = 4

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._cancelled = False
        self._start_time = None

    def cancel(self):
        self._cancelled = True

    def run(self):
        self._start_time = time.time()
        temp_files = []

        try:
            cfg = self.config
            export_folder = cfg["export_folder"]
            input_type = cfg["input_type"]  # "youtube" or "file"
            input_value = cfg["input_value"]
            fmt = cfg["format"]
            use_gpu = detect_gpu()

            ensure_dir(export_folder)
            final_dir = os.path.join(export_folder, "final_result")
            ensure_dir(final_dir)
            tmp_dir = os.path.join(export_folder, "_tmp")
            ensure_dir(tmp_dir)

            if use_gpu:
                self.log.emit("🚀 GPU detected — using CUDA acceleration")
            else:
                self.log.emit("💻 No GPU — using CPU (may be slow)")

            # ─── Step 1: Download or prepare audio ───────────────────────
            self._emit_step(1, "Downloading / Preparing audio...")
            self.progress.emit(5)

            if input_type == "youtube":
                audio_path = self._download_youtube(input_value, tmp_dir, fmt)
            else:
                # Copy file to tmp
                src = Path(input_value)
                dst = Path(tmp_dir) / sanitize_cli_filename(src.name)
                shutil.copy2(src, dst)
                audio_path = str(dst)
                self.log.emit(f"Using local file: {src.name}")

            temp_files.append(audio_path)
            song_name = sanitize_cli_filename(Path(audio_path).stem)
            self.progress.emit(20)

            if self._cancelled:
                return

            # ─── Step 2: Convert to WAV if needed ────────────────────────
            wav_path = audio_path
            if not audio_path.endswith(".wav"):
                self._emit_step(2, "Converting to WAV for processing...")
                wav_path = os.path.join(tmp_dir, song_name + ".wav")
                self._run_ffmpeg_convert(audio_path, wav_path)
                temp_files.append(wav_path)
            self.progress.emit(28)

            if self._cancelled:
                return

            time_range = cfg.get("time_range")
            if time_range is not None:
                start_sec, end_sec = time_range
                if start_sec > 0 or end_sec is not None:
                    self.log.emit(
                        f"Trimming to segment: {start_sec:.2f}s → "
                        f"{end_sec if end_sec is not None else 'end of file'}s"
                    )
                    segment_path = os.path.join(tmp_dir, song_name + "_segment.wav")
                    self._ffmpeg_trim_segment(wav_path, segment_path, start_sec, end_sec)
                    wav_path = segment_path
                    temp_files.append(wav_path)

            # ─── SOLO TIME PROCESSING MODE ───────────────────────────────────
            if cfg.get("solo_time_enabled", False) and len(cfg.get("solo_time_segments", [])) > 0:
                self.log.emit("🎸 SOLO TIME MODE ENABLED")
                self._emit_step(3, "Processing full track with Demucs...")
                
                global_start = 0.0
                if time_range is not None:
                    global_start = time_range[0]
                
                solo_segments = cfg["solo_time_segments"]
                
                # Get actual audio duration for the trimmed file
                import librosa
                import numpy as np
                import soundfile as sf
                from utils.helpers_mask import create_fade_mask, apply_solo_mask
                
                duration = librosa.get_duration(path=wav_path)
                sr = 44100
                
                # Convert absolute times (original audio) to relative times (within trimmed segment)
                relative_segments = []
                for start, end in solo_segments:
                    rel_start = start - global_start
                    rel_end = end - global_start
                    if rel_end > 0 and rel_start < duration:
                        rel_start = max(0.0, rel_start)
                        rel_end = min(duration, rel_end)
                        if rel_end > rel_start:
                            relative_segments.append( (rel_start, rel_end) )
                
                self.log.emit(f"Converted {len(solo_segments)} absolute solo segments to {len(relative_segments)} relative segments after trimming")

                # ✅ NEW CORRECT APPROACH: FULL TRACK PROCESSING ONCE
                demucs_full = os.path.join(tmp_dir, "demucs_full")
                ensure_dir(demucs_full)
                self._run_demucs(wav_path, demucs_full, use_gpu)
                
                # Load all 6 stems
                guitar_stem = self._find_stem(demucs_full, "guitar")
                other_stem = self._find_stem(demucs_full, "other")
                drums_stem = self._find_stem(demucs_full, "drums")
                bass_stem = self._find_stem(demucs_full, "bass")
                vocals_stem = self._find_stem(demucs_full, "vocals")
                piano_stem = self._find_stem(demucs_full, "piano")
                
                if not all([guitar_stem, other_stem, drums_stem, bass_stem, vocals_stem, piano_stem]):
                    self.error.emit("Demucs failed to produce all 6 stems", "Check Demucs installation")
                    return

                temp_files.append(demucs_full)
                self.progress.emit(60)
                
                # Load stems as numpy arrays
                self._emit_step(4, "Applying Solo Time masking...")
                
                guitar, _ = librosa.load(guitar_stem, sr=sr, mono=False)
                drums, _ = librosa.load(drums_stem, sr=sr, mono=False)
                bass, _ = librosa.load(bass_stem, sr=sr, mono=False)
                vocals, _ = librosa.load(vocals_stem, sr=sr, mono=False)
                piano, _ = librosa.load(piano_stem, sr=sr, mono=False)
                other, _ = librosa.load(other_stem, sr=sr, mono=False)
                
                # Reconstruct base mix without guitar
                base_mix = drums + bass + vocals + piano + other
                
                # Optional cleaning: run UVR only on guitar stem
                if cfg.get("remove_crowd", False) and os.path.exists(CROWD_MODEL_PATH):
                    self.log.emit("Running Crowd Removal on guitar stem...")
                    temp_guitar = os.path.join(tmp_dir, "guitar_temp.wav")
                    sf.write(temp_guitar, guitar.T, sr)
                    cleaned = run_onnx_model(temp_guitar, CROWD_MODEL_PATH, temp_guitar + "_cleaned.wav")
                    guitar, _ = librosa.load(cleaned, sr=sr, mono=False)
                    temp_files.extend([temp_guitar, cleaned])
                
                # Create time mask
                total_samples = base_mix.shape[1]
                mask = create_fade_mask(total_samples, relative_segments, sr=sr, fade_ms=150)
                
                # Apply masking blend
                output = apply_solo_mask(base_mix, guitar, mask)
                
                # Normalize final output to -1dB
                peak = np.max(np.abs(output))
                if peak > 0:
                    max_peak = 10 ** (-1 / 20)
                    output = output * max_peak / peak
                
                # Save final result
                final_output = os.path.join(final_dir, f"{song_name}_solo_mix.wav")
                sf.write(final_output, output.T, sr)
                
                self.log.emit(f"✅ Final track saved with Solo Time: {final_output}")
                final_path = final_output
                self.progress.emit(90)
                
            else:
                # ─── NORMAL MODE: Full stem separation ────────────────────
                self._emit_step(3, "Separating stems with htdemucs_6s...")
                self.eta_update.emit("~5-15 min depending on file length")
                demucs_out = os.path.join(tmp_dir, "demucs")
                ensure_dir(demucs_out)
                self._run_demucs(wav_path, demucs_out, use_gpu)

                guitar_stem = self._find_stem(demucs_out, "guitar")
                if not guitar_stem:
                    self.error.emit(
                        "Demucs did not produce 'guitar' stem.",
                        "Ensure demucs is installed correctly: pip install demucs"
                    )
                    return

                drums_stem = self._find_stem(demucs_out, "drums")
                bass_stem = self._find_stem(demucs_out, "bass")
                vocals_stem = self._find_stem(demucs_out, "vocals")
                piano_stem = self._find_stem(demucs_out, "piano")
                other_stem = self._find_stem(demucs_out, "other")
                
                missing = [n for n, p in (("drums", drums_stem), ("bass", bass_stem), ("vocals", vocals_stem), ("piano", piano_stem), ("other", other_stem)) if not p]
                if missing:
                    self.error.emit(
                        f"Demucs did not produce stem(s): {', '.join(missing)}.",
                        "Ensure demucs htdemucs_6s completed successfully (check disk space and logs).",
                    )
                    return

                temp_files.append(demucs_out)
                self.progress.emit(60)

                if self._cancelled:
                    return

                # ─── Step 4: Export guitar + mix everything-but-guitar ────────
                self._emit_step(4, "Exporting stems...")
                guitar_name = f"{song_name}_guitar.wav"
                final_guitar_path = os.path.join(final_dir, guitar_name)
                shutil.copy2(guitar_stem, final_guitar_path)
                self.log.emit(f"✅ Saved isolated guitar stem: {final_guitar_path}")
                final_path = final_guitar_path

                # Optional ONNX post-processing on top of `guitar.wav`.
                current_file = final_guitar_path
                if cfg.get("remove_crowd", False):
                    self.log.emit("Running Crowd Removal...")
                    if os.path.exists(CROWD_MODEL_PATH):
                        try:
                            self.log.emit("Crowd model loaded")
                            no_crowd_path = os.path.join(tmp_dir, f"{song_name}_no_crowd.wav")
                            cleaned = run_onnx_model(current_file, CROWD_MODEL_PATH, no_crowd_path)
                            self.log.emit("Crowd extraction complete")

                            crowd_mode = cfg.get("crowd_mode", "remove")
                            crowd_track = os.path.join(final_dir, f"{song_name}_crowd.wav")
                            if crowd_mode == "separate":
                                self._subtract_wavs(current_file, cleaned, crowd_track)
                                current_file = cleaned
                            elif crowd_mode == "mix_light":
                                mixed_path = os.path.join(tmp_dir, f"{song_name}_crowd_mixed.wav")
                                self._mix_back_lightly(current_file, cleaned, mixed_path, crowd_gain=0.2)
                                current_file = mixed_path
                            else:
                                current_file = cleaned
                        except Exception as e:
                            self.log.emit(f"⚠ Crowd ONNX failed, skipping: {e}")
                    else:
                        self.log.emit(f"⚠ Crowd model missing, skipping: {CROWD_MODEL_PATH}")

                if cfg.get("remove_reverb", False):
                    self.log.emit("Reverb removal started")
                    if REVERB_MODEL_PATH.lower().endswith(".onnx") and os.path.exists(REVERB_MODEL_PATH):
                        try:
                            no_reverb_path = os.path.join(tmp_dir, f"{song_name}_no_reverb.wav")
                            current_file = run_onnx_model(current_file, REVERB_MODEL_PATH, no_reverb_path)
                        except Exception as e:
                            self.log.emit(f"⚠ Reverb ONNX failed, skipping: {e}")
                    elif os.path.exists(REVERB_MODEL_PATH):
                        self.log.emit("⚠ Reverb model is not ONNX (.pth); skipping ONNX reverb stage")
                    else:
                        self.log.emit(f"⚠ Reverb model missing, skipping: {REVERB_MODEL_PATH}")

                final_processed = os.path.join(final_dir, f"{song_name}_guitar_final.wav")
                if current_file != final_processed:
                    shutil.copy2(current_file, final_processed)
                self.log.emit(f"Final guitar output saved: {final_processed}")
                final_path = final_processed

                mix_name = f"{song_name}_full_mix_no_guitar.wav"
                mix_path = os.path.join(final_dir, mix_name)
                if not self._ffmpeg_mix_stems([vocals_stem, drums_stem, bass_stem, piano_stem, other_stem], mix_path):
                    self.error.emit(
                        "ffmpeg failed to mix stems.",
                        "Ensure ffmpeg is installed and supports the amix filter.",
                    )
                    return
                self.log.emit(f"✅ Saved everything-but-guitar mix: {mix_path}")
                self.progress.emit(85)

            # ─── Cleanup ──────────────────────────────────────────────────
            if cfg.get("clean_temp", True):
                self.log.emit("Cleaning up temporary files...")
                clean_temp_files(temp_files)
                try:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                except Exception:
                    pass

            elapsed = time.time() - self._start_time
            self.log.emit(f"⏱ Total time: {self._format_time(int(elapsed))}")
            self.progress.emit(100)
            self.eta_update.emit("Done!")
            self.pipeline_finished.emit(final_path)

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.log.emit(f"❌ Unexpected error:\n{tb}")
            self.error.emit(str(e), "Check the log for full details.")

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _emit_step(self, step: int, message: str):
        self.step_changed.emit(step, self.TOTAL_STEPS)
        self.status.emit(message)
        self.log.emit(f"[Step {step}/{self.TOTAL_STEPS}] {message}")

    def _run_cmd(self, cmd: list, label: str = "") -> subprocess.CompletedProcess:
        """Run a subprocess command, streaming output to the log signal."""
        self.log.emit(f"$ {' '.join(str(c) for c in cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        output_lines = []
        for line in process.stdout:
            line = line.rstrip()
            if line:
                self.log.emit(line)
                output_lines.append(line)
                # Parse ETA from yt-dlp style output
                if "[download]" in line and "%" in line:
                    self._parse_ytdlp_eta(line)

        process.wait()
        result = subprocess.CompletedProcess(cmd, process.returncode, "\n".join(output_lines), "")
        return result

    def _parse_ytdlp_eta(self, line: str):
        """Extract ETA from yt-dlp download lines."""
        eta_match = re.search(r'ETA\s+([\d:]+)', line)
        pct_match = re.search(r'(\d+\.?\d*)%', line)
        if eta_match:
            self.eta_update.emit(eta_match.group(1))
        if pct_match:
            try:
                pct = float(pct_match.group(1))
                # Map 0-100% download to 5-20% of total progress
                mapped = int(5 + pct * 0.15)
                self.progress.emit(min(mapped, 19))
            except ValueError:
                pass

    def _download_youtube(self, url: str, out_dir: str, fmt: str) -> str:
        """Download audio from YouTube using yt-dlp."""
        # Keep downloader output ASCII-safe for Windows console tooling.
        out_template = os.path.join(out_dir, "%(title).200B.%(ext)s")
        out_template_fallback = os.path.join(out_dir, "%(id)s.%(ext)s")

        cmd = [
            "yt-dlp",
            "-f", "bestaudio",
            "-x",
            "--audio-format", "wav" if fmt == "wav" else fmt,
            "--audio-quality", "0",
            "-o", out_template,
            "--restrict-filenames",
            "--no-playlist",
            "--no-warnings",
            url
        ]

        result = self._run_cmd(cmd, "yt-dlp")
        if result.returncode != 0:
            # Try fallback
            self.log.emit("Retrying with fallback filename template...")
            cmd[-2] = out_template_fallback
            result = self._run_cmd(cmd, "yt-dlp fallback")
            if result.returncode != 0:
                self.error.emit(
                    "yt-dlp failed to download the audio.",
                    "Check your internet connection, URL validity, and that yt-dlp is up to date: pip install -U yt-dlp"
                )
                raise RuntimeError("yt-dlp download failed")

        # Find downloaded file
        target_ext = "wav" if fmt == "wav" else fmt
        for f in Path(out_dir).iterdir():
            if f.suffix.lstrip(".").lower() in (target_ext, "wav", "webm", "m4a", "opus", "mp3"):
                safe_name = sanitize_cli_filename(f.name)
                safe_path = f.parent / safe_name
                if f.name != safe_name:
                    try:
                        f.rename(safe_path)
                        f = safe_path
                    except Exception:
                        # If rename fails, keep original path; downstream conversion may still succeed.
                        pass
                return str(f)

        raise FileNotFoundError("Downloaded file not found in output directory")

    def _run_ffmpeg_convert(self, src: str, dst: str):
        """Convert audio file to WAV using ffmpeg."""
        cmd = ["ffmpeg", "-y", "-i", src, "-ar", "44100", "-ac", "2", dst]
        result = self._run_cmd(cmd, "ffmpeg")
        if result.returncode != 0:
            self.error.emit(
                "ffmpeg conversion failed.",
                "Ensure ffmpeg is installed and available in PATH."
            )
            raise RuntimeError("ffmpeg conversion failed")

    def _ffmpeg_trim_segment(self, src: str, dst: str, start_sec: float, end_sec: float | None):
        """Extract [start_sec, end_sec) from src; end_sec None means end of file."""
        cmd = ["ffmpeg", "-y", "-i", src, "-ss", str(start_sec)]
        if end_sec is not None:
            cmd += ["-t", str(end_sec - start_sec)]
        cmd += ["-ar", "44100", "-ac", "2", dst]
        result = self._run_cmd(cmd, "ffmpeg trim segment")
        if result.returncode != 0:
            self.error.emit(
                "ffmpeg failed to trim the selected time range.",
                "Check that start/end are valid for this file and that ffmpeg works.",
            )
            raise RuntimeError("ffmpeg trim failed")

    def _has_soundfile(self) -> bool:
        """Check if soundfile backend is available for torchaudio."""
        try:
            import soundfile  # noqa
            return True
        except ImportError:
            return False

    def _run_demucs(self, input_wav: str, out_dir: str, use_gpu: bool):
        """Run Demucs htdemucs_6s stem separation."""
        # Build base command
        def make_cmd(extra_flags=None):
            c = [sys.executable, "-m", "demucs", "-n", "htdemucs_6s", "--out", out_dir]
            if not use_gpu:
                c += ["-d", "cpu"]
            if extra_flags:
                c += extra_flags
            c.append(input_wav)
            return c

        # If soundfile is missing, tell the user and try mp3 output as workaround
        if not self._has_soundfile():
            self.log.emit("⚠ soundfile not found — attempting mp3 stem output as workaround")
            self.log.emit("  → For best results: pip install soundfile")
            result = self._run_cmd(make_cmd(["--mp3"]), "demucs (mp3 mode)")
        else:
            result = self._run_cmd(make_cmd(), "demucs")

        if result.returncode != 0:
            # Final retry with no extra flags
            self.log.emit("Retrying demucs with no extra flags...")
            result = self._run_cmd(make_cmd(), "demucs retry")
            if result.returncode != 0:
                self.error.emit(
                    "Demucs stem separation failed.",
                    "Run: pip install soundfile\nThen retry. Also ensure demucs is up to date: pip install -U demucs"
                )
                raise RuntimeError("Demucs failed")

    def _ffmpeg_mix_stems(self, input_paths: list[str], output_path: str) -> bool:
        """Mix multiple stems into one file (sum without per-input attenuation)."""
        if not input_paths:
            return False
        if len(input_paths) == 1:
            shutil.copy2(input_paths[0], output_path)
            return True
        cmd = ["ffmpeg", "-y"]
        for p in input_paths:
            cmd += ["-i", p]
        n = len(input_paths)
        ins = "".join(f"[{i}:a]" for i in range(n))
        filt = f"{ins}amix=inputs={n}:duration=longest:normalize=0[aout]"
        cmd += [
            "-filter_complex", filt,
            "-map", "[aout]",
            "-ar", "44100",
            "-ac", "2",
            output_path,
        ]
        result = self._run_cmd(cmd, "ffmpeg mix stems")
        return result.returncode == 0

    def _subtract_wavs(self, original_path: str, cleaned_path: str, output_path: str):
        """Write residual = original - cleaned, length-aligned and clipping-safe."""
        import librosa
        import numpy as np
        import soundfile as sf

        original, _ = librosa.load(original_path, sr=44100, mono=True)
        cleaned, _ = librosa.load(cleaned_path, sr=44100, mono=True)
        n = min(len(original), len(cleaned))
        residual = original[:n].astype(np.float32) - cleaned[:n].astype(np.float32)
        peak = float(np.max(np.abs(residual))) if residual.size else 0.0
        if peak > 1.0:
            residual = residual / peak
        sf.write(output_path, residual, 44100)

    def _mix_back_lightly(self, original_path: str, cleaned_path: str, output_path: str, crowd_gain: float = 0.2):
        """Compute mixed = cleaned + crowd_gain * (original - cleaned)."""
        import librosa
        import numpy as np
        import soundfile as sf

        original, _ = librosa.load(original_path, sr=44100, mono=True)
        cleaned, _ = librosa.load(cleaned_path, sr=44100, mono=True)
        n = min(len(original), len(cleaned))
        original = original[:n].astype(np.float32)
        cleaned = cleaned[:n].astype(np.float32)
        crowd = original - cleaned
        mixed = cleaned + float(crowd_gain) * crowd
        peak = float(np.max(np.abs(mixed))) if mixed.size else 0.0
        if peak > 1.0:
            mixed = mixed / peak
        sf.write(output_path, mixed, 44100)

    def _find_stem(self, search_dir: str, stem_name: str) -> str | None:
        """Find a Demucs stem file (e.g. ``.../drums.wav`` or ``..._vocals.wav``)."""
        pat = re.compile(
            rf"(^|_){re.escape(stem_name)}\.(wav|mp3|flac)$",
            re.IGNORECASE,
        )
        for root, _dirs, files in os.walk(search_dir):
            for f in sorted(files):
                fl = f.lower()
                if stem_name == "vocals" and "no_vocals" in fl:
                    continue
                if stem_name == "other" and "not_other" in fl:
                    continue
                if not pat.search(fl):
                    continue
                return os.path.join(root, f)
        return None

    @staticmethod
    def _format_time(seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}s"
        m, s = divmod(seconds, 60)
        if m < 60:
            return f"{m}m {s}s"
        h, m = divmod(m, 60)
        return f"{h}h {m}m {s}s"