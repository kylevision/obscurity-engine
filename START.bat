@echo off
title OBSCURITY ENGINE v7
color 0A
cls
echo.
echo  ============================================
echo       OBSCURITY ENGINE v7 — FINAL FORM
echo  ============================================
echo.
echo  [*] Starting server...
echo  [*] Browser will open automatically
echo  [*] Close this window to stop the server
echo.
cd /d "%~dp0"
streamlit run app.py --server.headless=true --browser.gatherUsageStats=false
pause
