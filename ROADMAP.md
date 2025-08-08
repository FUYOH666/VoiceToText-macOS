# SuperWhisper Roadmap

This roadmap outlines staged improvements. Pick by priority; each stage is
independent.

## Stage 1 — UX/Quality (short term)

- Settings window (rumps/pyobjc):
  - toggles: auto_paste_enabled, force_mode, delays
  - sliders: VAD sensitivity, max recording duration
- History of last transcripts (in-memory + save to file)
- Better errors: human‑readable alerts with tips
- Optional sound cues: start/stop recording

## Stage 2 — Performance/Memory

- Move transcription to a separate process (multiprocessing)
  - isolates RAM, guarantees memory release
  - crash safety: auto‑restart worker
- Periodic memory profiling and logs
- Optional model size selector (tiny/base/small) with UI hint

## Stage 3 — Models/Accuracy

- Language auto‑detect
- Configurable language list
- Punctuation model improvements or switchable backends
- Simple diacritics and sentence splitting

## Stage 4 — Distribution

- Provide signed .app builds in GitHub Releases
- Basic crash logs collection (opt‑in), local only
- Auto‑update check for new releases (no telemetry)

## Stage 5 — Developer Experience

- Pre‑commit: ruff/black/isort
- GitHub Actions: lint + tests on push
- Makefile targets: setup, run, test, package, clean

## Stage 6 — Nice‑to‑have

- Small floating widget (start/stop) instead of only menu bar
- Hotkey customization UI
- Export to Markdown/Notes from history
