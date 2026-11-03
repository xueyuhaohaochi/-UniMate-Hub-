"""成长拓展层 · 技能树构建师 SkillBuilder：目标拆解为每日微任务 + 进度追踪机制。"""
from __future__ import annotations

import re
from typing import List

from core.agent_base import BaseAgent, RunContext, get_field, parse_struct_hits
from core.rag import KBHit

_STRIP = ("帮我", "请", "我想", "我要", "学会", "学习", "掌握", "制定", "一个", "计划", "目标", "是", "？", "?", "。")


class SkillBuilderAgent(BaseAgent):
    id = "skill_builder"
    name = "技能树构建师"
    en_name = "SkillBuilder"
    layer = "成长拓展层"
    role = "学习目标拆解与每日任务追踪"
    description = "把宏大学习目标（如「学会 Python 数据分析」）拆解为每日可执行的微任务，并建立进度追踪机制。"
    capabilities = ["12周阶段规划", "每日微任务表", "里程碑验收标准", "打卡复盘机制"]
    keywords = ["拆解", "每日任务", "打卡", "学习路线", "微任务", "计划表", "目标管理", "坚持", "自律", "规划", "准备", "提升"]
    kb_files = ["study.txt"]

    @staticmethod
    def _goal(task: str, ctx: RunContext) -> str:
        t = task.strip()
        for w in _STRIP:
            t = t.replace(w, "")
        t = re.sub(r"^[，。,\s]+|[。？！?!.,，\s]+$", "", t).strip()
        return t[:24] if t else (ctx.profile.goal or "核心发展目标")

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        goal = self._goal(task, ctx)
        p = ctx.profile

        comp = "竞赛节奏" if any(k in task for k in ("赛", "比赛", "竞赛")) else "考试节奏" if any(k in task for k in ("考", "复习", "期末")) else "常规节奏"
        phases = {
            "竞赛节奏": [
                ("第1-2周 摸底选题", "定赛道与队友，完成 1 份竞品分析"),
                ("第3-6周 核心打磨", "完成最小可用作品 + 内测反馈 20 份"),
                ("第7-10周 材料冲刺", "完成 BP / PPT / 演示视频并通过 3 次模拟路演"),
                ("第11-12周 参赛复盘", "提交参赛材料，赛后输出复盘报告"),
            ],
            "考试节奏": [
                ("第1-2周 考纲摸底", "红黄绿标记全部知识点"),
                ("第3-6周 专题攻坚", "高频题型正确率 ≥ 80%"),
                ("第7-10周 套卷实战", "3 套全真模拟达到目标分"),
                ("第11-12周 冲刺定态", "错题清零 + 作息调整到考试时段"),
            ],
            "常规节奏": [
                ("第1-2周 输入期", "完成入门教程，建立知识地图"),
                ("第3-6周 练习期", "完成 3 个递进式练习项目"),
                ("第7-10周 实战期", "做一个可展示的完整作品并开源"),
                ("第11-12周 输出期", "写总结文章 / 参加相关认证或分享"),
            ],
        }[comp]

        parts = [
            f"### 目标：{goal}",
            f"拆解方式：{comp} · 12 周 · 每日 30~60 分钟微任务（适配 {p.grade}课业强度）",
            "",
            "### 四阶段里程碑",
            "",
            "| 阶段 | 阶段目标 | 验收标准（M.x） |",
            "| --- | --- | --- |",
        ]
        for i, (name, target) in enumerate(phases, 1):
            parts.append(f"| {name} | {target} | M{i} 达成即可进入下一阶段 |")
        parts += [
            "",
            "### 第一周每日微任务表",
            "",
            "| 日 | 时长 | 任务 | 完成标准 |",
            "| --- | --- | --- | --- |",
            "| 周一 | 45min | 明确「会了什么算赢」：写出 3 条可验证的成果定义 | 3 条写进笔记 |",
            "| 周二 | 45min | 收集 3 份高质量教程 / 课表，选定主教材 | 教材唯一化 |",
            "| 周三 | 30min | 搭环境 / 备齐工具，跑通第一个 Hello 级示例 | 截图存档 |",
            "| 周四 | 45min | 主教材第 1 章 + 笔记（费曼式复述 3 句话） | 笔记可公开 |",
            "| 周五 | 45min | 跟做 1 个最小案例，允许抄但要逐行注释 | 运行成功 |",
            "| 周六 | 60min | 改造案例：换数据 / 换功能，制造第一个 bug 并解决 | 记录 bug 清单 |",
            "| 周日 | 20min | 周复盘 + 下周任务微调（见复盘模板） | 打卡表无空行 |",
            "",
            "### 打卡与追踪机制",
            "",
            "- **每日一条记录**（1 分钟）：今天做了什么 / 卡点 / 明天第一件事；",
            "- **每周日复盘三问**：目标进度 %？最大阻力？下周砍掉或加强什么？",
            "- **防中断规则**：状态差时允许「最小动作」（只写 10 行 / 读 2 页），保连续性不断链；",
            "- **可视化**：把 M1~M4 贴在书桌，每完成一项涂黑，制造进度感。",
        ]
        if hits:
            parts += ["", "### 方法论支撑", ""]
            parts += [f"- **{h.title}**：{h.text.splitlines()[-1][:70]}" for h in hits[:2]]

        parts += [
            "",
            f"> 本计划已与你的画像联动（目标：{(p.goal or '未填写')[:30]}）。每周回来说一句「第 X 周打卡」，我帮你校准下一周任务。",
        ]
        return "\n".join(parts)
