"""Matplotlib 动画画布（嵌入 Tkinter）—— 动画左侧 + 分析图表右侧"""
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.animation as animation
import warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*tight_layout.*")

# 配置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


class AnimationCanvas:
    """机构运动仿真动画画布 + 内置分析图表"""

    COLORS = {
        "frame": "#333333",
        "fixed_joint": "#444444",
        "link_O2A": "#e74c3c",
        "link_AB": "#3498db",
        "link_O2C": "#e67e22",
        "link_CD": "#2ecc71",
        "link_O3D": "#9b59b6",
        "link_DE": "#1abc9c",
        "slider": "#e74c3c",
        "guide": "#999999",
        "joint": "#2c3e50",
        "trajectory": "#bdc3c7",
        "bg": "#fafafa",
        "grid": "#e0e0e0",
    }

    def __init__(self, parent, mechanism, status_callback=None):
        self.mechanism = mechanism
        self.status_callback = status_callback

        self.playing = False
        self.phi = 0.0
        self.speed = 1.0
        self.dt = 0.03  # 实速：每秒约4圈 (ω2*dt ≈ 45°/帧 @33fps)

        self.trail_E_x = []
        self.trail_E_y = []
        self._trail_locked = False    # 第一圈画完后锁定

        self._anim = None

        # 分析数据缓存
        self._analysis_data = None
        self._analysis_table = None

        # 创建图形：左侧动画(用GridSpec占2列) + 右侧4张子图(2x2)
        self.fig = Figure(figsize=(12, 7), dpi=100, facecolor=self.COLORS["bg"])
        gs = self.fig.add_gridspec(2, 4, width_ratios=[2.5, 2.5, 2, 2],
                                   hspace=0.45, wspace=0.4,
                                   left=0.04, right=0.97, top=0.94, bottom=0.07)

        # 左侧动画大图（占第1-2列，上下两行合并）
        self.ax_mech = self.fig.add_subplot(gs[:, :2])
        self.ax_mech.set_aspect("equal")
        self.ax_mech.set_facecolor(self.COLORS["bg"])
        self.ax_mech.grid(True, color=self.COLORS["grid"], linewidth=0.5, linestyle="--")
        self.ax_mech.set_xlabel("X (mm)", fontsize=8)
        self.ax_mech.set_ylabel("Y (mm)", fontsize=8)
        self.ax_mech.set_title("机构运动仿真", fontsize=10, fontweight="bold")

        # 右上：E轨迹
        self.ax_etraj = self.fig.add_subplot(gs[0, 2])
        self._setup_chart_ax(self.ax_etraj, "E 点运动轨迹")
        self.ax_etraj.set_xlabel("x (mm)", fontsize=7)
        self.ax_etraj.set_ylabel("y (mm)", fontsize=7)

        # 左上偏移：B位移
        self.ax_ydisp = self.fig.add_subplot(gs[0, 3])
        self._setup_chart_ax(self.ax_ydisp, "针杆位移 y_B")
        self.ax_ydisp.set_ylabel("y_B (mm)", fontsize=7)

        # 右下：B速度
        self.ax_v = self.fig.add_subplot(gs[1, 2])
        self._setup_chart_ax(self.ax_v, "针杆速度 v_B")
        self.ax_v.set_xlabel("φ (°)", fontsize=7)
        self.ax_v.set_ylabel("v_B (mm/s)", fontsize=7)

        # 右下：B加速度
        self.ax_a = self.fig.add_subplot(gs[1, 3])
        self._setup_chart_ax(self.ax_a, "针杆加速度 a_B")
        self.ax_a.set_xlabel("φ (°)", fontsize=7)
        self.ax_a.set_ylabel("a_B (mm/s²)", fontsize=7)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()

        self._compute_analysis_data()
        self._draw_analysis_charts()

    def _setup_chart_ax(self, ax, title):
        ax.set_facecolor(self.COLORS["bg"])
        ax.grid(True, color=self.COLORS["grid"], linewidth=0.5, linestyle="--")
        ax.tick_params(labelsize=7)
        ax.set_title(title, fontsize=8, fontweight="bold")

    def _compute_analysis_data(self):
        if not self.mechanism.valid:
            self._analysis_data = None
            self._analysis_table = None
            return
        m = self.mechanism
        m._prev_D = None  # 重置分支选择，确保从头开始
        self._analysis_data = m.get_full_cycle(720)
        self._analysis_table = m.get_kinematic_table(step_deg=1.0)

    def _draw_analysis_charts(self):
        """绘制右侧 4 张分析图"""
        if self._analysis_data is None:
            for ax in [self.ax_etraj, self.ax_ydisp, self.ax_v, self.ax_a]:
                ax.clear()
                self._setup_chart_ax(ax, ax.get_title())
                ax.text(0.5, 0.5, "参数无效", transform=ax.transAxes,
                        ha="center", va="center", fontsize=9, color="red")
            return

        data = self._analysis_data
        table = self._analysis_table
        phi = data["phi"]
        B_y = data["B_y"]
        E_x = data["E_x"]
        E_y = data["E_y"]
        phi_t = np.array([r["phi_deg"] for r in table])
        v_B = np.array([r["v_B_mm_s"] for r in table])
        a_B = np.array([r["a_B_mm_s2"] for r in table])

        # E 轨迹
        self.ax_etraj.clear()
        self._setup_chart_ax(self.ax_etraj, "E 点运动轨迹")
        self.ax_etraj.set_xlabel("x (mm)", fontsize=7)
        self.ax_etraj.set_ylabel("y (mm)", fontsize=7)
        self.ax_etraj.plot(E_x, E_y, color="#1abc9c", linewidth=1.2)
        self.ax_etraj.set_aspect("equal")

        # B 位移
        self.ax_ydisp.clear()
        self._setup_chart_ax(self.ax_ydisp, "针杆位移 y_B")
        self.ax_ydisp.set_ylabel("y_B (mm)", fontsize=7)
        self.ax_ydisp.plot(phi, B_y, color="#3498db", linewidth=1.0)
        self.ax_ydisp.set_xlim(0, 360)

        # B 速度
        self.ax_v.clear()
        self._setup_chart_ax(self.ax_v, "针杆速度 v_B")
        self.ax_v.set_xlabel("φ (°)", fontsize=7)
        self.ax_v.set_ylabel("v_B (mm/s)", fontsize=7)
        self.ax_v.plot(phi_t, v_B, color="#e67e22", linewidth=1.0)
        self.ax_v.set_xlim(0, 360)

        # B 加速度
        self.ax_a.clear()
        self._setup_chart_ax(self.ax_a, "针杆加速度 a_B")
        self.ax_a.set_xlabel("φ (°)", fontsize=7)
        self.ax_a.set_ylabel("a_B (mm/s²)", fontsize=7)
        self.ax_a.plot(phi_t, a_B, color="#e74c3c", linewidth=1.0)
        self.ax_a.set_xlim(0, 360)

    def set_mechanism(self, mechanism):
        self.mechanism = mechanism
        self.phi = 0.0
        self.trail_E_x = []
        self.trail_E_y = []
        self._trail_locked = False
        self._compute_analysis_data()
        self._update_view_limits()
        self._draw_analysis_charts()
        self._draw()

    def _update_view_limits(self):
        if not self.mechanism.valid:
            self.ax_mech.set_xlim(-60, 60)
            self.ax_mech.set_ylim(-60, 100)
            return

        pts = [np.array([0.0, 0.0]), self.mechanism.O3]
        margin = 10
        all_x = [p[0] for p in pts]
        all_y = [p[1] for p in pts]
        extent = (self.mechanism.O2C + self.mechanism.CD +
                  self.mechanism.params["O3D"] + self.mechanism.params["O2O3"])
        all_x += [-extent, extent]
        all_y += [-extent, extent]
        all_y.append(-(self.mechanism.O2A + self.mechanism.AB) - 5)
        x_min, x_max = min(all_x) - margin, max(all_x) + margin
        y_min, y_max = min(all_y) - margin, max(all_y) + margin
        self.ax_mech.set_xlim(x_min, x_max)
        self.ax_mech.set_ylim(y_min, y_max)

    def play(self):
        if not self.mechanism.valid:
            return
        self.playing = True
        if self._anim is None:
            self._anim = animation.FuncAnimation(
                self.fig, self._animate_frame,
                interval=33, blit=False, cache_frame_data=False
            )
        else:
            self._anim.event_source.start()
        self.canvas.draw_idle()

    def pause(self):
        self.playing = False
        if self._anim:
            self._anim.event_source.stop()

    def toggle_play(self):
        if self.playing:
            self.pause()
        else:
            self.play()
        return self.playing

    def reset(self):
        self.pause()
        self.phi = 0.0
        self.trail_E_x = []
        self.trail_E_y = []
        self._trail_locked = False
        self._draw()

    def set_speed(self, speed: float):
        self.speed = max(0.1, min(10.0, speed))

    def _animate_frame(self, frame):
        if not self.mechanism.valid or not self.playing:
            return []
        self.phi += self.mechanism.omega2 * self.dt * self.speed
        if self.phi > 2 * np.pi:
            self.phi -= 2 * np.pi
            self._trail_locked = True  # 第一圈结束，锁定轨迹
        return self._draw()

    def _draw(self):
        self.ax_mech.clear()
        self._setup_mech_style()

        if not self.mechanism.valid:
            self.canvas.draw_idle()
            return []

        m = self.mechanism
        result = m.solve_position(self.phi)

        O2, O3 = result["O2"], result["O3"]
        A, B, C, D, E = result["A"], result["B"], result["C"], result["D"], result["E"]

        # 机架
        for pt, label, marker in [(O2, "O2", "s"), (O3, "O3", "s")]:
            self.ax_mech.plot(pt[0], pt[1], marker=marker, color=self.COLORS["fixed_joint"],
                              markersize=10, zorder=10, markeredgecolor="white",
                              markeredgewidth=1.5)
            self.ax_mech.annotate(label, (pt[0], pt[1]),
                                  textcoords="offset points", xytext=(4, 4),
                                  fontsize=10, fontweight="bold",
                                  color=self.COLORS["fixed_joint"])

        # 导轨
        self.ax_mech.axvline(x=0, ymin=0.05, ymax=0.95, color=self.COLORS["guide"],
                             linewidth=1.5, linestyle="--", alpha=0.6, zorder=0)

        # 杆件
        self._link(O2, A, self.COLORS["link_O2A"], 2.5)
        self._link(A, B, self.COLORS["link_AB"], 2.0)
        self._link(O2, C, self.COLORS["link_O2C"], 2.5)
        self._link(C, D, self.COLORS["link_CD"], 3.0, zorder=7)
        self._link(O3, D, self.COLORS["link_O3D"], 2.0)
        self._link(D, E, self.COLORS["link_DE"], 2.0)

        # 铰接点
        for pt in [A, B, C, D, E]:
            self.ax_mech.plot(pt[0], pt[1], "o", color=self.COLORS["joint"],
                              markersize=6, zorder=11, markeredgecolor="white",
                              markeredgewidth=1)

        # 滑块
        sw, sh = 8, 6
        self.ax_mech.add_patch(Rectangle((B[0] - sw / 2, B[1] - sh / 2), sw, sh,
                                         facecolor=self.COLORS["slider"],
                                         edgecolor="#c0392b", linewidth=2,
                                         zorder=9, alpha=0.85))

        self.ax_mech.annotate("B(针杆)", (B[0], B[1]),
                              textcoords="offset points", xytext=(10, 0),
                              fontsize=9, color=self.COLORS["slider"])
        self.ax_mech.annotate("E(紧线头)", (E[0], E[1]),
                              textcoords="offset points", xytext=(6, 6),
                              fontsize=9, color=self.COLORS["link_DE"])

        # 轨迹 - 第一圈用预计算数据按当前角度渐进绘制
        if self._analysis_data is not None:
            all_phi = self._analysis_data["phi"]
            all_E_x = self._analysis_data["E_x"]
            all_E_y = self._analysis_data["E_y"]
            if not self._trail_locked:
                phi_deg = np.degrees(self.phi) % 360
                # 找到 phi 对应的索引位置
                idx = np.searchsorted(all_phi, phi_deg)
                if idx < len(all_phi):
                    trail_x = all_E_x[:idx + 1]
                    trail_y = all_E_y[:idx + 1]
                else:
                    trail_x = all_E_x
                    trail_y = all_E_y
            else:
                trail_x = all_E_x
                trail_y = all_E_y
            self.ax_mech.plot(trail_x, trail_y,
                              color=self.COLORS["trajectory"],
                              linewidth=1.8, alpha=0.8, zorder=1)

        phi_deg = np.degrees(self.phi) % 360
        self.ax_mech.set_title(
            f"机构运动仿真 | φ={phi_deg:.1f}° | "
            f"针杆={B[1]:.1f}mm | 摇杆={np.degrees(result['theta_rocker']):.1f}°",
            fontsize=9, fontweight="bold"
        )

        if self.status_callback:
            self.status_callback(phi_deg, B[1], np.degrees(result["theta_rocker"]))

        self.canvas.draw_idle()
        return []

    def _setup_mech_style(self):
        self.ax_mech.set_aspect("equal")
        self.ax_mech.set_facecolor(self.COLORS["bg"])
        self.ax_mech.grid(True, color=self.COLORS["grid"], linewidth=0.5, linestyle="--")
        if self.mechanism.valid:
            self._update_view_limits()

    def _link(self, p1, p2, color, width, zorder=5):
        self.ax_mech.plot([p1[0], p2[0]], [p1[1], p2[1]],
                          color=color, linewidth=width, solid_capstyle="round",
                          zorder=zorder)

    def get_widget(self):
        return self.canvas.get_tk_widget()

    def destroy(self):
        self.pause()
        if self._anim:
            self._anim.event_source.stop()
        self.canvas.get_tk_widget().destroy()
