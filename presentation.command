#!/bin/bash
# Запись того, как TrendAgent делает презентацию (для настройки бота)
cd "$(dirname "$0")"
.venv/bin/python -m bot.login --presentation
