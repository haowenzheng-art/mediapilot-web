
"""
MediaPilot 太空赛博朋克风格桌面端
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTabWidget, QLabel, QLineEdit, QTextEdit,
    QGroupBox, QFormLayout, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QScrollArea, QFileDialog,
    QCalendarWidget, QDateEdit, QComboBox, QSpinBox, QInputDialog,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient, QBrush, QPainter, QRadialGradient

import random
import json
from pathlib import Path

from backend.core.excel_exporter import ExcelExporter
from backend.core.ai_service import ai_manager
from desktop.themes import (
    THEME_WIDGETS, THEME_NAMES, THEME_STYLES,
    SpaceThemeWidget, ChineseThemeWidget, CyberpunkThemeWidget,
    PixarThemeWidget, AnimeThemeWidget, AbstractThemeWidget
)
from desktop.wechat_chat import FloatingChatManager
class NeonButton(QPushButton):
    """霓虹发光按钮 - 美观自适应版"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(56)
        self.setMinimumWidth(160)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()

    def update_style(self):
        self.setStyleSheet("""
            NeonButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1E1B4B, stop:0.5 #312E81, stop:1 #1E1B4B);
                color: #FFFFFF;
                border: 2px solid #818CF8;
                border-radius: 14px;
                padding: 14px 32px;
                font-size: 16px;
                font-weight: bold;
            }
            NeonButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #312E81, stop:0.5 #4F46E5, stop:1 #312E81);
                border: 2px solid #A5B4FC;
            }
            NeonButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1E1B4B, stop:0.5 #3730A3, stop:1 #1E1B4B);
                border: 2px solid #6366F1;
            }
        """)


