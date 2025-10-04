@echo off
chcp 65001 >nul
echo ====================================
echo     图片水印工具 - 构建可执行文件
echo     Photo Watermark Tool Builder
echo ====================================
echo.

echo [1/3] 正在安装 cx_Freeze...
py -m pip install cx_Freeze
if %errorlevel% neq 0 (
    echo 错误: cx_Freeze 安装失败！
    pause
    exit /b 1
)
echo      完成！
echo.

echo [2/3] 正在构建可执行文件...
py setup.py build
if %errorlevel% neq 0 (
    echo 错误: 构建失败！
    pause
    exit /b 1
)
echo      完成！
echo.

echo [3/3] 正在复制到桌面...
set BUILD_DIR=build
for /d %%d in (%BUILD_DIR%\exe.win-*) do (
    set EXE_DIR=%%d
    goto :found
)
:found

if exist "%EXE_DIR%\图片水印工具.exe" (
    copy "%EXE_DIR%\图片水印工具.exe" "图片水印工具.exe" >nul
    echo      完成！
    echo.
    echo ====================================
    echo  构建成功！
    echo.
    echo  可执行文件位置:
    echo  1. %EXE_DIR%\图片水印工具.exe
    echo  2. 图片水印工具.exe ^(当前目录^)
    echo.
    echo  注意: 运行 exe 需要将整个文件夹一起复制
    echo ====================================
) else (
    echo      未找到生成的 exe 文件
    echo.
    echo ====================================
    echo  构建完成，但 exe 文件位置可能不同
    echo  请查看: %BUILD_DIR% 文件夹
    echo ====================================
)
echo.
pause
