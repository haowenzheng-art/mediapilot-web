
"""
MediaPilot 主窗口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTabWidget, QStatusBar, QMenuBar, QAction,
    QFileDialog, QSplitter, QMessageBox, QProgressBar, QGroupBox,
    QCheckBox, QComboBox, QDialog, QLabel, QLineEdit, QDialogButtonBox,
    QListWidget, QFormLayout, QFrame, QStackedWidget, QScrollArea,
    QGridLayout, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSlot, QFile, QTextStream, QTimer, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPalette, QColor

from desktop.api_client import api_client


class ApiKeyDialog(QDialog):
    """API配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("配置 AI API")
        self.setMinimumWidth(550)
        self.setStyleSheet("background-color: #0F172A;")

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        info_label = QLabel("选择API类型并配置相关参数")
        info_label.setStyleSheet("color: #94A3B8; padding: 8px 0;")
        layout.addWidget(info_label)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.api_type_combo = QComboBox()
        self.api_type_combo.addItems([
            "Anthropic (Claude)",
            "OpenAI 兼容接口 (火山方舟/其他)",
            "火山方舟 (原生API)"
        ])
        self.api_type_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid rgba(99, 102, 241, 0.3);
                border-radius: 8px;
                padding: 10px 16px;
                background-color: #1E293B;
                color: #F8FAFC;
                min-height: 24px;
            }
        """)
        form_layout.addRow("API类型:", self.api_type_combo)

        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://ark.cn-beijing.volces.com/api/v3")
        form_layout.addRow("Base URL:", self.base_url_edit)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("输入你的API Key")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("API Key:", self.api_key_edit)

        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("例如: doubao-seed-2-0-pro-260215")
        form_layout.addRow("模型名称:", self.model_edit)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        skip_btn = QPushButton("跳过")
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #475569;
                color: white;
                padding: 10px 24px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #64748B;
            }
        """)
        skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(skip_btn)

        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def get_config(self):
        """获取配置"""
        api_type_index = self.api_type_combo.currentIndex()
        if api_type_index == 0:
            provider = "anthropic"
        elif api_type_index == 1:
            provider = "openai"
        else:
            provider = "ark"

        return {
            "provider": provider,
            "api_key": self.api_key_edit.text().strip(),
            "base_url": self.base_url_edit.text().strip() or None,
            "model": self.model_edit.text().strip() or None
        }


