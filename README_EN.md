# 🎤 SuperWhisper - Privacy-First Voice Dictation for macOS

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)

[Русская версия](README.md) | [English README](README_EN.md)

**Professional offline voice dictation tool for macOS that prioritizes privacy and works completely without internet connection.**

SuperWhisper is a native macOS menu bar application providing instant voice-to-text transcription with automatic text insertion. Designed for professionals who value privacy, work in secure environments, or need reliable dictation without cloud dependencies.

## 🎯 **Professional Use Cases**

### **Enterprise & Security**
- **Legal/Medical professionals**: Secure dictation for confidential documents
- **Government/Defense**: Air-gapped systems and classified environments  
- **Financial services**: Compliance with data protection regulations
- **Enterprise environments**: No data transmission outside corporate networks

### **Performance & Reliability**
- **Content creators**: Fast, accurate transcription for writers and journalists
- **Remote professionals**: Reliable operation in low-connectivity areas
- **Accessibility support**: Alternative input method for users with disabilities
- **Multilingual workflows**: Russian punctuation and capitalization support

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

Note: models are not downloaded automatically.

- Whisper (MLX) is used ONLY locally. Download the model manually and place
  the files into `./models` (see “Models” below).
- VAD and Punctuation also work locally and will cache into `./cache`.

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

How to prepare Whisper (MLX) manually:

1) Open the public model page `mlx-community/whisper-large-v3-mlx`.
2) Download the MLX model files (e.g. `config.json` and `weights.npz`).
3) Put them into the `./models` folder next to the project.
4) Ensure `config.yaml` has `models.whisper.path: "./models"`.

After that, the app runs fully offline with no tokens and no internet.

## 🏗️ **Architecture & Performance**

### **Apple Silicon Optimization**
- **MLX Framework**: Native Apple Silicon acceleration
- **Memory Efficiency**: Smart model caching and lazy loading
- **Real-time Processing**: Faster than real-time transcription
- **System Integration**: Native macOS APIs for optimal performance

### **Privacy Engineering**
- **Zero Network**: No internet connection required or used
- **Local Processing**: All computation happens on your Mac
- **No Telemetry**: No data collection or usage statistics
- **Secure by Design**: Meeting enterprise security requirements

## 🚀 **Build Distribution (Optional)**

For professional deployment:

```bash
./venv/bin/pip install pyinstaller
./venv/bin/pyinstaller \
  --windowed \
  --name "SuperWhisper" \
  --icon icon_256x256.png \
  --add-data "config.yaml:." \
  superwhisper.py
```

## 🤝 **Professional Development**

This project demonstrates expertise in:
- **macOS Native Development**: System integration and menu bar applications
- **AI/ML Engineering**: State-of-the-art speech recognition implementation
- **Performance Optimization**: Apple Silicon acceleration and memory management
- **Privacy Engineering**: Secure, offline-first application architecture
- **User Experience Design**: Intuitive professional software development

## 📄 **License & Contact**

- **License**: MIT - Free for personal and commercial use
- **Author**: Aleksandr Mordvinov
- **Portfolio**: Professional demonstration of AI and macOS development skills
- **Contact**: [iamfuyoh@gmail.com](mailto:iamfuyoh@gmail.com)
- **LinkedIn**: [aleksandr-mordvinov](https://www.linkedin.com/in/aleksandr-mordvinov-3bb853325/)

**⭐ Star this project if you find it useful for your professional work!**
