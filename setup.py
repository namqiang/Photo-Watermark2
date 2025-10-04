from cx_Freeze import setup, Executable
import sys

# 依赖配置
build_exe_options = {
    "packages": [
        "tkinter",
        "PIL",
        "tkinterdnd2",
        "os",
        "json",
        "pathlib",
        "traceback"
    ],
    "include_files": [],
    "excludes": ["unittest", "test", "email", "html", "http", "urllib", "xml"],
    "optimize": 2,
}

# Windows GUI 应用（不显示控制台窗口）
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="图片水印工具",
    version="1.0.0",
    description="图片批量添加水印工具 - Photo Watermark Tool",
    author="AI Assistant",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "watermark_app.py",
            base=base,
            target_name="图片水印工具.exe",
            icon=None
        )
    ],
)
