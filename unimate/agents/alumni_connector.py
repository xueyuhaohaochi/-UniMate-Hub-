"""成长拓展层 · 校友联络官 AlumniConnector：校友案例匹配 + 联络话术 + 访谈提问清单。"""
from __future__ import annotations

from typing import List

from core.agent_base import BaseAgent, RunContext, get_field, parse_struct_hits
from core.rag import KBHit


class AlumniConnectorAgent(BaseAgent):
    id = "alumni_connector"
    name = "校友联络官"
    en_name = "AlumniConnector"
    layer = "成长拓展层"
    role = "校友案例匹配与职场视角引入"
    description = "根据学生意向行业，匹配已毕业的校友案例或访谈记录，提供真实的职场视角。"
    capabilities = ["校友案例匹配", "成长路径还原", "咖啡 chat 话术", "访谈提问清单"]
    keywords = ["校友", "学长", "学姐", "毕业生", "前辈", "行业内幕", "职场", "内推", "过来人", "真实案例"]
    kb_files = ["alumni.txt"]

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        items = parse_struct_hits(hits)
        p = ctx.profile

        clue = task + " " + " ".join(p.interests) + " " + (p.goal or "")

        def score(it: dict) -> int:
            blob = it["title"] + get_field(it, "行业", "方向")
            return sum(1 for k in ("互联网", "技术", "金融", "教育", "公务员", "创业", "产品", "算法", "数据", "考研", "留学", "体制") if k in clue and k in blob)

        items = sorted(items, key=score, reverse=True)

        parts = ["### 与你意向匹配的校友案例", ""]
        if items:
            for it in items[:3]:
                parts.append(f"#### {it['title']}")
                industry = get_field(it, "行业", "方向")
                path = get_field(it, "路径", "经历")
                key_node = get_field(it, "关键节点", "转折")
                advice = get_field(it, "建议", "给学弟学妹")
                if industry:
                    parts.append(f"- **所在行业**：{industry}")
                if path:
                    parts.append(f"- **成长路径**：{path}")
                if key_node:
                    parts.append(f"- **关键转折**：{key_node}")
                if advice:
                    parts.append(f"- **TA 的建议**：{advice}")
                parts.append("")
        else:
            parts += ["暂未命中校友数据，请告诉我你的意向行业（如：互联网产品 / 券商行研 / 选调生）。", ""]

        parts += [
            "### 从案例中提炼的三条共性规律",
            "",
            "1. **实习前置**：大二末 ~ 大三上完成第一段实习的人，校招明显更从容；",
            "2. **作品沉淀**：把课程作业 / 竞赛成果整理成可展示的作品集，面试复用率极高；",
            "3. **信息与人脉主动经营**：关键机会几乎都来自「提前认识的人」，而非临时刷招聘软件。",
            "",
            "### 咖啡 chat 邀约模板（成功率最高的写法）",
            "",
            "> 学姐您好！我是咱们学院 X 专业 X 年级的 XXX。看了您从 XX 到 XX 的经历，特别受启发。"
            "我目前在准备 XX 方向，想请教您 2 个具体问题（约 15 分钟，线上即可）。请问您本周什么时间方便？",
            "",
            "### 访谈提问清单（挑 3 个就够）",
            "",
            "1. 入行以来最意外的一件事是什么？",
            "2. 如果重来一次，您会调整哪一步？",
            "3. 初级岗位真正看重什么？（去掉 JD 里的套话之后）",
            "4. 这个行业 3 年内最大的变数是什么？",
            "5. 以我现在的情况，接下来 3 个月做什么性价比最高？",
            "",
            f"> 已按你的意向（{'、'.join(p.interests) or '未填写'}）排序。访谈后把笔记发给我，我可以帮你把信息转化为行动计划。",
        ]
        return "\n".join(parts)
