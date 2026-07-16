"""输入校验模块"""
import re


def is_valid_numeric(value_str: str, allow_negative: bool = False) -> bool:
    """检查字符串是否为合法数字"""
    if not value_str or value_str.strip() == "":
        return False
    value_str = value_str.strip()
    pattern = r'^-?\d+\.?\d*$' if allow_negative else r'^\d+\.?\d*$'
    return bool(re.match(pattern, value_str))


def try_parse_float(value_str: str) -> float | None:
    """尝试解析浮点数，失败返回 None"""
    try:
        return float(value_str.strip())
    except (ValueError, AttributeError):
        return None


def validate_params_basic(params: dict) -> list[str]:
    """基本数值校验：非空、正数、角度范围"""
    errors = []

    # 正数参数
    positive_params = [
        ("n1", "主动齿轮转速 n1"),
        ("n2", "从动齿轮转速 n2"),
        ("m", "齿轮模数 m"),
        ("O1O2", "中心距 O1O2"),
        ("L", "水平距离 L"),
        ("H", "针杆冲程 H"),
        ("O2O3", "机架杆长 O2O3"),
        ("O3D", "摇杆杆长 O3D"),
        ("ratio_O2A_AB", "杆长比 O2A/AB"),
        ("ratio_DE_DC", "杆长比 DE/DC"),
    ]

    for key, name in positive_params:
        val = params.get(key)
        if val is None:
            errors.append(f"{name}：参数缺失")
        elif val <= 0:
            errors.append(f"{name}：必须为正数，当前值={val}")

    # 角度参数 (0~360)
    angle_params = [
        ("beta1", "曲柄相位角 β1"),
        ("beta2", "CDE夹角 β2"),
        ("beta3", "齿轮初始相位角 β3"),
        ("alpha_prime", "摇杆最小摆角 α'"),
        ("alpha_dprime", "摇杆最大摆角 α''"),
    ]

    for key, name in angle_params:
        val = params.get(key)
        if val is None:
            errors.append(f"{name}：参数缺失")
        elif val < 0 or val > 360:
            errors.append(f"{name}：必须在 0~360° 范围内，当前值={val}")

    # 摇杆角度范围
    ap = params.get("alpha_prime", 0)
    ad = params.get("alpha_dprime", 0)
    if ad <= ap:
        errors.append(f"摇杆最大摆角 α''({ad}°)必须大于最小摆角 α'({ap}°)")

    # O1O2 >= L
    O1O2 = params.get("O1O2", 0)
    L_val = params.get("L", 0)
    if O1O2 < L_val - 1e-9:
        errors.append(f"中心距 O1O2({O1O2})不能小于水平距离 L({L_val})")

    return errors


def validate_numeric_input(value_str: str, allow_negative: bool = False) -> bool:
    """检查输入字符串是否为合法数字格式"""
    if not value_str or value_str.strip() == "":
        return False
    value_str = value_str.strip()

    if allow_negative:
        pattern = r'^-?\d*\.?\d*$'
    else:
        pattern = r'^\d*\.?\d*$'

    return bool(re.match(pattern, value_str))
