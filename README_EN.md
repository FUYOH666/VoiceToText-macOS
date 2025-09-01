# 🎤 SuperWhisper - Local Voice Dictation for macOS

> Fast offline speech recognition with automatic text insertion. Works without internet!

![macOS](https://img.shields.io/badge/macOS-12.0+-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Apple Silicon](https://img.shields.io/badge/Apple_Silicon-Optimized-red)

## ✨ Features

- 🔒 **100% Privacy** - everything works locally, no data sent to cloud
- ⚡ **Apple Silicon Optimized** - uses MLX Whisper for maximum speed
- 🎯 **Auto Text Insertion** - text appears right at your cursor
- 🎤 **Simple Controls** - Option+Space to record/stop
- 📱 **Menu Bar App** - doesn't clutter your desktop
- 🇷🇺 **Excellent Russian** - quality punctuation and recognition

## 🚀 Quick Start

### 1. Install and Run (one command)

```bash
git clone https://github.com/FUYOH666/VoiceToText-macOS.git
cd VoiceToText-macOS
./install_and_run.sh
```

### 2. Grant Permissions

macOS will ask for:
- **Microphone** - to record your voice
- **Accessibility** - for automatic text insertion

### 3. Usage

1. Menu bar icon 🎤 will appear
2. Open any app and place your cursor
3. Press **Option+Space** → speak → press **Option+Space** again
4. Text automatically inserts! ✨

## 🖥 System Requirements

### Minimum
- **macOS** 12.0+ (Monterey)
- **Processor** Apple Silicon (M1/M2/M3) or Intel with AVX2
- **Memory** 8 GB RAM
- **Storage** 4 GB free space

### Recommended
- **macOS** 13.0+ (Ventura)
- **Processor** Apple Silicon (M1/M2/M3)
- **Memory** 16 GB RAM

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
ui:
  auto_paste_enabled: true        # Enable auto text insertion
  auto_paste_force_mode: true     # Works in all applications
  
audio:
  max_recording_duration: 600     # Maximum 10 minutes recording

punctuation:
  mode: "conservative"            # Punctuation mode
```

## 🛠 Troubleshooting

| Problem | Solution |
|---------|----------|
| Auto-paste not working | Add Python to **System Settings → Accessibility** |
| No microphone access | Allow in **System Settings → Privacy → Microphone** |
| App frozen | Use menu item **"Clear Memory"** |
| Won't start | Make sure **Python 3.11+** is installed |

## 🏗 Architecture

```
🎤 Microphone → 🧠 MLX Whisper → ✏️ Punctuation → 📋 Auto-paste
```

- **MLX Whisper** - speech recognition (optimized for Apple Silicon)
- **Silero VAD** - voice activity detection
- **Smart Punctuation** - automatic punctuation restoration
- **Auto-paste** - insertion into any application

## 📁 Project Structure

```
SuperWhisper/
├── superwhisper.py          # Main application
├── config.yaml              # Settings
├── install_and_run.sh       # Installation script
├── requirements.txt         # Dependencies
└── src/                     # Source code
    ├── whisper_service.py   # Speech recognition
    ├── auto_paste.py        # Auto text insertion
    ├── punctuation_service.py # Punctuation
    └── ...
```

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

MIT License - see [LICENSE](LICENSE)

## 🌟 Support the Project

If SuperWhisper was helpful:
- ⭐ Star the project on GitHub
- 🐛 Report bugs in Issues
- 💡 Suggest improvements
- 🔄 Share with friends

---

**SuperWhisper** - fast, private, and convenient dictation for your Mac! 🚀

[🇷🇺 Russian README](README.md)