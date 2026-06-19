@echo off
REM Сборка автономного exe патчера
python -m PyInstaller --onefile --windowed --name "OverTheHillPatcher" ^
  --add-data "data.json;." ^
  --collect-all customtkinter ^
  --hidden-import psutil ^
  oth_patcher.py
echo.
echo Готово: dist\OverTheHillPatcher.exe
pause
