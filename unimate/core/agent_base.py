"""智能体基类：统一的运行时上下文、LLM/本地双通道执行、结构化语料解析工具。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from core.llm import LLMClient
from core.memory import StudentProfile
from core.rag import KBHit, KnowledgeBase


@dataclass
class RunContext:
    profile: StudentProfile
    kb: Optional[KnowledgeBase]
    llm: Optional[LLMClient]
    history: List[dict] = field(default_factory=list)


@dataclass
class AgentResult:
    agent_id: str
    agent_name: str
    layer: str
    title: str
    content: str
    refs: List[str] = field(default_factory=list)
    status: str = "ok"  # ok=LLM生成 / mock=本地推理 / fallback=LLM失败回退
    note: str = ""
    elapsed: float = 0.0

    @property
    def status_label(self) -> str:
        return {"ok": "LLM 生成", "mock": "本地推理", "fallback": "回退本地"}.get(self.status, self.status)

    def as_trace(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.agent_name,
            "layer": self.layer,
            "title": self.title,
            "status": self.status,
            "status_label": self.status_label,
            "elapsed": self.elapsed,
            "content": self.content,
            "refs": self.refs,
            "note": self.note,
        }


class BaseAgent:
    """全部 12 个专家智能体的公共父类：声明元信息 + system prompt + run 双通道。"""

    id: str = "base"
    name: str = "未命名智能体"
    en_name: str = ""
    layer: str = ""
    role: str = ""
    description: str = ""
    capabilities: List[str] = []
    keywords: List[str] = []      # 供 UniBrain 离线模式做意图路由
    kb_files: List[str] = []      # 该智能体专属的知识库范围

    def system_prompt(self, profile: StudentProfile) -> str:
        caps = "、".join(self.capabilities)
        return (
            f"你是「UniMate Hub 大学生学业与职业发展智能体空间」中的专家智能体：{self.name}（{self.en_name}），"
            f"隶属于{self.layer}，专职负责：{self.role}。核心能力：{caps}。\n"
            "工作准则：\n"
            "1. 结合学生画像给出个性化建议，避免泛泛而谈；\n"
            "2. 充分利用提供的知识库资料，引用时注明资料名称；\n"
            "3. 输出使用结构化 Markdown（小标题、表格、清单），中文回复，篇幅 300~600 字；\n"
            "4. 只做辅助与引导，不代替学生完成作业、论文或人生决定；\n"
            "5. 你的输出会与其他智能体的结论一起汇总给用户，请聚焦自身职责范围。"
        )

    def run(self, task: str, ctx: RunContext) -> AgentResult:
        hits: List[KBHit] = []
        if ctx.kb is not None and self.kb_files:
            try:
                hits = ctx.kb.search(task, k=3, scope=self.kb_files)
            except Exception:
                hits = []
        ref_block = "\n\n".join(f"【{h.title}】\n{h.text}" for h in hits)
        refs = [f"{h.title}（{h.file}）" for h in hits]
        user_prompt = (
            f"【学生画像】{ctx.profile.summary()}\n\n"
            f"【知识库检索资料】\n{ref_block if ref_block else '（未命中相关资料）'}\n\n"
            f"【本次任务】\n{task}"
        )
        status, note, content = "ok", "", ""
        if ctx.llm is not None and ctx.llm.available:
            try:
                content = ctx.llm.chat(self.system_prompt(ctx.profile), user_prompt, history=ctx.history[-6:])
            except Exception as exc:  # 网络异常/额度不足等，回退本地引擎，保证空间永不宕机
                status, note = "fallback", f"LLM 调用失败，已回退本地推理：{type(exc).__name__}"
        if not content:
            if status == "ok":
                status = "mock"
            content = self.mock(task, ctx, hits).strip()
        return AgentResult(self.id, self.name, self.layer, self._title(task), content, refs, status, note)

    def _title(self, task: str) -> str:
        clean = re.sub(r"\s+", " ", task).strip()
        return clean[:18] + ("…" if len(clean) > 18 else "")

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        """离线演示模式下的本地规则引擎，由各子类按专业领域覆写。"""
        return (
            f"已接收任务：{task[:80]}\n\n当前为离线演示模式。本智能体（{self.name}）的专属本地"
            "推理引擎未覆盖该输入，请在侧边栏配置大模型 API Key 获得完整体验。"
        )


# ---------- 结构化语料解析工具（供各智能体复用） ----------

def parse_struct_hits(hits: List[KBHit]) -> List[dict]:
    """把知识库中「【标题】k1:v1 | k2:v2」格式的语料解析为字典列表。"""
    items: List[dict] = []
    for h in hits:
        for block in re.split(r"\n(?=【)", h.text):
            m = re.match(r"【(.+?)】\s*(.*)", block.strip(), re.S)
            if not m:
                continue
            title, body = m.group(1).strip(), m.group(2).strip()
            fields: dict = {}
            extras: List[str] = []
            for part in re.split(r"[|｜]", body):
                part = part.strip()
                if not part:
                    continue
                kv = re.split(r"[:：]", part, maxsplit=1)
                if len(kv) == 2 and kv[0].strip():
                    fields[kv[0].strip()] = kv[1].strip()
                else:
                    extras.append(part)
            if extras:
                fields["补充"] = "；".join(extras)
            items.append({"title": title, "fields": fields, "raw": block.strip()})
    return items


def get_field(item: dict, *keys: str) -> str:
    for k in keys:
        v = item["fields"].get(k)
        if v:
            return v
    return ""
