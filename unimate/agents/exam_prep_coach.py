"""基础服务层 · 备考教练 ExamPrepCoach：复习计划 + 苏格拉底提问 + 错题本机制。"""
from __future__ import annotations

import re
from typing import List

from core.agent_base import BaseAgent, RunContext, get_field, parse_struct_hits
from core.rag import KBHit

_STRIP = ("帮我", "请", "制定", "做一个", "一份", "的", "复习计划", "复习", "备考", "计划", "怎么", "如何")


class ExamPrepCoachAgent(BaseAgent):
    id = "exam_prep_coach"
    name = "备考教练"
    en_name = "ExamPrepCoach"
    layer = "基础服务层"
    role = "复习计划制定与知识掌握检测"
    description = "根据课程 syllabus 生成复习计划，提供模拟题与苏格拉底式提问检测掌握程度，自动生成错题本。"
    capabilities = ["14天复习计划", "苏格拉底式自测", "错题本与间隔重复", "模拟题策略"]
    keywords = ["复习", "备考", "期末", "考试", "刷题", "模拟题", "错题", "挂科", "四六级", "期末周", "补考"]
    kb_files = ["study.txt"]

    @staticmethod
    def _topic(task: str) -> str:
        t = task.strip()
        for w in _STRIP:
            t = t.replace(w, "")
        t = re.sub(r"^[，。,\s]+|[。？！?!.,，\s]+$", "", t).strip()
        return t[:16] if t else "目标课程"

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        topic = self._topic(task)
        p = ctx.profile

        methods = ""
        if hits:
            lines = [f"- **{h.title}**：{h.text.splitlines()[-1][:60]}" for h in hits[:2]]
            methods = "\n".join(lines)

        parts = [
            f"### {topic} · 14 天三阶段复习计划",
            "",
            "| 阶段 | 天数 | 重点 | 每日动作 |",
            "| --- | --- | --- | --- |",
            f"| 基础过盘 | D1~D5 | 按考纲过完全部知识点，标记红黄绿掌握度 | 2h 看书/课件 + 1h 例题复现 |",
            f"| 专题刷题 | D6~D10 | 按题型分专题攻坚（{topic}高频考点优先） | 1.5h 专题题 + 0.5h 整理错因 |",
            "| 套模冲刺 | D11~D13 | 全真模拟限时训练 + 错题回炉 | 1 套卷（限时）+ 错题重做 |",
            "| 考前定格 | D14 | 公式卡 / 概念卡快闪 + 早睡 | 只看错题本与笔记，不做新题 |",
            "",
            "### 苏格拉底式自测（检验真实掌握度）",
            "",
            f"1. 不看书画出「{topic}」的知识结构图，能画全吗？",
            f"2. 用一句话说清「{topic}」中最核心的概念，不许堆术语；",
            f"3. 它为什么存在？没有它会导致什么问题？",
            f"4. 「{topic}」与最容易被混淆的相邻概念，本质区别是什么？",
            f"5. 自己出一道典型题，并口述完整解题路径——卡壳处就是你的薄弱点。",
            "",
            "### 错题本自动生成模板",
            "",
            "| 日期 | 题号 | 错因分类 | 关联知识点 | 重做节点 |",
            "| --- | --- | --- | --- | --- |",
            "| 例：6/3 | T12 | 概念混淆 | XX 与 YY 的边界 | D+1 / D+3 / D+7 / D+14 |",
            "",
            "错因只允许三类：概念不清 / 计算粗心 / 审题偏差——分别对应「回教材」「限时重做」「圈关键词训练」。",
            "",
            "### 学习方法支撑",
            methods
            or "- 间隔重复：重做节点固定为 1 / 3 / 7 / 14 天；\n- 费曼技巧：每个知识点讲给外行听一遍；\n- 主动回忆：合上书先默写再对照，比反复阅读效率高 2 倍。",
            "",
            f"> 提示：{p.name}（{p.grade}）当前课业强度下，建议把本计划与选课规划师的课表联动，避免复习周撞车大作业截止。",
        ]
        return "\n".join(parts)
