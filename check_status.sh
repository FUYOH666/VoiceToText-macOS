#!/bin/bash

# SuperWhisper - Проверка статуса системы

echo "🎤 SuperWhisper - Проверка статуса"
echo "=================================="

# Проверяем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено"
    echo "Запустите: ./install_and_run.sh"
    exit 1
fi

# Проверяем Python
if ! ./venv/bin/python --version >/dev/null 2>&1; then
    echo "❌ Python в виртуальном окружении не работает"
    exit 1
fi

echo "✅ Система готова к работе"
echo "🚀 Для запуска: superwhisper"
