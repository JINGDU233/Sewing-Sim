"""缝纫机导针及紧线机构运动学计算模块"""
import numpy as np


class SewingMechanism:
    """缝纫机机构运动学求解器

    坐标系：O2 = (0, 0)，X 轴向右，Y 轴向上
    """

    def __init__(self, params: dict = None):
        # 衍生计算结果
        self.O2A = 0.0      # 曲柄长（导针）
        self.AB = 0.0       # 连杆长（导针）
        self.O2C = 0.0      # 曲柄长（紧线）
        self.CD = 0.0       # 连杆长（紧线）
        self.DE = 0.0       # 紧线头伸杆长
        self.omega2 = 0.0   # O2 轴角速度 (rad/s)
        self.z1 = 0         # 主动齿轮齿数
        self.z2 = 0         # 从动齿轮齿数
        self.O3 = np.zeros(2)  # O3 坐标
        self.O1 = np.zeros(2)  # O1 坐标
        self.valid = False
        self.errors = []

        # 上一帧 D 点位置（用于选择交点支）
        self._prev_D = None

        if params is not None:
            self.set_params(params)

    def set_params(self, params: dict) -> list:
        """设置参数并计算衍生量，返回错误列表"""
        self.errors = []
        self.valid = False

        # 存储原始参数
        self.params = dict(params)

        # 1. 计算 O2 轴角速度
        self.omega2 = 2.0 * np.pi * params["n2"] / 60.0

        # 2. 计算齿轮齿数
        O1O2 = params["O1O2"]
        m = params["m"]
        n1 = params["n1"]
        n2 = params["n2"]
        L = params["L"]

        z_sum = 2.0 * O1O2 / m
        z1_exact = 2.0 * O1O2 * n2 / (m * (n1 + n2))
        z2_exact = 2.0 * O1O2 * n1 / (m * (n1 + n2))
        self.z1 = int(round(z1_exact))
        self.z2 = int(round(z2_exact))

        # 校验中心距偏差（允许因齿数取整导致的偏差）
        actual_center = m * (self.z1 + self.z2) / 2.0
        if abs(actual_center - O1O2) > 0.5:
            self.errors.append(
                f"取整后中心距偏差过大：实际={actual_center:.2f}mm，"
                f"给定={O1O2:.2f}mm，偏差={abs(actual_center - O1O2):.2f}mm"
            )

        # 3. O1 位置
        if O1O2 < L - 1e-9:
            self.errors.append(f"O1O2({O1O2})不能小于L({L})")
        else:
            y1 = np.sqrt(max(0, O1O2**2 - L**2))
            self.O1 = np.array([-L, y1])

        # 4. 曲柄滑块机构：O2A 和 AB
        self.O2A = params["H"] / 2.0
        self.AB = self.O2A / params["ratio_O2A_AB"]

        if self.AB <= self.O2A:
            self.errors.append(
                f"导针机构无法装配：AB({self.AB:.2f})必须大于O2A({self.O2A:.2f})"
            )

        # 5. O3 位置（O2O3 与 X 轴负半轴夹角 = β3 - 90°）
        beta3 = params["beta3"]
        O3_theta_deg = (270.0 - beta3) % 360.0
        O3_theta = np.radians(O3_theta_deg)
        # 存储计算值供外部使用
        self.O3_theta_deg = O3_theta_deg
        O2O3 = params["O2O3"]
        self.O3 = np.array([O2O3 * np.cos(O3_theta), O2O3 * np.sin(O3_theta)])

        # 6. 计算 O2C 和 CD（极位共线法）
        alpha_prime = np.radians(params["alpha_prime"])
        alpha_dprime = np.radians(params["alpha_dprime"])
        O3D = params["O3D"]

        # 极位1（摇杆最大角 α''）
        D1 = self.O3 + O3D * np.array([np.cos(alpha_dprime), np.sin(alpha_dprime)])
        O2D_max = np.linalg.norm(D1)

        # 极位2（摇杆最小角 α'）
        D2 = self.O3 + O3D * np.array([np.cos(alpha_prime), np.sin(alpha_prime)])
        O2D_min = np.linalg.norm(D2)

        if O2D_max <= O2D_min:
            self.errors.append(
                f"摇杆极位计算异常：O2D_max({O2D_max:.2f}) <= O2D_min({O2D_min:.2f})，"
                f"请检查 O3 位置和摇杆角度范围"
            )
        else:
            self.O2C = (O2D_max - O2D_min) / 2.0
            self.CD = (O2D_max + O2D_min) / 2.0

            if self.O2C <= 0:
                self.errors.append(f"曲柄O2C长度无效：{self.O2C:.2f}，必须大于0")
            if self.CD <= 0:
                self.errors.append(f"连杆CD长度无效：{self.CD:.2f}，必须大于0")

            # Grashof 条件校验
            links = sorted([self.O2C, self.CD, O3D, O2O3])
            if links[0] + links[3] > links[1] + links[2] + 1e-9:
                self.errors.append(
                    f"不满足Grashof条件：最短杆({links[0]:.1f})+最长杆({links[3]:.1f})"
                    f" > 其余两杆之和({links[1]:.1f}+{links[2]:.1f})，曲柄无法整周回转"
                )
            if abs(links[0] - self.O2C) > 1e-9:
                self.errors.append("Grashof条件不满足：最短杆不是曲柄O2C，机构不是曲柄摇杆机构")

        # 7. DE 长度
        self.DE = self.CD * params["ratio_DE_DC"]

        # 重置上一帧 D 点
        self._prev_D = None

        self.valid = (len(self.errors) == 0)
        return self.errors

    def solve_slider(self, phi: float) -> tuple:
        """曲柄滑块 O2AB 求解

        Args:
            phi: 曲柄 O2A 转角 (rad)

        Returns:
            (A_x, A_y, B_y)
        """
        a = self.O2A
        b = self.AB

        A_x = a * np.cos(phi)
        A_y = a * np.sin(phi)

        # 约束：B 在 Y 轴上，|AB| = b
        # (A_x - 0)^2 + (A_y - B_y)^2 = b^2
        # B_y = A_y - sqrt(b^2 - A_x^2)   （针杆在下方）
        disc = b**2 - A_x**2
        if disc < 0:
            disc = 0.0  # 数值容错
        B_y = A_y - np.sqrt(disc)

        return A_x, A_y, B_y

    def solve_rocker(self, phi: float) -> tuple:
        """曲柄摇杆 O2CO3D 求解

        Args:
            phi: 曲柄 O2C 转角 (rad)

        Returns:
            (C_x, C_y, D_x, D_y, E_x, E_y)
        """
        a = self.O2C
        b = self.CD
        c = self.params["O3D"]

        # C 点
        C = np.array([a * np.cos(phi), a * np.sin(phi)])

        # D 点：两圆交点
        # 圆1: 圆心 O3，半径 c
        # 圆2: 圆心 C，半径 b
        D = self._circle_intersection(self.O3, c, C, b)

        # E 点：∠CDE = β2
        beta2 = np.radians(self.params["beta2"])
        v_CD = C - D
        len_CD = np.linalg.norm(v_CD)
        if len_CD < 1e-12:
            E = D.copy()
        else:
            # 将 v_CD 旋转 β2
            cos_b2 = np.cos(beta2)
            sin_b2 = np.sin(beta2)
            v_rot = np.array([
                v_CD[0] * cos_b2 - v_CD[1] * sin_b2,
                v_CD[0] * sin_b2 + v_CD[1] * cos_b2
            ])
            v_DE = v_rot * (self.DE / len_CD)
            E = D + v_DE

        return C[0], C[1], D[0], D[1], E[0], E[1]

    def _circle_intersection(self, P1, r1, P2, r2):
        """求两圆交点，返回离上一帧 D 更近的交点"""
        d_vec = P2 - P1
        d = np.linalg.norm(d_vec)

        if d > r1 + r2 + 1e-9 or d < abs(r1 - r2) - 1e-9:
            # 无交点，取两圆心连线上的最近点
            if d < 1e-12:
                return P1.copy()
            t = (r1**2 - r2**2 + d**2) / (2 * d**2) if d > 0 else 0.5
            return P1 + t * d_vec

        # 计算交点
        a_val = (r1**2 - r2**2 + d**2) / (2 * d)
        h = np.sqrt(max(0, r1**2 - a_val**2))
        mid = P1 + a_val * d_vec / d

        # 垂直方向
        perp = np.array([-d_vec[1], d_vec[0]]) / d

        D_a = mid + h * perp
        D_b = mid - h * perp

        if self._prev_D is None:
            self._prev_D = D_a
            return D_a

        dist_a = np.linalg.norm(D_a - self._prev_D)
        dist_b = np.linalg.norm(D_b - self._prev_D)

        chosen = D_a if dist_a <= dist_b else D_b
        self._prev_D = chosen
        return chosen

    def solve_position(self, phi: float) -> dict:
        """完整单帧求解

        Returns:
            dict with: O1, O2, O3, A, B, C, D, E, phi, theta_rocker, y_needle
        """
        A_x, A_y, B_y = self.solve_slider(phi)
        C_x, C_y, D_x, D_y, E_x, E_y = self.solve_rocker(phi + np.radians(self.params["beta1"]))

        # 摇杆角度（O3D 与 X 轴夹角）
        d_vec = np.array([D_x - self.O3[0], D_y - self.O3[1]])
        theta_rocker = np.arctan2(d_vec[1], d_vec[0])
        if theta_rocker < 0:
            theta_rocker += 2 * np.pi

        return {
            "O1": self.O1.copy(),
            "O2": np.array([0.0, 0.0]),
            "O3": self.O3.copy(),
            "A": np.array([A_x, A_y]),
            "B": np.array([0.0, B_y]),
            "C": np.array([C_x, C_y]),
            "D": np.array([D_x, D_y]),
            "E": np.array([E_x, E_y]),
            "phi": phi,
            "theta_rocker": theta_rocker,
            "y_needle": B_y,
        }

    def get_full_cycle(self, n_steps: int = 360) -> dict:
        """获取一个完整周期的位置数据"""
        phis = np.linspace(0, 2 * np.pi, n_steps)
        data = {
            "phi": [],
            "A_x": [], "A_y": [],
            "B_y": [],
            "C_x": [], "C_y": [],
            "D_x": [], "D_y": [],
            "E_x": [], "E_y": [],
            "theta_rocker": [],
        }
        for p in phis:
            result = self.solve_position(p)
            data["phi"].append(np.degrees(p))
            data["A_x"].append(result["A"][0])
            data["A_y"].append(result["A"][1])
            data["B_y"].append(result["B"][1])
            data["C_x"].append(result["C"][0])
            data["C_y"].append(result["C"][1])
            data["D_x"].append(result["D"][0])
            data["D_y"].append(result["D"][1])
            data["E_x"].append(result["E"][0])
            data["E_y"].append(result["E"][1])
            data["theta_rocker"].append(np.degrees(result["theta_rocker"]))

        for key in data:
            data[key] = np.array(data[key])
        return data

    def get_kinematic_table(self, step_deg: float = 10.0, dphi_deg: float = 0.5) -> list[dict]:
        """获取运动学数据表，每隔 step_deg 输出一行

        Args:
            step_deg: 输出间隔 (°)
            dphi_deg: 数值微分步长 (°)，用于速度和加速度计算

        Returns:
            list of dict，每行包含：
            phi_deg, y_B_mm, v_B_mm_s, a_B_mm_s2,
            x_E_mm, y_E_mm, v_E_mm_s, a_E_mm_s2
        """
        dphi = np.radians(dphi_deg)
        omega2 = self.omega2
        rows = []

        for phi_deg in np.arange(0, 360, step_deg):
            phi = np.radians(phi_deg)

            # 当前帧位置
            r0 = self.solve_position(phi)
            rp = self.solve_position(phi + dphi)
            rm = self.solve_position(phi - dphi)

            # B 点 (针杆)
            y_B = r0["B"][1]
            # v_B = d(y_B)/dφ * ω2  (中心差分)
            dyB_dphi = (rp["B"][1] - rm["B"][1]) / (2 * dphi)
            v_B = dyB_dphi * omega2
            # a_B = d²(y_B)/dφ² * ω2²
            d2yB_dphi2 = (rp["B"][1] - 2 * y_B + rm["B"][1]) / (dphi ** 2)
            a_B = d2yB_dphi2 * (omega2 ** 2)

            # E 点
            E0 = r0["E"]
            Ep = rp["E"]
            Em = rm["E"]

            # v_E 矢量
            dEx_dphi = (Ep[0] - Em[0]) / (2 * dphi)
            dEy_dphi = (Ep[1] - Em[1]) / (2 * dphi)
            v_Ex = dEx_dphi * omega2
            v_Ey = dEy_dphi * omega2
            v_E = np.sqrt(v_Ex**2 + v_Ey**2)

            # a_E 矢量
            d2Ex_dphi2 = (Ep[0] - 2 * E0[0] + Em[0]) / (dphi ** 2)
            d2Ey_dphi2 = (Ep[1] - 2 * E0[1] + Em[1]) / (dphi ** 2)
            a_Ex = d2Ex_dphi2 * (omega2 ** 2)
            a_Ey = d2Ey_dphi2 * (omega2 ** 2)
            a_E = np.sqrt(a_Ex**2 + a_Ey**2)

            rows.append({
                "phi_deg": round(phi_deg, 1),
                "y_B_mm": round(y_B, 3),
                "v_B_mm_s": round(v_B, 2),
                "a_B_mm_s2": round(a_B, 2),
                "x_E_mm": round(E0[0], 3),
                "y_E_mm": round(E0[1], 3),
                "v_E_mm_s": round(v_E, 2),
                "a_E_mm_s2": round(a_E, 2),
            })

        return rows

    def export_csv(self, filepath: str, step_deg: float = 10.0) -> bool:
        """导出运动学数据到 CSV 文件"""
        import csv

        rows = self.get_kinematic_table(step_deg)
        if not rows:
            return False

        headers = [
            "phi (deg)", "y_B (mm)", "v_B (mm/s)", "a_B (mm/s^2)",
            "x_E (mm)", "y_E (mm)", "v_E (mm/s)", "a_E (mm/s^2)"
        ]
        keys = ["phi_deg", "y_B_mm", "v_B_mm_s", "a_B_mm_s2",
                "x_E_mm", "y_E_mm", "v_E_mm_s", "a_E_mm_s2"]

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows:
                writer.writerow([row[k] for k in keys])

        return True
