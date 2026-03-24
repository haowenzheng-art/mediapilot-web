
"""
MediaPilot 主题系统 - 5种精美主题
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QLinearGradient, QBrush, QPainter, QRadialGradient
import random


class ThemeBackgroundWidget(QWidget):
    """主题背景组件基类"""

    def __init__(self, theme_name, parent=None):
        super().__init__(parent)
        self.theme_name = theme_name

    def paintEvent(self, event):
        painter = QPainter(self)
        self.draw_background(painter)

    def draw_background(self, painter):
        """由子类实现具体背景"""
        pass


class SpaceThemeWidget(ThemeBackgroundWidget):
    """太空主题"""

    def __init__(self, parent=None):
        super().__init__("space", parent)

    def draw_background(self, painter):
        # 主渐变 - 深空紫到黑
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(15, 10, 40))
        gradient.setColorAt(0.5, QColor(10, 5, 30))
        gradient.setColorAt(1, QColor(5, 2, 20))
        painter.fillRect(self.rect(), gradient)

        # 添加星星
        painter.setPen(Qt.NoPen)
        for i in range(100):
            x = int(random.randint(0, self.width()))
            y = int(random.randint(0, self.height()))
            size = int(random.randint(1, 3))
            brightness = random.randint(100, 255)
            painter.setBrush(QColor(brightness, brightness, brightness))
            painter.drawEllipse(x, y, size, size)

        # 星云光晕效果
        cx = int(self.width() * 0.8)
        cy = int(self.height() * 0.3)
        radial = QRadialGradient(cx, cy, 300)
        radial.setColorAt(0, QColor(139, 92, 246, 80))
        radial.setColorAt(0.5, QColor(99, 102, 241, 40))
        radial.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(radial)
        painter.drawEllipse(cx - 300, cy - 300, 600, 600)

        # 另一个光晕
        cx2 = int(self.width() * 0.2)
        cy2 = int(self.height() * 0.7)
        radial2 = QRadialGradient(cx2, cy2, 250)
        radial2.setColorAt(0, QColor(6, 182, 212, 60))
        radial2.setColorAt(0.5, QColor(99, 102, 241, 30))
        radial2.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(radial2)
        painter.drawEllipse(cx2 - 250, cy2 - 250, 500, 500)


class ChineseThemeWidget(ThemeBackgroundWidget):
    """中国风主题"""

    def __init__(self, parent=None):
        super().__init__("chinese", parent)

    def draw_background(self, painter):
        # 米黄纸底
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(252, 248, 232))
        gradient.setColorAt(0.5, QColor(249, 243, 220))
        gradient.setColorAt(1, QColor(245, 238, 210))
        painter.fillRect(self.rect(), gradient)

        # 添加水墨晕染效果
        painter.setPen(Qt.NoPen)
        for i in range(5):
            cx = int(random.randint(int(self.width() * 0.1), int(self.width() * 0.9)))
            cy = int(random.randint(int(self.height() * 0.1), int(self.height() * 0.9)))
            size = random.randint(100, 300)
            alpha = random.randint(10, 30)
            radial = QRadialGradient(cx, cy, size)
            radial.setColorAt(0, QColor(80, 60, 40, alpha))
            radial.setColorAt(1, QColor(80, 60, 40, 0))
            painter.setBrush(radial)
            painter.drawEllipse(cx - size, cy - size, size * 2, size * 2)


class CyberpunkThemeWidget(ThemeBackgroundWidget):
    """赛博朋克主题"""

    def __init__(self, parent=None):
        super().__init__("cyberpunk", parent)

    def draw_background(self, painter):
        # 深色背景
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(10, 5, 20))
        gradient.setColorAt(1, QColor(5, 2, 15))
        painter.fillRect(self.rect(), gradient)

        # 霓虹网格线
        painter.setPen(QColor(255, 0, 128, 30))
        for x in range(0, self.width(), 60):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 60):
            painter.drawLine(0, y, self.width(), y)

        # 霓虹光点
        painter.setPen(Qt.NoPen)
        colors = [QColor(255, 0, 128), QColor(0, 255, 255), QColor(255, 255, 0)]
        for i in range(30):
            x = int(random.randint(0, self.width()))
            y = int(random.randint(0, self.height()))
            color = random.choice(colors)
            color.setAlpha(random.randint(50, 150))
            size = random.randint(2, 6)
            painter.setBrush(color)
            painter.drawEllipse(x, y, size, size)


class PixarThemeWidget(ThemeBackgroundWidget):
    """皮克斯漫画风主题"""

    def __init__(self, parent=None):
        super().__init__("pixar", parent)

    def draw_background(self, painter):
        # 温暖的渐变天空
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(135, 206, 235))
        gradient.setColorAt(0.6, QColor(255, 218, 185))
        gradient.setColorAt(1, QColor(255, 182, 193))
        painter.fillRect(self.rect(), gradient)

        # 云朵
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 200))
        cloud_positions = [
            (0.15, 0.2), (0.5, 0.15), (0.8, 0.25),
            (0.25, 0.4), (0.7, 0.35)
        ]
        for cx_ratio, cy_ratio in cloud_positions:
            cx = int(self.width() * cx_ratio)
            cy = int(self.height() * cy_ratio)
            # 画云朵 - 几个圆叠加
            for i in range(5):
                ox = random.randint(-40, 40)
                oy = random.randint(-20, 20)
                size = random.randint(30, 60)
                painter.drawEllipse(cx + ox - size, cy + oy - size, size * 2, size * 2)


class AnimeThemeWidget(ThemeBackgroundWidget):
    """日漫风主题"""

    def __init__(self, parent=None):
        super().__init__("anime", parent)

    def draw_background(self, painter):
        # 粉紫渐变
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 182, 193))
        gradient.setColorAt(0.5, QColor(221, 160, 221))
        gradient.setColorAt(1, QColor(173, 216, 230))
        painter.fillRect(self.rect(), gradient)

        # 樱花花瓣
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 192, 203, 180))
        for i in range(40):
            x = int(random.randint(0, self.width()))
            y = int(random.randint(0, self.height()))
            size = random.randint(6, 15)
            # 画椭圆花瓣
            painter.save()
            painter.translate(x, y)
            painter.rotate(random.randint(0, 360))
            painter.drawEllipse(-size, -size // 2, size * 2, size)
            painter.restore()


class AbstractThemeWidget(ThemeBackgroundWidget):
    """伦敦艺术学院抽象设计主题"""

    def __init__(self, parent=None):
        super().__init__("abstract", parent)

    def draw_background(self, painter):
        # 高级灰底
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(245, 245, 245))
        gradient.setColorAt(0.5, QColor(235, 235, 235))
        gradient.setColorAt(1, QColor(225, 225, 225))
        painter.fillRect(self.rect(), gradient)

        # 抽象几何形状
        painter.setPen(Qt.NoPen)

        # 圆形
        for i in range(8):
            cx = int(random.randint(0, self.width()))
            cy = int(random.randint(0, self.height()))
            size = random.randint(50, 150)
            colors = [
                QColor(255, 107, 107, 150),
                QColor(78, 205, 196, 150),
                QColor(69, 183, 209, 150),
                QColor(150, 206, 180, 150),
                QColor(255, 238, 173, 150),
                QColor(255, 154, 162, 150),
            ]
            painter.setBrush(random.choice(colors))
            painter.drawEllipse(cx - size, cy - size, size * 2, size * 2)

        # 线条
        painter.setPen(QColor(50, 50, 50, 80))
        for i in range(15):
            x1 = int(random.randint(0, self.width()))
            y1 = int(random.randint(0, self.height()))
            x2 = int(random.randint(0, self.width()))
            y2 = int(random.randint(0, self.height()))
            painter.drawLine(x1, y1, x2, y2)


# 主题工厂
THEME_WIDGETS = {
    "space": SpaceThemeWidget,
    "chinese": ChineseThemeWidget,
    "cyberpunk": CyberpunkThemeWidget,
    "pixar": PixarThemeWidget,
    "anime": AnimeThemeWidget,
    "abstract": AbstractThemeWidget,
}

THEME_NAMES = {
    "space": "太空赛博",
    "chinese": "中国风",
    "cyberpunk": "赛博朋克",
    "pixar": "皮克斯漫画",
    "anime": "日漫风",
    "abstract": "伦敦艺术抽象",
}

THEME_STYLES = {
    "space": {
        "primary": "#8B5CF6",
        "secondary": "#06B6D4",
        "background": "#0F0A28",
        "background_light": "#1E1B4B",
        "text": "#E0E7FF",
        "text_secondary": "#94A3B8",
        "border": "rgba(139, 92, 246, 80)",
        "button_gradient_start": "#1E1B4B",
        "button_gradient_end": "#312E81",
    },
    "chinese": {
        "primary": "#8B4513",
        "secondary": "#DC143C",
        "background": "#FCF8E8",
        "background_light": "#F5F0E0",
        "text": "#2C1810",
        "text_secondary": "#6B5344",
        "border": "rgba(139, 69, 19, 80)",
        "button_gradient_start": "#8B4513",
        "button_gradient_end": "#A0522D",
    },
    "cyberpunk": {
        "primary": "#FF0080",
        "secondary": "#00FFFF",
        "background": "#0A0514",
        "background_light": "#1A0A2E",
        "text": "#FFFFFF",
        "text_secondary": "#FF0080",
        "border": "rgba(255, 0, 128, 80)",
        "button_gradient_start": "#1A0A2E",
        "button_gradient_end": "#2A0F4E",
    },
    "pixar": {
        "primary": "#FF6B6B",
        "secondary": "#4ECDC4",
        "background": "#FFF5E6",
        "background_light": "#FFE8CC",
        "text": "#2C3E50",
        "text_secondary": "#7F8C8D",
        "border": "rgba(255, 107, 107, 80)",
        "button_gradient_start": "#FF6B6B",
        "button_gradient_end": "#FF8E8E",
    },
    "anime": {
        "primary": "#FF69B4",
        "secondary": "#9370DB",
        "background": "#FFE4EC",
        "background_light": "#FFD1DC",
        "text": "#4A4A4A",
        "text_secondary": "#8B8B8B",
        "border": "rgba(255, 105, 180, 80)",
        "button_gradient_start": "#FF69B4",
        "button_gradient_end": "#FF8EC4",
    },
    "abstract": {
        "primary": "#1A1A2E",
        "secondary": "#16213E",
        "background": "#F5F5F5",
        "background_light": "#E8E8E8",
        "text": "#333333",
        "text_secondary": "#666666",
        "border": "rgba(26, 26, 46, 80)",
        "button_gradient_start": "#1A1A2E",
        "button_gradient_end": "#16213E",
    },
}

