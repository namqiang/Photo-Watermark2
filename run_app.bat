@echo off
echo Starting Photo Watermark Tool...
echo.

REM Try different Python commands
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo Found: python
    python watermark_app.py
    goto :end
)

where python3 >nul 2>&1
if %errorlevel% equ 0 (
    echo Found: python3
    python3 watermark_app.py
    goto :end
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    echo Found: py launcher
    py watermark_app.py
    goto :end
)

REM Try common installation paths
set PYTHON_PATHS=C:\Users\xuexue\AppData\Local\Programs\Python\Python314\python.exe;C:\Users\xuexue\AppData\Local\Programs\Python\Python313\python.exe;C:\Users\xuexue\AppData\Local\Programs\Python\Python312\python.exe;C:\Users\xuexue\AppData\Local\Programs\Python\Python311\python.exe;C:\Python314\python.exe;C:\Python313\python.exe;C:\Python312\python.exe;C:\Python311\python.exe

for %%p in (%PYTHON_PATHS%) do (
    if exist "%%p" (
        echo Found: %%p
        "%%p" watermark_app.py
        goto :end
    )
)

echo.
echo ERROR: Python not found!
echo.
echo Please install Python from: https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation
echo.
pause
exit /b 1

:end
if %errorlevel% neq 0 (
    echo.
    echo Error running the application!
    pause
)
