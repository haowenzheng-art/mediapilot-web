
"""
MediaPilot 微信风格AI助手浮动窗口 - 修复版
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QLineEdit, QFrame, QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QThread
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QRadialGradient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SimpleChatThread(QThread):
    """简单的AI聊天线程"""
    finished = pyqtSignal(str)  # 完整回复
    error = pyqtSignal(str)  # 错误

    def __init__(self, user_text, config=None):
        super().__init__()
        self.user_text = user_text
        self.config = config

    def run(self):
        try:
            if not self.config or not self.config.get("api_key"):
                self.error.emit("AI服务未配置，请先在主程序'设置'标签页配置API Key！")
                return

            api_key = self.config["api_key"]
            base_url = self.config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
            model = self.config.get("model", "")
            provider = self.config.get("provider", "openai")

            prompt = f"你是MediaPilot的AI助手，一个专业的新媒体运营助手。请用简洁、专业、友好的语气回答用户的问题。\n\n用户问题：{self.user_text}"

            if provider == "openai":
                # OpenAI兼容API
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key, base_url=base_url)

                    resp = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=2000,
                        temperature=0.7
                    )
                    response = resp.choices[0].message.content
                    self.finished.emit(response)

                except Exception as e:
                    self.error.emit(f"发生错误：{str(e)}\n\n请检查API配置是否正确。")
            else:
                # 火山方舟原生API
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

                resp = requests.post(url, headers=headers, json=data, timeout=60)
                if resp.status_code == 200:
                    result = resp.json()
                    response = ""
                    if "output" in result:
                        for content in result.get("output", []):
                            if content.get("type") == "message":
                                for msg_content in content.get("content", []):
                                    if msg_content.get("type") == "output_text":
                                        response = msg_content.get("text", "")
                                        if response:
                                            break
                    if response:
                        self.finished.emit(response)
                    else:
                        self.error.emit("抱歉，AI服务暂时不可用，请稍后再试。")
                else:
                    self.error.emit(f"请求失败：{resp.status_code}")

        except Exception as e:
            self.error.emit(f"发生错误：{str(e)}\n\n请检查API配置是否正确。")


class RobotIconWidget(QWidget):
    """机器人头像组件"""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景圆
        radial = QRadialGradient(32, 32, 32)
        radial.setColorAt(0, QColor(139, 92, 246))
        radial.setColorAt(1, QColor(99, 102, 241))
        painter.setBrush(QBrush(radial))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 64, 64)

        # 机器人脸部 - 简单的线条
        painter.setPen(QColor(255, 255, 255, 220))
        painter.setBrush(Qt.NoPen)

        # 眼睛
        painter.drawEllipse(18, 24, 8, 8)
        painter.drawEllipse(38, 24, 8, 8)

        # 嘴巴
        painter.drawArc(22, 36, 20, 12, 0, -180 * 16)

        # 天线
        painter.setPen(QColor(255, 255, 255, 180))
        painter.drawLine(32, 8, 32, 16)
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.drawEllipse(28, 4, 8, 8)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class WeChatChatWindow(QWidget):
    """微信风格聊天窗口"""

    minimize_requested = pyqtSignal()

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(420, 580)
        self.resize(440, 620)

        # 拖动相关
        self.dragging = False
        self.drag_position = QPoint()

        # 聊天相关
        self.chat_thread = None

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 主容器（带圆角背景）
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-radius: 16px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 标题栏
        title_bar = QFrame()
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #EDEDED;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border-bottom: 1px solid #DCDCDC;
            }
        """)
        title_bar.setFixedHeight(52)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 0, 12, 0)
        title_layout.setSpacing(10)

        # 标题
        title_label = QLabel("AI助手")
        title_label.setStyleSheet("""
            color: #333333;
            font-size: 16px;
            font-weight: bold;
        """)
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # 最小化按钮
        min_btn = QPushButton("—")
        min_btn.setFixedSize(32, 32)
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 50);
            }
        """)
        min_btn.clicked.connect(self.minimize_requested.emit)
        title_layout.addWidget(min_btn)

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                font-size: 24px;
                font-weight: bold;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: #FF5F57;
                color: #FFFFFF;
            }
        """)
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)

        container_layout.addWidget(title_bar)

        # 聊天记录区域
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #F5F5F5;
                border: none;
                padding: 16px;
                color: #333333;
                font-size: 15px;
            }
        """)
        container_layout.addWidget(self.chat_history, stretch=1)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #DCDCDC;")
        line.setMaximumHeight(1)
        container_layout.addWidget(line)

        # 输入区域
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }
        """)
        input_container.setFixedHeight(72)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(12, 12, 12, 12)
        input_layout.setSpacing(10)

        # 输入框
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("输入消息...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 20px;
                padding: 10px 16px;
                color: #333333;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 1px solid #8B5CF6;
            }
        """)
        input_layout.addWidget(self.chat_input, stretch=1)

        # 发送按钮
        send_btn = QPushButton("发送")
        send_btn.setFixedSize(72, 42)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: #FFFFFF;
                border: none;
                border-radius: 21px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
            QPushButton:pressed {
                background-color: #6D28D9;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        container_layout.addWidget(input_container)

        layout.addWidget(container)

        # 连接信号
        self.chat_input.returnPressed.connect(self.send_message)

        # 添加示例消息
        self.add_message("ai", "你好！我是MediaPilot AI助手，有什么可以帮助你的？")

    def add_message(self, sender, text):
        """添加聊天消息"""
        if sender == "ai":
            color = "#8B5CF6"
            name = "AI助手"
            align = "left"
            bg_color = "#FFFFFF"
        else:
            color = "#07C160"
            name = "你"
            align = "right"
            bg_color = "#95EC69"

        html = f"""
        <div style="margin: 8px 0; text-align: {align};">
            <div style="display: inline-block; text-align: left; max-width: 75%;">
                <div style="font-size: 12px; color: #999999; margin-bottom: 4px;">{name}</div>
                <div style="background-color: {bg_color};
                            border-radius: 8px; padding: 10px 14px;
                            color: #333333; font-size: 15px;
                            line-height: 1.6;">
                    {text}
                </div>
            </div>
        </div>
        """
        self.chat_history.append(html)

        # 滚动到底部
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_history.setTextCursor(cursor)

    def send_message(self):
        """发送消息"""
        text = self.chat_input.text().strip()
        if not text:
            return

        self.add_message("user", text)
        self.chat_input.clear()
        self.chat_input.setEnabled(False)

        # 显示正在输入
        self.add_message("ai", "正在思考...")

        # 使用后台线程
        self.chat_thread = SimpleChatThread(text, self.config)
        self.chat_thread.finished.connect(self.on_chat_finished)
        self.chat_thread.error.connect(self.on_chat_error)
        self.chat_thread.start()

    def on_chat_finished(self, response):
        """聊天完成"""
        # 移除最后一条"正在思考"，添加真实回复
        # 简化处理：直接添加新回复
        self.add_message("ai", response)
        self.chat_input.setEnabled(True)

    def on_chat_error(self, error_msg):
        """聊天错误"""
        self.add_message("ai", error_msg)
        self.chat_input.setEnabled(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False


class FloatingChatManager:
    """浮动聊天管理器"""

    def __init__(self, config=None, parent=None):
        self.parent = parent
        self.config = config
        self.chat_window = None
        self.icon_widget = None
        self.is_minimized = False

    def show_chat(self):
        """显示聊天窗口"""
        if not self.chat_window:
            self.chat_window = WeChatChatWindow(self.config)
            self.chat_window.minimize_requested.connect(self.minimize_chat)

        if self.icon_widget:
            self.icon_widget.hide()

        self.chat_window.show()
        self.is_minimized = False

    def minimize_chat(self):
        """最小化聊天窗口到右下角"""
        if self.chat_window:
            self.chat_window.hide()

        if not self.icon_widget:
            self.icon_widget = RobotIconWidget()
            self.icon_widget.clicked.connect(self.show_chat)
            self.icon_widget.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            self.icon_widget.setAttribute(Qt.WA_TranslucentBackground)

        # 移动到右下角
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = screen_geometry.width() - 80
        y = screen_geometry.height() - 80
        self.icon_widget.move(x, y)
        self.icon_widget.show()
        self.is_minimized = True

    def toggle_chat(self):
        """切换显示/隐藏"""
        if self.is_minimized or (self.chat_window and not self.chat_window.isVisible()):
            self.show_chat()
        elif self.chat_window and self.chat_window.isVisible():
            self.minimize_chat()

    def update_config(self, config):
        """更新配置"""
        self.config = config
        if self.chat_window:
            self.chat_window.config = config


# 测试代码
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 测试配置
    test_config = {
        "provider": "openai",
        "api_key": "1a73929c-d549-43e8-b03f-0d6e3e979771",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "ep-m-20260311150444-fn2zc"
    }

    manager = FloatingChatManager(test_config)
    manager.show_chat()

    sys.exit(app.exec_())

