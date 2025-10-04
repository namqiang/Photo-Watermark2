"""
Photo Watermark Tool - 图片水印工具
支持批量添加文本和图片水印
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
import json
from pathlib import Path
import traceback

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片水印工具 - Photo Watermark")
        self.root.geometry("1400x800")

        # 数据存储
        self.images = []  # 存储图片路径
        self.current_image_index = 0
        self.watermark_config = self.default_config()
        self.templates_file = "watermark_templates.json"

        # 缩放和位置相关
        self.current_scale_ratio = 1.0
        self.last_calculated_x = 50
        self.last_calculated_y = 50

        # 创建UI
        self.create_ui()

        # 加载上次的配置
        self.load_last_config()

    def default_config(self):
        """默认配置"""
        return {
            'type': 'text',  # 'text' or 'image'
            'text': '© 版权所有',
            'font_family': 'Arial',
            'font_size': 36,
            'bold': False,
            'italic': False,
            'color': '#FFFFFF',
            'opacity': 128,  # 0-255
            'position': 'bottom_right',
            'offset_x': 50,
            'offset_y': 50,
            'rotation': 0,
            'image_path': '',
            'scale': 1.0,
            'shadow': False,
            'outline': False,
            'outline_color': '#000000'
        }

    def create_ui(self):
        """创建用户界面"""
        # 主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧面板 - 图片列表和导入
        left_panel = ttk.Frame(main_container, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left_panel.pack_propagate(False)

        # 导入按钮区域
        import_frame = ttk.LabelFrame(left_panel, text="导入图片", padding=10)
        import_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(import_frame, text="选择图片", command=self.select_images).pack(fill=tk.X, pady=2)
        ttk.Button(import_frame, text="选择文件夹", command=self.select_folder).pack(fill=tk.X, pady=2)
        ttk.Button(import_frame, text="清空列表", command=self.clear_images).pack(fill=tk.X, pady=2)

        # 拖拽提示
        drag_label = ttk.Label(import_frame, text="或拖拽图片/文件夹到列表",
                               font=('Arial', 9), foreground='gray')
        drag_label.pack(pady=5)

        # 图片列表
        list_frame = ttk.LabelFrame(left_panel, text="图片列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.image_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.image_listbox.pack(fill=tk.BOTH, expand=True)
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)
        scrollbar.config(command=self.image_listbox.yview)

        # 启用拖拽
        self.image_listbox.drop_target_register(DND_FILES)
        self.image_listbox.dnd_bind('<<Drop>>', self.on_drop)

        # 中间面板 - 预览
        center_panel = ttk.Frame(main_container)
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        preview_frame = ttk.LabelFrame(center_panel, text="预览 (实时)", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)

        # 预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg='#2b2b2b')
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas.bind('<Button-1>', self.on_canvas_click)
        self.preview_canvas.bind('<B1-Motion>', self.on_canvas_drag)

        # 右侧面板 - 水印设置和导出
        right_panel = ttk.Frame(main_container, width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_panel.pack_propagate(False)

        # 创建可滚动的设置区域
        canvas_right = tk.Canvas(right_panel)
        scrollbar_right = ttk.Scrollbar(right_panel, orient="vertical", command=canvas_right.yview)
        scrollable_frame = ttk.Frame(canvas_right)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_right.configure(scrollregion=canvas_right.bbox("all"))
        )

        canvas_right.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_right.configure(yscrollcommand=scrollbar_right.set)

        canvas_right.pack(side="left", fill="both", expand=True)
        scrollbar_right.pack(side="right", fill="y")

        # 水印类型选择
        type_frame = ttk.LabelFrame(scrollable_frame, text="水印类型", padding=10)
        type_frame.pack(fill=tk.X, pady=(0, 5))

        self.watermark_type = tk.StringVar(value='text')
        ttk.Radiobutton(type_frame, text="文本水印", variable=self.watermark_type,
                       value='text', command=self.update_preview).pack(anchor=tk.W)
        ttk.Radiobutton(type_frame, text="图片水印", variable=self.watermark_type,
                       value='image', command=self.update_preview).pack(anchor=tk.W)

        # 文本水印设置
        self.text_frame = ttk.LabelFrame(scrollable_frame, text="文本水印设置", padding=10)
        self.text_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.text_frame, text="水印文本:").pack(anchor=tk.W)
        self.text_entry = ttk.Entry(self.text_frame)
        self.text_entry.insert(0, "© 版权所有")
        self.text_entry.pack(fill=tk.X, pady=(0, 10))
        self.text_entry.bind('<KeyRelease>', lambda e: self.update_preview())

        # 字体设置
        font_row = ttk.Frame(self.text_frame)
        font_row.pack(fill=tk.X, pady=5)
        ttk.Label(font_row, text="字号:").pack(side=tk.LEFT)
        self.font_size = tk.IntVar(value=36)
        ttk.Spinbox(font_row, from_=10, to=200, textvariable=self.font_size,
                   width=8, command=self.update_preview).pack(side=tk.LEFT, padx=5)

        # 颜色选择
        color_row = ttk.Frame(self.text_frame)
        color_row.pack(fill=tk.X, pady=5)
        ttk.Label(color_row, text="颜色:").pack(side=tk.LEFT)
        self.color_var = tk.StringVar(value='#FFFFFF')
        self.color_display = tk.Label(color_row, bg='#FFFFFF', width=3, relief=tk.SUNKEN)
        self.color_display.pack(side=tk.LEFT, padx=5)
        ttk.Button(color_row, text="选择", command=self.choose_color).pack(side=tk.LEFT)

        # 透明度
        ttk.Label(self.text_frame, text="透明度:").pack(anchor=tk.W, pady=(10, 0))
        self.opacity = tk.IntVar(value=50)
        opacity_scale = ttk.Scale(self.text_frame, from_=0, to=100,
                                 variable=self.opacity, command=lambda e: self.update_preview())
        opacity_scale.pack(fill=tk.X)

        # 图片水印设置
        self.image_wm_frame = ttk.LabelFrame(scrollable_frame, text="图片水印设置", padding=10)
        self.image_wm_frame.pack(fill=tk.X, pady=5)

        ttk.Button(self.image_wm_frame, text="选择水印图片",
                  command=self.select_watermark_image).pack(fill=tk.X, pady=5)
        self.wm_image_label = ttk.Label(self.image_wm_frame, text="未选择", foreground='gray')
        self.wm_image_label.pack()

        ttk.Label(self.image_wm_frame, text="缩放 (%):").pack(anchor=tk.W, pady=(10, 0))
        self.wm_scale = tk.IntVar(value=100)
        scale_scale = ttk.Scale(self.image_wm_frame, from_=10, to=200,
                               variable=self.wm_scale, command=lambda e: self.update_preview())
        scale_scale.pack(fill=tk.X)

        ttk.Label(self.image_wm_frame, text="透明度:").pack(anchor=tk.W, pady=(10, 0))
        self.img_opacity = tk.IntVar(value=50)
        img_opacity_scale = ttk.Scale(self.image_wm_frame, from_=0, to=100,
                                     variable=self.img_opacity, command=lambda e: self.update_preview())
        img_opacity_scale.pack(fill=tk.X)

        # 位置设置
        position_frame = ttk.LabelFrame(scrollable_frame, text="位置设置", padding=10)
        position_frame.pack(fill=tk.X, pady=5)

        ttk.Label(position_frame, text="预设位置:").pack(anchor=tk.W)

        # 九宫格位置按钮
        grid_frame = ttk.Frame(position_frame)
        grid_frame.pack(pady=5)

        positions = [
            ['top_left', 'top_center', 'top_right'],
            ['middle_left', 'center', 'middle_right'],
            ['bottom_left', 'bottom_center', 'bottom_right']
        ]

        for i, row in enumerate(positions):
            row_frame = ttk.Frame(grid_frame)
            row_frame.pack()
            for pos in row:
                btn = ttk.Button(row_frame, text="●", width=3,
                               command=lambda p=pos: self.set_position(p))
                btn.pack(side=tk.LEFT, padx=2, pady=2)

        ttk.Label(position_frame, text="或在预览区拖拽水印",
                 font=('Arial', 9), foreground='gray').pack()

        # 旋转
        ttk.Label(position_frame, text="旋转角度:").pack(anchor=tk.W, pady=(10, 0))
        self.rotation = tk.IntVar(value=0)
        rotation_scale = ttk.Scale(position_frame, from_=0, to=360,
                                  variable=self.rotation, command=lambda e: self.update_preview())
        rotation_scale.pack(fill=tk.X)

        # 模板管理
        template_frame = ttk.LabelFrame(scrollable_frame, text="模板管理", padding=10)
        template_frame.pack(fill=tk.X, pady=5)

        ttk.Button(template_frame, text="保存当前设置为模板",
                  command=self.save_template).pack(fill=tk.X, pady=2)
        ttk.Button(template_frame, text="加载模板",
                  command=self.load_template).pack(fill=tk.X, pady=2)

        # 导出设置
        export_frame = ttk.LabelFrame(scrollable_frame, text="导出设置", padding=10)
        export_frame.pack(fill=tk.X, pady=5)

        ttk.Label(export_frame, text="输出格式:").pack(anchor=tk.W)
        self.output_format = tk.StringVar(value='PNG')
        format_frame = ttk.Frame(export_frame)
        format_frame.pack(fill=tk.X)
        ttk.Radiobutton(format_frame, text="PNG", variable=self.output_format,
                       value='PNG').pack(side=tk.LEFT)
        ttk.Radiobutton(format_frame, text="JPEG", variable=self.output_format,
                       value='JPEG').pack(side=tk.LEFT)

        ttk.Label(export_frame, text="文件名规则:").pack(anchor=tk.W, pady=(10, 0))
        self.filename_rule = tk.StringVar(value='suffix')
        ttk.Radiobutton(export_frame, text="保留原名", variable=self.filename_rule,
                       value='original').pack(anchor=tk.W)
        ttk.Radiobutton(export_frame, text="添加前缀", variable=self.filename_rule,
                       value='prefix').pack(anchor=tk.W)
        ttk.Radiobutton(export_frame, text="添加后缀", variable=self.filename_rule,
                       value='suffix').pack(anchor=tk.W)

        custom_frame = ttk.Frame(export_frame)
        custom_frame.pack(fill=tk.X, pady=5)
        ttk.Label(custom_frame, text="自定义:").pack(side=tk.LEFT)
        self.custom_affix = ttk.Entry(custom_frame)
        self.custom_affix.insert(0, "_watermarked")
        self.custom_affix.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 导出按钮
        ttk.Button(export_frame, text="导出所有图片",
                  command=self.export_images, style='Accent.TButton').pack(fill=tk.X, pady=(10, 0))

    def select_images(self):
        """选择图片"""
        files = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("所有文件", "*.*")
            ]
        )
        if files:
            self.add_images(files)

    def select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            image_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.JPG', '*.JPEG', '*.PNG']:
                image_files.extend(Path(folder).glob(ext))
            if image_files:
                self.add_images([str(f) for f in image_files])
            else:
                messagebox.showinfo("提示", "文件夹中没有找到图片文件")

    def add_images(self, files):
        """添加图片到列表"""
        for file in files:
            if file not in self.images:
                self.images.append(file)
                self.image_listbox.insert(tk.END, os.path.basename(file))

        if self.images:
            self.image_listbox.selection_clear(0, tk.END)
            self.image_listbox.selection_set(0)
            self.current_image_index = 0
            self.update_preview()

    def clear_images(self):
        """清空图片列表"""
        self.images = []
        self.image_listbox.delete(0, tk.END)
        self.preview_canvas.delete('all')
        self.current_image_index = 0

    def on_drop(self, event):
        """处理拖拽事件"""
        files = self.root.tk.splitlist(event.data)
        image_files = []

        for file in files:
            file = file.strip('{}')
            if os.path.isdir(file):
                # 如果是文件夹，递归查找图片
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.JPG', '*.JPEG', '*.PNG']:
                    image_files.extend(Path(file).glob(ext))
            elif os.path.isfile(file):
                # 检查是否是图片文件
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                    image_files.append(file)

        if image_files:
            self.add_images([str(f) for f in image_files])

    def on_image_select(self, event):
        """切换预览图片"""
        selection = self.image_listbox.curselection()
        if selection:
            self.current_image_index = selection[0]
            self.update_preview()

    def select_watermark_image(self):
        """选择水印图片"""
        file = filedialog.askopenfilename(
            title="选择水印图片",
            filetypes=[
                ("PNG图片", "*.png"),
                ("所有图片", "*.jpg *.jpeg *.png *.bmp")
            ]
        )
        if file:
            self.watermark_config['image_path'] = file
            self.wm_image_label.config(text=os.path.basename(file), foreground='black')
            self.update_preview()

    def choose_color(self):
        """选择颜色"""
        color = colorchooser.askcolor(title="选择水印颜色", initialcolor=self.color_var.get())
        if color[1]:
            self.color_var.set(color[1])
            self.color_display.config(bg=color[1])
            self.update_preview()

    def set_position(self, position):
        """设置水印位置"""
        self.watermark_config['position'] = position
        self.update_preview()

    def on_canvas_click(self, event):
        """记录鼠标点击位置"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_canvas_drag(self, event):
        """拖拽水印"""
        if not hasattr(self, 'drag_start_x') or not hasattr(self, 'current_scale_ratio'):
            return

        try:
            # 计算偏移（考虑图片缩放）
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y

            # 转换为原始图片坐标（除以缩放比例）
            if self.current_scale_ratio > 0:
                dx_original = dx / self.current_scale_ratio
                dy_original = dy / self.current_scale_ratio
            else:
                dx_original = dx
                dy_original = dy

            # 初始化位置（如果是第一次拖拽）
            if self.watermark_config.get('position') != 'custom':
                # 从预设位置转换为自定义位置
                if hasattr(self, 'last_calculated_x') and hasattr(self, 'last_calculated_y'):
                    self.watermark_config['offset_x'] = self.last_calculated_x
                    self.watermark_config['offset_y'] = self.last_calculated_y
                else:
                    self.watermark_config['offset_x'] = 50
                    self.watermark_config['offset_y'] = 50

            # 更新位置
            self.watermark_config['offset_x'] += dx_original
            self.watermark_config['offset_y'] += dy_original

            self.drag_start_x = event.x
            self.drag_start_y = event.y

            self.watermark_config['position'] = 'custom'
            self.update_preview()
        except Exception as e:
            print(f"拖拽错误: {e}")
            traceback.print_exc()

    def update_preview(self):
        """更新预览"""
        if not self.images or self.current_image_index >= len(self.images):
            return

        try:
            # 加载原图
            image_path = self.images[self.current_image_index]
            original = Image.open(image_path)

            # 保持纵横比缩放以适应预览区
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            if canvas_width < 100:  # 初始化时
                canvas_width = 800
                canvas_height = 600

            # 计算缩放比例
            ratio = min(canvas_width / original.width, canvas_height / original.height)
            ratio = min(ratio, 1.0)  # 不放大

            # 保存当前缩放比例供拖拽使用
            self.current_scale_ratio = ratio

            new_width = int(original.width * ratio)
            new_height = int(original.height * ratio)

            display_img = original.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 添加水印
            watermarked = self.add_watermark(display_img, ratio)

            # 显示
            self.photo = ImageTk.PhotoImage(watermarked)
            self.preview_canvas.delete('all')
            self.preview_canvas.create_image(
                canvas_width // 2, canvas_height // 2,
                image=self.photo, anchor=tk.CENTER
            )

        except Exception as e:
            print(f"预览错误: {e}")
            traceback.print_exc()

    def add_watermark(self, image, scale_ratio=1.0):
        """添加水印到图片"""
        # 转换为RGBA以支持透明度
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        wm_type = self.watermark_type.get()

        if wm_type == 'text':
            return self.add_text_watermark(image, scale_ratio)
        else:
            return self.add_image_watermark(image, scale_ratio)

    def has_chinese(self, text):
        """检测文本中是否包含中文字符"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False

    def load_chinese_font(self, size):
        """尝试加载支持中文的字体"""
        font_paths = [
            "C:\\Windows\\Fonts\\msyh.ttc",      # 微软雅黑
            "C:\\Windows\\Fonts\\msyhbd.ttc",    # 微软雅黑粗体
            "C:\\Windows\\Fonts\\simhei.ttf",    # 黑体
            "C:\\Windows\\Fonts\\simsun.ttc",    # 宋体
            "C:\\Windows\\Fonts\\simkai.ttf",    # 楷体
            "C:\\Windows\\Fonts\\simfang.ttf",   # 仿宋
        ]

        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size)
                    print(f"使用字体: {font_path}")
                    return font
            except Exception as e:
                continue

        return None

    def add_text_watermark(self, image, scale_ratio=1.0):
        """添加文本水印 - 支持中英文"""
        try:
            # 获取文本
            text = self.text_entry.get()
            if not text:
                return image

            # 获取用户设置的字体大小
            user_font_size = int(self.font_size.get() * scale_ratio)
            if user_font_size < 10:
                user_font_size = 10

            # 检测是否包含中文
            has_cn = self.has_chinese(text)

            # 选择字体
            if has_cn:
                # 中文：尝试加载系统中文字体
                font = self.load_chinese_font(user_font_size)
                if font is None:
                    print("警告: 无法加载中文字体，中文可能无法显示")
                    font = ImageFont.load_default()
                    scale_factor = max(1, user_font_size // 11)
                else:
                    scale_factor = 1  # TrueType字体已经是正确大小
            else:
                # 英文：使用默认位图字体并放大
                font = ImageFont.load_default()
                scale_factor = max(1, user_font_size // 11)

            # 创建临时画布来测量文本
            temp_img = Image.new('RGBA', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), text, font=font)
            base_text_width = bbox[2] - bbox[0]
            base_text_height = bbox[3] - bbox[1]

            if base_text_width <= 0 or base_text_height <= 0:
                print(f"文本大小无效: {base_text_width}x{base_text_height}")
                return image

            # 创建文本图层（留出足够空间）
            text_layer = Image.new('RGBA', (base_text_width + 20, base_text_height + 20), (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_layer)

            # 颜色和透明度
            color = self.color_var.get()
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            opacity = int(self.opacity.get() * 2.55)

            # 绘制文本
            draw.text((10, 10), text, font=font, fill=(r, g, b, opacity))

            # 裁剪到实际内容
            bbox = text_layer.getbbox()
            if not bbox:
                print("文本bbox为空")
                return image

            text_layer = text_layer.crop(bbox)

            # 如果是位图字体，需要放大
            if scale_factor > 1:
                scaled_width = text_layer.width * scale_factor
                scaled_height = text_layer.height * scale_factor
                if scaled_width > 0 and scaled_height > 0:
                    text_layer = text_layer.resize(
                        (scaled_width, scaled_height),
                        Image.Resampling.NEAREST
                    )

            # 旋转
            rotation = self.rotation.get()
            if rotation != 0:
                # 中文用BICUBIC，英文用NEAREST保持像素风格
                resample = Image.Resampling.BICUBIC if has_cn else Image.Resampling.NEAREST
                text_layer = text_layer.rotate(-rotation, expand=True, resample=resample)

            # 计算位置
            wm_width = text_layer.width
            wm_height = text_layer.height
            x, y = self.calculate_position(image.width, image.height, wm_width, wm_height, scale_ratio)

            # 确保位置不超出边界
            x = int(max(0, min(x, image.width - wm_width)))
            y = int(max(0, min(y, image.height - wm_height)))

            # 创建最终图层并粘贴
            final_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
            final_layer.paste(text_layer, (x, y), text_layer)

            # 合并到原图
            result = Image.alpha_composite(image, final_layer)

            print(f"文本水印已添加: '{text}' at ({x}, {y}), size: {wm_width}x{wm_height}, 中文: {has_cn}")
            return result

        except Exception as e:
            print(f"添加文本水印错误: {e}")
            import traceback
            traceback.print_exc()
            return image

    def add_image_watermark(self, image, scale_ratio=1.0):
        """添加图片水印"""
        wm_path = self.watermark_config.get('image_path', '')
        if not wm_path or not os.path.exists(wm_path):
            return image

        try:
            # 加载水印图片
            watermark = Image.open(wm_path)
            if watermark.mode != 'RGBA':
                watermark = watermark.convert('RGBA')

            # 缩放水印
            scale = self.wm_scale.get() / 100.0 * scale_ratio
            wm_width = int(watermark.width * scale)
            wm_height = int(watermark.height * scale)
            watermark = watermark.resize((wm_width, wm_height), Image.Resampling.LANCZOS)

            # 调整透明度
            opacity = self.img_opacity.get() / 100.0
            alpha = watermark.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            watermark.putalpha(alpha)

            # 旋转
            rotation = self.rotation.get()
            if rotation != 0:
                watermark = watermark.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)

            # 计算位置
            x, y = self.calculate_position(image.width, image.height,
                                          watermark.width, watermark.height, scale_ratio)

            # 创建透明图层
            txt_layer = Image.new('RGBA', image.size, (255, 255, 255, 0))
            txt_layer.paste(watermark, (int(x), int(y)), watermark)

            # 合并
            result = Image.alpha_composite(image, txt_layer)
            return result

        except Exception as e:
            print(f"添加图片水印错误: {e}")
            return image

    def calculate_position(self, img_width, img_height, wm_width, wm_height, scale_ratio=1.0):
        """计算水印位置"""
        position = self.watermark_config.get('position', 'bottom_right')

        # 如果是自定义位置，使用原始图片坐标，然后根据缩放比例调整
        if position == 'custom':
            x_original = int(self.watermark_config.get('offset_x', 50))
            y_original = int(self.watermark_config.get('offset_y', 50))

            # 根据缩放比例调整位置（用于预览）
            x = int(x_original * scale_ratio)
            y = int(y_original * scale_ratio)

            # 确保位置在图片范围内
            x = max(0, min(x, img_width - max(1, wm_width)))
            y = max(0, min(y, img_height - max(1, wm_height)))

            # 保存计算的位置（用于拖拽）
            self.last_calculated_x = x_original
            self.last_calculated_y = y_original

            return (x, y)

        # 预设位置的偏移量需要根据缩放比例调整
        offset_x = int(self.watermark_config.get('offset_x', 50) * scale_ratio)
        offset_y = int(self.watermark_config.get('offset_y', 50) * scale_ratio)

        positions = {
            'top_left': (offset_x, offset_y),
            'top_center': ((img_width - wm_width) // 2, offset_y),
            'top_right': (img_width - wm_width - offset_x, offset_y),
            'middle_left': (offset_x, (img_height - wm_height) // 2),
            'center': ((img_width - wm_width) // 2, (img_height - wm_height) // 2),
            'middle_right': (img_width - wm_width - offset_x, (img_height - wm_height) // 2),
            'bottom_left': (offset_x, img_height - wm_height - offset_y),
            'bottom_center': ((img_width - wm_width) // 2, img_height - wm_height - offset_y),
            'bottom_right': (img_width - wm_width - offset_x, img_height - wm_height - offset_y),
        }

        result = positions.get(position, positions['bottom_right'])

        # 保存计算的位置（转换回原始坐标）
        if scale_ratio > 0:
            self.last_calculated_x = int(result[0] / scale_ratio)
            self.last_calculated_y = int(result[1] / scale_ratio)

        return result

    def export_images(self):
        """导出所有图片"""
        if not self.images:
            messagebox.showwarning("警告", "没有要导出的图片")
            return

        # 选择输出文件夹
        output_folder = filedialog.askdirectory(title="选择导出文件夹")
        if not output_folder:
            return

        # 检查是否是原文件夹
        source_folders = set(os.path.dirname(img) for img in self.images)
        if output_folder in source_folders:
            if not messagebox.askyesno("警告", "导出文件夹与原文件夹相同，可能会覆盖原文件。是否继续？"):
                return

        # 导出格式
        output_format = self.output_format.get()

        # 进度窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title("导出进度")
        progress_window.geometry("400x100")
        progress_window.transient(self.root)
        progress_window.grab_set()

        progress_label = ttk.Label(progress_window, text="正在导出...")
        progress_label.pack(pady=10)

        progress_bar = ttk.Progressbar(progress_window, length=350, mode='determinate')
        progress_bar.pack(pady=10)
        progress_bar['maximum'] = len(self.images)

        success_count = 0
        error_count = 0

        for i, image_path in enumerate(self.images):
            try:
                # 加载原图
                original = Image.open(image_path)

                # 添加水印
                watermarked = self.add_watermark(original, scale_ratio=1.0)

                # 转换为RGB（如果导出为JPEG）
                if output_format == 'JPEG':
                    watermarked = watermarked.convert('RGB')

                # 生成输出文件名
                output_filename = self.generate_output_filename(image_path, output_format)
                output_path = os.path.join(output_folder, output_filename)

                # 保存
                if output_format == 'JPEG':
                    watermarked.save(output_path, 'JPEG', quality=95)
                else:
                    watermarked.save(output_path, 'PNG')

                success_count += 1

            except Exception as e:
                print(f"导出错误 {image_path}: {e}")
                error_count += 1

            # 更新进度
            progress_bar['value'] = i + 1
            progress_label.config(text=f"正在导出 {i+1}/{len(self.images)}")
            progress_window.update()

        progress_window.destroy()

        # 显示结果
        messagebox.showinfo("完成",
                           f"导出完成！\n成功: {success_count}\n失败: {error_count}")

    def generate_output_filename(self, original_path, output_format):
        """生成输出文件名"""
        basename = os.path.basename(original_path)
        name, _ = os.path.splitext(basename)

        rule = self.filename_rule.get()
        custom = self.custom_affix.get()

        if rule == 'original':
            new_name = name
        elif rule == 'prefix':
            new_name = custom + name
        else:  # suffix
            new_name = name + custom

        ext = '.jpg' if output_format == 'JPEG' else '.png'
        return new_name + ext

    def save_template(self):
        """保存模板"""
        template_name = tk.simpledialog.askstring("保存模板", "请输入模板名称:")
        if not template_name:
            return

        # 收集当前配置
        config = {
            'type': self.watermark_type.get(),
            'text': self.text_entry.get(),
            'font_size': self.font_size.get(),
            'color': self.color_var.get(),
            'opacity': self.opacity.get(),
            'position': self.watermark_config['position'],
            'offset_x': self.watermark_config.get('offset_x', 50),
            'offset_y': self.watermark_config.get('offset_y', 50),
            'rotation': self.rotation.get(),
            'image_path': self.watermark_config.get('image_path', ''),
            'wm_scale': self.wm_scale.get(),
            'img_opacity': self.img_opacity.get()
        }

        # 加载现有模板
        templates = {}
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
            except:
                pass

        # 添加新模板
        templates[template_name] = config

        # 保存
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("成功", f"模板 '{template_name}' 已保存")

    def load_template(self):
        """加载模板"""
        if not os.path.exists(self.templates_file):
            messagebox.showinfo("提示", "没有保存的模板")
            return

        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)

            if not templates:
                messagebox.showinfo("提示", "没有保存的模板")
                return

            # 显示模板列表
            template_window = tk.Toplevel(self.root)
            template_window.title("选择模板")
            template_window.geometry("300x400")
            template_window.transient(self.root)

            ttk.Label(template_window, text="选择一个模板:").pack(pady=10)

            listbox = tk.Listbox(template_window)
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            for name in templates.keys():
                listbox.insert(tk.END, name)

            def apply_template():
                selection = listbox.curselection()
                if not selection:
                    return

                template_name = listbox.get(selection[0])
                config = templates[template_name]

                # 应用配置
                self.watermark_type.set(config.get('type', 'text'))
                self.text_entry.delete(0, tk.END)
                self.text_entry.insert(0, config.get('text', ''))
                self.font_size.set(config.get('font_size', 36))
                self.color_var.set(config.get('color', '#FFFFFF'))
                self.color_display.config(bg=config.get('color', '#FFFFFF'))
                self.opacity.set(config.get('opacity', 50))
                self.rotation.set(config.get('rotation', 0))
                self.wm_scale.set(config.get('wm_scale', 100))
                self.img_opacity.set(config.get('img_opacity', 50))

                self.watermark_config['position'] = config.get('position', 'bottom_right')
                self.watermark_config['offset_x'] = config.get('offset_x', 50)
                self.watermark_config['offset_y'] = config.get('offset_y', 50)
                self.watermark_config['image_path'] = config.get('image_path', '')

                if self.watermark_config['image_path']:
                    self.wm_image_label.config(
                        text=os.path.basename(self.watermark_config['image_path']),
                        foreground='black'
                    )

                self.update_preview()
                template_window.destroy()
                messagebox.showinfo("成功", f"已加载模板 '{template_name}'")

            ttk.Button(template_window, text="应用", command=apply_template).pack(pady=10)

        except Exception as e:
            messagebox.showerror("错误", f"加载模板失败: {e}")

    def load_last_config(self):
        """加载上次的配置"""
        config_file = "last_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                self.watermark_type.set(config.get('type', 'text'))
                self.text_entry.delete(0, tk.END)
                self.text_entry.insert(0, config.get('text', '© 版权所有'))
                self.font_size.set(config.get('font_size', 36))
                self.color_var.set(config.get('color', '#FFFFFF'))
                self.color_display.config(bg=config.get('color', '#FFFFFF'))
                self.opacity.set(config.get('opacity', 50))
                self.rotation.set(config.get('rotation', 0))

            except:
                pass

    def save_last_config(self):
        """保存当前配置"""
        config = {
            'type': self.watermark_type.get(),
            'text': self.text_entry.get(),
            'font_size': self.font_size.get(),
            'color': self.color_var.get(),
            'opacity': self.opacity.get(),
            'rotation': self.rotation.get()
        }

        try:
            with open("last_config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass

def main():
    try:
        root = TkinterDnD.Tk()
        app = WatermarkApp(root)

        # 绑定窗口大小变化事件
        root.bind('<Configure>', lambda e: app.update_preview() if e.widget == root else None)

        # 关闭时保存配置
        def on_closing():
            app.save_last_config()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        root.mainloop()
    except Exception as e:
        print(f"程序错误: {e}")
        traceback.print_exc()
        input("按回车键退出...")

if __name__ == "__main__":
    main()
