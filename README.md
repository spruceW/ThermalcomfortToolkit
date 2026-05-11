本软件使用了以下开源项目：

- [pythermalcomfort](https://github.com/pythermalcomfort/pythermalcomfort.git) - papers: F. Tartarini, S. Schiavon, pythermalcomfort: A Python package for thermal comfort research, SoftwareX (2020), doi: https://doi.org/10.1016/j.softx.2020.100578
- [JOS-3](https://github.com/TanabeLab/JOS-3.git) - papers: Y. Takahashi, A. Nomoto, S. Yoda, R. Hisayama, M. Ogata, Y. Ozeki, S. Tanabe, Thermoregulation Model JOS-3 with New Open Source Code, Energy & Buildings (2020), doi: https://doi.org/10.1016/j.enbuild.2020.110575
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- [pandas](https://pandas.pydata.org/) 
- [numpy](https://numpy.org/) 

感谢以上项目的开发者！

# ThermalcomfortToolkit

一个适用于热舒适领域的学生\研究员的热舒适模型计算工具。\A thermal comfort model calculation tool for student\researchers in the field of thermal comfort.
热舒适指标计算工具，支持UTCI、PMV/PPD、PET、RDTS计算，集成JOS-3生理模型。


## 功能特性

- ✅ 单点计算 / 批量计算
- ✅ UTCI（通用热气候指数）
- ✅ PMV/PPD（预测平均投票）
- ✅ RDTS（骑行动态的感觉模型）
- ✅ JOS-3生理模拟（皮肤温度预测）


## 运行环境

- Windows 7/10/11


## 输入参数

| 参数 | 单位 | 说明 |
|------|------|------|
| Ta | °C | 空气温度 |
| RH | % | 相对湿度 |
| Va | m/s | 风速 |
| Tr | °C | 平均辐射温度 |

启用JOS-3需要额外输入人体参数：
| 参数 | 单位 | 说明 |
|------|------|------|
| height| m | 身高 |
| weight | kg | 体重 |
| fat | %| 体脂率 |
| PAR | met | 代谢率 |
| posture | \ | 姿势 |
| Icl | clo | 服装热阻 |


## 联系方式
sprucewang1001@163.com

