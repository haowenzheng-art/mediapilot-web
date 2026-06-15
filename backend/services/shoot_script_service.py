"""
拍摄脚本生成服务
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from backend.core.ai_service import ai_manager
from backend.models.domain.shoot_script import (
    ShootScriptRequest, ShootScriptResponse, Shot,
    PlatformType, ScriptStyle
)

logger = logging.getLogger(__name__)


class ShootScriptService:
    """拍摄脚本生成服务"""

    def __init__(self):
        self._scripts = {}  # 临时存储（生产环境应该存数据库）

    def generate(self, request: ShootScriptRequest) -> ShootScriptResponse:
        """
        生成拍摄脚本

        Args:
            request: 生成请求

        Returns:
            生成的拍摄脚本
        """
        script_id = str(uuid.uuid4())

        # 获取平台配置
        platform_config = self._get_platform_config(request.platform, request.style)

        # 构建AI提示词
        prompt = self._build_prompt(request, platform_config)

        # AI生成
        shots = []
        title = ""
        hooks = []
        call_to_action = ""
        tags = []

        if ai_manager.is_available():
            try:
                ai_result = ai_manager.generate(prompt, max_tokens=3000)
                parsed = self._parse_ai_result(ai_result, request.platform)
                shots = parsed.get("shots", [])
                title = parsed.get("title", "")
                hooks = parsed.get("hooks", [])
                call_to_action = parsed.get("call_to_action", "")
                tags = parsed.get("tags", [])
            except Exception as e:
                logger.warning(f"AI生成失败: {e}")
                # 回退到mock
                pass

        # 如果AI生成失败或不可用，使用mock
        if not shots:
            shots, title, hooks, call_to_action, tags = self._mock_generate(
                request, platform_config
            )

        # 计算总时长
        estimated_duration = self._calculate_duration(shots)

        # 存储结果
        result = ShootScriptResponse(
            id=script_id,
            topic=request.topic,
            platform=request.platform,
            style=request.style,
            persona=request.persona,
            shots=shots,
            title=title,
            hooks=hooks,
            call_to_action=call_to_action,
            tags=tags,
            estimated_duration=estimated_duration,
            created_at=datetime.utcnow()
        )
        self._scripts[script_id] = result

        return result

    def get_script(self, script_id: str) -> Optional[ShootScriptResponse]:
        """获取脚本"""
        return self._scripts.get(script_id)

    def _get_platform_config(self, platform: PlatformType, style: ScriptStyle) -> dict:
        """获取平台配置"""
        configs = {
            PlatformType.DOUYIN: {
                "orientation": "竖屏",
                "target_duration": "60秒",
                "shot_count": 5,
                "shot_duration": "10-15秒",
                "style_prefix": "短平快"
            },
            PlatformType.XIAOHONGSHU: {
                "orientation": "竖屏",
                "target_duration": "3分钟",
                "shot_count": 8,
                "shot_duration": "20-25秒",
                "style_prefix": "详实"
            },
            PlatformType.BILIBILI: {
                "orientation": "横屏",
                "target_duration": "5-10分钟",
                "shot_count": 15,
                "shot_duration": "20-40秒",
                "style_prefix": "深度"
            }
        }
        return configs.get(platform, configs[PlatformType.DOUYIN])

    def _build_prompt(self, request: ShootScriptRequest, platform_config: dict) -> str:
        """构建AI生成提示词"""
        style_map = {
            ScriptStyle.ENERGETIC: "激情热血，充满能量",
            ScriptStyle.RELAXED: "轻松幽默，有趣风趣",
            ScriptStyle.PROFESSIONAL: "专业分析，数据驱动"
        }

        style_desc = style_map.get(request.style, "")

        prompt = f"""你是一位{request.persona or '专业视频创作者'}。

请为以下主题创作一个拍摄脚本。

【目标平台】{request.platform.value}
【平台特点】{platform_config['orientation']}、目标时长{platform_config['target_duration']}、{platform_config['style_prefix']}风格
【脚本风格】{style_desc}
【话题】{request.topic}

【输出要求】
- 生成{platform_config['shot_count']}个左右的分镜头
- 每个镜头包含：编号、时长、画面描述、台词、场景建议、运镜建议
- 禁止使用"#"符号
- 格式工整
- 去除AI感，不要使用"本文""文章""综上所述"等表达

【输出格式】
标题：xxx

钩子（2-3个备选）：
1. xxx
2. xxx

