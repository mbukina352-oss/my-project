#!/bin/bash
# Выключить фоновую работу бота
PLIST="$HOME/Library/LaunchAgents/ru.planirovki.bot.plist"
launchctl unload -w "$PLIST" 2>/dev/null
rm -f "$PLIST"
echo "Фоновый бот выключен. Запускать вручную: bash start.command"
