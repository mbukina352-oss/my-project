#!/bin/bash
# Запуск на Mac: двойной клик по файлу
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null; then
  echo "Python не установлен: скачайте с https://www.python.org/downloads/"; read -r; exit 1
fi
if [ ! -d .venv ]; then
  echo "Первый запуск: устанавливаю всё нужное, это займёт 3-5 минут..."
  python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt \
    && .venv/bin/python -m playwright install chromium || { rm -rf .venv; read -r; exit 1; }
fi
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Откроется TextEdit: впишите свои данные, сохраните (Cmd+S) и запустите start.command снова."
  open -e .env; exit 0
fi
echo "Бот запущен. Не закрывайте это окно."
.venv/bin/python -m bot.main
