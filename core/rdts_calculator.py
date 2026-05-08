"""
RDTS计算器
"""
import numpy as np


def calculate_rdts(season, utci, tmrt, vr, dtsk_dt):
    """
    计算RDTS指数

    参数:
        season: 季节 ('winter' 或 'summer')
        utci: UTCI值 (°C)
        tmrt: 平均辐射温度 (°C)
        vr: 相对风速 (m/s)
        dtsk_dt: 皮肤温度变化率 (°C/s)

    返回:
        RDTS值
    """
    if season == 'winter':
        # 冬季公式
        rdts = (3 * (1 - 2 / (1 + np.exp(0.0406 * (utci - 31))))
                + 0.031 * tmrt
                - 0.312 * vr +
                + 1.944 * dtsk_dt
                + 0.845)
    else:  # summer
        # 夏季公式
        rdts = (3 * (1 - 2 / (1 + np.exp(0.046 * (utci - 21.85))))
                + 0.098 * tmrt
                + 0.24 * vr
                - 1.11 * dtsk_dt
                - 4.61)

    return round(rdts, 1)
