#!/bin/bash
# Скрипт для исправления проблем с accessibility на macOS

echo "🔧 Исправление проблем с accessibility для VTT"
echo ""

# Сбросить настройки accessibility
echo "📋 Сбрасываем настройки accessibility..."
tccutil reset Accessibility

if [ $? -eq 0 ]; then
    echo "✅ Accessibility сброшен успешно"
else
    echo "⚠️  Не удалось сбросить accessibility (требуются права администратора)"
    echo "   Попробуйте: sudo tccutil reset Accessibility"
fi

echo ""
echo "📝 Следующие шаги:"
echo "1. Откройте System Settings → Privacy & Security → Accessibility"
echo "2. Найдите и включите Python (/usr/bin/python3 или /opt/homebrew/bin/python3)"
echo "3. Перезапустите VTT"
echo ""
echo "Если проблема остается:"
echo "- Добавьте полный путь к Python в список"
echo "- Перезагрузите компьютер"
echo "- Проверьте что VTT запущен с правильным Python (./venv/bin/python)"