class TrendingWidget(QWidget):
    """热点追踪模块"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 搜索区域
        search_group = QGroupBox("🔍 热点搜索")
        search_group.setObjectName("CardWidget")
        search_layout = QFormLayout(search_group)
        search_layout.setSpacing(12)

        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("输入关键词，如：美妆、科技、创业...")
        search_layout.addRow("关键词:", self.keyword_edit)

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["全部平台", "抖音", "小红书", "微博"])
        search_layout.addRow("平台:", self.platform_combo)

        self.days_combo = QComboBox()
        self.days_combo.addItems(["1天", "3天", "7天", "14天", "30天"])
        self.days_combo.setCurrentIndex(2)
        search_layout.addRow("时间范围:", self.days_combo)

        self.search_btn = QPushButton("🚀 开始搜索")
        self.search_btn.clicked.connect(self.search_trending)
        search_layout.addRow(self.search_btn)

        layout.addWidget(search_group)

        # 结果区域
        result_group = QGroupBox("📊 热点列表")
        result_group.setObjectName("CardWidget")
        result_layout = QVBoxLayout(result_group)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(["标题", "热度", "平台", "趋势", "链接"])
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        result_layout.addWidget(self.result_table)

        layout.addWidget(result_group, 1)

    def search_trending(self):
        """搜索热点"""
        keyword = self.keyword_edit.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入关键词")
            return

        platforms = ["douyin", "xiaohongshu", "weibo"]
        days = int(self.days_combo.currentText().replace("天", ""))

        success, data = api_client.search_trending(keyword, platforms, days)

        if success and data:
            self.display_results(data.get("hot_topics", []))
        else:
            QMessageBox.warning(self, "提示", "搜索失败，请检查后端服务是否启动")

    def display_results(self, topics):
        """显示结果"""
        self.result_table.setRowCount(len(topics))
        for row, topic in enumerate(topics):
            self.result_table.setItem(row, 0, QTableWidgetItem(topic.get("title", "")))
            self.result_table.setItem(row, 1, QTableWidgetItem(str(topic.get("heat_index", 0))))
            self.result_table.setItem(row, 2, QTableWidgetItem(topic.get("platform", "")))
            self.result_table.setItem(row, 3, QTableWidgetItem(topic.get("trend", "")))
            self.result_table.setItem(row, 4, QTableWidgetItem(topic.get("url", "")))


class CompetitorWidget(QWidget):
    """对标账号模块"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 搜索区域
        search_group = QGroupBox("🎯 对标搜索")
        search_group.setObjectName("CardWidget")
        search_layout = QFormLayout(search_group)
        search_layout.setSpacing(12)

        self.niche_edit = QLineEdit()
        self.niche_edit.setPlaceholderText("输入赛道，如：护肤、编程、美食...")
        search_layout.addRow("赛道:", self.niche_edit)

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["全部", "抖音", "小红书"])
        search_layout.addRow("平台:", self.platform_combo)

        self.search_btn = QPushButton("🔍 开始搜索")
        self.search_btn.clicked.connect(self.search_competitors)
        search_layout.addRow(self.search_btn)

        layout.addWidget(search_group)

        # 结果区域
        result_group = QGroupBox("📋 账号列表")
        result_group.setObjectName("CardWidget")
        result_layout = QVBoxLayout(result_group)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(7)
        self.result_table.setHorizontalHeaderLabels(["昵称", "平台", "粉丝", "获赞", "作品", "平均点赞", "主页链接"])
        for i in range(7):
            self.result_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        result_layout.addWidget(self.result_table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.export_btn = QPushButton("📥 导出Excel")
        self.export_btn.setObjectName("SuccessBtn")
        self.export_btn.clicked.connect(self.export_excel)
        btn_layout.addWidget(self.export_btn)
        result_layout.addLayout(btn_layout)

        layout.addWidget(result_group, 1)

        self.current_niche = ""

    def search_competitors(self):
        """搜索对标账号"""
        niche = self.niche_edit.text().strip()
        if not niche:
            QMessageBox.warning(self, "提示", "请输入赛道")
            return

        self.current_niche = niche
        platforms = ["douyin", "xiaohongshu"]

        success, data = api_client.search_competitors(niche, platforms)

        if success and data:
            self.display_results(data.get("accounts", []))
        else:
            QMessageBox.warning(self, "提示", "搜索失败，请检查后端服务是否启动")

    def display_results(self, accounts):
        """显示结果"""
        self.result_table.setRowCount(len(accounts))
        for row, acc in enumerate(accounts):
            self.result_table.setItem(row, 0, QTableWidgetItem(acc.get("nickname", "")))
            self.result_table.setItem(row, 1, QTableWidgetItem(acc.get("platform", "")))
            self.result_table.setItem(row, 2, QTableWidgetItem(str(acc.get("followers", 0))))
            self.result_table.setItem(row, 3, QTableWidgetItem(str(acc.get("total_likes", 0))))
            self.result_table.setItem(row, 4, QTableWidgetItem(str(acc.get("video_count", 0))))
            self.result_table.setItem(row, 5, QTableWidgetItem(str(acc.get("avg_likes", 0))))
            self.result_table.setItem(row, 6, QTableWidgetItem(acc.get("profile_url", "")))

    def export_excel(self):
        """导出Excel"""
        if not self.current_niche:
            QMessageBox.warning(self, "提示", "请先搜索对标账号")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Excel文件", "", "Excel文件 (*.xlsx);;所有文件 (*.*)"
        )
        if file_path:
            success = api_client.export_competitors(self.current_niche, file_path)
            if success:
                QMessageBox.information(self, "成功", "✓ 导出成功！")
            else:
                QMessageBox.warning(self, "失败", "导出失败")


