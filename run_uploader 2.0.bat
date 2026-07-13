@echo off
title Rumble Video Uploader + Embed Grabber - Virowatch
cd /d "%~dp0"

REM --- Check if Python is installed ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Installing dependencies...
    python -m pip install selenium webdriver-manager
) else (
    echo ^ Python found!
)

echo.
echo ==========================================
echo   RUMBLE VIDEO UPLOADER V2 STARTING...
echo ==========================================
echo.

REM --- Start Chrome with Debug Port ---
echo Starting Chrome on debug port 8989...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=8989 --user-data-dir="C:\Selenium\Chrome_Test_Profile"

echo.
echo ^ Chrome started! Log in to https://rumble.com if needed.
echo   Waiting 15 seconds before starting the uploader...
timeout /t 15 >nul

REM ─────────────────────────────────────────
REM  PHASE 1: UPLOAD ALL VIDEOS
REM ─────────────────────────────────────────
echo.
echo ==========================================
echo   PHASE 1: UPLOADING VIDEOS...
echo ==========================================
echo.
cd "%~dp0"
python rumble_uploader_v10.py

echo.
echo ==========================================
echo   UPLOAD PHASE COMPLETE!
echo ==========================================
echo.

REM ─────────────────────────────────────────
REM  PHASE 2: GRAB EMBED URLS
REM ─────────────────────────────────────────
echo ==========================================
echo   PHASE 2: GRABBING EMBED URLS...
echo ==========================================
echo.
echo   The grabber will now open your content page and
echo   collect Embed iframe URLs from your uploaded videos.
echo   You will be asked how many videos to process.
echo.
timeout /t 3 >nul

cd "%~dp0"
python rumble_embed_grabber4.py

echo.
echo ==========================================
echo   ALL DONE! Check embed_urls.txt
echo ==========================================
pause
