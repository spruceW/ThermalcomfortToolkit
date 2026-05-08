"""
文件处理工具
"""
import pandas as pd
import os


def read_input_file(file_path, sheet_name=0):
    """
    读取输入文件（支持Excel和CSV）

    参数:
        file_path: 文件路径
        sheet_name: Excel工作表名称或索引

    返回:
        DataFrame对象
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.xlsx' or ext == '.xls':
        return pd.read_excel(file_path, sheet_name=sheet_name)
    elif ext == '.csv':
        return pd.read_csv(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def save_results(df, file_path, sheet_name='Results', extra_sheets=None):
    """
    保存结果到文件，支持多个工作表

    参数:
        df: 主结果DataFrame
        file_path: 输出文件路径
        sheet_name: 主工作表名称（Excel）
        extra_sheets: 字典，{sheet_name: DataFrame}，额外的工作表，仅Excel支持
    """
    ext = os.path.splitext(file_path)[1].lower()

    if extra_sheets is None:
        extra_sheets = {}

    if ext == '.xlsx' or ext == '.xls':
        # 使用ExcelWriter可以写多个sheet
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            for sheet, data in extra_sheets.items():
                if data is not None and not data.empty:
                    data.to_excel(writer, sheet_name=sheet, index=False)
    elif ext == '.csv':
        if extra_sheets:
            raise ValueError("CSV不支持多个工作表，请使用Excel格式")
        df.to_csv(file_path, index=False)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def validate_input_data(df, required_columns):
    """
    验证输入数据是否包含必要的列

    参数:
        df: 输入DataFrame
        required_columns: 必需的列名列表

    返回:
        (is_valid, missing_columns)
    """
    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing
