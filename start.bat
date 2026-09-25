@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Бот планировок

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo Python не установлен. Скачайте его с https://www.python.org/downloads/
  echo При установке обязательно поставьте галочку "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

if not exist .venv (
  echo Первый запуск: устанавливаю всё нужное, это займёт 3-5 минут...
  python -m venv .venv || goto :error
  .venv\Scripts\python -m pip install --upgrade pip -q
  .venv\Scripts\python -m pip install -r requirements.txt -q || goto :error
  .venv\Scripts\python -m playwright install chromium || goto :error
)

if not exist .env (
  copy .env.example .env >nul
  echo.
  echo Сейчас откроется Блокнот. Впишите свои данные, сохраните файл (Ctrl+S),
  echo закройте Блокнот и снова запустите start.bat.
  echo.
  pause
  notepad .env
  exit /b 0
)

echo.
echo Бот запущен. Не закрывайте это окно, пока пользуетесь ботом.
echo.
.venv\Scripts\python -m bot.main
echo.
echo Бот остановился.
pause
exit /b 0

:error
echo.
echo Что-то пошло не так при установке. Сделайте скриншот этого окна и пришлите мне.
rmdir /s /q .venv 2>nul
pause
exit /b 1