class ContentWidget(QWidget):
    """内容生成模块"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 输入区域
        input_group = QGroupBox("✍️ 内容生成")
        input_group.setObjectName("CardWidget")
        input_layout = QFormLayout(input_group)
        input_layout.setSpacing(12)

        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("输入选题，如：如何护肤、Python入门...")
        input_layout.addRow("选题:", self.topic_edit)

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["抖音", "小红书", "B站"])
        input_layout.addRow("平台:", self.platform_combo)

        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["15秒", "30秒", "60秒", "90秒", "120秒"])
        self.duration_combo.setCurrentIndex(2)
        input_layout.addRow("时长:", self.duration_combo)

        self.style_combo = QComboBox()
        self.style_combo.addItems(["专业", "幽默", "简洁", "情感", "讲故事"])
        input_layout.addRow("风格:", self.style_combo)

        self.generate_btn = QPushButton("✨ 生成脚本")
        self.generate_btn.clicked.connect(self.generate_content)
        input_layout.addRow(self.generate_btn)

        layout.addWidget(input_group)

        # 结果区域
        result_group = QGroupBox("📝 生成结果")
        result_group.setObjectName("CardWidget")
        result_layout = QVBoxLayout(result_group)

        self.result_tabs = QTabWidget()

        # 分镜头脚本Tab
        self.script_table = QTableWidget()
        self.script_table.setColumnCount(5)
        self.script_table.setHorizontalHeaderLabels(["场景", "时长", "画面", "台词", "备注"])
        for i in range(5):
            self.script_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.result_tabs.addTab(self.script_table, "🎬 分镜头脚本")

        # 文案Tab
        self.copy_text = QTextEdit()
        self.copy_text.setReadOnly(True)
        self.result_tabs.addTab(self.copy_text, "📋 文案建议")

        result_layout.addWidget(self.result_tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.export_btn = QPushButton("📥 导出脚本")
        self.export_btn.setObjectName("SuccessBtn")
        btn_layout.addWidget(self.export_btn)
        result_layout.addLayout(btn_layout)

        layout.addWidget(result_group, 1)

    def generate_content(self):
        """生成内容"""
        topic = self.topic_edit.text().strip()
        if not topic:
            QMessageBox.warning(self, "提示", "请输入选题")
            return

        platform_map = {"抖音": "douyin", "小红书": "xiaohongshu", "B站": "bilibili"}
        style_map = {"专业": "professional", "幽默": "humorous", "简洁": "concise",
                    "情感": "emotional", "讲故事": "storytelling"}

        platform = platform_map.get(self.platform_combo.currentText(), "douyin")
        style = style_map.get(self.style_combo.currentText(), "professional")
        duration = int(self.duration_combo.currentText().replace("秒", ""))

        success, data = api_client.generate_content(topic, platform, duration, style)

        if success and data:
            self.display_results(data)
        else:
            QMessageBox.warning(self, "提示", "生成失败，请检查后端服务和AI配置")

    def display_results(self, data):
        """显示结果"""
        script = data.get("script", [])
        self.script_table.setRowCount(len(script))
        for row, shot in enumerate(script):
            self.script_table.setItem(row, 0, QTableWidgetItem(str(shot.get("scene", ""))))
            self.script_table.setItem(row, 1, QTableWidgetItem(shot.get("duration", "")))
            self.script_table.setItem(row, 2, QTableWidgetItem(shot.get("visual", "")))
            self.script_table.setItem(row, 3, QTableWidgetItem(shot.get("audio", "")))
            self.script_table.setItem(row, 4, QTableWidgetItem(shot.get("notes", "")))

        copy = data.get("copywriting", {})
        copy_text = f"""
标题: {copy.get('title', '')}

🎣 钩子:
{chr(10).join(f'  • {h}' for h in copy.get('hooks', []))}

📢 引导语: {copy.get('call_to_action', '')}

