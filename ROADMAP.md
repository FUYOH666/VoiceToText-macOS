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
- Packaging as DMG installer for macOS

## Stage 5 — Developer Experience

- Pre‑commit: ruff/black/isort
- GitHub Actions: lint + tests on push
- Makefile targets: setup, run, test, package, clean

## Stage 6 — Nice‑to‑have

- Small floating widget (start/stop) instead of only menu bar
- Hotkey customization UI
- Export to Markdown/Notes from history

## Дополнительно — Упаковка приложения

### Создание установочного файла для macOS

1. Подготовка приложения для распространения:
   - Сборка .app с помощью PyInstaller
   - Подпись приложения (для распространения за пределами App Store)
   - Нотаризация приложения (требование Apple для распространения)

2. Создание DMG установщика:
   - Подготовка шаблона DMG с иконкой приложения
   - Автоматическое копирование .app в DMG
   - Настройка автоматического монтирования и установки

3. Системные требования:
   - macOS 12.0 (Monterey) или новее
   - Apple Silicon (M1/M2/M3) или Intel с поддержкой AVX2
   - 8 ГБ RAM (рекомендуется 16 ГБ)
   - 4 ГБ свободного места на диске (для моделей и кэша)
   - Доступ к микрофону

4. Совместимость:
   - Поддержка всех версий macOS от Monterey до последней
   - Поддержка Rosetta 2 для Intel Mac
   - Совместимость с темными и светлыми темами macOS