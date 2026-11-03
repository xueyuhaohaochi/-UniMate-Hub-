"""基础服务层 · 学术资源导航员 LibraryGuide：文献检索 + 综述大纲 + 检索式构造。"""
from __future__ import annotations

import re
from typing import List

from core.agent_base import BaseAgent, RunContext, get_field, parse_struct_hits
from core.rag import KBHit

_NOISE = ("帮我", "请", "找一下", "找", "关于", "有关", "最新", "相关", "的资料", "文献", "综述", "资料")


class LibraryGuideAgent(BaseAgent):
    id = "library_guide"
    name = "学术资源导航员"
    en_name = "LibraryGuide"
    layer = "基础服务层"
    role = "文献检索与学术资源导航"
    description = "帮助学生快速查找馆藏图书与数据库论文，直接生成特定主题的文献综述大纲与检索式。"
    capabilities = ["多数据库检索策略", "检索式构造", "文献综述大纲", "馆藏与数据库导航"]
    keywords = ["文献", "检索", "图书馆", "综述", "数据库", "查资料", "参考文献", "查论文", "知网"]
    kb_files = ["library.txt"]

    @staticmethod
    def _topic(task: str) -> str:
        t = task.strip()
        for w in _NOISE:
            t = t.replace(w, "")
        t = re.sub(r"[。？！?!.,，\s]+$", "", t).strip()
        return t[:24] if t else "研究主题"

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        items = parse_struct_hits(hits)
        topic = self._topic(task)

        parts = ["### 推荐检索资源", ""]
        if items:
            parts += ["| 资源 / 文献 | 类型与收录 | 使用建议 |", "| --- | --- | --- |"]
            for it in items[:5]:
                parts.append(
                    f"| **{it['title']}** | {get_field(it, '类型', '收录') or '—'} "
                    f"| {get_field(it, '技巧', '建议', '入口', '备注') or '—'} |"
                )
        else:
            parts += [
                "- 校图书馆门户：统一检索馆藏纸质书与电子资源；",
                "- CNKI 中国知网：中文期刊 / 学位论文主力库；",
                "- IEEE Xplore / ACM DL：计算机与工程类外文文献；",
                "- Web of Science / Scopus：跨库引文追踪，找高被引综述。",
            ]

        parts += [
            f"",
            f"### 检索式示例（主题：{topic}）",
            "",
            "- CNKI：`主题 = (\"{topic}\") AND (综述 OR 进展 OR 研究现状)`，按「被引量降序 + 近3年」筛选；",
            f"- IEEE Xplore：`(\"{topic}\") AND (\"survey\" OR \"review\")`，限定 2023 年以后；",
            "- 追加技巧：从 1 篇高质量综述的参考文献反向溯源（滚雪球法）。",
            "",
            f"### 《{topic}研究综述》大纲框架",
            "",
            f"1. **研究背景与意义**：{topic}的应用价值与待解决的问题；",
            f"2. **国内外研究现状**：按技术路线 / 学派分组梳理代表性工作；",
            "3. **方法对比分析**：以表格对比各方法的原理、数据集、指标与优劣；",
            f"4. **挑战与趋势**：当前{topic}研究的瓶颈与未来 3~5 年方向；",
            "5. **结论**：总结共识与分歧，指出值得深入的具体切入点。",
            "",
            "### 文献筛选策略",
            "",
            "- 优先级：近 3 年 > 高被引 > 顶级期刊 / 会议 > 综述类；",
            "- 先读标题 + 摘要 + 结论三遍法初筛，通过后再精读；",
            "- 用文献管理工具（Zotero）分组归档并记录一句话笔记。",
        ]
        return "\n".join(parts)
