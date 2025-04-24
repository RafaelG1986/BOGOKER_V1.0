@echo off
REM filepath: c:\xampp\htdocs\BOGOKER_V1.0\telegram_bot\botrunner.bat
cd /d C:\xampp\htdocs\BOGOKER_V1.0
python telegram_bot\bot.py
echo Bot iniciado con PID: %ERRORLEVEL% > telegram_bot\bot_runner.log