"""UniBrain：UniMate 空间调度中枢。

职责：意图识别 → 任务分解 → 智能体编排执行 → 结论汇总。
支持三种调度通道：@指定直连 / LLM 规划（在线）/ 关键词规则规划（离线演示）。
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from core.agent_base import AgentResult, BaseAgent, RunContext
from core.llm import LLMClient
from core.memory import StudentProfile
from core.rag import KnowledgeBase

CHITCHAT_REPLY = (
    "你好，我是 UniMate Hub 的调度中枢 **UniBrain**。\n\n"
    "本空间聚集了 12 位覆盖大学全周期的专家智能体：\n\n"
    "- **基础服务层**：选课规划师、学术资源导航员、备考教练、生活事务管家\n"
    "- **专业指导层**：科研启蒙导师、代码审查专家、论文写作顾问\n"
    "- **成长拓展层**：职业生涯规划师、技能树构建师、心理陪伴伙伴、校友联络官、校园活动雷达\n\n"
    "你可以这样使用本空间：\n"
    "1. 直接描述需求，我会自动分解任务，编排合适的智能体协作完成；\n"
    "2. 使用「@智能体名 + 内容」与某位专家点对点交流；\n"
    "3. 在左侧侧边栏完善学生画像，让全体智能体的建议更个性化。\n\n"
    "试试告诉我：「我想参加互联网+大赛，但还没组队，也不知道怎么写商业计划书。」"
)


@dataclass
class PlanStep:
    agent_id: str
    goal: str


@dataclass
class Plan:
    mode: str = "single"  # single / collab / direct / chitchat
    reason: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    intro: str = ""       # chitchat 模式下由 UniBrain 直接应答

    @property
    def mode_label(self) -> str:
        return {
            "single": "单智能体执行",
            "collab": "多智能体协作",
            "direct": "指定智能体对话",
            "chitchat": "空间导览",
        }.get(self.mode, self.mode)


class UniBrain:
    def __init__(self, agents: List[BaseAgent]):
        self.agents: Dict[str, BaseAgent] = {a.id: a for a in agents}
        self.order: List[str] = [a.id for a in agents]
        self.catalog = "\n".join(
            f"- {a.id}｜{a.name}｜职责：{a.role}｜线索词：{'/'.join(a.keywords[:8])}"
            for a in agents
        )

    # ---------------- 意图识别与任务分解 ----------------

    def plan(self, user_msg: str, profile: StudentProfile,
             llm: Optional[LLMClient] = None, history: Optional[List[dict]] = None) -> Plan:
        direct = self._match_direct(user_msg)
        if direct:
            return direct
        if llm is not None and llm.available:
            try:
                return self._llm_plan(user_msg, profile, llm, history or [])
            except Exception:
                pass  # LLM 规划失败时静默降级到规则规划
        return self.keyword_plan(user_msg)

    def _match_direct(self, user_msg: str) -> Optional[Plan]:
        m = re.match(r"^\s*@(?P<name>\S+)(?:\s+(?P<rest>.+))?$", user_msg, re.S)
        if not m:
            return None
        token = m.group("name").strip()
        rest = (m.group("rest") or "").strip()
        for agent in self.agents.values():
            if token in (agent.id, agent.name, agent.en_name) or token in agent.name or token in agent.en_name:
                goal = rest or "请针对用户的完整消息给出你的专业建议"
                return Plan("direct", f"用户指定与 {agent.name} 对话", [PlanStep(agent.id, goal)])
        return None

    def _llm_plan(self, user_msg: str, profile: StudentProfile,
                  llm: LLMClient, history: List[dict]) -> Plan:
        system = (
            "你是「UniMate Hub 大学生学业与职业发展智能体空间」的调度中枢 UniBrain。"
            "你的职责是理解大学生用户的真实需求，从下列智能体目录中选择合适的执行者并分解任务。\n\n"
            f"可用智能体目录：\n{self.catalog}\n\n"
            "调度规则：\n"
            "1. 单一明确的需求 → mode=single，只选 1 个最合适的智能体；\n"
            "2. 复合型需求（如学科竞赛、升学、就业等跨领域目标）→ mode=collab，选 2~6 个智能体，"
            "按合理执行顺序排列（先信息核实，再分析定位，后规划落地）；\n"
            "3. 问候、寒暄或与学业/职业发展无关 → mode=chitchat，steps 为空数组；\n"
            "4. 每步 goal 必须具体，说明该智能体本次要产出什么。\n"
            "只输出 JSON，不要输出任何其他文字：\n"
            '{"mode": "single|collab|chitchat", "reason": "一句话调度理由", '
            '"steps": [{"agent": "智能体id", "goal": "该步目标"}]}'
        )
        user = f"学生画像：{profile.summary()}\n用户消息：{user_msg}"
        raw = llm.chat(system, user, history=history[-4:], temperature=0.2, max_tokens=600)
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            raise ValueError("LLM 未返回 JSON")
        data = json.loads(m.group(0))
        mode = str(data.get("mode", "single")).strip()
        steps: List[PlanStep] = []
        for s in (data.get("steps") or [])[:6]:
            aid = str(s.get("agent", "")).strip()
            if aid in self.agents:
                goal = str(s.get("goal", "")).strip() or self.agents[aid].role
                steps.append(PlanStep(aid, goal))
        if mode == "chitchat":
            return Plan("chitchat", str(data.get("reason", "")).strip(), [], CHITCHAT_REPLY)
        if not steps:
            raise ValueError("步骤为空")
        return Plan(mode if mode in ("single", "collab") else "collab",
                    str(data.get("reason", "")).strip(), steps)

    def keyword_plan(self, user_msg: str) -> Plan:
        """离线演示模式：关键词命中 + 协作增强规则。"""
        text = user_msg.lower()
        matched: Dict[str, List[str]] = {}
        for aid, agent in self.agents.items():
            kws = [k for k in agent.keywords if k.lower() in text]
            if kws:
                matched[aid] = kws
        if not matched:
            return Plan("chitchat", "未识别到具体学业或发展需求，UniBrain 直接导览", [], CHITCHAT_REPLY)

        picked = sorted(matched, key=lambda aid: (-len(matched[aid]), self.order.index(aid)))[:6]
        # 空间级协作增强：明确的参赛/备赛意图时，补充经验与执行维度
        contest_intent = any(k in user_msg for k in ("参加", "参赛", "组队", "备赛", "拿奖", "夺奖", "路演"))
        if "event_scout" in picked and contest_intent and len(picked) >= 2:
            for extra, goal in (
                ("alumni_connector", "调取往届参赛/获奖团队与相关校友案例，提供真实经验参考"),
                ("skill_builder", "把备赛过程拆解为阶段目标与每日可执行的微任务"),
            ):
                if extra not in picked:
                    picked.append(extra)
        picked = picked[:6]
        # 行政事务场景（报销/经费/流程）即使提到“竞赛”，也归属生活事务管家单独处理
        if "life_admin_bot" in picked and "event_scout" in picked and not contest_intent:
            picked.remove("event_scout")
        picked.sort(key=lambda aid: self.order.index(aid))  # 按层级行进：信息 → 分析 → 规划
        # 信息核实类智能体（活动雷达）优先执行，为后续分析提供时间线依据
        if "event_scout" in picked and len(picked) > 1:
            picked.remove("event_scout")
            picked.insert(0, "event_scout")

        steps = [PlanStep(aid, self._goal_for(aid, matched.get(aid))) for aid in picked]
        mode = "collab" if len(steps) > 1 else "single"
        reason = "；".join(
            f"{self.agents[aid].name}（线索：{'、'.join(matched.get(aid, ['协作规则'])[:3])}）" for aid in picked
        )
        return Plan(mode, reason, steps)

    def direct_plan(self, agent_id: str, user_msg: str) -> Plan:
        """@指定智能体的点对点对话计划。"""
        agent = self.agents[agent_id]
        return Plan("direct", f"用户指定与 {agent.name} 对话",
                    [PlanStep(agent.id, "请针对用户的完整消息给出你的专业建议")])

    def _goal_for(self, aid: str, kws: Optional[List[str]]) -> str:
        agent = self.agents[aid]
        clue = "、".join((kws or [])[:3]) or "上下文"
        return f"围绕用户需求中与「{clue}」相关的部分，以{agent.role}的专业视角产出可执行结论"

    # ---------------- 编排执行与汇总 ----------------

    def execute(
        self,
        plan: Plan,
        user_msg: str,
        profile: StudentProfile,
        kb: Optional[KnowledgeBase],
        llm: Optional[LLMClient],
        history: Optional[List[dict]] = None,
        on_step: Optional[Callable[[int, AgentResult], None]] = None,
    ):
        if plan.mode == "chitchat":
            return plan.intro, {"mode": "chitchat", "mode_label": plan.mode_label,
                                "reason": plan.reason, "steps": []}, []

        results: List[AgentResult] = []
        prev_summary = ""
        for i, step in enumerate(plan.steps):
            agent = self.agents[step.agent_id]
            task = f"用户原始需求：{user_msg}\n你的分工：{step.goal}"
            if prev_summary:
                task += f"\n前序智能体已产出（供衔接，勿重复）：\n{prev_summary}"
            t0 = time.time()
            res = agent.run(task, RunContext(profile, kb, llm, history or []))
            res.elapsed = round(time.time() - t0, 1)
            results.append(res)
            prev_summary += f"- {res.agent_name}：{res.title}\n"
            if on_step:
                on_step(i, res)

        final = self._synthesize(plan, user_msg, results, llm)
        trace = {
            "mode": plan.mode,
            "mode_label": plan.mode_label,
            "reason": plan.reason,
            "steps": [r.as_trace() for r in results],
        }
        return final, trace, results

    def _synthesize(self, plan: Plan, user_msg: str,
                    results: List[AgentResult], llm: Optional[LLMClient]) -> str:
        if plan.mode in ("single", "direct"):
            r = results[0]
            refs = f"\n\n---\n*参考资料：{'；'.join(r.refs)}*" if r.refs else ""
            return r.content + refs

        # 多智能体协作：优先用 LLM 融合，失败则用模板拼装
        if llm is not None and llm.available:
            try:
                materials = "\n\n".join(f"## 来自 {r.agent_name} 的结论\n{r.content}" for r in results)
                merged = llm.chat(
                    "你是 UniMate 空间的汇总官。把多个智能体的输出整合为一份连贯、不重复的最终答复："
                    "开头 1~2 句总述协作结论；正文按主题合并要点，保留具体可执行的内容与表格；"
                    "结尾给出「下一步行动」清单（3~5 条）。中文 Markdown，不超过 900 字。",
                    f"用户需求：{user_msg}\n\n{materials}",
                    temperature=0.4,
                    max_tokens=1400,
                )
                if merged:
                    return merged
            except Exception:
                pass

        header = plan.reason or f"已为你的需求安排 {len(results)} 位智能体协同完成"
        body = "\n\n".join(
            f"### {i + 1}. {r.agent_name}｜{r.title}\n\n{r.content}" for i, r in enumerate(results)
        )
        ending = (
            "### 下一步行动\n\n"
            "1. 从排期最靠前的一项开始执行（建议今天就完成第一个小动作）；\n"
            "2. 取得新进展后回到本空间同步信息，我会动态调整后续规划；\n"
            "3. 如需深入某一部分，使用「@智能体名 + 问题」与对应专家单独沟通。"
        )
        return f"针对你的需求「{user_msg[:40]}」，UniBrain 编排了 {len(results)} 位智能体协作完成。{header}\n\n{body}\n\n{ending}"
