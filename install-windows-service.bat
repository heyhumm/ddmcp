@echo off
REM Windows Service Installation Script for ddmcp
REM Requires NSSM (Non-Sucking Service Manager)
REM Download from: https://nssm.cc/download

echo ========================================
echo ddmcp Windows Service Installer
echo ========================================
echo.

REM Check if NSSM is installed
where nssm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: NSSM is not installed!
    echo.
    echo Please download NSSM from https://nssm.cc/download
    echo Extract it and add the win64 folder to your PATH
    echo.
    pause
    exit /b 1
)

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: uv is not installed!
    echo.
    echo Please install uv from https://docs.astral.sh/uv/getting-started/installation/
    echo.
    pause
    exit /b 1
)

REM Get API credentials from user
set /p DD_API_KEY="Enter your Datadog API Key: "
set /p DD_APP_KEY="Enter your Datadog App Key: "
set /p DD_SITE="Enter your Datadog Site (us1, us3, us5, eu, ap1, gov) [default: us1]: "
if "%DD_SITE%"=="" set DD_SITE=us1

echo.
echo Installing ddmcp service...
echo.

REM Get paths
for %%i in ("%~dp0.") do set DDMCP_DIR=%%~fi
for /f "delims=" %%i in ('where uv') do set UV_PATH=%%i

REM Install service
nssm install ddmcp "%UV_PATH%" "run python -m ddmcp.server"

REM Configure service
nssm set ddmcp AppDirectory "%DDMCP_DIR%"
nssm set ddmcp AppEnvironmentExtra DD_API_KEY=%DD_API_KEY% DD_APP_KEY=%DD_APP_KEY% DD_SITE=%DD_SITE%
nssm set ddmcp DisplayName "Datadog MCP Server"
nssm set ddmcp Description "MCP server for Datadog APM integration"
nssm set ddmcp Start SERVICE_AUTO_START
nssm set ddmcp AppStdout "%DDMCP_DIR%\ddmcp.out.log"
nssm set ddmcp AppStderr "%DDMCP_DIR%\ddmcp.err.log"

REM Start service
echo Starting ddmcp service...
nssm start ddmcp

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Service Status:
nssm status ddmcp
echo.
echo Logs location:
echo   Output: %DDMCP_DIR%\ddmcp.out.log
echo   Errors: %DDMCP_DIR%\ddmcp.err.log
echo.
echo Useful commands:
echo   Start:   nssm start ddmcp
echo   Stop:    nssm stop ddmcp
echo   Restart: nssm restart ddmcp
echo   Status:  nssm status ddmcp
echo   Remove:  nssm remove ddmcp confirm
echo.
pause
