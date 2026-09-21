@echo off
chcp 65001 >nul
title PromoPilot AI
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo LOI: Chua cai dat. Vui long bam vao file "CAI_DAT_LAN_DAU.bat" truoc.
    pause
    exit /b 1
)

echo Dang khoi dong PromoPilot AI...
echo Trinh duyet se tu mo sau vai giay tai dia chi http://localhost:8501
echo.
echo *** KHONG DONG cua so nay trong luc dang su dung ung dung. ***
echo De dung ung dung, dong cua so nay hoac bam Ctrl+C.
echo.

".venv\Scripts\python.exe" -m streamlit run app.py

pause
