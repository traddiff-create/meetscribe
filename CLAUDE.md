# MeetScribe — macOS Port

**Fork of:** [pretyflaco/meetscribe](https://github.com/pretyflaco/meetscribe)
**Location:** `/Applications/Apps/meetscribe/`
**Branch:** `feat/macos-port`

## What This Is

Fully local meeting transcription with speaker diarization, AI summaries, and PDF output.
Originally Linux-only (PulseAudio/PipeWire + GTK3). This fork adds macOS support (CLI-only).

## Tech Stack

- Python 3.10+, Click (CLI), ReportLab (PDF)
- WhisperX + faster-whisper (transcription)
- pyannote-audio (speaker diarization)
- Ollama (AI summaries, local)
- ffmpeg + AVFoundation (macOS audio capture)
- BlackHole (virtual audio driver for system audio)

## Architecture

- `meet/capture.py` — Platform dispatcher (Linux uses PulseAudio, macOS uses `capture_macos.py`)
- `meet/capture_macos.py` — macOS AVFoundation audio capture via ffmpeg
- `meet/transcribe.py` — WhisperX pipeline with MPS/CUDA/CPU auto-detection
- `meet/cli.py` — Click CLI entrypoint
- `meet/pdf.py`, `meet/summarize.py`, `meet/label.py` — Cross-platform modules

## macOS Prerequisites

```bash
brew install ffmpeg blackhole-2ch
# Then: Audio MIDI Setup → Create Multi-Output Device → Check speakers + BlackHole
```

## Conventions

- Platform checks use `platform.system() == "Darwin"`
- macOS-specific code lives in dedicated `_macos.py` modules
- Conventional commits: feat/fix/refactor/docs
