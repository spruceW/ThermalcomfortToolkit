"""
PMV/PPD计算器
"""
from pythermalcomfort.models import pmv_ppd_ashrae
from pythermalcomfort.utilities import clo_dynamic_ashrae, v_relative


def calculate_pmv_ppd(tdb, tr, v, rh, met, clo):
    """
    计算PMV和PPD指数

    参数:
        tdb: 空气温度 (°C)
        tr: 平均辐射温度 (°C)
        v: 风速 (m/s)
        rh: 相对湿度 (%)
        met: 代谢率 (met)
        clo: 服装热阻 (clo)

    返回:
        PMV和PPD值
    """
    # 计算动态参数
    vr = v_relative(v, met)
    clo_d = clo_dynamic_ashrae(clo, met)

    result = pmv_ppd_ashrae(
        tdb=tdb,
        tr=tr,
        vr=vr,
        rh=rh,
        met=met,
        clo=clo_d,
        limit_inputs=False,
        airspeed_control=True
    )

    return {
        'pmv': result.pmv,
        'ppd': result.ppd,
    }
