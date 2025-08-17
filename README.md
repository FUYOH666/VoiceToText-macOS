# 🎤 SuperWhisper - Privacy-First Voice Dictation for macOS

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)

[English README](README_EN.md) | [Русская версия](README.md)

**A professional offline voice dictation tool for macOS that prioritizes privacy and works completely without internet connection.**

SuperWhisper is a native macOS menu bar application that provides instant voice-to-text transcription with automatic text insertion. Perfect for professionals who value privacy, work in secure environments, or need reliable dictation without cloud dependencies.

## 🎯 **Use Cases & Benefits**

### **💼 Professional Applications**
- **Legal/Medical professionals**: Secure dictation for sensitive documents
- **Journalists & Writers**: Fast content creation without cloud risks
- **Remote workers**: Reliable dictation in low-connectivity environments
- **Privacy-conscious users**: No data ever leaves your Mac

### **⚡ Key Features**
- **🔒 100% Offline**: Zero internet dependency, complete privacy
- **⌨️ Instant Integration**: Auto-paste to any active application
- **🎛️ System-level Control**: Option+Space hotkey, menu bar access
- **🧠 Smart Processing**: MLX-accelerated Whisper on Apple Silicon
- **💾 Memory Optimized**: Lazy loading and automatic cleanup
- **🌍 Multi-language**: Russian punctuation and capitalization support

## 🛡️ **Privacy & Security First**

### **Why Offline Matters**
- **🏢 Enterprise Security**: Meets strict corporate data policies
- **⚖️ Legal Compliance**: GDPR, HIPAA, and data sovereignty requirements
- **🔐 Zero Data Leaks**: Nothing ever transmitted or stored externally
- **📱 Always Available**: Works without internet connection

### **Technical Advantages**
- **⚡ Apple Silicon Optimized**: MLX framework for M1/M2/M3 performance
- **🧠 Advanced AI**: WhisperX for superior accuracy
- **💾 Resource Efficient**: Smart memory management and model caching
- **🔄 Real-time Processing**: Instant transcription and text insertion

## 🛠️ **Technology Stack**

### **AI & Machine Learning**
- **MLX Whisper**: Apple's ML framework for optimal Apple Silicon performance
- **Silero VAD**: Voice Activity Detection for smart audio processing
- **Custom Punctuation Models**: Language-specific text enhancement
- **Memory Management**: Intelligent model caching and cleanup

### **System Integration**
- **macOS Native**: Built with system-level APIs for seamless integration
- **Menu Bar App**: Professional system tray application using `rumps`
- **Global Hotkeys**: System-wide keyboard shortcuts with `pynput`
- **Audio Pipeline**: Real-time audio processing with `PyAudio`

### **Performance Optimizations**
- **Lazy Loading**: Models loaded only when needed
- **Memory Efficiency**: Automatic garbage collection and cache management
- **Apple Silicon**: MLX acceleration for M1/M2/M3 processors
- **Async Processing**: Non-blocking UI with background transcription

## 📦 Установка и запуск

Самый быстрый способ:

```bash
./install_and_run.sh
```

Скрипт создаст виртуальное окружение, поставит зависимости и запустит
приложение. При первом запуске macOS попросит разрешения на Доступность
(Accessibility) и Микрофон.

Внимание: модели не скачиваются автоматически.

- Whisper (MLX) используется ТОЛЬКО локально. Скачайте модель вручную и
  положите файлы в каталог `./models` (см. раздел «Модели» ниже).
- VAD и Пунктуация также работают локально и кэшируются в `./cache`.

Ручной запуск после установки:

```bash
./venv/bin/python superwhisper.py
```

## 🔐 Разрешения macOS (важно)

System Settings → Privacy & Security → Accessibility → добавьте Python
(`opt/homebrew/bin/python3.x`) и включите тумблер. При сборке .app — добавьте
само приложение.

## 🕹 Использование

1) Запустите приложение — в меню‑баре появится 🎤
2) Перейдите в приложение, куда нужно вставить текст, поставьте курсор
3) Нажмите Option+Space — запись начнётся (иконка станет 🔴)
4) Скажите фразу и снова нажмите Option+Space — начнётся распознавание
5) Текст автоматически вставится в курсор и скопируется в буфер

В меню доступно:

- Статус и таймер записи
- Начать/остановить запись
- Копировать текст / Показать текст
- О программе
- Очистить память (ручной сброс кешей и сборка мусора)

## ⚙️ Настройка (`config.yaml`)

