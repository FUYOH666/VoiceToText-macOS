# 🎤 SuperWhisper - Локальная диктовка для macOS

> Быстрое офлайн распознавание речи с автоматической вставкой текста. Работает без интернета!

![macOS](https://img.shields.io/badge/macOS-12.0+-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Apple Silicon](https://img.shields.io/badge/Apple_Silicon-Optimized-red)

## ✨ Особенности

- 🔒 **100% приватность** - всё работает локально, без отправки данных в облако
- ⚡ **Apple Silicon оптимизация** - использует MLX Whisper для максимальной скорости
- 🎯 **Автоматическая вставка** - текст появляется прямо в курсоре
- 🎤 **Простое управление** - Option+Space для записи/остановки
- 📱 **Живет в меню-баре** - не загромождает рабочий стол
- 🇷🇺 **Отличный русский** - качественная пунктуация и распознавание

## 🚀 Быстрый старт

### 1. Установка и запуск (одна команда)

```bash
git clone https://github.com/FUYOH666/VoiceToText-macOS.git
cd VoiceToText-macOS
./install_and_run.sh
```

### 2. Настройка разрешений

macOS попросит разрешения:
- **Микрофон** - для записи голоса
- **Accessibility** - для автовставки текста

### 3. Использование

1. В меню-баре появится иконка 🎤
2. Откройте любое приложение и поставьте курсор
3. Нажмите **Option+Space** → говорите → снова **Option+Space**
4. Текст автоматически вставится! ✨

## 🖥 Системные требования

### Минимальные
- **macOS** 12.0+ (Monterey)
- **Процессор** Apple Silicon (M1/M2/M3) или Intel с AVX2
- **Память** 8 ГБ RAM
- **Место** 4 ГБ свободного места

### Рекомендуемые
- **macOS** 13.0+ (Ventura)
- **Процессор** Apple Silicon (M1/M2/M3)
- **Память** 16 ГБ RAM

## ⚙️ Настройка

Отредактируйте `config.yaml`:

```yaml
ui:
  auto_paste_enabled: true        # Автовставка текста
  auto_paste_force_mode: true     # Работает во всех приложениях
  
audio:
  max_recording_duration: 600     # Максимум 10 минут записи

punctuation:
  mode: "conservative"            # Режим пунктуации
```

## 🛠 Решение проблем

| Проблема | Решение |
|----------|---------|
| Не работает автовставка | Добавьте Python в **System Settings → Accessibility** |
| Нет доступа к микрофону | Разрешите в **System Settings → Privacy → Microphone** |
| Приложение зависло | Используйте пункт меню **"Очистить память"** |
| Не запускается | Убедитесь что установлен **Python 3.11+** |

## 🏗 Архитектура

```
🎤 Микрофон → 🧠 MLX Whisper → ✏️ Пунктуация → 📋 Автовставка
```

- **MLX Whisper** - распознавание речи (оптимизировано для Apple Silicon)
- **Silero VAD** - определение начала/конца речи
- **Умная пунктуация** - автоматическая расстановка знаков препинания
- **Автовставка** - вставка в любое приложение

## 📁 Структура проекта

```
SuperWhisper/
├── superwhisper.py          # Главное приложение
├── config.yaml              # Настройки
├── install_and_run.sh       # Установка
├── requirements.txt         # Зависимости
└── src/                     # Исходный код
    ├── whisper_service.py   # Распознавание речи
    ├── auto_paste.py        # Автовставка
    ├── punctuation_service.py # Пунктуация
    └── ...
```

## 🤝 Участие в разработке

1. Fork проекта
2. Создайте ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## 📜 Лицензия

MIT License - см. [LICENSE](LICENSE)

## 🌟 Поддержите проект

Если SuperWhisper оказался полезным:
- ⭐ Поставьте звездочку на GitHub
- 🐛 Сообщите о багах в Issues
- 💡 Предложите улучшения
- 🔄 Поделитесь с друзьями

---

**SuperWhisper** - быстрая, приватная и удобная диктовка для вашего Mac! 🚀

[🇬🇧 English README](README_EN.md)