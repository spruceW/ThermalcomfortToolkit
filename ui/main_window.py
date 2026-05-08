"""
主界面 - PyQt5实现
"""
import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton, QFileDialog,
    QGroupBox, QTextEdit, QProgressBar, QMessageBox, QSpinBox, QDoubleSpinBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utci_calculator import calculate_utci
from core.pmv_calculator import calculate_pmv_ppd
from core.pet_calculator import calculate_pet
from core.rdts_calculator import calculate_rdts
from core.jos3_simulator import batch_simulate_skin_temperature
from utils.file_handler import read_input_file, save_results, validate_input_data


class CalculationThread(QThread):
    """计算线程，避免界面卡顿"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, calc_type, input_data, params):
        super().__init__()
        self.calc_type = calc_type
        self.input_data = input_data
        self.params = params

    def run(self):
        try:
            results = {}

            if self.calc_type == 'single':
                # 单点计算
                result = self.calculate_single()
                results['single'] = result
            else:
                # 批量计算，返回 (结果DataFrame, 原始模拟皮肤温度DataFrame 或 None)
                result_df, origin_skin_df = self.calculate_batch()
                results['batch'] = result_df
                results['origin_skin'] = origin_skin_df  # 可能为None

            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

    def calculate_single(self):
        """单点计算"""
        result = {}

        # PMV/PPD的计算
        if self.params.get('calc_pmv', False):
            pmv_result = calculate_pmv_ppd(
                tdb=self.params['tdb'],
                tr=self.params['tr'],
                v=self.params['v'],
                rh=self.params['rh'],
                met=self.params.get('met', 1.2),
                clo=self.params.get('clo', 0.5)
            )
            result['PMV'] = pmv_result['pmv']
            result['PPD'] = pmv_result['ppd']

        if self.params.get('calc_pet', False):
            pet_result = calculate_pet(
                tdb=self.params['tdb'],
                tr=self.params['tr'],
                v=self.params['v'],
                rh=self.params['rh'],
                met=self.params.get('met', 1.2),
                clo=self.params.get('clo', 0.5),
                posture=self.params['posture'],
                age=self.params['age'],
                gender=self.params['gender'],
                weight=self.params.get('weight', 70),
                height=self.params.get('height', 1.7),
            )
            result['PET'] = pet_result['pet']

        # UTCI和RDTS的计算
        if self.params.get('calc_utci', False) or self.params.get('calc_rdts', False):
            # 先计算UTCI
            utci_result = calculate_utci(
                h=self.params.get('height_measure', 1.1),
                tdb=self.params['tdb'],
                tr=self.params['tr'],
                v=self.params['v'],
                rh=self.params['rh']
            )
            result['UTCI'] = utci_result['utci']
            # 若勾选了RDTS再计算RDTS
            if self.params.get('calc_rdts', False):
                rdts = calculate_rdts(
                    season=self.params.get('season', 'summer'),
                    utci=utci_result['utci'],
                    tmrt=self.params['tr'],
                    vr=self.params['v'],
                    dtsk_dt=self.params.get('dtsk_dt', 0)
                )
                result['RDTS'] = rdts

        return result

    def calculate_batch(self):
        """批量计算"""
        df = self.input_data
        results = []

        # ===== 如果选择使用JOS-3，先一次性模拟整个时间序列，然后提取出变化率 =====
        df_tsk_with_dtsk = None
        origin_df_tsk_with_dtsk = None
        if self.params.get('use_jos3', True):
            try:
                dict_df_tsk_with_dtsk = batch_simulate_skin_temperature(df)
                df_tsk_with_dtsk = dict_df_tsk_with_dtsk['processed_results']
                origin_df_tsk_with_dtsk = dict_df_tsk_with_dtsk['origin_results']
            except Exception as e:
                # 如果失败，则使用文件中的dtsk_dt列
                df_tsk_with_dtsk = df.copy()
                # 如果没有dtsk_dt列则默认变化率为0
                if 'dtsk_dt' not in df_tsk_with_dtsk.columns:
                    df_tsk_with_dtsk['dtsk_dt'] = 0
                self.error.emit(f"模拟失败: {str(e)}")

        # ===== 然后逐行计算其他指标 =====
        for idx, row in df.iterrows():
            self.progress.emit(int((idx + 1) / len(df) * 100))
            row_result = {'index': idx}

            # PMV/PPD计算
            if self.params.get('calc_pmv', False):
                pmv_result = calculate_pmv_ppd(
                    tdb=row.get('tdb', row.get('Ta', 25)),
                    tr=row.get('tr', row.get('Tr', 25)),
                    v=row.get('v', row.get('Va', 0.1)),
                    rh=row.get('rh', row.get('RH', 50)),
                    met=row.get('met', row.get('PAR', 1.2)),
                    clo=row.get('clo', row.get('Icl', 0.5))
                )
                row_result['PMV'] = pmv_result['pmv']
                row_result['PPD'] = pmv_result['ppd']

            # PET计算
            if self.params.get('calc_pet', False):
                pet_result = calculate_pet(
                    tdb=row.get('tdb', row.get('Ta', 25)),
                    tr=row.get('tr', row.get('Tr', 25)),
                    v=row.get('v', row.get('Va', 0.1)),
                    rh=row.get('rh', row.get('RH', 50)),
                    met=row.get('met', row.get('PAR', 1.2)),
                    clo=row.get('clo', row.get('Icl', 0.5)),
                    posture=row.get('posture', row.get('position', 'sitting')),
                    age=row.get('age', row.get('age', 25)),
                    gender=row.get('gender', row.get('sex', 'male')),
                    weight=row.get('weight', row.get('weight', 70)),
                    height=row.get('height', row.get('height', 1.7)),
                )
                row_result['PET'] = pet_result['pet']

            # UTCI和RDTS的计算
            if self.params.get('calc_utci', False) or self.params.get('calc_rdts', False):
                # 判断是否勾选了UTCI，则先计算UTCI
                utci_result = calculate_utci(
                    h=self.params.get('height_measure', 1.1),
                    tdb=row.get('tdb', row.get('Ta', 25)),
                    tr=row.get('tr', row.get('Tr', 25)),
                    v=row.get('v', row.get('Va', 0.5)),
                    rh=row.get('rh', row.get('RH', 50))
                )
                row_result['UTCI'] = utci_result['utci']
                # 判断是否勾选了RDTS，是就输出RDTS
                # RDTS计算
                if self.params.get('calc_rdts', False):
                    # 从JOS-3获取皮肤温度变化率
                    if self.params.get('use_jos3', False) and df_tsk_with_dtsk is not None:
                        # 勾选JOS-3模拟
                        dtsk_dt = df_tsk_with_dtsk.iloc[idx].get('dtsk_dt', 0)
                    else:
                        # 勾选从文件读取
                        dtsk_dt = row.get('dtsk_dt', 0) if 'dtsk_dt' in row else 0
                    rdts = calculate_rdts(
                        season=self.params.get('season', 'summer'),
                        utci=utci_result['utci'],
                        tmrt=row.get('tr', row.get('Tr', 25)),
                        vr=row.get('v', row.get('Va', 0.5)),
                        dtsk_dt=dtsk_dt
                    )
                    row_result['RDTS'] = rdts

            results.append(row_result)
        # 创建基础计算结果
        result_df = pd.DataFrame(results)

        # ===== 将JOS-3的结果合并到最终的DataFrame；仅当用户勾选“输出模拟皮肤温度”时，将原始模拟结果输出到第二张工作簿 =====
        origin_skin_to_save = None
        if self.params.get('use_jos3', False) and self.params.get('calc_tsk', False):
            if origin_df_tsk_with_dtsk is not None and not origin_df_tsk_with_dtsk.empty:
                origin_skin_to_save = origin_df_tsk_with_dtsk.copy()

        return result_df,  origin_skin_to_save


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("热舒适模型工具包")
        self.setMinimumSize(900, 700)

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建菜单栏
        menubar = self.menuBar()
        # 创建"文件"菜单
        file_menu = menubar.addMenu('文件')
        # 添加"生成模板"动作
        generate_action = QAction('生成批量计算模板', self)
        generate_action.triggered.connect(self.generate_template)  # 连接函数
        file_menu.addAction(generate_action)
        # 添加"打开操作指南"动作
        guide_action = QAction('打开操作指南', self)
        guide_action.triggered.connect(self.open_user_guide)
        file_menu.addAction(guide_action)

        main_layout = QVBoxLayout(central_widget)

        # 创建选项卡
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        # 选项卡1：单点计算
        single_tab = self.create_single_tab()
        tabs.addTab(single_tab, "单点计算")
        # 选项卡2：批量计算
        batch_tab = self.create_batch_tab()
        tabs.addTab(batch_tab, "批量计算")
        # 状态栏
        self.statusBar().showMessage("就绪")

    def get_resource_path(self, relative_path):
        """获取资源文件的绝对路径"""
        try:
            # PyInstaller 创建临时文件夹，将路径存储在 _MEIPASS 中
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def generate_template(self):
        """生成批量计算模板到桌面"""
        try:
            # 1. 找到模板文件的路径
            # 模板文件路径
            template_path = self.get_resource_path(os.path.join('resources', 'template.xlsx'))
            # 检查模板是否存在
            if not os.path.exists(template_path):
                QMessageBox.warning(self, "错误", "模板文件不存在！")
                return

            # 2. 获取桌面路径
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')

            # 3. 生成目标文件名
            base_name = "thermal_comfort_template.xlsx"
            target_path = os.path.join(desktop, base_name)
            # 如果文件已存在，添加数字后缀
            counter = 1
            while os.path.exists(target_path):
                name, ext = os.path.splitext(base_name)
                target_path = os.path.join(desktop, f"{name}_{counter}{ext}")
                counter += 1

            # 4. 复制文件
            import shutil
            shutil.copy2(template_path, target_path)  # copy2 保留元数据
            QMessageBox.information(
                self,
                "成功",
                f"模板已生成到桌面：\n{os.path.basename(target_path)}"
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成模板失败：{str(e)}")

    def open_user_guide(self):
        """打开操作指南PDF"""
        try:
            # 获取PDF文件路径
            guide_path = self.get_resource_path(os.path.join('resources', '操作指南.pdf'))

            # 检查文件是否存在
            if not os.path.exists(guide_path):
                QMessageBox.warning(self, "错误", "操作指南文件不存在！")
                return
            # 使用系统默认的PDF阅读器打开（当前仅支持Windows系统）
            os.startfile(guide_path)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开操作指南失败：{str(e)}")

    def create_single_tab(self):
        """创建单点计算选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 计算选项组
        calc_group = QGroupBox("输出选项")
        calc_layout = QHBoxLayout()

        self.calc_pmv_cb = QCheckBox("PMV/PPD")
        self.calc_pet_cb = QCheckBox("PET")
        self.calc_utci_cb = QCheckBox("UTCI")
        self.calc_rdts_cb = QCheckBox("RDTS")

        calc_layout.addWidget(self.calc_pmv_cb)
        calc_layout.addWidget(self.calc_pet_cb)
        calc_layout.addWidget(self.calc_utci_cb)
        calc_layout.addWidget(self.calc_rdts_cb)
        calc_layout.addStretch()
        calc_group.setLayout(calc_layout)
        layout.addWidget(calc_group)

        # 其他基本参数选项组
        rdts_group = QGroupBox("基本参数")
        rdts_layout = QGridLayout()

        rdts_layout.addWidget(QLabel("季节:"), 0, 0)
        self.season_combo = QComboBox()
        self.season_combo.addItems(["夏季", "冬季"])
        rdts_layout.addWidget(self.season_combo, 0, 1)

        rdts_layout.addWidget(QLabel("测点高度:"), 1, 0)
        self.height_measure_input = QDoubleSpinBox()
        self.height_measure_input.setRange(0.1, 1.7)
        self.height_measure_input.setSingleStep(0.1)
        self.height_measure_input.setValue(1.1)
        self.height_measure_input.setDecimals(1)
        rdts_layout.addWidget(self.height_measure_input, 1, 1)

        rdts_group.setLayout(rdts_layout)
        layout.addWidget(rdts_group)

        # 人体参数组
        body_group = QGroupBox("人体参数")
        body_layout = QGridLayout()

        body_layout.addWidget(QLabel("性别:"), 0, 0)
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["male", "female"])
        body_layout.addWidget(self.gender_combo, 0, 1)

        body_layout.addWidget(QLabel("年龄 (岁):"), 0, 2)
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 120)
        self.age_spin.setValue(30)
        body_layout.addWidget(self.age_spin, 0, 3)

        body_layout.addWidget(QLabel("身高 (m):"), 1, 0)
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0.5, 2.5)
        self.height_spin.setSingleStep(0.01)
        self.height_spin.setValue(1.7)
        body_layout.addWidget(self.height_spin, 1, 1)

        body_layout.addWidget(QLabel("体重 (kg):"), 1, 2)
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(10, 300)
        self.weight_spin.setValue(70)
        body_layout.addWidget(self.weight_spin, 1, 3)

        body_layout.addWidget(QLabel("姿势:"), 2, 0)
        self.posture_combo = QComboBox()
        self.posture_combo.addItems(["sitting", "standing"])
        body_layout.addWidget(self.posture_combo, 2, 1)

        body_layout.addWidget(QLabel("代谢率 (met):"), 2, 2)
        self.met_spin = QDoubleSpinBox()
        self.met_spin.setRange(0.5, 5)
        self.met_spin.setSingleStep(0.1)
        self.met_spin.setValue(1.2)
        body_layout.addWidget(self.met_spin, 2, 3)

        body_layout.addWidget(QLabel("服装热阻 (clo):"), 3, 0)
        self.clo_spin = QDoubleSpinBox()
        self.clo_spin.setRange(0, 5)
        self.clo_spin.setSingleStep(0.01)
        self.clo_spin.setValue(0.5)
        body_layout.addWidget(self.clo_spin, 3, 1)

        body_layout.addWidget(QLabel("皮肤温度变化率 (dTsk/dt, °C/min):"), 3, 2)
        self.dtsk_input = QDoubleSpinBox()
        self.dtsk_input.setRange(-3, 3)
        self.dtsk_input.setSingleStep(0.01)
        self.dtsk_input.setValue(0)
        self.dtsk_input.setDecimals(3)
        body_layout.addWidget(self.dtsk_input, 3, 3)

        body_group.setLayout(body_layout)
        layout.addWidget(body_group)

        # 环境参数组
        env_group = QGroupBox("环境参数")
        env_layout = QGridLayout()

        env_layout.addWidget(QLabel("空气温度 Ta (°C):"), 0, 0)
        self.ta_spin = QDoubleSpinBox()
        self.ta_spin.setRange(-30, 60)
        self.ta_spin.setValue(25)
        env_layout.addWidget(self.ta_spin, 0, 1)

        env_layout.addWidget(QLabel("平均辐射温度 Tr (°C):"), 0, 2)
        self.tr_spin = QDoubleSpinBox()
        self.tr_spin.setRange(-30, 60)
        self.tr_spin.setValue(25)
        env_layout.addWidget(self.tr_spin, 0, 3)

        env_layout.addWidget(QLabel("相对湿度 RH (%):"), 1, 0)
        self.rh_spin = QDoubleSpinBox()
        self.rh_spin.setRange(0, 100)
        self.rh_spin.setValue(50)
        env_layout.addWidget(self.rh_spin, 1, 1)

        env_layout.addWidget(QLabel("风速 v (m/s):"), 1, 2)
        self.v_spin = QDoubleSpinBox()
        self.v_spin.setRange(0, 20)
        self.v_spin.setSingleStep(0.1)
        self.v_spin.setValue(0.1)
        env_layout.addWidget(self.v_spin, 1, 3)

        env_group.setLayout(env_layout)
        layout.addWidget(env_group)

        # 按钮和结果显示
        self.calc_btn = QPushButton("开始计算")
        self.calc_btn.clicked.connect(self.on_single_calc)
        layout.addWidget(self.calc_btn)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(200)
        layout.addWidget(self.result_text)

        layout.addStretch()

        return widget

    def create_batch_tab(self):
        """创建批量计算选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 文件选择
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("输入文件:"))
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path_edit)
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.clicked.connect(self.on_browse_file)
        file_layout.addWidget(self.browse_btn)
        layout.addLayout(file_layout)

        # 计算选项组
        calc_group = QGroupBox("输出选项")
        calc_layout = QHBoxLayout()

        self.batch_calc_pmv_cb = QCheckBox("PMV/PPD")
        self.batch_calc_pet_cb = QCheckBox("PET")
        self.batch_calc_utci_cb = QCheckBox("UTCI")
        self.batch_calc_rdts_cb = QCheckBox("RDTS")
        self.batch_calc_tsk_cb = QCheckBox("模拟皮肤温度")

        calc_layout.addWidget(self.batch_calc_pmv_cb)
        calc_layout.addWidget(self.batch_calc_pet_cb)
        calc_layout.addWidget(self.batch_calc_utci_cb)
        calc_layout.addWidget(self.batch_calc_rdts_cb)
        calc_layout.addWidget(self.batch_calc_tsk_cb)
        calc_layout.addStretch()
        calc_group.setLayout(calc_layout)
        layout.addWidget(calc_group)

        # RDTS选项组
        rdts_group = QGroupBox("RDTS选项卡")
        rdts_layout = QGridLayout()

        rdts_layout.addWidget(QLabel("季节:"), 0, 0)
        self.batch_season_combo = QComboBox()
        self.batch_season_combo.addItems(["夏季", "冬季"])
        rdts_layout.addWidget(self.batch_season_combo, 0, 1)

        rdts_layout.addWidget(QLabel("皮肤温度变化率来源:"), 1, 0)
        self.batch_dtsk_source_combo = QComboBox()
        self.batch_dtsk_source_combo.addItems(["从文件读取", "JOS-3模拟"])
        rdts_layout.addWidget(self.batch_dtsk_source_combo, 1, 1)

        rdts_layout.addWidget(QLabel("测点高度:"), 2, 0)
        self.batch_height_measure_input = QDoubleSpinBox()
        self.batch_height_measure_input.setRange(0.1, 1.7)
        self.batch_height_measure_input.setSingleStep(0.1)
        self.batch_height_measure_input.setValue(1.1)
        self.batch_height_measure_input.setDecimals(1)
        rdts_layout.addWidget(self.batch_height_measure_input, 2, 1)

        rdts_group.setLayout(rdts_layout)
        layout.addWidget(rdts_group)

        # 输出文件选择
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件:"))
        self.output_path_edit = QLineEdit()
        output_layout.addWidget(self.output_path_edit)
        self.save_btn = QPushButton("保存位置")
        self.save_btn.clicked.connect(self.on_save_location)
        output_layout.addWidget(self.save_btn)
        layout.addLayout(output_layout)

        # 计算按钮
        self.batch_calc_btn = QPushButton("开始批量计算")
        self.batch_calc_btn.clicked.connect(self.on_batch_calc)
        layout.addWidget(self.batch_calc_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 结果预览
        self.preview_table = QTableWidget()
        layout.addWidget(self.preview_table)

        return widget

    def on_single_calc(self):
        """单点计算主线程"""
        # 收集参数
        params = {
            'calc_utci': self.calc_utci_cb.isChecked(),
            'calc_pmv': self.calc_pmv_cb.isChecked(),
            'calc_pet': self.calc_pet_cb.isChecked(),
            'calc_rdts': self.calc_rdts_cb.isChecked(),
            'season': 'winter' if self.season_combo.currentText() == "冬季" else 'summer',
            'height_measure': self.height_measure_input.value(),
            'dtsk_dt': self.dtsk_input.value(),
            'tdb': self.ta_spin.value(),
            'tr': self.tr_spin.value(),
            'v': self.v_spin.value(),
            'rh': self.rh_spin.value(),
            'met': self.met_spin.value(),
            'clo': self.clo_spin.value(),
            'height': self.height_spin.value(),
            'weight': self.weight_spin.value(),
            'age': self.age_spin.value(),
            'gender': self.gender_combo.currentText(),
            'posture': self.posture_combo.currentText()
        }

        # 检查是否选择了计算内容
        if not any([params['calc_utci'], params['calc_pmv'], params['calc_rdts']]):
            QMessageBox.warning(self, "警告", "请至少选择一项计算内容")
            return

        # 启动计算线程
        self.calc_btn.setEnabled(False)
        self.statusBar().showMessage("计算中...")

        self.calc_thread = CalculationThread('single', None, params)
        self.calc_thread.finished.connect(self.on_single_calc_finished)
        self.calc_thread.error.connect(self.on_calc_error)
        self.calc_thread.start()

    def on_single_calc_finished(self, results):
        """单点计算完成"""
        self.calc_btn.setEnabled(True)
        self.statusBar().showMessage("计算完成")

        # 显示结果
        result_data = results.get('single', {})
        text = "计算结果:\n" + "=" * 40 + "\n"
        for key, value in result_data.items():
            text += f"{key}: {value:.1f}\n"

        self.result_text.setText(text)

    def on_browse_file(self):
        """浏览输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择输入文件", "", "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def on_save_location(self):
        """选择保存位置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果", "results.xlsx", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if file_path:
            self.output_path_edit.setText(file_path)

    def on_batch_calc(self):
        """批量计算主线程"""

        # ===== 执行计算前先做选项卡检查 =====
        file_path = self.file_path_edit.text()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择输入文件")
            return

        output_path = self.output_path_edit.text()
        if not output_path:
            QMessageBox.warning(self, "警告", "请选择输出文件位置")
            return

        # 检查是否选择了计算内容
        if not any([self.batch_calc_utci_cb.isChecked(),
                    self.batch_calc_pmv_cb.isChecked(),
                    self.batch_calc_rdts_cb.isChecked(),
                    self.batch_calc_tsk_cb.isChecked()]):
            QMessageBox.warning(self, "警告", "请至少选择一项计算内容")
            return

        # 检查输出皮肤温度的同时是否勾选了jos3
        if self.batch_calc_tsk_cb.isChecked() and not self.batch_dtsk_source_combo.currentText() == "JOS-3模拟":
            QMessageBox.warning(self, "警告", "输出模拟皮肤温度必须选择JOS-3")
            return

        try:
            # 读取输入文件
            df = read_input_file(file_path)

            # 收集参数
            params = {
                'calc_utci': self.batch_calc_utci_cb.isChecked(),
                'calc_pmv': self.batch_calc_pmv_cb.isChecked(),
                'calc_pet': self.batch_calc_pet_cb.isChecked(),
                'calc_rdts': self.batch_calc_rdts_cb.isChecked(),
                'calc_tsk': self.batch_calc_tsk_cb.isChecked(),
                'season': 'winter' if self.batch_season_combo.currentText() == "冬季" else 'summer',
                'use_jos3': self.batch_dtsk_source_combo.currentText() == "JOS-3模拟",
                'use_actual': self.batch_dtsk_source_combo.currentText() == "从文件读取",
                'height_measure': self.batch_height_measure_input.value()
            }

            # 启动计算线程
            self.batch_calc_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            self.statusBar().showMessage("批量计算中...")

            self.batch_thread = CalculationThread('batch', df, params)
            self.batch_thread.progress.connect(self.progress_bar.setValue)
            self.batch_thread.finished.connect(lambda r: self.on_batch_calc_finished(r, output_path))
            self.batch_thread.error.connect(self.on_calc_error)
            self.batch_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")

    def on_batch_calc_finished(self, results, output_path):
        """批量计算完成"""
        self.batch_calc_btn.setEnabled(True)
        self.statusBar().showMessage("计算完成")

        result_df = results.get('batch')
        origin_skin_df = results.get('origin_skin')  # 原始模拟皮肤温度数据（可能为None）
        if result_df is not None and not result_df.empty:
            try:
                # 准备额外的工作表
                extra_sheets = {}
                if origin_skin_df is not None and not origin_skin_df.empty:
                    extra_sheets['SimulationResults'] = origin_skin_df

                save_results(result_df, output_path, sheet_name='Results', extra_sheets=extra_sheets)
                QMessageBox.information(self, "成功", f"结果已保存到: {output_path}")

                # 预览结果
                self.preview_table.setRowCount(min(10, len(result_df)))
                self.preview_table.setColumnCount(len(result_df.columns))
                self.preview_table.setHorizontalHeaderLabels(result_df.columns.tolist())

                for i in range(min(10, len(result_df))):
                    for j, col in enumerate(result_df.columns):
                        value = result_df.iloc[i][col]
                        if isinstance(value, float):
                            self.preview_table.setItem(i, j, QTableWidgetItem(f"{value:.1f}"))
                        else:
                            self.preview_table.setItem(i, j, QTableWidgetItem(str(value)))

                self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存结果失败: {str(e)}")
        else:
            QMessageBox.warning(self, "警告", "未生成有效结果")

    def on_calc_error(self, error_msg):
        """计算错误"""
        self.calc_btn.setEnabled(True)
        self.batch_calc_btn.setEnabled(True)
        self.statusBar().showMessage("计算失败")
        QMessageBox.critical(self, "错误", f"计算失败: {error_msg}")
