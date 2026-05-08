"""
JOS-3生理模拟器
"""
import jos3
import pandas as pd

def config_model(row: pd.Series) -> jos3.JOS3:
    """
    设定JOS-3模型的仿真体
    """
    # 指定人体参数
    model = jos3.JOS3(
        height=row['height'],
        weight=row['weight'],
        fat=row['fat'],
        age=row['age'],
        sex=row['gender'],
        bmr_equation="harris-benedict",  # 默认值为harris-benedict, 修改时请参考官方文档
        bsa_equation="dubois",  # 默认值为dubois, 修改时请参考官方文档
        ex_output="None"
    )

    # 指定环境参数
    model.Ta = row['Ta']
    model.Tr = row['Tr']
    model.Va = row['Va']
    model.RH = row['RH']
    model.Icl = row['Icl']
    model.PAR = row['PAR']
    model.posture = row['posture']

    return model


def single_simulate_skin_temperature(df) -> dict[str, pd.DataFrame]:
    """
    模拟一个仿真体的时间序列皮肤温度

    参数:
        df: 单个仿真体的DataFrame

    返回:
        元组 (sim_results, origin_results):
        - sim_results: 平均皮肤温度和平均变化率的DataFrame
        - origin_results: 全序列皮肤温度和变化率的DataFrame
    """
    # 1. 初始化假体参数
    first_row = df.iloc[0]
    model = config_model(first_row)

    # 2. 准备存储模拟结果
    # 用于存储每行平均结果
    skin_results_list = []
    rate_results_list = []
    # 用于存储全序列原始结果
    all_origin_tsk = []
    all_origin_dtsk = []
    # 初始化皮肤温度，之后每次循环后更新
    previous_tsk_mean = None

    # 3. 逐行连续模拟
    for idx, row in df.iterrows():
        # 循环更新环境参数
        model.Ta = row.get('Ta', 25)
        model.Tr = row.get('Tr', 25)
        model.Va = row.get('Va', 0.1)
        model.RH = row.get('RH', 50)
        model.Icl = row.get('Icl', 0.5)
        model.PAR = row.get('PAR', 1.0)
        # 获取模拟参数
        times = int(row.get('times', 1))
        dtime = int(row.get('dtime', 60))

        # 执行模拟并将结果从字典中取出
        model.simulate(times, dtime)
        temp_results_dict = model.dict_results()
        full_tsk_list = temp_results_dict['TskMean']

        # JOS-3会存储所有结果，因此计算变化率前先截取本次模拟产生的最后times个数据点
        if len(full_tsk_list) >= times:
            new_tsk_list = full_tsk_list[-times:]
        else:
            new_tsk_list = full_tsk_list

        # 计算本行每个时间点的变化率
        new_dtsk_dt_list = []
        for i, tsk in enumerate(new_tsk_list):
            if i == 0 and previous_tsk_mean is not None:
                # 跨行：用上一行最后一个点计算
                rate = (tsk - previous_tsk_mean) / dtime * 60
            elif i == 0 and previous_tsk_mean is None:
                # 整条序列的第一个点，变化率定为 0
                rate = 0.0
            else:
                # 行内：用本行前一个点计算
                rate = (tsk - new_tsk_list[i - 1]) / dtime * 60
            new_dtsk_dt_list.append(rate)

        # 更新上一次模拟的最后一个皮肤温度
        previous_tsk_mean = new_tsk_list[-1]

        # 收集平均结果（processed）
        ave_tsk = sum(new_tsk_list) / len(new_tsk_list)
        ave_rate = sum(new_dtsk_dt_list) / len(new_dtsk_dt_list)
        skin_results_list.append(ave_tsk)
        rate_results_list.append(ave_rate)
        # 收集原始全序列结果（origin）
        all_origin_tsk.extend(new_tsk_list)
        all_origin_dtsk.extend(new_dtsk_dt_list)

    single_processed_df = pd.DataFrame({
        'tsk': skin_results_list,
        'dtsk_dt': rate_results_list
    })
    single_origin_df = pd.DataFrame({
        'origin_tsk': all_origin_tsk,
        'origin_dtsk': all_origin_dtsk
    })

    return {
        'processed_results': single_processed_df,
        'origin_results': single_origin_df
    }


def batch_simulate_skin_temperature(df: pd.DataFrame, return_origin: bool = True):
    """"
    识别不同序号的仿真体并批量模拟

    参数：
        df: 所有仿真体的包含'Num'的人体参数、环境参数Dataframe
        return_origin: 是否返回全序列结果，默认为False

    返回：
        tuple (ave_results, origin_results):
        - ave_results: 所有仿真体平均皮肤温度结果合并的DataFrame
        - origin_results: 所有仿真体全序列结果合并的DataFrame，若return_origin=False则返回None
    """
    processed_results_list = []
    origin_results_list = []

    # sim_ids标识不同仿真体，sim_df指同一仿真体下的不同时间序列Dataframe
    sim_ids = df['Num'].unique()

    for sim_id in sim_ids:
        sim_df = df[df['Num'] == sim_id].copy()
        result_dict = single_simulate_skin_temperature(sim_df)  # 返回字典
        processed_results_list.append(result_dict['processed_results'])

        if return_origin:
            origin_results_list.append(result_dict['origin_results'])

    series_processed_results = pd.concat(processed_results_list, ignore_index=True)

    if return_origin and origin_results_list:
        series_origin_results = pd.concat(origin_results_list, ignore_index=True)
        return {
            'processed_results': series_processed_results,
            'origin_results': series_origin_results
        }
    else:
        return {
            'processed_results': series_processed_results,
            'origin_results': None
        }
