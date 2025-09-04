# 🎤 SuperWhisper - Локальная диктовка для macOS

> Полностью оффлайн решение для диктовки с автоматической вставкой текста

## ✨ Особенности

- **100% локально** - без облачных API
- **Автовставка** - текст автоматически вставляется в активное приложение
- **Кастомный словарь** - поддержка профессиональных терминов
- **Русский язык** - оптимизировано для русского языка
- **Простота** - одна команда для запуска

## 🚀 Быстрый старт

### 1. Установка
```bash
./install_and_run.sh
```

### 2. Запуск
```bash
# Из любой директории
superwhisper
```

## ⌨️ Управление

- **Option + Space** - начать/остановить запись
- **Иконка в меню**: 🎤 (готов) / 🔴 (запись)
- **Текст вставляется автоматически** в место курсора

## 📚 Кастомный словарь

Отредактируйте файлы в папке `vocabulary/`:
- `custom_terms.json` - ваши профессиональные термины
- `abbreviations.json` - сокращения (AI, ML, API)
- `names.json` - имена и специальные слова

## 🛠 Технические детали

- **Модель**: MLX Whisper Large v3
- **Python**: 3.12+
- **macOS**: 12.0+
- **Архитектура**: оптимизировано для Apple Silicon

## 📂 Структура проекта

```
SuperWhisper/
├── superwhisper          # Исполняемый файл
├── superwhisper.py       # Основное приложение
├── config.yaml           # Конфигурация
├── requirements.txt      # Зависимости
├── install_and_run.sh    # Скрипт установки
├── vocabulary/           # Кастомный словарь
└── src/                  # Исходный код
```

## 🔧 Настройка

Основные настройки в `config.yaml`:
```yaml
ui:
  auto_paste_enabled: true
  auto_paste_delay: 0.1

audio:
  sample_rate: 16000

whisper:
  model_name: "mlx-community/whisper-large-v3"
  language: "ru"

vocabulary:
  enabled: true
```

## 🐛 Устранение проблем

### Автовставка не работает
1. Добавьте Python в Accessibility: System Settings → Privacy & Security → Accessibility
2. Или включите `force_mode` в config.yaml

### Нет звука при записи
1. Проверьте микрофон в System Settings → Sound
2. Перезапустите приложение

### Ошибки с зависимостями
```bash
rm -rf venv
./install_and_run.sh
```

---

**SuperWhisper** - простое и надежное решение для локальной диктовки! 🎤✨