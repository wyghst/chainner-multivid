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

:: Install dependencies if needed
if not exist "node_modules\" (
    echo.
    echo node_modules not found - running npm install...
    npm install
    if errorlevel 1 (
        echo ERROR: npm install failed.
        pause
        exit /b 1
    )
)

echo.
echo Starting chainner-multivid...
echo ^(The app window will open. Close it or press Ctrl+C here to stop.^)
echo.

npm start
