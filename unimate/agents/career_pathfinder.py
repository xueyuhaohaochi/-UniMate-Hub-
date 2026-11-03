"""成长拓展层 · 职业生涯规划师 CareerPathfinder：简历对标 JD + 技能差距 + 模拟面试。"""
from __future__ import annotations

import re
from typing import List

from core.agent_base import BaseAgent, RunContext, get_field, parse_struct_hits
from core.rag import KBHit


def _split_skills(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"[,，、/;；\s]+", text or "") if s.strip()]


class CareerPathfinderAgent(BaseAgent):
    id = "career_pathfinder"
    name = "职业生涯规划师"
    en_name = "CareerPathfinder"
    layer = "成长拓展层"
    role = "职业定位、技能差距分析与求职准备"
    description = "分析学生简历，对比目标岗位 JD 指出技能差距，推荐实习机会，模拟 HR 面试。"
    capabilities = ["简历 vs JD 对标", "技能差距矩阵", "实习机会匹配", "HR 模拟面试"]
    keywords = ["实习", "求职", "简历", "面试", "岗位", "JD", "秋招", "春招", "校招", "职业", "就业",
                "组队", "角色", "考研", "保研", "升学", "留学", "offer", "研究生"]
    kb_files = ["careers.txt"]

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        items = parse_struct_hits(hits)
        p = ctx.profile
        parts: List[str] = []
        have = {s["name"].lower(): s["level"] for s in p.skills}
        have_pairs = [(s["name"], s["level"]) for s in p.skills]

        # 岗位匹配：任务词与岗位标题/技能重合度
        def match_score(it: dict) -> int:
            blob = it["title"] + get_field(it, "硬技能") + get_field(it, "类型")
            return sum(1 for k in _split_skills(task) if k and k in blob)

        items = sorted(items, key=match_score, reverse=True) or items
        target = items[0] if items else None

        if target:
            parts += [f"### 对标岗位：{target['title']}", ""]
            for label, key in (("类型", "类型"), ("学历要求", "学历"), ("薪资参考", "薪资"), ("重点关注", "重点关注")):
                v = get_field(target, key, label)
                if v:
                    parts.append(f"- **{label}**：{v}")
            parts.append("")

            # 技能差距矩阵
            required = _split_skills(get_field(target, "硬技能")) + _split_skills(get_field(target, "加分"))
            parts += ["### 技能差距矩阵", "", "| 要求 | 状态 | 行动建议 |", "| --- | --- | --- |"]
            for r in required[:10]:
                rl = r.lower()
                hit_name, lvl = None, 0
                for name, level in have.items():
                    if rl in name.lower() or name.lower() in rl:
                        hit_name, lvl = name, level
                        break
                if hit_name and lvl >= 4:
                    parts.append(f"| {r} | 已具备(Lv{lvl}) | 写进简历并准备一个项目佐证 |")
                elif hit_name:
                    parts.append(f"| {r} | 需提升(Lv{lvl}) | 2 周内做一个该方向小项目并记录过程 |")
                else:
                    parts.append(f"| {r} | 缺失 | 列入 30 天速成清单：官方入门教程 + 一个练手 Demo |")
            parts.append("")

        parts += [
            "### 简历优化四要点",
            "",
            "- **STAR 量化**：每条经历按「背景-任务-动作-量化结果」改写，结果带数字；",
            "- **关键词对齐**：把 JD 中的硬技能词自然嵌入项目描述（机筛通过率 +40%）；",
            "- **项目深挖**：1 个讲得深的项目 > 3 个浅尝辄止的项目，准备 3 分钟版本与 30 秒版本；",
            "- **一页原则**：本科生一页以内，教育经历放顶部（校招场景）。",
            "",
            "### HR 模拟面试题（先自答，再让我点评）",
            "",
            "1. 用 90 秒做一次自我介绍（结构：身份 → 匹配点 → 证据 → 意愿）；",
            "2. 讲一个你最有挑战的项目：最大困难是什么，你如何定位并解决？",
            "3. 你认为这个岗位最需要的三种能力，你如何证明自己具备？",
            "4. 未来三年的职业规划是什么？（考察稳定性与自我认知）",
            "5. 你有什么想问我们的？（考察信息搜集深度，禁止问薪资以外零问题）",
        ]

        if any(k in task for k in ("组队", "队友", "团队")):
            tech = any(lvl >= 4 for name, lvl in have_pairs if any(t in name.lower() for t in ("python", "java", "c/", "开发", "机器学习", "数据")))
            parts += [
                "",
                "### 竞赛组队角色定位",
                "",
                f"- 建议角色：**{'技术负责人' if tech else '产品 / 市场负责人'}**"
                f"（依据画像技能：{'、'.join(f'{n}(Lv{l})' for n, l in have_pairs[:4]) or '待完善'}）；",
                "- 理想团队配置：技术 ×2 + 产品 / 设计 ×1 + 市场路演 ×1，跨专业组队评审加分；",
                "- 招募话术：「我在做 XX 赛道的互联网+项目，已有 X 人，缺 XX 角色，预期 X 个月投入，获奖后综测/保研加分，欢迎聊聊。」",
            ]

        parts += [
            "",
            f"> 已结合你的画像（{p.major} · {p.grade}）。把 JD 全文或简历粘给我，可做逐条逐句对标。",
        ]
        return "\n".join(parts)
