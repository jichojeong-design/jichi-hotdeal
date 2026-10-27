@echo off
chcp 65001 >nul
title 지치 아뜰리에 (JICHI ATELIER) 핫딜 최저가 판정기
echo ========================================================
echo  [JICHI ATELIER] 실시간 핫딜 최저가 판정기 구동 중...
echo ========================================================
echo.
cd /d "%~dp0"
start http://localhost:8000
python server.py
pause
