#!/bin/bash
# Бот работает всегда: запускается при входе в Mac, перезапускается при сбое,
# не даёт Mac уснуть, пока он на зарядке. Выключить: bash autostart_off.command
LABEL="ru.planirovki.bot"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/planirovki"

# Фоновым программам macOS не даёт читать Рабочий стол, поэтому бот живёт в домашней папке
if [ "$SRC" != "$DEST" ]; then
  if [ -e "$DEST" ]; then
    echo "Папка $DEST уже существует. Переименуйте или удалите её и запустите снова."; exit 1
  fi
  mv "$SRC" "$DEST" || exit 1
  echo "Бот перенесён в папку planirovki в вашей домашней папке."
fi
cd "$DEST" || exit 1
[ -x .venv/bin/python ] || { echo "Сначала запустите бота один раз: bash start.command"; exit 1; }
mkdir -p data "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string><string>-is</string>
    <string>$DEST/.venv/bin/python</string><string>-m</string><string>bot.main</string>
  </array>
  <key>WorkingDirectory</key><string>$DEST</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>StandardOutPath</key><string>$DEST/data/bot.log</string>
  <key>StandardErrorPath</key><string>$DEST/data/bot.log</string>
  <key>EnvironmentVariables</key>
  <dict><key>PYTHONUNBUFFERED</key><string>1</string></dict>
</dict>
</plist>
PLIST

launchctl unload "$PLIST" 2>/dev/null
launchctl load -w "$PLIST" || { echo "Не удалось включить автозапуск"; exit 1; }
sleep 8
echo
echo "Готово! Бот работает в фоне, окно Терминала можно закрыть."
echo "Он сам запустится после перезагрузки Mac и перезапустится при сбое."
echo "Последние строки журнала бота:"
tail -5 data/bot.log 2>/dev/null
echo
echo "Теперь все команды выполняйте из новой папки:  cd ~/planirovki"
