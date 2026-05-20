@echo off
setlocal

echo === chainner-multivid test launcher ===
echo.

:: Check Node.js
where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found.
    echo Install it from https://nodejs.org  ^(LTS recommended^)
    pause
    exit /b 1
)
for /f "delims=" %%v in ('node --version') do set NODE_VER=%%v
echo Node.js %NODE_VER% found.

:: Pull latest from git
echo.
echo Pulling latest changes...
git pull origin update/dependencies
echo.

:: Install / sync dependencies
echo Syncing dependencies...
call npm install --legacy-peer-deps --no-audit
if errorlevel 1 (
    echo ERROR: npm install failed.
    pause
    exit /b 1
)

echo.
echo Starting chainner-multivid...
echo ^(Close the app window to return here.^)
echo.

call npm start
echo.
echo App closed.
pause
