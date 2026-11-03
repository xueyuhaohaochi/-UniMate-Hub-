"""成长拓展层 · 校园活动雷达 EventScout：活动聚合 + 画像匹配推荐 + 截止提醒。"""
from __future__ import annotations

from datetime import datetime
import re
from typing import List

from core.agent_base import BaseAgent, RunContext, get_field, parse_struct_hits
from core.rag import KBHit


def _stage_hint(month: int) -> str:
    if month <= 5:
        return "校赛备赛期（组队 + 选题黄金窗口）"
    if month == 6:
        return "校级初赛 / 复赛密集期"
    if month <= 9:
        return "省级选拔窗口期"
    return "全国总决赛与年终收官期"


class EventScoutAgent(BaseAgent):
    id = "event_scout"
    name = "校园活动雷达"
    en_name = "EventScout"
    layer = "成长拓展层"
    role = "讲座、竞赛、社团活动的高价值筛选与提醒"
    description = "聚合讲座、比赛、社团活动信息，根据学生画像精准推送「高价值」活动，拒绝信息过载。"
    capabilities = ["活动价值评分", "画像匹配推荐", "时间线与截止提醒", "信息降噪"]
    keywords = ["活动", "讲座", "比赛", "竞赛", "大赛", "社团", "互联网+", "挑战杯", "报名", "截止", "创新大赛"]
    kb_files = ["events.txt"]

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        items = parse_struct_hits(hits)
        p = ctx.profile
        now = datetime.now()
        clue = task + " " + " ".join(p.interests) + " " + (p.goal or "")

        def score(it: dict) -> int:
            blob = it["raw"]
            kw = sum(1 for k in ("竞赛", "大赛", "实习", "保研", "综测", "奖学金", "科研", "创业", "讲座") if k in clue and k in blob)
            interest = sum(1 for i in p.interests if i and i in blob)
            return kw * 2 + interest

        ranked = sorted(items, key=score, reverse=True)
        top, rest = ranked[:3], ranked[3:]

        parts = ["### 高价值活动推荐（按你的画像排序）", ""]
        for i, it in enumerate(top, 1):
            badge = "（与画像高匹配）" if score(it) >= 3 else ""
            parts.append(f"**Top{i} · {it['title']}**{badge}")
            for label, keys in (("类型", ("类型",)), ("时间", ("时间", "时间线")), ("适合谁", ("适合", "适合人群")), ("核心价值", ("价值", "亮点")), ("报名方式", ("报名", "入口"))):
                v = get_field(it, *keys)
                if v:
                    parts.append(f"- **{label}**：{v}")
            parts.append("")

        if rest:
            parts += ["| 其他值得关注 | 类型 | 时间 |", "| --- | --- | --- |"]
            for it in rest[:5]:
                parts.append(f"| {it['title']} | {get_field(it, '类型') or '—'} | {get_field(it, '时间', '时间线') or '—'} |")
            parts.append("")

        parts += [
            f"### 时间提醒（当前为 {now.year} 年 {now.month} 月 · {_stage_hint(now.month)}）",
            "",
        ]
        for it in items:
            timeline = get_field(it, "时间线", "截止", "时间")
            if timeline and any(k in it["raw"] for k in ("大赛", "竞赛", "比赛")):
                parts.append(f"- **{it['title']}**：{timeline}")
        parts += [
            "- 建议：把关键截止日写进日历并设置「提前 3 天」提醒，避免临时抱佛脚；",
            "- 拒绝过载：每学期主线活动不超过 2 个，其余做「围观者」即可。",
        ]
        return "\n".join(parts)
