"""基础服务层 · 生活事务管家 LifeAdminBot：报销 / 报修 / 奖学金等行政事务指引。"""
from __future__ import annotations

from typing import List

from core.agent_base import BaseAgent, RunContext, get_field, parse_struct_hits
from core.rag import KBHit


class LifeAdminBotAgent(BaseAgent):
    id = "life_admin_bot"
    name = "生活事务管家"
    en_name = "LifeAdminBot"
    layer = "基础服务层"
    role = "校园行政与生活事务指引"
    description = "处理报销流程咨询、宿舍报修指引、奖学金申请时间节点提醒等行政琐事，一站式给出办理路径。"
    capabilities = ["报销流程指引", "宿舍报修通道", "奖助学金节点提醒", "证明开具导航"]
    keywords = ["报销", "报修", "宿舍", "奖学金", "助学金", "请假", "教务", "证明", "学生证", "医保", "补贴", "落户"]
    kb_files = ["admin.txt"]

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        items = parse_struct_hits(hits)
        p = ctx.profile
        if not items:
            return (
                "为了给你精准的办理路径，请补充事项类型，例如：\n"
                "- 差旅 / 竞赛经费报销；\n- 宿舍水电或设施报修；\n- 奖学金 / 助学金申请；\n- 在读证明 / 成绩单开具。"
            )

        parts = ["### 办事指引", ""]
        for it in items[:3]:
            path = get_field(it, "路径", "地点", "入口")
            material = get_field(it, "材料", "所需材料")
            limit = get_field(it, "时限", "时间", "节点")
            parts.append(f"#### {it['title']}")
            if path:
                parts.append(f"- **办理路径**：{path}")
            if material:
                parts.append(f"- **所需材料**：{material}")
            if limit:
                parts.append(f"- **关键时限**：{limit}")
            extra = it["fields"].get("补充", "")
            if extra:
                steps = [s.strip("；;。 ") for s in extra.split("；") if s.strip("；;。 ")]
                for i, s in enumerate(steps, 1):
                    parts.append(f"- **步骤 {i}**：{s}")
            parts.append("")

        parts += [
            "### 通用提醒",
            "",
            "- 材料统一多备 2 份复印件 + 电子扫描件（PDF 命名：事项_姓名_学号）；",
            "- 截止日前 3 个工作日提交，预留打回补正时间；",
            "- 线上事项统一从学校信息门户进入，谨防钓鱼链接；",
            "- 遇到推诿时，先找辅导员书面说明情况，再走教务 / 后勤对应窗口。",
            "",
            f"> 已按你的身份（{p.major} · {p.grade}）过滤流程。其余事项可直接说「@生活事务管家 + 事项名」。",
        ]
        return "\n".join(parts)