🏷️ 标签: {', '.join(copy.get('tags', []))}
"""
        self.copy_text.setPlainText(copy_text)


class TranscribeWidget(QWidget):
    """音视频转写模块"""

    def __init__(self):
        super().__init__()
        self.current_task_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 上传区域
        upload_group = QGroupBox("🎤 音视频转写")
        upload_group.setObjectName("CardWidget")
        upload_layout = QVBoxLayout(upload_group)

        self.file_label = QLabel("请选择 mp3 或 mp4 文件")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet("color: #94A3B8; padding: 40px;")
        upload_layout.addWidget(self.file_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.select_btn = QPushButton("📂 选择文件")
        self.select_btn.setObjectName("SecondaryBtn")
        self.select_btn.clicked.connect(self.select_file)
        btn_layout.addWidget(self.select_btn)
        self.upload_btn = QPushButton("🚀 开始转写")
        self.upload_btn.clicked.connect(self.upload_and_transcribe)
        self.upload_btn.setEnabled(False)
        btn_layout.addWidget(self.upload_btn)
        btn_layout.addStretch()
        upload_layout.addLayout(btn_layout)

        layout.addWidget(upload_group)

        # 进度区域
        self.progress_group = QGroupBox("⏳ 处理状态")
        self.progress_group.setObjectName("CardWidget")
        self.progress_group.hide()
        progress_layout = QVBoxLayout(self.progress_group)

        self.status_label = QLabel("准备中...")
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(self.progress_group)

        # 结果区域
        result_group = QGroupBox("📝 转写结果")
        result_group.setObjectName("CardWidget")
        result_layout = QVBoxLayout(result_group)

        self.result_tabs = QTabWidget()

        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.result_tabs.addTab(self.transcript_text, "📄 全文")

        self.outline_table = QTableWidget()
        self.outline_table.setColumnCount(3)
        self.outline_table.setHorizontalHeaderLabels(["章节", "标题", "摘要"])
        self.result_tabs.addTab(self.outline_table, "📋 大纲")

        result_layout.addWidget(self.result_tabs)

        layout.addWidget(result_group, 1)

        self.current_file = None

        # 轮询定时器
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_status)

    def select_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音视频文件", "",
            "音视频文件 (*.mp3 *.mp4 *.wav *.m4a *.mov);;所有文件 (*.*)"
        )
        if file_path:
            self.current_file = file_path
            self.file_label.setText(f"已选择: {os.path.basename(file_path)}")
            self.file_label.setStyleSheet("color: #6366F1; padding: 40px;")
            self.upload_btn.setEnabled(True)

    def upload_and_transcribe(self):
        """上传并转写"""
        if not self.current_file:
            return

        success, data = api_client.upload_media(self.current_file)

        if success and data:
            self.current_task_id = data.get("task_id")
            self.progress_group.show()
            self.status_label.setText("处理中...")
            self.poll_timer.start(2000)
        else:
            QMessageBox.warning(self, "提示", "上传失败，请检查后端服务")

    def poll_status(self):
        """轮询状态"""
        if not self.current_task_id:
            return

        success, data = api_client.get_media_status(self.current_task_id)

        if success and data:
            status = data.get("status", "")
            self.status_label.setText(f"状态: {status}")

            if status == "completed":
                self.poll_timer.stop()
                self.get_result()
            elif status == "failed":
                self.poll_timer.stop()
                QMessageBox.warning(self, "失败", "处理失败")

    def get_result(self):
        """获取结果"""
        success, data = api_client.get_media_result(self.current_task_id)

        if success and data:
            self.transcript_text.setPlainText(data.get("transcript", ""))

            outline = data.get("outline", [])
            self.outline_table.setRowCount(len(outline))
            for row, item in enumerate(outline):
                self.outline_table.setItem(row, 0, QTableWidgetItem(item.get("section", "")))
                self.outline_table.setItem(row, 1, QTableWidgetItem(item.get("title", "")))
                self.outline_table.setItem(row, 2, QTableWidgetItem(item.get("summary", "")))


class MainWindow(QMainWindow):
    """MediaPilot 主窗口"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.check_backend()

    def init_ui(self):
        self.setWindowTitle("🚀 MediaPilot - 媒体领航员")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧导航栏
        nav_widget = QWidget()
        nav_widget.setFixedWidth(220)
        nav_widget.setStyleSheet("background-color: #1E293B;")
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setSpacing(8)
        nav_layout.setContentsMargins(12, 20, 12, 20)

        # Logo
        logo_label = QLabel("🚀 MediaPilot")
        logo_label.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
        logo_label.setStyleSheet("color: #6366F1; padding: 10px;")
        nav_layout.addWidget(logo_label)

        nav_layout.addSpacing(20)

        # 导航按钮
        self.nav_buttons = []

        self.dashboard_btn = self.create_nav_button("📊 仪表盘")
        self.dashboard_btn.setChecked(True)
        nav_layout.addWidget(self.dashboard_btn)

        self.trending_btn = self.create_nav_button("🔥 热点追踪")
        nav_layout.addWidget(self.trending_btn)

        self.competitor_btn = self.create_nav_button("🎯 对标账号")
        nav_layout.addWidget(self.competitor_btn)

        self.video_btn = self.create_nav_button("🎬 视频分析")
        nav_layout.addWidget(self.video_btn)

        self.transcribe_btn = self.create_nav_button("🎤 音视频转写")
        nav_layout.addWidget(self.transcribe_btn)

        self.content_btn = self.create_nav_button("✍️ 内容生成")
        nav_layout.addWidget(self.content_btn)

        self.calendar_btn = self.create_nav_button("📅 内容日历")
        nav_layout.addWidget(self.calendar_btn)

        nav_layout.addStretch()

        # 设置按钮
        self.settings_btn = self.create_nav_button("⚙️ 设置")
        nav_layout.addWidget(self.settings_btn)

        main_layout.addWidget(nav_widget)

        # 右侧内容区
        self.content_stack = QStackedWidget()

        # 仪表盘
        dashboard_widget = self.create_dashboard()
        self.content_stack.addWidget(dashboard_widget)

        # 热点追踪
        self.trending_widget = TrendingWidget()
        self.content_stack.addWidget(self.trending_widget)

        # 对标账号
        self.competitor_widget = CompetitorWidget()
        self.content_stack.addWidget(self.competitor_widget)

        # 视频分析
        video_widget = QLabel("🚧 视频分析模块开发中...")
        video_widget.setAlignment(Qt.AlignCenter)
        self.content_stack.addWidget(video_widget)

        # 音视频转写
        self.transcribe_widget = TranscribeWidget()
        self.content_stack.addWidget(self.transcribe_widget)

        # 内容生成
        self.content_widget = ContentWidget()
        self.content_stack.addWidget(self.content_widget)

        # 内容日历
        calendar_widget = QLabel("🚧 内容日历模块开发中...")
        calendar_widget.setAlignment(Qt.AlignCenter)
        self.content_stack.addWidget(calendar_widget)

        # 设置
        settings_widget = self.create_settings()
        self.content_stack.addWidget(settings_widget)

        main_layout.addWidget(self.content_stack, 1)

        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("就绪")
        self.setStatusBar(self.status_bar)

        # 连接按钮
        self.dashboard_btn.clicked.connect(lambda: self.switch_tab(0))
        self.trending_btn.clicked.connect(lambda: self.switch_tab(1))
        self.competitor_btn.clicked.connect(lambda: self.switch_tab(2))
        self.video_btn.clicked.connect(lambda: self.switch_tab(3))
        self.transcribe_btn.clicked.connect(lambda: self.switch_tab(4))
        self.content_btn.clicked.connect(lambda: self.switch_tab(5))
        self.calendar_btn.clicked.connect(lambda: self.switch_tab(6))
        self.settings_btn.clicked.connect(lambda: self.switch_tab(7))

        # 应用样式
        self.apply_styles()

    def create_nav_button(self, text):
        """创建导航按钮"""
        btn = QPushButton(text)
        btn.setObjectName("NavButton")
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.on_nav_clicked(btn))
        self.nav_buttons.append(btn)
        return btn

    def on_nav_clicked(self, clicked_btn):
        """导航点击"""
        for btn in self.nav_buttons:
            if btn != clicked_btn:
                btn.setChecked(False)

    def switch_tab(self, index):
        """切换标签"""
        self.content_stack.setCurrentIndex(index)

    def create_dashboard(self):
        """创建仪表盘"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # 欢迎
        welcome_label = QLabel("👋 欢迎使用 MediaPilot!")
        welcome_label.setFont(QFont("Microsoft YaHei UI", 20, QFont.Bold))
        welcome_label.setStyleSheet("color: #F8FAFC;")
        layout.addWidget(welcome_label)

        subtitle_label = QLabel("您的全能新媒体AI助手")
        subtitle_label.setStyleSheet("color: #94A3B8; font-size: 14px;")
        layout.addWidget(subtitle_label)

        layout.addSpacing(20)

        # 功能卡片
        grid = QGridLayout()
        grid.setSpacing(16)

        cards = [
            ("🔥 热点追踪", "搜索行业最近热点", "#6366F1"),
            ("🎯 对标分析", "找到赛道对标账号", "#8B5CF6"),
            ("🎬 爆款拆解", "分析爆款视频脚本", "#06B6D4"),
            ("🎤 音视频转写", "一键语音转文字", "#10B981"),
            ("✍️ 内容生成", "AI生成分镜头脚本", "#F59E0B"),
            ("📅 内容日历", "规划发布排期", "#EF4444"),
        ]

        for i, (title, desc, color) in enumerate(cards):
            card = QGroupBox()
            card.setObjectName("CardWidget")
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(8)

            title_label = QLabel(title)
            title_label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
            title_label.setStyleSheet(f"color: {color};")
            card_layout.addWidget(title_label)

            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #94A3B8;")
            card_layout.addWidget(desc_label)

            card_layout.addStretch()

            grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(grid)
        layout.addStretch()

        return widget

    def create_settings(self):
        """创建设置页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("⚙️ 设置")
        title.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold))
        layout.addWidget(title)

        layout.addSpacing(16)

        # AI设置
        ai_group = QGroupBox("🤖 AI配置")
        ai_group.setObjectName("CardWidget")
        ai_layout = QVBoxLayout(ai_group)

        self.api_status_label = QLabel("状态: 未配置")
        ai_layout.addWidget(self.api_status_label)

        config_btn = QPushButton("🔑 配置API")
        config_btn.clicked.connect(self.show_api_config)
        ai_layout.addWidget(config_btn)

        layout.addWidget(ai_group)

        # 后端设置
        backend_group = QGroupBox("🔌 后端服务")
        backend_group.setObjectName("CardWidget")
        backend_layout = QVBoxLayout(backend_group)

        self.backend_status_label = QLabel("状态: 未连接")
        backend_layout.addWidget(self.backend_status_label)

        refresh_btn = QPushButton("🔄 检查连接")
        refresh_btn.setObjectName("SecondaryBtn")
        refresh_btn.clicked.connect(self.check_backend)
        backend_layout.addWidget(refresh_btn)

        layout.addWidget(backend_group)

        layout.addStretch()

        return widget

    def show_api_config(self):
        """显示API配置"""
        dialog = ApiKeyDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_config()
            if config.get("api_key"):
                success, _ = api_client.configure_ai(**config)
                if success:
                    self.api_status_label.setText("状态: 已配置 ✓")
                    self.api_status_label.setStyleSheet("color: #10B981;")
                else:
                    QMessageBox.warning(self, "提示", "配置失败")

    def check_backend(self):
        """检查后端连接"""
        is_ok = api_client.check_health()
        if is_ok:
            self.backend_status_label.setText("状态: 已连接 ✓")
            self.backend_status_label.setStyleSheet("color: #10B981;")
            self.status_bar.showMessage("后端服务已连接")
        else:
            self.backend_status_label.setText("状态: 未连接 ✗")
            self.backend_status_label.setStyleSheet("color: #EF4444;")
            self.status_bar.showMessage("后端服务未启动，请运行 backend/main.py")

    def apply_styles(self):
        """应用样式"""
        style_path = os.path.join(
            os.path.dirname(__file__),
            "resources", "styles", "sci-fi.qss"
        )
        if os.path.exists(style_path):
            file = QFile(style_path)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                self.setStyleSheet(stream.readAll())

