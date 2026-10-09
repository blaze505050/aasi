@echo off
setlocal
title AASI - Autonomous Aerospace Scientific Intelligence

echo ======================================================================
echo    AASI - Flight-Grade Aerospace Engineering Platform
echo ======================================================================
echo.

if exist .venv\Scripts\python.exe (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
) else (
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% run_aasi.py
pause
