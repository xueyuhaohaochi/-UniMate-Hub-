"""基础服务层 · 选课规划师 CoursePlanner：学期课表推荐 + 难度/给分分析。"""
from __future__ import annotations

from typing import List

from core.agent_base import BaseAgent, RunContext, get_field, parse_struct_hits
from core.rag import KBHit


def _is_hard(diff: str) -> bool:
    diff = diff.strip()
    try:
        return float(diff) >= 4.0
    except ValueError:
        return ("难" in diff) or ("高" in diff)


class CoursePlannerAgent(BaseAgent):
    id = "course_planner"
    name = "选课规划师"
    en_name = "CoursePlanner"
    layer = "基础服务层"
    role = "学期课表与选课策略规划"
    description = "根据专业、兴趣与先修课要求推荐学期课表，基于历史数据分析课程难度与给分情况。"
    capabilities = ["个性化课表推荐", "课程难度与给分分析", "先修链检查", "学分与强度平衡"]
    keywords = ["选课", "课表", "补选", "退课", "学分", "给分", "课程推荐", "先修", "培养方案"]
    kb_files = ["courses.txt"]

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        items = parse_struct_hits(hits)
        p = ctx.profile
        if not items:
            return (
                f"{p.name} 同学，知识库中暂未命中课程数据。请先在侧边栏完善专业与年级，"
                "再说明你想选的课程方向（如「下学期想选后端方向的课」），我会重新规划。"
            )

        # 按专业 + 年级过滤（宽松匹配）
        fit_rows, other_rows = [], []
        for it in items:
            f = it["fields"]
            fit = get_field(it, "适用", "适用专业")
            term = get_field(it, "学期", "建议学期")
            major_ok = (not fit) or any(k in fit for k in p.major[:4]) or ("通用" in fit) or ("不限" in fit)
            grade_ok = (not term) or (p.grade[:2] in term) or ("不限" in term)
            (fit_rows if (major_ok and grade_ok) else other_rows).append((it, f))
        rows = fit_rows or other_rows

        table = ["| 课程 | 难度 | 给分 | 先修课 | 建议学期 |", "| --- | --- | --- | --- | --- |"]
        for it, _f in rows[:8]:
            table.append(
                f"| **{it['title']}** | {get_field(it, '难度', '难度系数') or '—'} "
                f"| {get_field(it, '给分') or '—'} | {get_field(it, '先修', '先修课') or '无'} "
                f"| {get_field(it, '学期', '建议学期') or '不限'} |"
            )

        hard = [it["title"] for it, _f in rows if _is_hard(get_field(it, "难度", "难度系数"))]
        strategy = [
            "- **先修链优先**：先修课未通过的课程请顺延，避免知识断链；",
            f"- **难度搭配**：{'、'.join(hard[:2]) or '本学期无高难课程'} 属于硬课，建议与给分友好的课程搭配，每学期硬课控制在 1~2 门；",
            "- **学分上限**：总学分建议 22~26，为竞赛 / 实习 / 科研预留弹性时间；",
            "- **试听确认**：开学前两周试听后再最终定课，留意补退选截止时间。",
        ]
        if any(("考研" in i) or ("保研" in i) for i in p.interests) or ("保研" in (p.goal or "")) or ("考研" in (p.goal or "")):
            strategy.insert(3, "- **升学导向**：优先修完与目标专业笔试 / 面试强相关的核心课；")

        return (
            f"### {p.grade} · {p.major} 推荐课表\n\n"
            f"已结合你的画像（兴趣方向：{'、'.join(p.interests) or '未填写'}）与近年给分数据筛选：\n\n"
            + "\n".join(table)
            + "\n\n### 选课策略\n\n" + "\n".join(strategy)
            + "\n\n> 说明：难度 / 给分来自近年学长学姐评价汇总，仅供参考，请以学院最新培养方案为准。"
        )
