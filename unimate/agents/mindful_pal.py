"""成长拓展层 · 心理陪伴伙伴 MindfulPal：情绪倾听 + CBT 引导 + 危机信号转介。"""
from __future__ import annotations

from typing import List

from core.agent_base import BaseAgent, AgentResult, RunContext
from core.rag import KBHit

CRISIS_WORDS = ("自杀", "轻生", "不想活", "活不下去", "了结", "伤害自己", "自残")

CRISIS_BANNER = (
    "> **请立即寻求现实中的帮助**\n>\n"
    "> - 联系辅导员或学校 24 小时心理援助电话，或直接前往校医院；\n"
    "> - 全国统一心理援助热线：**12356**（24 小时）；\n"
    "> - 如有紧迫的人身危险，请立即拨打 **110 / 120**。\n>\n"
    "> 你并不孤单，寻求帮助是勇敢且有效的。"
)

SYSTEM_EXTRA = (
    "\n特别协议：\n"
    "1. 你不是医生，不做任何诊断，不给用药建议；\n"
    "2. 用户出现自伤、自杀等危机信号时，第一步永远是温和而明确地引导其联系现实中的专业帮助"
    "（校心理中心、辅导员、全国心理援助热线 12356，紧急情况 110/120），不得替代专业干预；\n"
    "3. 采用倾听-共情-引导的语气，先接纳情绪，再给可执行的小步骤。"
)


class MindfulPalAgent(BaseAgent):
    id = "mindful_pal"
    name = "心理陪伴伙伴"
    en_name = "MindfulPal"
    layer = "成长拓展层"
    role = "情绪倾听与认知调适陪伴"
    description = "提供 7x24 小时情绪倾听，进行简单的 CBT（认知行为疗法）对话引导，识别危机信号并转接人工心理中心。"
    capabilities = ["情绪倾听与命名", "CBT 四步自助引导", "身心平静技巧", "危机识别与转介"]
    keywords = ["焦虑", "压力", "emo", "失眠", "迷茫", "孤独", "情绪", "紧张", "内耗", "心态", "不开心", "抑郁", "崩溃", "自卑", "烦躁"]
    kb_files = ["wellness.txt"]

    def system_prompt(self, profile) -> str:
        return super().system_prompt(profile) + SYSTEM_EXTRA

    def run(self, task: str, ctx: RunContext) -> AgentResult:
        res = super().run(task, ctx)
        if any(w in task for w in CRISIS_WORDS):
            res.content = CRISIS_BANNER + "\n\n" + res.content
            res.note = "已触发危机转介协议"
        return res

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        emotion = next((w for w in ("焦虑", "压力", "失眠", "迷茫", "孤独", "内耗", "抑郁", "崩溃", "自卑", "紧张", "不开心", "emo", "烦躁") if w in task), "低落")
        p = ctx.profile

        return (
            f"谢谢你愿意说出来。听起来你现在被「{emotion}」的感觉裹住了——这种感受是真实的，也不代表你脆弱。"
            f"先深呼吸一下，我们慢慢来。\n\n"
            "### 此刻可以先做（2 分钟）\n\n"
            "- **4-7-8 呼吸**：吸气 4 秒 → 屏息 7 秒 → 缓慢呼气 8 秒，重复 4 轮；\n"
            "- **5-4-3-2-1 着地**：说出你看到的 5 样东西、听到的 4 种声音、能摸到的 3 样物品、"
            "能闻到的 2 种气味、尝到的 1 种味道，把注意力拉回当下。\n\n"
            "### CBT 自助四步（想到什么就写什么，不用写得好看）\n\n"
            "| 步骤 | 引导提问 | 你的记录 |\n| --- | --- | --- |\n"
            f"| 1. 情境 | 刚刚发生了什么？（只陈述事实） | _ |\n"
            f"| 2. 自动想法 | 脑海里冒出的第一句话是什么？ | _ |\n"
            f"| 3. 证据检验 | 支持 / 反对这个想法的证据各有哪些？有没有别的解释？ | _ |\n"
            f"| 4. 替代想法 | 如果是好朋友遇到同样的事，你会对 TA 说什么？ | _ |\n\n"
            f"很多同学在「{emotion}」时会把单次挫折放大成「我不行」。试着把「我完了」改成具体句式："
            "「我在 ___ 上暂时没做好，因为 ___，我可以先尝试 ___。」\n\n"
            "### 本周微小行动（选一个就好）\n\n"
            "1. 固定一个「睡眠锚点」：比今天提前 30 分钟放下手机；\n"
            "2. 每天午后 15 分钟散步（阳光 + 步行是性价比最高的情绪调节剂）；\n"
            "3. 跟一位信任的人（朋友 / 家人 / 辅导员）说一件今天的小事。\n\n"
            "### 什么时候需要专业帮助\n\n"
            f"如果「{emotion}」持续两周以上，已经影响上课、饮食或睡眠，请让学校心理中心的老师陪你一起梳理——"
            "预约是免费且保密的。也可拨打全国心理援助热线 **12356**（24 小时）。\n\n"
            f"> {p.name}，我一直在。你愿意多讲一点「最近具体发生了什么」吗？我会认真听。"
        )
