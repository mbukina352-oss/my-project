#!/bin/bash
# Обновление бота до последней версии (ваши .env, логотип и вход сохраняются)
cd "$(dirname "$0")"
URL="https://codeload.github.com/mbukina352-oss/my-project/zip/refs/heads/claude/trend-agent-planning-umwdo0"
TMP="$(mktemp -d)"
curl -fsSL --retry 8 --retry-all-errors --retry-delay 3 "$URL" -o "$TMP/bot.zip" && unzip -q "$TMP/bot.zip" -d "$TMP" || { echo "Не удалось скачать обновление"; exit 1; }
SRC="$(ls -d "$TMP"/*/ | head -1)"
rm -rf bot && cp -R "$SRC/bot" . \
  && cp "$SRC"/requirements.txt "$SRC"/*.command "$SRC"/README.md "$SRC"/.env.example . \
  && .venv/bin/python -m pip install -q -r requirements.txt \
  && echo "Бот обновлён."
if launchctl list 2>/dev/null | grep -q ru.planirovki.bot; then
  launchctl kickstart -k "gui/$(id -u)/ru.planirovki.bot" && echo "Фоновый бот перезапущен с новой версией."
else
  echo "Запустите его заново: bash start.command"
fi
rm -rf "$TMP"
