@echo off
chcp 65001 >nul
title PromotionPilot AI - Cai dat lan dau
echo ============================================================
echo   PROMOTIONPILOT AI - CAI DAT LAN DAU TIEN
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/4] Dang kiem tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo LOI: May tinh nay chua cai Python.
    echo Vui long tai Python tai: https://www.python.org/downloads/
    echo QUAN TRONG: khi cai dat, nho TICK vao o "Add Python to PATH".
    echo Sau khi cai xong Python, chay lai file nay.
    echo.
    pause
    exit /b 1
)
echo     Da tim thay Python.
echo.

echo [2/4] Dang tao moi truong lam viec rieng (chi lam 1 lan)...
if not exist ".venv" (
    python -m venv .venv
)
echo     Xong.
echo.

echo [3/4] Dang cai dat cac thu vien can thiet (co the mat 2-5 phut, can Internet)...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo LOI: Cai dat thu vien that bai. Vui long kiem tra ket noi Internet roi chay lai file nay.
    pause
    exit /b 1
)
echo     Xong.
echo.

echo [4/4] Dang chuan bi du lieu demo de dung thu...
if not exist "data\pharmacity_demo.csv" (
    ".venv\Scripts\python.exe" scripts\generate_pharmacity_demo.py
)
echo     Xong.
echo.

echo ============================================================
echo   CAI DAT HOAN TAT!
echo   Tu lan sau, chi can bam vao file "CHAY_UNG_DUNG.bat" de mo app.
echo ============================================================
echo.
pause