class GlassCard(QFrame):
    """玻璃拟态卡片 - 美观自适应版"""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            GlassCard {
                background-color: rgba(20, 15, 50, 200);
                border: 1px solid rgba(129, 140, 248, 100);
                border-radius: 18px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                color: #E0E7FF;
                font-size: 18px;
                font-weight: bold;
                padding: 6px 0;
            """)
            layout.addWidget(title_label)

        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout, stretch=1)


class SpaceLineEdit(QLineEdit):
    """太空风格输入框 - 美观自适应版"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("""
            SpaceLineEdit {
                background-color: rgba(15, 10, 40, 220);
                border: 2px solid rgba(129, 140, 248, 120);
                border-radius: 12px;
                padding: 12px 16px;
                color: #F8FAFC;
                font-size: 15px;
            }
            SpaceLineEdit:focus {
                border: 2px solid rgba(165, 180, 252, 220);
                background-color: rgba(20, 15, 50, 240);
            }
        """)


class SpaceTextEdit(QTextEdit):
    """太空风格文本框 - 美观自适应版"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            SpaceTextEdit {
                background-color: rgba(15, 10, 40, 200);
                border: 1px solid rgba(129, 140, 248, 100);
                border-radius: 14px;
                padding: 18px;
                color: #E0E7FF;
                font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
                font-size: 15px;
            }
        """)


class SpaceTable(QTableWidget):
    """太空风格表格"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            SpaceTable {
                background-color: rgba(15, 10, 40, 150);
                border: 1px solid rgba(99, 102, 241, 60);
                border-radius: 12px;
                gridline-color: rgba(99, 102, 241, 40);
            }
            SpaceTable::item {
                padding: 12px;
                border: none;
                color: #E0E7FF;
            }
            SpaceTable::item:selected {
                background-color: rgba(99, 102, 241, 100);
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8B5CF6, stop:1 #6366F1);
                color: #FFFFFF;
                padding: 14px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
        """)


class TestAIThread(QThread):
    """测试AI连接的线程"""
    finished = pyqtSignal(bool, str)  # (success, message)
    error = pyqtSignal(str)

    def __init__(self, api_key, base_url, model_name, model_index):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.model_index = model_index

    def run(self):
        try:
            from backend.core.ai_service import ai_manager

            provider = "ark" if self.model_index == 0 else "openai"

            ai_manager.configure_service(
                provider=provider,
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model_name
            )

            result = ai_manager.generate("你好，请简单回复")

            if result and len(result.strip()) > 0:
                self.finished.emit(True, f"连接成功！\n\nAI回复: {result[:100]}...")
            else:
                self.finished.emit(False, "连接失败，请检查配置！")

        except Exception as e:
            self.error.emit(str(e))


class ChatThread(QThread):
    """AI聊天的线程 - 支持流式输出"""
    text_chunk = pyqtSignal(str)  # 文本片段
    stream_started = pyqtSignal()  # 流式开始
    stream_finished = pyqtSignal()  # 流式结束
    error = pyqtSignal(str)  # 错误

    def __init__(self, user_text, config=None):
        super().__init__()
        self.user_text = user_text
        self.config = config

    def run(self):
        try:
            if not self.config or not self.config.get("api_key"):
                self.error.emit("AI服务未配置，请先在'设置'标签页配置API Key！")
                return

            api_key = self.config["api_key"]
            base_url = self.config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
            model = self.config.get("model", "")
            provider = self.config.get("provider", "openai")

            prompt = f"你是MediaPilot的AI助手，一个专业的新媒体运营助手。请用简洁、专业、友好的语气回答用户的问题。\n\n用户问题：{self.user_text}"

            if provider == "openai":
                # OpenAI兼容API - 支持流式
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key, base_url=base_url)

                    self.stream_started.emit()

                    stream = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=2000,
                        temperature=0.7,
                        stream=True
                    )

                    for chunk in stream:
                        if chunk.choices and len(chunk.choices) > 0:
                            delta = chunk.choices[0].delta
                            if delta.content:
                                self.text_chunk.emit(delta.content)

                    self.stream_finished.emit()

                except Exception as e:
                    self.error.emit(f"发生错误：{str(e)}\n\n请检查API配置是否正确。")
            else:
                # 火山方舟原生API - 不支持流式，用普通方式
                import requests

                if base_url.endswith("/responses"):
                    url = base_url
                else:
                    url = f"{base_url}/responses"

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model,
                    "input": [{
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}]
                    }]
                }

                self.stream_started.emit()

                resp = requests.post(url, headers=headers, json=data, timeout=60)
                if resp.status_code == 200:
                    result = resp.json()
                    if "output" in result:
                        for content in result.get("output", []):
                            if content.get("type") == "message":
                                for msg_content in content.get("content", []):
                                    if msg_content.get("type") == "output_text":
                                        response_text = msg_content.get("text", "")
                                        if response_text:
                                            self.text_chunk.emit(response_text)
                                            break

                self.stream_finished.emit()

        except Exception as e:
            self.error.emit(f"发生错误：{str(e)}\n\n请检查API配置是否正确。")


class ScriptThread(QThread):
    """脚本生成的线程"""
    finished = pyqtSignal(str)  # response

    def __init__(self, topic, config=None):
        super().__init__()
        self.topic = topic
        self.config = config

    def run(self):
        try:
            # 直接调用API，不依赖全局ai_manager
            if not self.config or not self.config.get("api_key"):
                self.finished.emit("AI服务未配置，请先在'设置'标签页配置API Key！")
                return

            import requests
            import json

            api_key = self.config["api_key"]
            base_url = self.config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
            model = self.config.get("model", "")
            provider = self.config.get("provider", "ark")

            prompt = f"""你是一个资深的新媒体内容策划专家，擅长创作有网感、能引爆流量的短视频内容。

请为"{self.topic}"这个主题，创作一套完整的短视频落地执行方案。

要求：
1. 风格要接地气、有网感，不要太官方太死板
2. 画面描述要具体、有画面感，能直接指导拍摄
3. 台词要口语化、有记忆点，符合短视频平台的语言习惯
4. 要有创意亮点，能吸引用户看完并互动

请输出以下内容：

【分镜头脚本】（约60秒，5-8个场景）
每个场景包含：
- 时长（如0:00-0:05）
- 画面：具体的画面描述，包括景别、动作、表情等
- 台词：人物说的话，要口语化
- 备注：拍摄注意事项或剪辑提示

【文案包装】
- 主标题：1个，要有爆款潜质，用疑问句或数字法
- 备选标题：1-2个，不同风格
- 开头钩子：3个版本，分别用痛点法、好奇法、反差法
- 结尾引导：引导关注、点赞、评论的话术
- 话题标签：5-8个，包含核心词、领域词、热词

直接输出，用清晰的标题分隔，不要用任何JSON格式。"""

            response = ""

            if provider == "ark":
                # 火山方舟原生API
                if base_url.endswith("/responses"):
                    url = base_url
                else:
                    url = f"{base_url}/responses"

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model,
                    "input": [{
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}]
                    }]
                }

                resp = requests.post(url, headers=headers, json=data, timeout=60)
                if resp.status_code == 200:
                    result = resp.json()
                    if "output" in result:
                        for content in result.get("output", []):
                            if content.get("type") == "message":
                                for msg_content in content.get("content", []):
                                    if msg_content.get("type") == "output_text":
                                        response = msg_content.get("text", "")
                                        if response:
                                            break
            else:
                # OpenAI兼容API
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    resp = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=3000,
                        temperature=0.7
                    )
                    response = resp.choices[0].message.content
                except:
                    pass

            if not response:
                self.finished.emit("抱歉，AI服务暂时不可用，请稍后再试。")
                return

            # 直接显示AI返回的内容，不解析JSON
            formatted_text = f"选题：{self.topic}\n"
            formatted_text += "="*50 + "\n\n"
            formatted_text += response

            self.finished.emit(formatted_text)

        except Exception as e:
            self.finished.emit(f"发生错误：{str(e)}\n\n请检查API配置是否正确。")


class TemplateThread(QThread):
    """AI生成模板的线程"""
    finished = pyqtSignal(str)  # response

    def __init__(self, template_type, topic, config=None):
        super().__init__()
        self.template_type = template_type
        self.topic = topic
        self.config = config

    def run(self):
        try:
            if not self.config or not self.config.get("api_key"):
                self.finished.emit("AI服务未配置，请先在'设置'标签页配置API Key！")
                return

            import requests
            import json

            api_key = self.config["api_key"]
            base_url = self.config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
            model = self.config.get("model", "")
            provider = self.config.get("provider", "ark")

            prompt = f"""你是一个专业的短视频模板创作专家。请为"{self.topic}"这个主题，创作一个{self.template_type}类型的短视频分镜头脚本模板。

要求：
1. 风格要接地气、有网感
2. 画面描述要具体，有画面感
3. 台词要口语化，符合短视频平台语言习惯
4. 时长约60秒，5-8个场景

请直接输出分镜头脚本，格式如下：

【镜头1】0:00-0:05 - 场景名称
画面：具体画面描述
台词：人物说的话

【镜头2】0:05-0:15 - 场景名称
画面：具体画面描述
台词：人物说的话

...以此类推"""

            response = ""

            if provider == "ark":
                # 火山方舟原生API
                if base_url.endswith("/responses"):
                    url = base_url
                else:
                    url = f"{base_url}/responses"

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model,
                    "input": [{
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}]
                    }]
                }

                resp = requests.post(url, headers=headers, json=data, timeout=60)
                if resp.status_code == 200:
                    result = resp.json()
                    if "output" in result:
                        for content in result.get("output", []):
                            if content.get("type") == "message":
                                for msg_content in content.get("content", []):
                                    if msg_content.get("type") == "output_text":
                                        response = msg_content.get("text", "")
                                        if response:
                                            break
            else:
                # OpenAI兼容API
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    resp = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=3000,
                        temperature=0.7
                    )
                    response = resp.choices[0].message.content
                except:
                    pass

            if not response:
                self.finished.emit("抱歉，AI服务暂时不可用，请稍后再试。")
                return

            self.finished.emit(response)

        except Exception as e:
            self.finished.emit(f"发生错误：{str(e)}\n\n请检查API配置是否正确。")


class MediaPilotSpaceWindow(QMainWindow):
    """MediaPilot 太空风格主窗口"""

    def __init__(self):
        super().__init__()
        # 聊天历史记录（保存消息对象，用于流式更新）
        self.chat_messages = []
        self.current_ai_response = ""
        # 流式输出缓冲
        self.pending_chunks = ""
        self.stream_update_timer = QTimer()
        self.stream_update_timer.timeout.connect(self._flush_pending_chunks)
        # 当前主题
        self.current_theme = "space"
        # 浮动聊天管理器
        self.floating_chat = None
        self.config = self.load_config()
        self.init_ui()
        self.init_ai_service()
        # 初始化浮动聊天
        self.init_floating_chat()

    def load_config(self):
        """加载配置"""
        config_path = Path.home() / ".mediapilot_config.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {
            "provider": "openai",
            "api_key": "1a73929c-d549-43e8-b03f-0d6e3e979771",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "ep-m-20260311150444-fn2zc"
        }

    def save_config(self):
        """保存配置"""
        config_path = Path.home() / ".mediapilot_config.json"
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def init_ai_service(self):
        """初始化AI服务"""
        if self.config.get("api_key"):
            try:
                ai_manager.configure_service(
                    provider=self.config.get("provider", "openai"),
                    api_key=self.config["api_key"],
                    base_url=self.config.get("base_url"),
                    model=self.config.get("model")
                )
            except Exception as e:
                print(f"初始化AI服务失败: {e}")

    def init_floating_chat(self):
        """初始化浮动聊天"""
        from desktop.wechat_chat import FloatingChatManager
        self.floating_chat = FloatingChatManager(self.config, self)

    def changeEvent(self, event):
        """处理窗口状态变化"""
        if event.type() == event.WindowStateChange:
            if self.isMinimized() and self.floating_chat:
                # 主窗口最小化时，也最小化AI助手
                if self.floating_chat.chat_window and self.floating_chat.chat_window.isVisible():
                    self.floating_chat.minimize_chat()
        super().changeEvent(event)

    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("MediaPilot  SPACE EDITION")
        self.setMinimumSize(1400, 900)
        self.resize(1650, 1050)

        # 设置全局字体 - 更大更清晰，全屏时也舒服
        font = QFont()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(14)
        self.setFont(font)

        # 设置初始主题
        self.apply_theme_colors()

        # 主部件 - 先不使用特殊背景，让调色板生效
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 主布局
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(24)

        # 标题区域
        title_layout = QHBoxLayout()
        title_layout.setSpacing(20)

        title_label = QLabel("  MediaPilot")
        title_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 42px;
            font-weight: bold;
            letter-spacing: 3px;
        """)
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # 主题切换
        theme_label = QLabel("主题：")
        theme_label.setStyleSheet("color: #E0E7FF; font-size: 14px;")
        title_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "太空赛博", "中国风", "赛博朋克",
            "皮克斯漫画", "日漫风", "伦敦艺术抽象"
        ])
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(30, 20, 60, 200);
                border: 2px solid rgba(129, 140, 248, 120);
                border-radius: 10px;
                padding: 8px 16px;
                color: #F8FAFC;
                font-size: 14px;
                min-width: 140px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #818CF8;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(20, 15, 50, 250);
                border: 2px solid rgba(129, 140, 248, 150);
                border-radius: 8px;
                padding: 4px;
                color: #E0E7FF;
                font-size: 14px;
            }
            QComboBox QAbstractItemView::item {
                padding: 10px 14px;
                border-radius: 6px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(99, 102, 241, 150);
            }
        """)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        title_layout.addWidget(self.theme_combo)

        # 微信AI助手按钮
        wechat_btn = QPushButton("💬 AI助手")
        wechat_btn.setFixedSize(120, 40)
        wechat_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #07C160, stop:1 #06AD56);
                color: #FFFFFF;
                border: none;
                border-radius: 20px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06AD56, stop:1 #05984A);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #05984A, stop:1 #04823E);
            }
        """)
        wechat_btn.clicked.connect(self.open_wechat_chat)
        title_layout.addWidget(wechat_btn)
        title_layout.addSpacing(15)

        badge_label = QLabel("SPACE EDITION")
        badge_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #8B5CF6, stop:1 #06B6D4);
            color: #FFFFFF;
            padding: 10px 24px;
            border-radius: 24px;
            font-size: 13px;
            font-weight: bold;
        """)
        title_layout.addWidget(badge_label)

        main_layout.addLayout(title_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(99, 102, 241, 80);")
        line.setMaximumHeight(2)
        main_layout.addWidget(line)

        # Tab 窗口 - 优化尺寸策略
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: rgba(30, 20, 60, 150);
                color: #94A3B8;
                padding: 18px 36px;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                margin-right: 6px;
                font-size: 15px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B5CF6, stop:1 #6366F1);
                color: #FFFFFF;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: rgba(50, 40, 80, 180);
                color: #E0E7FF;
            }
        """)
        main_layout.addWidget(self.tabs, stretch=1)

        # 创建标签页
        self.create_trending_tab()
        self.create_competitors_tab()
        self.create_script_tab()
        self.create_transcription_tab()
        self.create_calendar_tab()
        self.create_analytics_tab()
        self.create_templates_tab()
        self.create_settings_tab()

        # 初始化模型选择
        self.init_model_selection()

    def on_theme_changed(self, index):
        """主题切换 - 真正能看到效果的版本！"""
        theme_names = ["space", "chinese", "cyberpunk", "pixar", "anime", "abstract"]
        self.current_theme = theme_names[index]

        # 应用主题颜色！
        self.apply_theme_colors()

        # 提示用户
        QMessageBox.information(self, "成功", f"🎉 主题已切换为：{self.theme_combo.currentText()}\n\n背景和按钮颜色已更新！")

    def apply_theme_colors(self):
        """应用主题颜色 - 这个真的能看到效果！"""
        theme = THEME_STYLES[self.current_theme]

        # 更新主窗口调色板
        palette = QPalette()
        bg_color = QColor(theme["background"])
        text_color = QColor(theme["text"])
        palette.setColor(QPalette.Window, bg_color)
        palette.setColor(QPalette.WindowText, text_color)
        palette.setColor(QPalette.Base, QColor(theme["background_light"]))
        palette.setColor(QPalette.Text, text_color)
        QApplication.setPalette(palette)

        # 更新标签页颜色（如果tabs已创建）
        if hasattr(self, 'tabs') and self.tabs is not None:
            self.update_tab_colors(theme)

        # 强制重新绘制
        self.update()

    def update_tab_colors(self, theme):
        """更新标签页颜色"""
        # 更新标签页样式
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            QTabBar::tab {{
                background-color: {theme['background_light']};
                color: {theme['text_secondary']};
                padding: 18px 36px;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                margin-right: 6px;
                font-size: 15px;
                min-width: 100px;
            }}
            QTabBar::tab:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme['primary']}, stop:1 {theme['secondary']});
                color: #FFFFFF;
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {theme['background']};
                color: {theme['text']};
            }}
        """)

    def open_wechat_chat(self):
        """打开微信风格AI助手"""
        if not self.floating_chat:
            self.floating_chat = FloatingChatManager(self)
        self.floating_chat.show_chat()

    def apply_space_theme(self):
        """应用太空主题"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(10, 5, 25))
        palette.setColor(QPalette.WindowText, QColor(248, 250, 252))
        palette.setColor(QPalette.Base, QColor(20, 15, 50))
        palette.setColor(QPalette.Text, QColor(248, 250, 252))
        palette.setColor(QPalette.Button, QColor(99, 102, 241))
        palette.setColor(QPalette.ButtonText, QColor(248, 250, 252))
        QApplication.setPalette(palette)

    def create_trending_tab(self):
        """创建热点搜索标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)

        # 搜索卡片
        group = GlassCard("  热点搜索")
        form_layout = QFormLayout()
        form_layout.setSpacing(18)

        self.trending_keyword = SpaceLineEdit()
        self.trending_keyword.setPlaceholderText("输入关键词，例如：美妆")
        self.trending_keyword.setText("美妆")
        form_layout.addRow("关键词：", self.trending_keyword)

        search_btn = NeonButton("  搜索")
        search_btn.clicked.connect(self.search_trending)
        form_layout.addRow(search_btn)

        group.content_layout.addLayout(form_layout)
        layout.addWidget(group)

        # 结果卡片
        result_group = GlassCard("  搜索结果")
        self.trending_result = SpaceTextEdit()
        result_group.content_layout.addWidget(self.trending_result)
        layout.addWidget(result_group)

        self.tabs.addTab(tab, "  热点")

    def create_competitors_tab(self):
        """创建对标账号标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)

        # 搜索卡片
        group = GlassCard("  对标账号")
        form_layout = QFormLayout()
        form_layout.setSpacing(18)

        self.competitor_niche = SpaceLineEdit()
        self.competitor_niche.setPlaceholderText("输入赛道，例如：护肤")
        self.competitor_niche.setText("护肤")
        form_layout.addRow("赛道：", self.competitor_niche)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        search_btn = NeonButton("  搜索")
        search_btn.clicked.connect(self.search_competitors)
        btn_layout.addWidget(search_btn)

        export_btn = NeonButton("  导出")
        export_btn.clicked.connect(self.export_competitors)
        btn_layout.addWidget(export_btn)

        form_layout.addRow(btn_layout)
        group.content_layout.addLayout(form_layout)
        layout.addWidget(group)

        # 结果表格
        result_group = GlassCard("  账号列表")
        self.competitor_table = SpaceTable()
        self.competitor_table.setColumnCount(5)
        self.competitor_table.setHorizontalHeaderLabels(["账号ID", "昵称", "平台", "粉丝数", "平均点赞"])
        self.competitor_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        result_group.content_layout.addWidget(self.competitor_table)
        layout.addWidget(result_group)

        self.tabs.addTab(tab, "  对标")

    def create_script_tab(self):
        """创建脚本生成标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)

        # 输入卡片
        group = GlassCard("  脚本生成")
        form_layout = QFormLayout()
        form_layout.setSpacing(18)

        self.script_topic = SpaceLineEdit()
        self.script_topic.setPlaceholderText("输入选题，例如：如何做短视频")
        self.script_topic.setText("如何做短视频")
        form_layout.addRow("选题：", self.script_topic)

        generate_btn = NeonButton("  生成")
        generate_btn.clicked.connect(self.generate_script)
        form_layout.addRow(generate_btn)

        group.content_layout.addLayout(form_layout)
        layout.addWidget(group)

        # 结果卡片
        result_group = GlassCard("  生成结果")
        self.script_result = SpaceTextEdit()
        result_group.content_layout.addWidget(self.script_result)
        layout.addWidget(result_group)

        self.tabs.addTab(tab, "  脚本")

    def create_transcription_tab(self):
        """创建音视频转录标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)

        # 输入卡片
        group = GlassCard("  音视频转录")
        form_layout = QFormLayout()
        form_layout.setSpacing(18)

        # 文件路径输入
        self.transcription_file = SpaceLineEdit()
        self.transcription_file.setPlaceholderText("选择音视频文件 (mp3/mp4)")
        form_layout.addRow("文件：", self.transcription_file)

        # 选择文件按钮
        select_btn = NeonButton("  选择文件")
        select_btn.clicked.connect(self.select_transcription_file)

        # 转录按钮
        transcribe_btn = NeonButton("  开始转录")
        transcribe_btn.clicked.connect(self.start_transcription)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addWidget(select_btn)
        btn_layout.addWidget(transcribe_btn)
        form_layout.addRow(btn_layout)

        group.content_layout.addLayout(form_layout)
        layout.addWidget(group)

        # 结果卡片
        result_group = GlassCard("  转录结果")
        self.transcription_result = SpaceTextEdit()
        result_group.content_layout.addWidget(self.transcription_result)
        layout.addWidget(result_group)

        self.tabs.addTab(tab, "  转录")

    def select_transcription_file(self):
        """选择音视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择音视频文件",
            "",
            "音视频文件 (*.mp3 *.mp4 *.wav *.m4a *.avi *.mov)"
        )
        if file_path:
            self.transcription_file.setText(file_path)

    def start_transcription(self):
        """开始转录"""
        file_path = self.transcription_file.text()
        if not file_path:
            QMessageBox.warning(self, "提示", "请先选择音视频文件！")
            return
        self.show_mock_transcription(file_path)

    def show_mock_transcription(self, file_path):
        """显示模拟转录结果"""
        import os
        filename = os.path.basename(file_path)

        text = f"文件：{filename}\n"
        text += "="*50 + "\n\n"
        text += "【逐字稿】\n\n"

        mock_lines = [
            {"time": "0:00", "text": "大家好，欢迎来到今天的节目。"},
            {"time": "0:05", "text": "今天我们来聊一聊非常重要的话题。"},
            {"time": "0:12", "text": "首先，我们来看第一个要点。"},
            {"time": "0:20", "text": "这个要点的核心在于理解基本概念。"},
            {"time": "0:28", "text": "接下来，我们看第二个要点。"},
            {"time": "0:35", "text": "这里需要注意几个关键点。"},
            {"time": "0:42", "text": "最后，我们来总结一下今天的内容。"},
            {"time": "0:50", "text": "希望对大家有所帮助，我们下期再见！"}
        ]

        for line in mock_lines:
            text += f"[{line['time']}]  {line['text']}\n"

        text += "\n" + "="*50 + "\n\n"
        text += "【内容大纲】\n\n"
        text += "1. 开场白和欢迎\n"
        text += "2. 主题介绍\n"
        text += "3. 第一个要点详解\n"
        text += "4. 第二个要点分析\n"
        text += "5. 总结和结束语\n"

        self.transcription_result.setText(text)

    def create_calendar_tab(self):
        """创建内容日历标签页"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setSpacing(25)

        # 左侧：日历
        left_group = GlassCard("  日历")
        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: rgba(15, 10, 40, 200);
                color: #E0E7FF;
                border: none;
            }
            QCalendarWidget QTableView {
                background-color: rgba(20, 15, 50, 180);
                alternate-background-color: rgba(30, 20, 60, 180);
                selection-background-color: rgba(99, 102, 241, 150);
                color: #E0E7FF;
                gridline-color: rgba(99, 102, 241, 40);
            }
            QCalendarWidget QToolButton {
                color: #E0E7FF;
                background-color: rgba(99, 102, 241, 100);
                border-radius: 6px;
                padding: 6px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: rgba(139, 92, 246, 150);
            }
            QCalendarWidget QMenu {
                background-color: rgba(20, 15, 50, 250);
                color: #E0E7FF;
            }
            QCalendarWidget QSpinBox {
                background-color: rgba(20, 15, 50, 200);
                color: #E0E7FF;
                border: 1px solid rgba(99, 102, 241, 100);
                border-radius: 6px;
            }
        """)
        self.calendar.clicked.connect(self.on_calendar_date_clicked)
        left_group.content_layout.addWidget(self.calendar)
        main_layout.addWidget(left_group, stretch=1)

        # 右侧：日程列表和添加日程
        right_layout = QVBoxLayout()
        right_layout.setSpacing(25)

        # 添加日程卡片
        add_group = GlassCard("  添加日程")
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.calendar_date = QDateEdit()
        self.calendar_date.setDate(QDate.currentDate())
        self.calendar_date.setCalendarPopup(True)
        self.calendar_date.setStyleSheet("""
            QDateEdit {
                background-color: rgba(15, 10, 40, 200);
                border: 2px solid rgba(99, 102, 241, 100);
                border-radius: 10px;
                padding: 12px 16px;
                color: #F8FAFC;
                font-size: 14px;
            }
        """)
        form_layout.addRow("日期：", self.calendar_date)

        self.calendar_title = SpaceLineEdit()
        self.calendar_title.setPlaceholderText("输入内容标题")
        form_layout.addRow("标题：", self.calendar_title)

        self.calendar_platform = QComboBox()
        self.calendar_platform.addItems(["抖音", "小红书", "微博", "B站", "全平台"])
        self.calendar_platform.setStyleSheet("""
            QComboBox {
                background-color: rgba(15, 10, 40, 200);
                border: 2px solid rgba(99, 102, 241, 100);
                border-radius: 10px;
                padding: 12px 16px;
                color: #F8FAFC;
                font-size: 14px;
                min-height: 46px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #818CF8;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(20, 15, 50, 250);
                color: #E0E7FF;
                selection-background-color: rgba(99, 102, 241, 150);
                border: 1px solid rgba(99, 102, 241, 100);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        form_layout.addRow("平台：", self.calendar_platform)

        self.calendar_content = SpaceTextEdit()
        self.calendar_content.setReadOnly(False)
        self.calendar_content.setMaximumHeight(100)
        self.calendar_content.setPlaceholderText("输入内容描述...")
        form_layout.addRow("描述：", self.calendar_content)

        add_btn = NeonButton("  添加日程")
        add_btn.clicked.connect(self.add_calendar_event)
        form_layout.addRow(add_btn)

        add_group.content_layout.addLayout(form_layout)
        right_layout.addWidget(add_group)

        # 日程列表卡片
        list_group = GlassCard("  日程列表")
        self.calendar_list = SpaceTable()
        self.calendar_list.setColumnCount(4)
        self.calendar_list.setHorizontalHeaderLabels(["日期", "标题", "平台", "操作"])
        self.calendar_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        list_group.content_layout.addWidget(self.calendar_list)
        right_layout.addWidget(list_group, stretch=1)

        main_layout.addLayout(right_layout, stretch=1)

        # 初始化一些示例数据
        self.calendar_events = []
        self.add_mock_calendar_events()

        self.tabs.addTab(tab, "  日历")

    def add_mock_calendar_events(self):
        """添加示例日程"""
        today = QDate.currentDate()
        mock_events = [
            {"date": today.addDays(1), "title": "美妆新品测评", "platform": "抖音", "content": "测评本月新品粉底液"},
            {"date": today.addDays(2), "title": "护肤干货分享", "platform": "小红书", "content": "冬季护肤小技巧"},
            {"date": today.addDays(3), "title": "穿搭教程", "platform": "全平台", "content": "春季穿搭指南"},
        ]
        for event in mock_events:
            self.calendar_events.append(event)
        self.refresh_calendar_list()

    def refresh_calendar_list(self):
        """刷新日程列表"""
        self.calendar_list.setRowCount(len(self.calendar_events))
        for row, event in enumerate(self.calendar_events):
            self.calendar_list.setItem(row, 0, QTableWidgetItem(event["date"].toString("yyyy-MM-dd")))
            self.calendar_list.setItem(row, 1, QTableWidgetItem(event["title"]))
            self.calendar_list.setItem(row, 2, QTableWidgetItem(event["platform"]))

            # 删除按钮
            delete_btn = QPushButton("删除")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(236, 72, 153, 150);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: rgba(236, 72, 153, 200);
                }
            """)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_calendar_event(r))
            self.calendar_list.setCellWidget(row, 3, delete_btn)

    def on_calendar_date_clicked(self, date):
        """日历日期点击"""
        self.calendar_date.setDate(date)

    def add_calendar_event(self):
        """添加日程"""
        title = self.calendar_title.text()
        if not title:
            QMessageBox.warning(self, "提示", "请输入标题！")
            return

        event = {
            "date": self.calendar_date.date(),
            "title": title,
            "platform": self.calendar_platform.currentText(),
            "content": self.calendar_content.toPlainText()
        }
        self.calendar_events.append(event)
        self.refresh_calendar_list()

        # 清空输入
        self.calendar_title.clear()
        self.calendar_content.clear()

        QMessageBox.information(self, "成功", "日程添加成功！")

    def delete_calendar_event(self, row):
        """删除日程"""
        reply = QMessageBox.question(
            self, "确认", "确定要删除这个日程吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            del self.calendar_events[row]
            self.refresh_calendar_list()

    def create_analytics_tab(self):
        """创建数据分析看板标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)

        # 统计卡片区域
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)

        # 总粉丝数卡片
        fans_card = self.create_stat_card("总粉丝数", "1,234,567", "+12.5%", "#8B5CF6")
        stats_layout.addWidget(fans_card)

        # 总获赞卡片
        likes_card = self.create_stat_card("总获赞", "8,765,432", "+8.3%", "#06B6D4")
        stats_layout.addWidget(likes_card)

        # 作品数卡片
        videos_card = self.create_stat_card("作品数", "456", "+5.2%", "#EC4899")
        stats_layout.addWidget(videos_card)

        # 平均播放卡片
        views_card = self.create_stat_card("平均播放", "56,789", "+15.7%", "#10B981")
        stats_layout.addWidget(views_card)

        layout.addLayout(stats_layout)

        # 图表区域
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(25)

        # 左侧：平台数据分布
        platform_group = GlassCard("  平台数据分布")
        platform_table = SpaceTable()
        platform_table.setColumnCount(5)
        platform_table.setHorizontalHeaderLabels(["平台", "粉丝数", "获赞数", "作品数", "平均播放"])
        platform_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        platform_data = [
            ["抖音", "856,432", "5,432,100", "234", "78,456"],
            ["小红书", "312,567", "2,123,456", "156", "45,678"],
            ["微博", "65,568", "1,209,876", "66", "32,109"]
        ]
        platform_table.setRowCount(len(platform_data))
        for row, data in enumerate(platform_data):
            for col, value in enumerate(data):
                platform_table.setItem(row, col, QTableWidgetItem(value))

        platform_group.content_layout.addWidget(platform_table)
        charts_layout.addWidget(platform_group, stretch=1)

        # 右侧：趋势概览
        trend_group = GlassCard("  近期趋势")
        trend_text = SpaceTextEdit()
        trend_content = """【数据概览】

• 本月新增粉丝: 156,789 (+12.5%)
• 本月新增获赞: 1,234,567 (+8.3%)
• 本月新增作品: 23 (+5.2%)

【热门内容】

1. 《冬季护肤指南》- 234,567 播放
2. 《美妆开箱》- 187,654 播放
3. 《穿搭分享》- 156,789 播放

【建议】

• 抖音流量增长明显，建议增加更新频率
• 小红书互动率高，可多做抽奖活动
• 视频时长建议控制在 60-90 秒
"""
        trend_text.setText(trend_content)
        trend_group.content_layout.addWidget(trend_text)
        charts_layout.addWidget(trend_group, stretch=1)

        layout.addLayout(charts_layout, stretch=1)

        self.tabs.addTab(tab, "  数据")

    def create_stat_card(self, title, value, change, color):
        """创建统计卡片"""
        card = GlassCard("")
        card.setStyleSheet(f"""
            GlassCard {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}40, stop:1 {color}20);
                border: 1px solid {color}80;
                border-radius: 16px;
            }}
        """)

        card_layout = QVBoxLayout()
        card_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #94A3B8;
            font-size: 14px;
        """)
        card_layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 32px;
            font-weight: bold;
        """)
        card_layout.addWidget(value_label)

        change_label = QLabel(change)
        change_label.setStyleSheet("""
            color: #10B981;
            font-size: 14px;
            font-weight: bold;
        """)
        card_layout.addWidget(change_label)

        card.content_layout.addLayout(card_layout)
        return card

    def create_chat_tab(self):
        """创建AI聊天助手标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)

        # 聊天消息区域
        chat_group = GlassCard("  AI助手")
        chat_group.setStyleSheet("""
            GlassCard {
                background-color: rgba(30, 20, 60, 180);
                border: 1px solid rgba(139, 92, 246, 80);
                border-radius: 16px;
            }
        """)

        # 聊天历史
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #E0E7FF;
                font-size: 14px;
                padding: 10px;
            }
        """)
        chat_group.content_layout.addWidget(self.chat_history)

        layout.addWidget(chat_group, stretch=1)

        # 输入区域
        input_layout = QHBoxLayout()
        input_layout.setSpacing(15)

        self.chat_input = SpaceLineEdit()
        self.chat_input.setPlaceholderText("输入你的问题...")
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input, stretch=1)

        send_btn = NeonButton("  发送")
        send_btn.clicked.connect(self.send_chat_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        # 欢迎消息
        self.add_chat_message("ai", "你好！我是MediaPilot AI助手。我可以帮你：\n\n"
                                "• 分析热点趋势\n"
                                "• 优化内容策略\n"
                                "• 生成创意想法\n"
                                "• 解答运营问题\n\n"
                                "有什么我可以帮你的吗？")

        self.tabs.addTab(tab, "  助手")

    def add_chat_message(self, sender, text, is_placeholder=False):
        """添加聊天消息"""
        # 保存到消息列表
        self.chat_messages.append({
            "sender": sender,
            "text": text,
            "is_placeholder": is_placeholder
        })
        # 刷新显示
        self.refresh_chat_history()

    def refresh_chat_history(self):
        """刷新聊天历史显示"""
        self.chat_history.clear()
        for msg in self.chat_messages:
            if msg["sender"] == "ai":
                color = "#8B5CF6"
                name = "AI助手"
            else:
                color = "#06B6D4"
                name = "你"

            html = f"""
            <div style="margin: 12px 0;">
                <span style="color: {color}; font-weight: bold; font-size: 16px;">{name}</span>
                <div style="background-color: rgba(99, 102, 241, 20);
                            border-radius: 14px; padding: 16px 20px; margin-top: 8px;
                            border: 1px solid rgba(99, 102, 241, 40);">
                    <pre style="white-space: pre-wrap; margin: 0; color: #E0E7FF; font-family: inherit; font-size: 15px; line-height: 1.6;">{msg["text"]}</pre>
                </div>
            </div>
            """
            self.chat_history.append(html)

    def update_last_ai_message(self, text):
        """更新最后一条AI消息"""
        if self.chat_messages and self.chat_messages[-1]["sender"] == "ai":
            self.chat_messages[-1]["text"] = text
            self.refresh_chat_history()

    def send_chat_message(self):
        """发送聊天消息"""
        text = self.chat_input.text().strip()
        if not text:
            return

        self.add_chat_message("user", text)
        self.chat_input.clear()

        # 显示正在输入的占位消息
        self.current_ai_response = ""
        self.add_chat_message("ai", "正在思考...")
        self.chat_input.setEnabled(False)

        # 使用后台线程，传入config
        self.chat_thread = ChatThread(text, self.config)
        self.chat_thread.text_chunk.connect(self.on_chat_chunk)
        self.chat_thread.stream_started.connect(self.on_chat_stream_started)
        self.chat_thread.stream_finished.connect(self.on_chat_stream_finished)
        self.chat_thread.error.connect(self.on_chat_error)
        self.chat_thread.start()

    def on_chat_stream_started(self):
        """流式开始 - 清空占位消息"""
        self.current_ai_response = ""
        self.pending_chunks = ""
        if self.chat_messages and self.chat_messages[-1]["sender"] == "ai":
            self.chat_messages[-1]["text"] = ""
            self.refresh_chat_history()
        # 启动定时器，每50ms刷新一次
        self.stream_update_timer.start(50)

    def on_chat_chunk(self, chunk):
        """收到文本片段 - 先缓冲"""
        self.pending_chunks += chunk

    def _flush_pending_chunks(self):
        """将缓冲的内容刷新到显示"""
        if self.pending_chunks:
            self.current_ai_response += self.pending_chunks
            self.pending_chunks = ""
            self.update_last_ai_message(self.current_ai_response)

    def on_chat_stream_finished(self):
        """流式结束"""
        # 停止定时器
        self.stream_update_timer.stop()
        # 刷新剩余的缓冲内容
        if self.pending_chunks:
            self.current_ai_response += self.pending_chunks
            self.pending_chunks = ""
            self.update_last_ai_message(self.current_ai_response)
        self.chat_input.setEnabled(True)

    def on_chat_error(self, error_msg):
        """聊天错误"""
        self.update_last_ai_message(error_msg)
        self.chat_input.setEnabled(True)

    def _format_chat_message(self, sender, text):
        """格式化聊天消息HTML"""
        if sender == "ai":
            color = "#8B5CF6"
            name = "AI助手"
        else:
            color = "#06B6D4"
            name = "你"

        return f"""
        <div style="margin: 10px 0;">
            <span style="color: {color}; font-weight: bold; font-size: 14px;">{name}</span>
            <div style="background-color: rgba(99, 102, 241, 20);
                        border-radius: 12px; padding: 12px 16px; margin-top: 5px;
                        border: 1px solid rgba(99, 102, 241, 40);">
                <pre style="white-space: pre-wrap; margin: 0; color: #E0E7FF; font-family: inherit;">{text}</pre>
            </div>
        </div>
        """

    def generate_ai_response(self, user_text):
        """生成AI回复（旧的模拟回复，保留备用）"""
        responses = [
            "这是个好问题！根据当前热点趋势，我建议你可以从以下几个角度切入：\n\n"
            "1. 结合当下流行的话题\n"
            "2. 突出产品的独特卖点\n"
            "3. 用真实案例增加说服力",

            "根据数据分析，这类内容在以下时间段发布效果最好：\n\n"
            "• 工作日：12:00-14:00, 18:00-22:00\n"
            "• 周末：10:00-12:00, 15:00-21:00\n\n"
            "建议根据你的目标受众调整发布时间。",

            "这个选题很棒！我建议可以这样结构：\n\n"
            "【开头】3秒钩子 - 用痛点或疑问吸引\n"
            "【中段】3-5个要点 - 每个要点配案例\n"
            "【结尾】引导关注 - 点赞收藏+评论互动\n\n"
            "需要我帮你生成完整脚本吗？"
        ]

        import random
        response = random.choice(responses)
        self.add_chat_message("ai", response)

    def create_templates_tab(self):
        """创建模板库标签页"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(25)

        # 左侧：模板列表
        list_group = GlassCard("  模板列表")

        self.template_list = QTableWidget()
        self.template_list.setColumnCount(3)
        self.template_list.setHorizontalHeaderLabels(["名称", "类型", "操作"])
        self.template_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.template_list.setStyleSheet("""
            QTableWidget {
                background-color: rgba(15, 10, 40, 150);
                border: 1px solid rgba(99, 102, 241, 60);
                border-radius: 12px;
                gridline-color: rgba(99, 102, 241, 40);
            }
            QTableWidget::item {
                padding: 12px;
                border: none;
                color: #E0E7FF;
            }
            QTableWidget::item:selected {
                background-color: rgba(99, 102, 241, 100);
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8B5CF6, stop:1 #6366F1);
                color: #FFFFFF;
                padding: 14px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        self.template_list.itemClicked.connect(self.on_template_selected)
        list_group.content_layout.addWidget(self.template_list)
        layout.addWidget(list_group, stretch=1)

        # 右侧：模板预览和编辑
        right_layout = QVBoxLayout()
        right_layout.setSpacing(25)

        # AI生成模板区域
        ai_group = GlassCard("  AI生成模板")
        ai_layout = QFormLayout()
        ai_layout.setSpacing(15)

        self.template_topic_input = SpaceLineEdit()
        self.template_topic_input.setPlaceholderText("请输入模板主题，如：产品开箱、干货分享等")
        ai_layout.addRow("主题：", self.template_topic_input)

        self.template_type_combo = QComboBox()
        self.template_type_combo.addItems(["测评", "教程", "种草", "剧情", "vlog", "其他"])
        self.template_type_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(15, 10, 40, 220);
                border: 2px solid rgba(129, 140, 248, 120);
                border-radius: 12px;
                padding: 12px 16px;
                color: #F8FAFC;
                font-size: 16px;
                min-height: 50px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 8px solid transparent;
                border-right: 8px solid transparent;
                border-top: 8px solid #818CF8;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(20, 15, 50, 250);
                border: 2px solid rgba(129, 140, 248, 150);
                border-radius: 10px;
                padding: 8px;
                color: #E0E7FF;
                font-size: 16px;
            }
            QComboBox QAbstractItemView::item {
                padding: 12px 16px;
                border-radius: 8px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(99, 102, 241, 150);
            }
        """)
        ai_layout.addRow("类型：", self.template_type_combo)

        ai_group.content_layout.addLayout(ai_layout)

        gen_template_btn = NeonButton("  AI生成模板")
        gen_template_btn.clicked.connect(self.generate_template_ai)
        ai_group.content_layout.addWidget(gen_template_btn)

        right_layout.addWidget(ai_group)

        # 预览卡片
        preview_group = GlassCard("  模板内容")
        self.template_preview = SpaceTextEdit()
        preview_group.content_layout.addWidget(self.template_preview)
        right_layout.addWidget(preview_group, stretch=1)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        use_btn = NeonButton("  使用模板")
        use_btn.clicked.connect(self.use_template)
        btn_layout.addWidget(use_btn)

        save_btn = NeonButton("  保存新模板")
        save_btn.clicked.connect(self.save_new_template)
        btn_layout.addWidget(save_btn)

        right_layout.addLayout(btn_layout)
        layout.addLayout(right_layout, stretch=1)

        # 初始化模板数据
        self.templates = [
            {
                "name": "产品开箱模板",
                "type": "测评",
                "content": """【镜头1】0:00-0:05 - 产品特写+钩子
画面：产品精美特写
台词：这东西居然这么好用！

【镜头2】0:05-0:15 - 开箱展示
画面：开箱过程
台词：今天我们来开箱测评一下...

【镜头3】0:15-0:35 - 使用演示
画面：实际使用场景
台词：我们来试试看效果如何...

【镜头4】0:35-0:50 - 总结推荐
画面：产品+人出镜
台词：总的来说，这款产品...

【镜头5】0:50-1:00 - 引导关注
画面：指向关注按钮
台词：记得点赞关注，下期更精彩！"""
            },
            {
                "name": "干货分享模板",
                "type": "教程",
                "content": """【镜头1】0:00-0:03 - 痛点提问
画面：夸张表情
台词：你是不是还在为XX烦恼？

【镜头2】0:03-0:08 - 自我介绍
画面：本人出镜
台词：大家好，我是XX，今天给大家分享...

【镜头3】0:08-0:40 - 干货讲解（3点）
画面：分屏展示
台词：第一点...第二点...第三点...

【镜头4】0:40-0:55 - 总结升华
画面：温馨画面
台词：以上就是今天的全部内容...

【镜头5】0:55-1:00 - 引导互动
画面：指向评论区
台词：有问题评论区留言，我们下期见！"""
            },
            {
                "name": "好物推荐模板",
                "type": "种草",
                "content": """【镜头1】0:00-0:05 - 惊喜展示
画面：手持产品展示
台词：今天给大家推荐一个宝藏好物！

【镜头2】0:05-0:20 - 外观展示
画面：360度展示
台词：首先看这个颜值，是不是超级好看...

【镜头3】0:20-0:40 - 功能介绍
画面：功能演示
台词：它的功能也特别强大...

【镜头4】0:40-0:50 - 使用感受
画面：使用场景
台词：我自己用了一段时间，感觉...

【镜头5】0:50-1:00 - 购买引导
画面：指向购买链接
台词：喜欢的朋友赶紧入手吧！"""
            }
        ]
        self.refresh_template_list()

        self.tabs.addTab(tab, "  模板")

    def refresh_template_list(self):
        """刷新模板列表"""
        self.template_list.setRowCount(len(self.templates))
        for row, template in enumerate(self.templates):
            self.template_list.setItem(row, 0, QTableWidgetItem(template["name"]))
            self.template_list.setItem(row, 1, QTableWidgetItem(template["type"]))

            use_btn = QPushButton("使用")
            use_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(99, 102, 241, 150);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: rgba(139, 92, 246, 200);
                }
            """)
            use_btn.clicked.connect(lambda checked, r=row: self.use_template_by_index(r))
            self.template_list.setCellWidget(row, 2, use_btn)

    def on_template_selected(self, item):
        """模板选中"""
        row = item.row()
        if 0 <= row < len(self.templates):
            self.template_preview.setText(self.templates[row]["content"])

    def use_template_by_index(self, row):
        """使用指定索引的模板"""
        if 0 <= row < len(self.templates):
            template = self.templates[row]
            self.template_preview.setText(template["content"])
            QMessageBox.information(self, "提示", f"已加载模板：{template['name']}\n\n可以切换到'脚本'标签页使用！")

    def use_template(self):
        """使用当前模板"""
        current_row = self.template_list.currentRow()
        if current_row >= 0:
            self.use_template_by_index(current_row)
        else:
            QMessageBox.warning(self, "提示", "请先选择一个模板！")

    def save_new_template(self):
        """保存新模板"""
        content = self.template_preview.toPlainText()
        if not content:
            QMessageBox.warning(self, "提示", "请输入模板内容！")
            return

        name, ok = QInputDialog.getText(self, "保存模板", "请输入模板名称：")
        if ok and name:
            template_type, ok2 = QInputDialog.getText(self, "保存模板", "请输入模板类型：")
            if ok2:
                self.templates.append({
                    "name": name,
                    "type": template_type or "自定义",
                    "content": content
                })
                self.refresh_template_list()
                QMessageBox.information(self, "成功", "模板保存成功！")

    def generate_template_ai(self):
        """AI生成模板"""
        topic = self.template_topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "提示", "请输入模板主题！")
            return

        template_type = self.template_type_combo.currentText()

        self.template_preview.setText("正在AI生成模板，请稍候...")

        self.template_thread = TemplateThread(template_type, topic, self.config)
        self.template_thread.finished.connect(self.on_template_generated)
        self.template_thread.start()

    def on_template_generated(self, content):
        """模板生成完成"""
        self.template_preview.setText(content)

    def search_trending(self):
        """搜索热点"""
        keyword = self.trending_keyword.text() or "美妆"
        self.show_mock_trending(keyword)

    def show_mock_trending(self, keyword):
        """显示模拟数据"""
        topics = [
            f"{keyword}行业新趋势",
            f"{keyword}爆款内容分析",
            f"{keyword}怎么做",
            f"{keyword}避坑指南",
            f"{keyword}入门教程"
        ]
        platforms = ["抖音", "小红书", "微博"]

        text = f"关键词：{keyword}\n"
        text += f"找到 {len(topics)} 个热点\n\n"
        text += "="*50 + "\n\n"

        for i, title in enumerate(topics, 1):
            heat = random.randint(10000, 999999)
            text += f"{i}. {title}\n"
            text += f"   热度：{heat:,}  |  平台：{random.choice(platforms)}\n\n"

        self.trending_result.setText(text)

    def search_competitors(self):
        """搜索对标账号"""
        niche = self.competitor_niche.text() or "护肤"
        self.show_mock_competitors(niche)

    def show_mock_competitors(self, niche):
        """显示模拟数据"""
        nicknames = [
            f"{niche}小能手",
            f"{niche}达人",
            f"{niche}研习社",
            f"{niche}学姐",
            f"{niche}学长"
        ]
        platforms = ["抖音", "小红书", "微博"]

        # 保存数据用于导出
        self.competitor_data = []

        self.competitor_table.setRowCount(len(nicknames))
        for row, nickname in enumerate(nicknames):
            followers = random.randint(10000, 1000000)
            total_likes = random.randint(100000, 10000000)
            video_count = random.randint(10, 500)
            avg_likes = total_likes // video_count if video_count > 0 else 0

            account = {
                "account_id": f"account_{row:04d}",
                "nickname": nickname,
                "platform": random.choice(platforms),
                "followers": followers,
                "total_likes": total_likes,
                "video_count": video_count,
                "avg_likes": avg_likes,
                "profile_url": f"https://example.com/profile/{row:04d}"
            }
            self.competitor_data.append(account)

            self.competitor_table.setItem(row, 0, QTableWidgetItem(account["account_id"]))
            self.competitor_table.setItem(row, 1, QTableWidgetItem(account["nickname"]))
            self.competitor_table.setItem(row, 2, QTableWidgetItem(account["platform"]))
            self.competitor_table.setItem(row, 3, QTableWidgetItem(f"{account['followers']:,}"))
            self.competitor_table.setItem(row, 4, QTableWidgetItem(f"{account['avg_likes']:.1f}"))

    def export_competitors(self):
        """导出Excel"""
        if not hasattr(self, 'competitor_data') or not self.competitor_data:
            QMessageBox.warning(self, "提示", "请先搜索对标账号！")
            return

        # 选择保存位置
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存Excel文件",
            f"对标账号_{self.competitor_niche.text() or 'export'}.xlsx",
            "Excel文件 (*.xlsx)"
        )
        if not file_path:
            return

        try:
            exporter = ExcelExporter()
            output = exporter.export_competitors(self.competitor_data)

            with open(file_path, 'wb') as f:
                f.write(output.getvalue())

            QMessageBox.information(self, "成功", f"导出成功！\n文件已保存到：{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")

    def generate_script(self):
        """生成脚本"""
        topic = self.script_topic.text() or "如何做短视频"

        # 显示加载状态
        self.script_result.setText("正在生成脚本，请稍候...")

        # 使用后台线程
        self.script_thread = ScriptThread(topic, self.config)
        self.script_thread.finished.connect(self.on_script_finished)
        self.script_thread.start()

    def on_script_finished(self, result):
        """脚本生成完成"""
        self.script_result.setText(result)

    def show_mock_script(self, topic):
        """显示模拟脚本"""
        text = f"选题：{topic}\n"
        text += "="*50 + "\n\n"
        text += "【分镜头脚本】\n\n"

        script = [
            {"scene": 1, "duration": "0:00-0:05", "visual": "开头吸引眼球", "audio": "大家好！今天给大家分享一个超实用的技巧！"},
            {"scene": 2, "duration": "0:05-0:15", "visual": "展示主题", "audio": f"今天我们来聊一聊{topic}"},
            {"scene": 3, "duration": "0:15-0:30", "visual": "详细讲解", "audio": "具体怎么做呢？首先..."},
            {"scene": 4, "duration": "0:30-0:45", "visual": "总结升华", "audio": "以上就是今天的全部内容"},
            {"scene": 5, "duration": "0:45-0:60", "visual": "引导关注", "audio": "记得点赞关注，下期更精彩！"}
        ]

        for shot in script:
            text += f"场景 {shot['scene']}  ({shot['duration']})\n"
            text += f"  画面：{shot['visual']}\n"
            text += f"  台词：{shot['audio']}\n\n"

        text += "【文案建议】\n\n"
        text += f"标题：{topic}爆款标题 - 90%的人都不知道！\n\n"
        text += "钩子：\n"
        text += "  - 你还不知道的秘密！\n"
        text += "  - 建议收藏！\n"
        text += "  - 最后一条绝了\n\n"
        text += "引导语：点赞关注，下期更精彩！\n\n"
        text += f"标签：#{topic}  #新媒体  #干货\n"

        self.script_result.setText(text)

    def create_settings_tab(self):
        """创建设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)

        # AI配置卡片
        ai_group = GlassCard("  AI服务配置")
        form_layout = QFormLayout()
        form_layout.setSpacing(18)

        # 模型选择
        self.settings_model = QComboBox()
        self.settings_model.addItems([
            "Doubao (火山方舟-原生API)",
            "Doubao (火山方舟-OpenAI兼容)",
            "GLM-4.7 (智谱AI)",
            "DeepSeek V3 (深度求索)",
            "自定义"
        ])
        self.settings_model.currentIndexChanged.connect(self.on_model_changed)
        self.settings_model.setStyleSheet("""
            QComboBox {
                background-color: rgba(15, 10, 40, 200);
                border: 2px solid rgba(99, 102, 241, 100);
                border-radius: 10px;
                padding: 12px 16px;
                color: #F8FAFC;
                font-size: 14px;
                min-height: 46px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #818CF8;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(20, 15, 50, 250);
                color: #E0E7FF;
                selection-background-color: rgba(99, 102, 241, 150);
                border: 1px solid rgba(99, 102, 241, 100);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        form_layout.addRow("选择模型：", self.settings_model)

        # API Key
        self.settings_api_key = SpaceLineEdit()
        self.settings_api_key.setPlaceholderText("输入API Key")
        self.settings_api_key.setEchoMode(QLineEdit.Password)
        self.settings_api_key.setText(self.config.get("api_key", ""))
        form_layout.addRow("API Key：", self.settings_api_key)

        # Base URL
        self.settings_base_url = SpaceLineEdit()
        self.settings_base_url.setPlaceholderText("输入API Base URL")
        self.settings_base_url.setText(self.config.get("base_url", ""))
        form_layout.addRow("Base URL：", self.settings_base_url)

        # Model Name
        self.settings_model_name = SpaceLineEdit()
        self.settings_model_name.setPlaceholderText("输入Model名称")
        self.settings_model_name.setText(self.config.get("model", ""))
        form_layout.addRow("Model名称：", self.settings_model_name)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        test_btn = NeonButton("  测试连接")
        test_btn.clicked.connect(self.test_ai_connection)
        btn_layout.addWidget(test_btn)

        save_btn = NeonButton("  保存配置")
        save_btn.clicked.connect(self.save_ai_settings)
        btn_layout.addWidget(save_btn)

        form_layout.addRow(btn_layout)

        # 状态显示
        self.settings_status = QLabel("状态：未连接")
        self.settings_status.setStyleSheet("color: #94A3B8; font-size: 13px;")
        form_layout.addRow(self.settings_status)

        ai_group.content_layout.addLayout(form_layout)
        layout.addWidget(ai_group)

        # 预设配置说明
        help_group = GlassCard("  预设配置")
        help_text = SpaceTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(200)
        help_content = """【预设配置说明】

• Doubao (火山方舟-原生API)
  Base URL: https://ark.cn-beijing.volces.com/api/v3
  Model: 请输入接入点ID (格式: ep-xxxxx)

• Doubao (火山方舟-OpenAI兼容)
  Base URL: https://ark.cn-beijing.volces.com/api/v3
  Model: 请输入接入点ID (格式: ep-xxxxx)

• GLM-4.7 (智谱AI)
  Base URL: https://open.bigmodel.cn/api/paas/v4
  Model: glm-4.7

• DeepSeek V3 (深度求索)
  Base URL: https://api.deepseek.com
  Model: deepseek-chat

【如何获取火山方舟接入点ID】
1. 登录 https://console.volcengine.com/ark
2. 进入"模型推理" → "接入点管理"
3. 创建或查看已有接入点
4. 复制接入点ID (ep-开头的字符串)
"""
        help_text.setText(help_content)
        help_group.content_layout.addWidget(help_text)
        layout.addWidget(help_group)

        layout.addStretch()

        self.tabs.addTab(tab, "  设置")

        # 根据当前config初始化模型选择
        QTimer.singleShot(100, self.init_model_selection)

    def init_model_selection(self):
        """初始化模型选择"""
        provider = self.config.get("provider", "ark")
        model = self.config.get("model", "")
        if provider == "ark":
            self.settings_model.setCurrentIndex(0)
        elif provider == "openai" and "ark.cn-beijing" in self.config.get("base_url", ""):
            self.settings_model.setCurrentIndex(1)
        elif "glm" in model.lower():
            self.settings_model.setCurrentIndex(2)
        elif "deepseek" in model.lower():
            self.settings_model.setCurrentIndex(3)
        else:
            self.settings_model.setCurrentIndex(4)

    def on_model_changed(self, index):
        """模型选择变化"""
        presets = {
            0: {
                "provider": "ark",
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "model": "ep-m-20260311150444-fn2zc"
            },
            1: {
                "provider": "openai",
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "model": "ep-m-20260311150444-fn2zc"
            },
            2: {
                "provider": "openai",
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
                "model": "glm-4.7"
            },
            3: {
                "provider": "openai",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat"
            },
            4: {
                "provider": "openai",
                "base_url": "",
                "model": ""
            }
        }
        if index in presets:
            self.config["provider"] = presets[index]["provider"]
            self.settings_base_url.setText(presets[index]["base_url"])
            self.settings_model_name.setText(presets[index]["model"])

    def save_ai_settings(self):
        """保存AI设置"""
        # 根据模型选择确定provider
        model_index = self.settings_model.currentIndex()
        if model_index == 0:
            self.config["provider"] = "ark"
        else:
            self.config["provider"] = "openai"
        self.config["api_key"] = self.settings_api_key.text()
        self.config["base_url"] = self.settings_base_url.text()
        self.config["model"] = self.settings_model_name.text()

        if self.save_config():
            self.init_ai_service()
            QMessageBox.information(self, "成功", "配置已保存！")
        else:
            QMessageBox.warning(self, "错误", "配置保存失败！")

    def test_ai_connection(self):
        """测试AI连接"""
        api_key = self.settings_api_key.text()
        base_url = self.settings_base_url.text()
        model_name = self.settings_model_name.text()

        if not api_key:
            QMessageBox.warning(self, "提示", "请输入API Key！")
            return

        self.settings_status.setText("状态：正在测试...")
        self.settings_status.setStyleSheet("color: #F59E0B; font-size: 13px;")

        # 禁用按钮防止重复点击
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(False)

        # 使用QThread避免界面卡死
        self.test_thread = TestAIThread(api_key, base_url, model_name, self.settings_model.currentIndex())
        self.test_thread.finished.connect(self.on_test_finished)
        self.test_thread.error.connect(self.on_test_error)
        self.test_thread.start()

    def on_test_finished(self, success, message):
        """测试完成"""
        # 重新启用按钮
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(True)

        if success:
            self.settings_status.setText("状态：连接成功！")
            self.settings_status.setStyleSheet("color: #10B981; font-size: 13px;")
            QMessageBox.information(self, "成功", message)
        else:
            self.settings_status.setText("状态：连接失败")
            self.settings_status.setStyleSheet("color: #EF4444; font-size: 13px;")
            QMessageBox.warning(self, "失败", message)

    def on_test_error(self, error_msg):
        """测试出错"""
        # 重新启用按钮
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(True)

        self.settings_status.setText("状态：连接失败")
        self.settings_status.setStyleSheet("color: #EF4444; font-size: 13px;")
        QMessageBox.critical(self, "错误", f"连接失败：{error_msg}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = MediaPilotSpaceWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

