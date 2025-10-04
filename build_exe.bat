@echo off
echo ====================================
echo Photo Watermark Tool - Builder
echo ====================================
echo.

echo [1/3] Installing dependencies...
py -m pip install Pillow>=10.0.0 tkinterdnd2>=0.3.0 pyinstaller>=6.0.0
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo Done!
echo.

echo [2/3] Building executable...
echo (This may take a few minutes...)
py -m PyInstaller --onefile --windowed --name=PhotoWatermark --clean watermark_app.py
if %errorlevel% neq 0 (
    echo ERROR: Build failed!
    echo.
    echo Possible reasons:
    echo - Python version too new (Recommend 3.11 or 3.12)
    echo - PyInstaller incompatible with current Python
    echo.
    echo Try using build_exe_cx.bat instead
    pause
    exit /b 1
)
echo Done!
echo.

echo [3/3] Copying files...
if exist "dist\PhotoWatermark.exe" (
    copy "dist\PhotoWatermark.exe" "PhotoWatermark.exe" >nul
    echo Done!
    echo.
    echo ====================================
    echo BUILD SUCCESSFUL!
    echo.
    echo Executable locations:
    echo 1. dist\PhotoWatermark.exe
    echo 2. PhotoWatermark.exe (current folder)
    echo.
    echo Tips:
    echo - The exe file can run independently
    echo - Just double-click to start
    echo - First run may be slow
    echo ====================================
) else (
    echo ERROR: exe file not found
    echo.
    echo ====================================
    echo BUILD FAILED
    echo Please check the dist folder
    echo ====================================
)
echo.
pause
