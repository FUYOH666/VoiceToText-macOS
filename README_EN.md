# 🎤 SuperWhisper (local speech‑to‑text for macOS)

[Русская версия](README.md)

SuperWhisper is a tiny offline dictation tool for macOS. Menu‑bar app (🎤),
record/stop with Option+Space, auto‑paste the transcript into the active app.
No internet required.

## Why

- Privacy: everything runs locally on your Mac, no cloud uploads
- Offline: useful on the go, on boats, in the mountains, or when Starlink has
  data caps. Dictate ideas without the internet. Boats are not included 🙂

## Features

- Auto‑paste transcript to the active window
- Option+Space hotkey (start/stop)
- Punctuation and capitalization (RU)
- Clipboard copy
- Native macOS notifications
- Fully offline
- Memory‑friendly: lazy model loading and manual cleanup

## Install & Run

Fastest way:

```bash
./install_and_run.sh
```

Manual run after setup:

```bash
./venv/bin/python superwhisper.py
```

Grant Accessibility/Microphone permissions in macOS System Settings.

## Settings (`config.yaml`)

```yaml
ui:
  auto_paste_enabled: true
  auto_paste_delay: 0.1
  auto_paste_force_mode: true

audio:
  max_recording_duration: 600

performance:
  force_garbage_collection: true
  clear_model_cache_after_use: true

punctuation:
  lazy_load: true

vad:
  lazy_load: true
```

## Models

- Whisper (MLX)
- Silero VAD
- Punctuation model (RU)

## Build .app (optional)

```bash
./venv/bin/pip install pyinstaller
./venv/bin/pyinstaller \
  --windowed \
  --name "SuperWhisper" \
  --icon icon_256x256.png \
  --add-data "config.yaml:." \
  superwhisper.py
```

## License

MIT (see LICENSE).