分镜头脚本：
镜头1 [时长：x:xx]
画面：xxx
台词：xxx
场景建议：xxx
运镜建议：xxx

镜头2 [时长：x:xx]
画面：xxx
台词：xxx
场景建议：xxx
运镜建议：xxx

...

行动号召：
xxx

标签：xxx, xxx
"""
        return prompt

    def _parse_ai_result(self, ai_result: str, platform: PlatformType) -> dict:
        """解析AI生成结果"""
        result = {
            "shots": [],
            "title": "",
            "hooks": [],
            "call_to_action": "",
            "tags": []
        }

        lines = ai_result.split("\n")
        current_section = None
        current_shot = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 移除#号
            line = line.replace("#", "").strip()

            if line.startswith("标题："):
                result["title"] = line.replace("标题：", "").strip()
            elif line.startswith("钩子"):
                current_section = "hooks"
            elif line.startswith("分镜头脚本"):
                current_section = "shots"
            elif line.startswith("行动号召"):
                current_section = "cta"
                result["call_to_action"] = line.replace("行动号召：", "").strip()
            elif line.startswith("标签"):
                tags_line = line.replace("标签：", "").strip()
                result["tags"] = [t.strip() for t in tags_line.split("，")]
            elif current_section == "hooks":
                hook = line
                if hook.startswith(("1.", "2.", "3.")):
                    hook = hook.split(".", 1)[1].strip()
                result["hooks"].append(hook)
            elif current_section == "shots":
                # 解析镜头
                if line.startswith("镜头"):
                    # 新镜头开始
                    if current_shot and current_shot.get("dialogue"):
                        result["shots"].append(current_shot)
                    shot_num = int("".join([c for c in line if c.isdigit()]) or "1")
                    current_shot = {"shot_number": shot_num}
                elif line.startswith("时长："):
                    duration = line.split("时长：", 1)[1].strip()
                    if current_shot:
                        current_shot["duration"] = duration
                elif line.startswith("画面："):
                    desc = line.split("画面：", 1)[1].strip()
                    if current_shot:
                        current_shot["visual_description"] = desc
                elif line.startswith("台词："):
                    dialogue = line.split("台词：", 1)[1].strip()
                    if current_shot:
                        current_shot["dialogue"] = dialogue
                elif line.startswith("场景建议："):
                    scene = line.split("场景建议：", 1)[1].strip()
                    if current_shot:
                        current_shot["scene_suggestion"] = scene
                elif line.startswith("运镜建议："):
                    camera = line.split("运镜建议：", 1)[1].strip()
                    if current_shot:
                        current_shot["camera_movement"] = camera

        # 添加最后一个镜头
        if current_shot and current_shot.get("dialogue"):
            result["shots"].append(current_shot)

        # 如果解析失败，使用mock数据
        if not result["shots"]:
            result["shots"] = []
            result["title"] = "拍摄脚本"

        return result

    def _mock_generate(self, request: ShootScriptRequest, platform_config: dict) -> tuple:
        """Mock生成（用于开发测试）"""
        # 根据平台生成不同的镜头
        if request.platform == PlatformType.DOUYIN:
            shots = [
                Shot(
                    shot_number=1,
                    duration="0:00-0:08",
                    visual_description="人物正面特写，表情兴奋",
                    dialogue="今天要聊个超级重要的东西！",
                    scene_suggestion="使用纯色背景或简洁场景",
                    camera_movement="轻微推进"
                ),
                Shot(
                    shot_number=2,
                    duration="0:08-0:18",
                    visual_description="人物中景，手势丰富",
                    dialogue="很多人都问我，这个问题到底怎么解决？",
                    scene_suggestion="保持良好光线",
                    camera_movement="固定镜头"
                ),
                Shot(
                    shot_number=3,
                    duration="0:18-0:30",
                    visual_description="人物近景，认真讲解",
                    dialogue="其实核心就三点，听完你就明白了。",
                    scene_suggestion="可以加一些字幕效果",
                    camera_movement="稳定拍摄"
                ),
                Shot(
                    shot_number=4,
                    duration="0:30-0:45",
                    visual_description="人物全身，示范动作",
                    dialogue="第一点，关注细节。第二点，持续练习。第三点，保持耐心。",
                    scene_suggestion="适当留白展示动作",
                    camera_movement="跟随人物动作"
                ),
                Shot(
                    shot_number=5,
                    duration="0:45-0:60",
                    visual_description="人物特写，微笑结尾",
                    dialogue="点个赞，下期分享更多干货！",
                    scene_suggestion="可以加点赞动画效果",
                    camera_movement="轻微后拉"
                )
            ]
            return (
                shots,
                f"60秒{request.topic}快速讲解",
                [f"关于{request.topic}的秘密是什么？",
                  f"{request.topic}，90%的人都不知道！"],
                "点赞关注，下期更精彩！",
                [request.topic, "干货分享", "短视频"]
            )

        elif request.platform == PlatformType.XIAOHONGSHU:
            shots = [
                Shot(
                    shot_number=1,
                    duration="0:00-0:20",
                    visual_description="场景全景，人物入场",
                    dialogue="大家好，今天来深度聊聊{request.topic}这个话题。",
                    scene_suggestion="温馨的居家或工作室环境",
                    camera_movement="缓慢摇镜"
                ),
                Shot(
                    shot_number=2,
                    duration="0:20-0:50",
                    visual_description="人物中景，表情自然",
                    dialogue="首先，我想问大家一个问题，你们平时是怎么应对的？",
                    scene_suggestion="可以准备一些道具",
                    camera_movement="固定镜头"
                ),
                Shot(
                    shot_number=3,
                    duration="0:50-1:20",
                    visual_description="人物近景，手势配合",
                    dialogue="其实{request.topic}的关键在于理解本质，而不是盲目跟风。",
                    scene_suggestion="适当添加文字说明",
                    camera_movement="轻微推拉"
                ),
                Shot(
                    shot_number=4,
                    duration="1:20-1:50",
                    visual_description="人物特写，认真讲解",
                    dialogue="我总结了三个实用方法，每个都很简单，但效果很好。",
                    scene_suggestion="突出重点内容",
                    camera_movement="稳定拍摄"
                ),
                Shot(
                    shot_number=5,
                    duration="1:50-2:20",
                    visual_description="场景细节，展示物品",
                    dialogue="方法一，建立正确的认知框架。方法二，培养持续的学习习惯。",
                    scene_suggestion="镜头对准关键物品",
                    camera_movement="跟随焦点"
                ),
                Shot(
                    shot_number=6,
                    duration="2:20-2:50",
                    visual_description="人物中景，继续讲解",
                    dialogue="方法三，找到适合自己的实践方式。这三个方法我都亲自验证过，确实有效。",
                    scene_suggestion="保持人物在画面中心",
                    camera_movement="平移镜头"
                ),
                Shot(
                    shot_number=7,
                    duration="2:50-3:10",
                    visual_description="人物近景，总结要点",
                    dialogue="总结一下，{request.topic}不是什么神秘的东西，只要方法对，谁都可以掌握。",
                    scene_suggestion="可以添加总结字幕",
                    camera_movement="固定镜头"
                ),
                Shot(
                    shot_number=8,
                    duration="3:10-3:30",
                    visual_description="人物特写，微笑结尾",
                    dialogue="如果觉得有用，收藏起来慢慢看，记得点赞关注哦！",
                    scene_suggestion="温馨的结尾氛围",
                    camera_movement="轻微后拉"
                )
            ]
            return (
                shots,
                f"3分钟深度解读{request.topic}",
                [f"关于{request.topic}的那些事",
                  f"{request.topic}，一篇讲明白"],
                "收藏关注，下次不迷路！",
                [request.topic, "干货分享", "小红书"]
            )

        else:  # BILIBILI
            shots = [
                Shot(
                    shot_number=1,
                    duration="0:00-0:45",
                    visual_description="片头，标题画面",
                    dialogue="大家好，今天我们来深度探讨{request.topic}这个话题。",
                    scene_suggestion="专业的片头设计",
                    camera_movement="淡入效果"
                ),
                Shot(
                    shot_number=2,
                    duration="0:45-1:30",
                    visual_description="人物中景，背景信息",
                    dialogue="在开始之前，我想先说明一下，这个话题涉及的几个核心概念，希望大家能耐心看完。",
                    scene_suggestion="整洁的桌面环境",
                    camera_movement="稳定固定"
                ),
                Shot(
                    shot_number=3,
                    duration="1:30-2:15",
                    visual_description="人物近景，讲解第一部分",
                    dialogue="第一部分，{request.topic}的基本原理和发展历程。这个部分很重要，它是理解后续内容的基础。",
                    scene_suggestion="可以添加关键词字幕",
                    camera_movement="轻微推进"
                ),
                Shot(
                    shot_number=4,
                    duration="2:15-3:00",
                    visual_description="PPT/图表展示",
                    dialogue="大家看这张图，可以看到{request.topic}的核心结构...",
                    scene_suggestion="清晰的图表展示",
                    camera_movement="固定镜头"
                ),
                Shot(
                    shot_number=5,
                    duration="3:00-3:45",
                    visual_description="人物中景，案例讲解",
                    dialogue="这里我举个具体的例子，帮助大家更好地理解。比如说...",
                    scene_suggestion="准备案例素材",
                    camera_movement="跟随讲解节奏"
                ),
                Shot(
                    shot_number=6,
                    duration="3:45-4:30",
                    visual_description="人物近景，深入分析",
                    dialogue="通过这个案例，我们可以看出几个关键点。第一点，...第二点，...第三点，...",
                    scene_suggestion="突出重点内容",
                    camera_movement="稳定拍摄"
                ),
                Shot(
                    shot_number=7,
                    duration="4:30-5:15",
                    visual_description="多画面分屏",
                    dialogue="这里我们把几个相关概念放在一起对比，大家可以更清楚地看到它们之间的区别。",
                    scene_suggestion="清晰的分屏效果",
                    camera_movement="平移过渡"
                ),
                Shot(
                    shot_number=8,
                    duration="5:15-6:00",
                    visual_description="人物中景，实践方法",
                    dialogue="接下来，我想分享几个实用的方法。这些方法我都亲自验证过，确实有效。",
                    scene_suggestion="准备演示素材",
                    camera_movement="跟随动作"
                ),
                Shot(
                    shot_number=9,
                    duration="6:00-6:45",
                    visual_description="操作演示特写",
                    dialogue="方法一，具体操作步骤是...",
                    scene_suggestion="特写展示操作",
                    camera_movement="稳定跟随"
                ),
                Shot(
                    shot_number=10,
                    duration="6:45-7:30",
                    visual_description="人物中景，继续讲解",
                    dialogue="方法二，这个方法的关键在于...",
                    scene_suggestion="保持画面稳定",
                    camera_movement="平移镜头"
                ),
                Shot(
                    shot_number=11,
                    duration="7:30-8:15",
                    visual_description="综合案例展示",
                    dialogue="掌握了这些方法后，我们可以看看实际应用的效果。比如在...场景下...",
                    scene_suggestion="准备案例视频",
                    camera_movement="画面切换"
                ),
                Shot(
                    shot_number=12,
                    duration="8:15-9:00",
                    visual_description="数据对比分析",
                    dialogue="从数据上看，使用这些方法后，效率提升了约40%，这个结果是很显著的。",
                    scene_suggestion="清晰的数据展示",
                    camera_movement="固定镜头"
                ),
                Shot(
                    shot_number=13,
                    duration="9:00-9:45",
                    visual_description="人物近景，总结要点",
                    dialogue="总结一下，{request.topic}的核心就是这三点：第一，...第二，...第三，...",
                    scene_suggestion="添加总结字幕",
                    camera_movement="稳定拍摄"
                ),
                Shot(
                    shot_number=14,
                    duration="9:45-10:15",
                    visual_description="人物中景，延伸讨论",
                    dialogue="除了这些基础内容，还有一些进阶技巧值得了解。比如...",
                    scene_suggestion="保持自然节奏",
                    camera_movement="轻微推进"
                ),
                Shot(
                    shot_number=15,
                    duration="10:15-10:30",
                    visual_description="人物特写，片尾",
                    dialogue="好了，今天的分享就到这里。如果觉得有用，记得三连支持，下期更精彩！",
                    scene_suggestion="专业的片尾设计",
                    camera_movement="淡出效果"
                )
            ]
            return (
                shots,
                f"5-10分钟{request.topic}深度分析",
                [f"关于{request.topic}的完整解析",
                  f"{request.topic}，从入门到精通"],
                "三连支持，关注获取更多干货！",
                [request.topic, "干货分享", "B站"]
            )

    def _calculate_duration(self, shots: List[Shot]) -> str:
        """计算总时长"""
        # 简化处理，基于镜头数量估算
        shot_count = len(shots)
        if shot_count <= 5:
            return "约60秒"
        elif shot_count <= 10:
            return "约3分钟"
        else:
            return "约5-10分钟"


# 全局实例
shoot_script_service = ShootScriptService()
