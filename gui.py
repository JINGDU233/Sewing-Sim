"""Tkinter 图形界面模块"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from mechanism import SewingMechanism
from animation_canvas import AnimationCanvas
from validation import validate_params_basic, validate_numeric_input, try_parse_float


# 默认参数（按课程设计参数表顺序排列）
DEFAULT_PARAMS = {
    "n1": 200,
    "n2": 250,
    "m": 1.25,
    "O1O2": 54,
    "L": 40,
    "H": 30,
    "beta1": 40,
    "beta2": 120,
    "beta3": 135,
    "alpha_prime": 20,
    "alpha_dprime": 90,
    "O2O3": 40,
    "O3D": 30,
    "ratio_DE_DC": 1.2,
    "ratio_O2A_AB": 0.3,
}

# ===== 十组备选方案（与课程设计原始数据表一致）=====
PRESET_SCHEMES = {
    "方案一": {"n1": 200, "n2": 230, "m": 1.25, "O1O2": 54, "L": 40, "H": 36,
              "beta1": 42, "beta2": 120, "beta3": 144, "alpha_prime": 10, "alpha_dprime": 80,
              "O2O3": 34, "O3D": 29, "ratio_DE_DC": 1.3, "ratio_O2A_AB": 0.3},
    "方案二": {"n1": 200, "n2": 240, "m": 1.25, "O1O2": 54, "L": 40, "H": 40,
              "beta1": 45, "beta2": 120, "beta3": 140, "alpha_prime": 15, "alpha_dprime": 90,
              "O2O3": 36, "O3D": 25, "ratio_DE_DC": 1.4, "ratio_O2A_AB": 0.4},
    "方案三": {"n1": 200, "n2": 250, "m": 1.25, "O1O2": 54, "L": 40, "H": 32,
              "beta1": 40, "beta2": 120, "beta3": 135, "alpha_prime": 20, "alpha_dprime": 90,
              "O2O3": 40, "O3D": 30, "ratio_DE_DC": 1.2, "ratio_O2A_AB": 0.35},
    "方案四": {"n1": 200, "n2": 260, "m": 1.5, "O1O2": 54, "L": 40, "H": 30,
              "beta1": 35, "beta2": 120, "beta3": 145, "alpha_prime": 15, "alpha_dprime": 75,
              "O2O3": 38, "O3D": 24, "ratio_DE_DC": 1.25, "ratio_O2A_AB": 0.25},
    "方案五": {"n1": 200, "n2": 270, "m": 1.5, "O1O2": 54, "L": 40, "H": 38,
              "beta1": 30, "beta2": 120, "beta3": 150, "alpha_prime": 10, "alpha_dprime": 75,
              "O2O3": 36, "O3D": 28, "ratio_DE_DC": 1.35, "ratio_O2A_AB": 0.3},
    "方案六": {"n1": 200, "n2": 230, "m": 1.25, "O1O2": 54, "L": 40, "H": 32,
              "beta1": 42, "beta2": 120, "beta3": 144, "alpha_prime": 10, "alpha_dprime": 80,
              "O2O3": 34, "O3D": 29, "ratio_DE_DC": 1.3, "ratio_O2A_AB": 0.35},
    "方案七": {"n1": 200, "n2": 240, "m": 1.25, "O1O2": 54, "L": 40, "H": 36,
              "beta1": 45, "beta2": 120, "beta3": 140, "alpha_prime": 15, "alpha_dprime": 90,
              "O2O3": 36, "O3D": 25, "ratio_DE_DC": 1.4, "ratio_O2A_AB": 0.4},
    "方案八": {"n1": 200, "n2": 250, "m": 1.25, "O1O2": 54, "L": 40, "H": 30,
              "beta1": 40, "beta2": 120, "beta3": 135, "alpha_prime": 20, "alpha_dprime": 90,
              "O2O3": 40, "O3D": 30, "ratio_DE_DC": 1.2, "ratio_O2A_AB": 0.3},
    "方案九": {"n1": 200, "n2": 260, "m": 1.5, "O1O2": 54, "L": 40, "H": 38,
              "beta1": 35, "beta2": 120, "beta3": 145, "alpha_prime": 15, "alpha_dprime": 75,
              "O2O3": 38, "O3D": 24, "ratio_DE_DC": 1.25, "ratio_O2A_AB": 0.25},
    "方案十": {"n1": 200, "n2": 270, "m": 1.5, "O1O2": 54, "L": 40, "H": 40,
              "beta1": 30, "beta2": 120, "beta3": 150, "alpha_prime": 10, "alpha_dprime": 75,
              "O2O3": 36, "O3D": 28, "ratio_DE_DC": 1.35, "ratio_O2A_AB": 0.35},
}


class ValidatedEntry(ttk.Entry):
    """带输入校验的输入框"""

    def __init__(self, parent, allow_negative=False, error_label=None, **kwargs):
        self.allow_negative = allow_negative
        self.error_label = error_label  # 关联的错误标签
        self.var = tk.StringVar()
        vcmd = (parent.register(self._validate_input), "%P")
        super().__init__(parent, textvariable=self.var, validate="key",
                         validatecommand=vcmd, **kwargs)
        self.var.trace_add("write", self._on_change)
        self.bind("<FocusOut>", self._on_focus_out)
        self._error_text = ""

    def _validate_input(self, new_value):
        if new_value == "" or new_value == "-":
            return True
        return validate_numeric_input(new_value, self.allow_negative)

    def _on_change(self, *args):
        val = self.var.get().strip()
        if val == "":
            self.configure(style="TEntry")
            self._set_error("")
            return
        if validate_numeric_input(val, self.allow_negative):
            self.configure(style="Valid.TEntry")
            self._set_error("")
        else:
            self.configure(style="Invalid.TEntry")
            self._set_error("格式错误")

    def _on_focus_out(self, event):
        """焦点离开时校验数值"""
        val = self.var.get().strip()
        if val == "":
            self._set_error("不能为空")
        elif not validate_numeric_input(val, self.allow_negative):
            self._set_error("格式错误")
        else:
            fv = float(val)
            if not self.allow_negative and fv < 0:
                self._set_error("不能为负")
            elif fv == 0:
                self._set_error("不能为0")
            else:
                self._set_error("")

    def _set_error(self, msg: str):
        """设置关联错误标签的文本"""
        if self.error_label:
            self.error_label.msg = msg
            self.error_label.config(text=msg, foreground="red" if msg else "#ccc")

    def get_value(self) -> float | None:
        return try_parse_float(self.var.get())

    def set_value(self, value):
        self.var.set(str(value))
        self._set_error("")


class ParameterGroup(ttk.LabelFrame):
    """参数分组面板"""

    def __init__(self, parent, title, params_def, **kwargs):
        super().__init__(parent, text=title, padding=8, **kwargs)
        self.entries = {}
        self.error_labels = []

        for i, (key, (label, default, unit, allow_neg)) in enumerate(params_def.items()):
            ttk.Label(self, text=label, font=("Microsoft YaHei", 9)).grid(
                row=i, column=0, sticky="w", padx=(0, 5), pady=2)

            el = ttk.Label(self, text="", font=("Microsoft YaHei", 7), width=8, anchor="w")
            el.grid(row=i, column=3, sticky="w", padx=(2, 0), pady=2)
            el.msg = ""
            self.error_labels.append(el)

            entry = ValidatedEntry(self, allow_negative=allow_neg, width=8, error_label=el)
            entry.set_value(default)
            entry.grid(row=i, column=1, sticky="w", padx=(0, 3), pady=2)

            ttk.Label(self, text=unit, font=("Microsoft YaHei", 8),
                      foreground="#888888").grid(row=i, column=2, sticky="w", pady=2)

            self.entries[key] = entry

    def get_values(self) -> dict:
        """获取所有参数值"""
        result = {}
        for key, entry in self.entries.items():
            val = entry.get_value()
            if val is not None:
                result[key] = val
        return result

    def set_values(self, params: dict):
        """设置所有参数值"""
        for key, entry in self.entries.items():
            if key in params:
                entry.set_value(params[key])


class SewingMachineApp:
    """主应用程序"""

    def __init__(self, root: tk.Tk):
        self.root = root

        # 样式
        self._setup_styles()

        # 机构实例
        self.mechanism = SewingMechanism(DEFAULT_PARAMS)

        # 构建界面
        self._build_ui()

        # 初始化动画
        self.animation = AnimationCanvas(
            self.anim_frame,
            self.mechanism,
            status_callback=self._update_status
        )
        self.anim_widget = self.animation.get_widget()
        self.anim_widget.pack(fill="both", expand=True)

        # 初始应用默认参数
        self._apply_params()

        # 窗口关闭时清理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        """设置 ttk 样式"""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TLabel", font=("Microsoft YaHei", 9))
        style.configure("TButton", font=("Microsoft YaHei", 9), padding=4)
        style.configure("TLabelframe", font=("Microsoft YaHei", 10, "bold"))
        style.configure("TLabelframe.Label", font=("Microsoft YaHei", 10, "bold"))
        style.configure("TEntry", fieldbackground="white")

        style.configure("Valid.TEntry", fieldbackground="#e8f5e9")
        style.configure("Invalid.TEntry", fieldbackground="#ffebee")

        style.configure("Play.TButton", font=("Microsoft YaHei", 10, "bold"),
                        background="#27ae60")
        style.configure("Apply.TButton", font=("Microsoft YaHei", 10, "bold"),
                        background="#2980b9")

    def _build_ui(self):
        """构建 UI 布局"""
        # 主容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        # 左侧参数面板（可滚动）
        left_frame = ttk.Frame(main_frame, width=380)
        left_frame.pack(side="left", fill="both", padx=(8, 4), pady=8)
        left_frame.pack_propagate(False)

        # 滚动区域
        canvas = tk.Canvas(left_frame, highlightthickness=0, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 绑定 canvas 宽度变化，让 scroll_frame 自适应宽度
        def _on_canvas_configure(event):
            canvas.itemconfig(win_id, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮绑定
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # === 方案预设选择器 ===
        preset_frame = ttk.Frame(scroll_frame)
        preset_frame.pack(fill="x", padx=4, pady=(4, 4))

        ttk.Label(preset_frame, text="备选方案:",
                  font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 4))
        self.preset_var = tk.StringVar(value="方案八")
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var,
                                    values=list(PRESET_SCHEMES.keys()),
                                    state="readonly", width=10,
                                    font=("Microsoft YaHei", 9))
        preset_combo.pack(side="left", padx=(0, 4))
        ttk.Button(preset_frame, text="加载方案", width=8,
                   command=self._load_preset).pack(side="left", padx=(0, 4))
        ttk.Label(preset_frame,
                  text="选择方案后点击加载，再点击应用参数",
                  font=("Microsoft YaHei", 7), foreground="#888888").pack(side="left")

        # === 所有参数（按课程设计参数表顺序，不再分组） ===
        all_params = {
            "n1": ("齿轮转速 n₁", DEFAULT_PARAMS["n1"], "rpm", False),
            "n2": ("齿轮转速 n₂", DEFAULT_PARAMS["n2"], "rpm", False),
            "m": ("模数 m", DEFAULT_PARAMS["m"], "mm", False),
            "O1O2": ("中心距 O₁O₂", DEFAULT_PARAMS["O1O2"], "mm", False),
            "L": ("距离 L", DEFAULT_PARAMS["L"], "mm", False),
            "H": ("针杆冲程 H", DEFAULT_PARAMS["H"], "mm", False),
            "beta1": ("角度 β₁", DEFAULT_PARAMS["beta1"], "deg", False),
            "beta2": ("角度 β₂", DEFAULT_PARAMS["beta2"], "deg", False),
            "beta3": ("角度 β₃", DEFAULT_PARAMS["beta3"], "deg", False),
            "alpha_prime": ("角度 α'", DEFAULT_PARAMS["alpha_prime"], "deg", False),
            "alpha_dprime": ("角度 α''", DEFAULT_PARAMS["alpha_dprime"], "deg", False),
            "O2O3": ("杆长 O₂O₃", DEFAULT_PARAMS["O2O3"], "mm", False),
            "O3D": ("杆长 O₃D", DEFAULT_PARAMS["O3D"], "mm", False),
            "ratio_DE_DC": ("杆长比 DE/DC", DEFAULT_PARAMS["ratio_DE_DC"], "", False),
            "ratio_O2A_AB": ("杆长比 O₂A/AB", DEFAULT_PARAMS["ratio_O2A_AB"], "", False),
        }
        self.params_group = ParameterGroup(scroll_frame, "机构参数", all_params)
        self.params_group.pack(fill="x", padx=4, pady=(0, 8))

        # 全局错误提示区
        self.error_frame = ttk.Frame(scroll_frame)
        self.error_frame.pack(fill="x", padx=4, pady=(0, 4))
        self.global_error_label = ttk.Label(self.error_frame, text="",
                                            font=("Microsoft YaHei", 8),
                                            foreground="red", wraplength=280)
        self.global_error_label.pack(fill="x")

        # 应用按钮
        btn_frame = ttk.Frame(scroll_frame)
        btn_frame.pack(fill="x", padx=4, pady=(4, 8))

        self.apply_btn = ttk.Button(btn_frame, text="应用参数",
                                    style="Apply.TButton",
                                    command=self._apply_params)
        self.apply_btn.pack(side="left", fill="x", expand=True, padx=2)

        self.reset_default_btn = ttk.Button(btn_frame, text="恢复默认",
                                            command=self._reset_default)
        self.reset_default_btn.pack(side="left", fill="x", expand=True, padx=2)

        # 右侧动画区域
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=(4, 8), pady=8)

        self.anim_frame = ttk.Frame(right_frame)

        # 底部控制栏 — 先 pack 占位，固定在底部
        ctrl_frame = ttk.Frame(right_frame)
        ctrl_frame.pack(side="bottom", fill="x", pady=(4, 0))
        self.anim_frame.pack(side="top", fill="both", expand=True)

        # 播放/暂停按钮
        self.play_btn = ttk.Button(ctrl_frame, text="▶ 播放",
                                   style="Play.TButton",
                                   command=self._toggle_play)
        self.play_btn.pack(side="left", padx=2)

        # 重置按钮
        self.reset_btn = ttk.Button(ctrl_frame, text="↺ 重置",
                                    command=self._reset_anim)
        self.reset_btn.pack(side="left", padx=2)

        # 导出按钮
        self.export_btn = ttk.Button(ctrl_frame, text="📊 导出数据",
                                     command=self._export_data)
        self.export_btn.pack(side="left", padx=2)

        # 速度调节
        ttk.Label(ctrl_frame, text="速度:", font=("Microsoft YaHei", 9)).pack(
            side="left", padx=(15, 3))
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(ctrl_frame, from_=0.1, to=5.0,
                                     variable=self.speed_var,
                                     orient="horizontal", length=120,
                                     command=self._on_speed_change)
        self.speed_scale.pack(side="left", padx=2)

        self.speed_label = ttk.Label(ctrl_frame, text="1.0x",
                                     font=("Microsoft YaHei", 9), width=5)
        self.speed_label.pack(side="left", padx=2)

        # 状态信息
        self.status_label = ttk.Label(ctrl_frame, text="",
                                      font=("Microsoft YaHei", 9),
                                      foreground="#555555")
        self.status_label.pack(side="right", padx=5)

    def _load_preset(self):
        """加载选定方案参数到输入框（不自动应用）"""
        scheme_name = self.preset_var.get()
        if scheme_name not in PRESET_SCHEMES:
            messagebox.showwarning("提示", f"方案 '{scheme_name}' 不存在")
            return
        params = PRESET_SCHEMES[scheme_name]
        self.params_group.set_values(params)
        self.global_error_label.config(
            text=f"已加载「{scheme_name}」参数，请点击「应用参数」生成机构")

    def _apply_params(self):
        """收集参数、校验、应用"""
        # 收集所有参数
        params = self.params_group.get_values()

        # 检查是否所有参数都填写了
        all_keys = list(self.params_group.entries.keys())
        missing = [k for k in all_keys if k not in params or params[k] is None]
        if missing:
            self.global_error_label.config(
                text=f"❌ 以下参数未填写或格式错误：{', '.join(missing)}")
            messagebox.showerror("输入错误",
                                 f"以下参数未填写或格式错误：\n{', '.join(missing)}")
            return

        # 基本校验
        basic_errors = validate_params_basic(params)
        if basic_errors:
            self.global_error_label.config(
                text="❌ " + "；".join(basic_errors))
            messagebox.showerror("参数校验失败",
                                 "以下参数不合法：\n\n" + "\n".join(basic_errors))
            return

        # 创建机构并校验
        self.animation.pause()
        self.mechanism = SewingMechanism(params)

        if not self.mechanism.valid:
            self.global_error_label.config(
                text="❌ " + "；".join(self.mechanism.errors))
            messagebox.showerror("机构设计校验失败",
                                 "机构无法装配，请检查参数：\n\n" +
                                 "\n".join(self.mechanism.errors))
            return

        self.global_error_label.config(text="")
        self.animation.set_mechanism(self.mechanism)
        self.status_label.config(text="参数已应用，机构就绪")

    def _reset_default(self):
        """恢复默认参数"""
        self.params_group.set_values(DEFAULT_PARAMS)
        self._apply_params()

    def _toggle_play(self):
        """切换播放/暂停"""
        if not self.mechanism.valid:
            messagebox.showwarning("提示", "请先应用有效参数")
            return
        playing = self.animation.toggle_play()
        if playing:
            self.play_btn.config(text="⏸ 暂停")
        else:
            self.play_btn.config(text="▶ 播放")

    def _reset_anim(self):
        """重置动画"""
        self.animation.reset()
        self.play_btn.config(text="▶ 播放")

    def _on_speed_change(self, *args):
        """速度滑块变化"""
        speed = self.speed_var.get()
        self.animation.set_speed(speed)
        self.speed_label.config(text=f"{speed:.1f}x")

    def _update_status(self, phi_deg, y_needle, theta_rocker):
        """更新状态栏"""
        self.status_label.config(
            text=f"φ={phi_deg:.1f}° | 针杆 y={y_needle:.1f}mm | 摇杆角={theta_rocker:.1f}°"
        )

    def _export_data(self):
        """导出运动学数据到 CSV"""
        if not self.mechanism.valid:
            messagebox.showwarning("提示", "请先应用有效参数")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
            initialfile="运动学数据_10deg.csv",
            title="导出运动学数据"
        )
        if not filepath:
            return

        try:
            self.mechanism.export_csv(filepath, step_deg=10.0)
            messagebox.showinfo("导出成功", f"数据已导出到：\n{filepath}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _on_close(self):
        """窗口关闭"""
        self.animation.destroy()
        self.root.destroy()
