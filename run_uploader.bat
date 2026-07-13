@echo off
title Rumble Video Uploader - Version 2 (With Categories)!
cd /d "%~dp0"

REM --- Check if Python is installed ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo "Python not found. Installing..."
    python -m pip install selenium webdriver-manager
) else (
    echo "✓ Python found!"
)

echo ""
echo "=========================================="
echo "   RUMBLE VIDEO UPLOADER V2 STARTING...     "
echo "=========================================="
echo ""

REM --- Start Chrome with Debug Port First ---
cd C:\Selenium\Chrome_Test_Profile
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=8989 --user-data-dir="C:\Selenium\Chrome_Test_Profile"

echo "✓ Chrome started! Go to https://rumble.com and log in..."
timeout /t 15 >nul

REM --- Run Your Python Script (from current folder) ---
cd "%~dp0"
python rumble_uploader_v9.py

echo ""
echo "=========================================="
echo "   UPLOAD COMPLETE!                      "
echo "=========================================="
pause
