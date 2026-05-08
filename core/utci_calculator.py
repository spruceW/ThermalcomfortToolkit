"""
UTCI计算器
"""
from pythermalcomfort.models import utci
import numpy as np


def calculate_utci(h, tdb, tr, v, rh):
    """
    计算UTCI指数

    参数:
        tdb: 空气温度 (°C)
        tr: 平均辐射温度 (°C)
        v: 风速 (m/s)
        rh: 相对湿度 (%)

    返回:
        utci值 (°C)
    """
    # 风速修正（假设测点高度为1.1m，标准高度为10m）
    if v > 0.3:
        v_10 = v * np.log(10 / 0.01) / np.log(h / 0.01)
    else:
        v_10 = 0.5

    result = utci(
        tdb=tdb,
        tr=tr,
        v=v_10,
        rh=rh
    )

    return {
        'utci': result.utci,
    }