```yaml
ui:
  auto_paste_enabled: true      # Включить автовставку
  auto_paste_delay: 0.1         # Задержка перед вставкой (секунды)
  auto_paste_force_mode: true   # Принудительная вставка везде

audio:
  max_recording_duration: 600   # Максимальная длительность записи (сек)

performance:
  force_garbage_collection: true       # Принудительный gc после транскрипции
  clear_model_cache_after_use: true    # Чистить кеш моделей после использования

punctuation:
  lazy_load: true                # Ленивая загрузка модели пунктуации

vad:
  lazy_load: true                # Ленивая загрузка модели VAD
```

## 🧠 Память и стабильность

- Ленивая загрузка VAD и Пунктуации — модели инициализируются по требованию
- После каждой транскрипции вызывается централизованный `free_memory()`:
  сборка мусора, очистка кешей (в т.ч. MLX/torch если применимо)
- Меню‑пункт «Очистить память» позволяет выполнить ручной сброс
- Исправлена критичная ошибка macOS «Must only be used from the main thread»:
  все UI‑операции теперь выполняются строго на главном потоке

## 🔬 Модели

- Whisper (MLX) — быстрый инференс на Apple Silicon
- Silero VAD — определение голоса/тишины
- Пунктуация — модель восстановления знаков препинания

Как подготовить Whisper (MLX) вручную:

1) Откройте страницу модели `mlx-community/whisper-large-v3-mlx` (публичная).
2) Скачайте оттуда файлы модели для MLX (например, `config.json` и `weights.npz`).
3) Поместите скачанные файлы в каталог `./models` рядом с проектом.
4) Убедитесь, что в `config.yaml` указано `models.whisper.path: "./models"`.

После этого приложение будет работать полностью офлайн, без каких‑либо токенов
или доступа к интернету.

## 🧪 Тесты

```bash
./venv/bin/python -m pytest -q
```

Локальные проверки:

- `test_auto_paste.py` — проверка автовставки
- `test_basic.py` — базовый запуск и основные операции

## 🗂 Структура проекта

```text
superwhisper.py            # Меню‑бар приложение
config.yaml                # Настройки
install_and_run.sh         # Установка и запуск
src/
  hotkey_manager.py        # Глобальные хоткеи (Option+Space)
  audio_recorder.py        # Запись аудио (PyAudio)
  whisper_service.py       # Whisper (MLX)
  vad_service.py           # VAD (ленивая загрузка)
  punctuation_service.py   # Пунктуация (ленивая загрузка)
  async_processor.py       # Последовательная/параллельная обработка
  auto_paste.py            # Автовставка текста
  notification_service.py  # Уведомления macOS
  memory_manager.py        # Очистка памяти
```

## 🧰 Устранение неполадок

- Автовставка не работает — проверьте Accessibility и `auto_paste_force_mode`
- Нет звука — проверьте доступ к микрофону в System Settings → Privacy
- Приложение «зависло» — нажмите «Очистить память» в меню и попробуйте снова
- Длинные записи — по умолчанию ограничены 10 минутами (`max_recording_duration`)

## 🍏 Как собрать .app для macOS (опционально)

Проще всего через PyInstaller:

```bash
./venv/bin/pip install pyinstaller
./venv/bin/pyinstaller \
  --windowed \
  --name "SuperWhisper" \
  --icon icon_256x256.png \
  --add-data "config.yaml:." \
  superwhisper.py
```

Ищите `dist/SuperWhisper.app`. Для корректной работы выдайте этому приложению
разрешение в Accessibility. Для распространения за пределами своего Mac может
потребоваться подпись/нотарификация.

## 🤝 Вклад

PR и идеи приветствуются: улучшения точности, поддержка новых моделей,
усовершенствование очистки памяти, сборка и дистрибуция.

## 📜 Лицензия

MIT (см. LICENSE).

---

## 🤝 **Contributing & Support**

### **Professional Development**
This project demonstrates advanced skills in:
- **macOS Native Development**: System integration and menu bar applications
- **AI/ML Integration**: Implementing state-of-the-art speech recognition
- **Performance Optimization**: Memory management and Apple Silicon acceleration
- **Privacy Engineering**: Building secure, offline-first applications
- **User Experience**: Creating intuitive, professional software

### **Get Involved**
- 🐛 **Report Issues**: Found a bug? Open an issue
- 💡 **Feature Requests**: Ideas for improvements are welcome  
- 🔧 **Pull Requests**: Contributions following coding standards
- 📧 **Contact**: [iamfuyoh@gmail.com](mailto:iamfuyoh@gmail.com)

### **License & Recognition**
- **MIT License**: Free for personal and commercial use
- **Author**: Aleksandr Mordvinov - [LinkedIn](https://www.linkedin.com/in/aleksandr-mordvinov-3bb853325/)
- **Portfolio Project**: Demonstrating AI, macOS development, and privacy engineering

**⭐ If this project helps you, please star it on GitHub!**
