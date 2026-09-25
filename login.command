#!/bin/bash
# Вход в TrendAgent в окне браузера: бот запомнит вход
cd "$(dirname "$0")"
.venv/bin/python -m bot.login
