"""
PET计算器
"""
from pythermalcomfort.models import pet_steady

def calculate_pet(tdb, tr, v, rh, met, clo, posture, age, gender, weight, height):
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
        PET值
    """

    result = pet_steady(
        tdb=tdb,
        tr=tr,
        v=v,
        rh=rh,
        met=met,
        clo=clo,
        position=posture,
        age=age,
        sex=gender,
        weight=weight,
        height=height
    )

    return {
        'pet': result.pet,
    }
