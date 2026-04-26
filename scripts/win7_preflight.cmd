@echo off
setlocal

set SCRIPT_DIR=%~dp0
set APP_ROOT=%~1
if "%APP_ROOT%"=="" set APP_ROOT=.

where powershell >nul 2>nul
if errorlevel 1 (
  echo [FAIL] PowerShell not found. Cannot run preflight.
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%win7_preflight.ps1" -AppRoot "%APP_ROOT%"
set EXITCODE=%ERRORLEVEL%

if not "%EXITCODE%"=="0" (
  echo [FAIL] win7 preflight failed.
  exit /b %EXITCODE%
)

echo [OK] win7 preflight passed.
exit /b 0
