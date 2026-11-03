"""UniMate Hub —— 大学生学业与职业发展多智能体协作空间（Streamlit 前端）。

运行：streamlit run app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config import (
    COMMON_SKILLS, DATA_DIR, GRADES, INTEREST_TAGS, LLM_API_KEY, LLM_BASE_URL,
    LLM_MODEL, LLM_TEMPERATURE, MAJORS, PROVIDER_PRESETS, SPACE_DESC, SPACE_NAME,
)
from core.agent_base import RunContext  # noqa: F401
from core.llm import LLMClient
from core.memory import StudentProfile, load_profile, save_profile
from core.orchestrator import UniBrain
from core.rag import KnowledgeBase
from agents import LAYER_DESC, build_agents

st.set_page_config(page_title=SPACE_NAME, page_icon=None, layout="wide",
                   initial_sidebar_state="expanded")

EXAMPLES = [
    "我想参加互联网+大赛，但还没组队，也不知道怎么写商业计划书",
    "我想申请计算机系的研究生，现在该做什么准备？",
    "下学期课表怎么选？给分好的课有哪些？",
    "最近备考数据结构，帮我制定复习计划",
    "帮我找深度学习在医疗影像方向的最新综述",
    "最近压力大睡不好，总是焦虑内耗",
]

WELCOME = (
    "欢迎来到 **UniMate Hub** —— 大学生学业与职业发展多智能体协作空间。\n\n"
    "这不是一个单一的聊天机器人，而是由 **UniBrain 调度中枢 + 12 位领域专家智能体** 组成的虚拟导师团队：\n\n"
    "| 层级 | 成员 |\n| --- | --- |\n"
    "| 基础服务层 | 选课规划师 · 学术资源导航员 · 备考教练 · 生活事务管家 |\n"
    "| 专业指导层 | 科研启蒙导师 · 代码审查专家 · 论文写作顾问 |\n"
    "| 成长拓展层 | 职业生涯规划师 · 技能树构建师 · 心理陪伴伙伴 · 校友联络官 · 校园活动雷达 |\n\n"
    "**使用方式**\n"
    "1. 直接描述需求，UniBrain 自动分解任务并编排智能体协作；\n"
    "2. 「@智能体名 + 内容」与某位专家点对点交流；\n"
    "3. 在左侧边栏完善学生画像，全体智能体的建议将随画像个性化。\n\n"
    "试试下方示例，或直接说出你的困惑。"
)


# ---------------- 资源与状态 ----------------

@st.cache_resource
def get_kb() -> KnowledgeBase:
    return KnowledgeBase(ROOT / "knowledge")


@st.cache_resource
def get_agents():
    return build_agents()


def get_brain() -> UniBrain:
    return UniBrain(get_agents())


def get_agent_map():
    return {a.id: a for a in get_agents()}


def get_llm():
    key = st.session_state.get("api_key", "").strip()
    if not key:
        return None
    return LLMClient(key, st.session_state.get("base_url", ""), st.session_state.get("model", "qwen-plus"),
                     float(st.session_state.get("temperature", 0.6)))


ss = st.session_state
ss.setdefault("messages", [{"role": "assistant", "content": WELCOME}])
ss.setdefault("direct_agent", None)
ss.setdefault("api_key", LLM_API_KEY)
ss.setdefault("base_url", LLM_BASE_URL)
ss.setdefault("model", LLM_MODEL)
ss.setdefault("temperature", LLM_TEMPERATURE)
ss.setdefault("profile", load_profile(DATA_DIR / "profile.json"))


# ---------------- 对话处理 ----------------

def handle_prompt(text: str) -> None:
    text = (text or "").strip()
    if not text:
        return
    ss["messages"].append({"role": "user", "content": text})
    profile: StudentProfile = ss["profile"]
    llm = get_llm()
    brain = get_brain()
    history = [{"role": m["role"], "content": m["content"]} for m in ss["messages"][:-1]]

    with st.chat_message("user"):
        st.markdown(text)
    with st.chat_message("assistant"):
        with st.status("UniBrain 调度中", expanded=True) as status:
            st.write(f"**需求**：{text}")
            direct_id = ss.get("direct_agent")
            if direct_id:
                plan = brain.direct_plan(direct_id, text)
            else:
                plan = brain.plan(text, profile, llm, history)
            if plan.mode == "chitchat":
                st.write("未识别到具体任务，由 UniBrain 直接应答。")
                final = plan.intro
                trace = {"mode": "chitchat", "mode_label": plan.mode_label, "reason": plan.reason, "steps": []}
            else:
                st.write(f"**调度策略**：{plan.mode_label}")
                if plan.reason:
                    st.write(f"**理由**：{plan.reason}")

                def on_step(i, res):
                    st.write(f"第 {i + 1} 步 · {res.agent_name} 完成（{res.status_label} · {res.elapsed}s）")

                final, trace, _ = brain.execute(plan, text, profile, get_kb(), llm, history, on_step)
            status.update(label="UniBrain 协作完成", state="complete", expanded=False)
        st.markdown(final)
    if direct_id:
        ss["direct_agent"] = None
        st.toast(f"已结束与 {get_agent_map()[direct_id].name} 的指定对话")
    ss["messages"].append({"role": "assistant", "content": final, "trace": trace})
    st.rerun()


def render_inline_trace(trace: dict) -> None:
    steps = trace.get("steps") or []
    if not steps:
        return
    with st.expander(f"查看协作链路（{trace.get('mode_label', '')} · {len(steps)} 步）"):
        st.caption(trace.get("reason", ""))
        for i, s in enumerate(steps, 1):
            st.markdown(f"**{i}. {s['name']}** · {s['layer']} · {s['status_label']} · {s['elapsed']}s")
            with st.expander("查看该步完整输出"):
                st.markdown(s["content"])
                if s.get("refs"):
                    st.caption("参考资料：" + "；".join(s["refs"]))


# ---------------- 侧边栏 ----------------

with st.sidebar:
    st.title(SPACE_NAME)
    st.caption(SPACE_DESC + " · 1 个空间 × 12 个专家智能体")

    llm_online = get_llm() is not None
    if llm_online:
        st.success(f"在线模型：{ss.get('model')}")
    else:
        st.info("离线演示模式（本地规则引擎）")

    # ---- 学生画像 ----
    with st.expander("学生画像（全体智能体共享）", expanded=True):
        p: StudentProfile = ss["profile"]
        p.name = st.text_input("姓名", value=p.name)
        major_idx = MAJORS.index(p.major) if p.major in MAJORS else MAJORS.index("其他")
        p.major = st.selectbox("专业", MAJORS, index=major_idx)
        grade_idx = GRADES.index(p.grade) if p.grade in GRADES else 1
        p.grade = st.selectbox("年级", GRADES, index=grade_idx)
        p.interests = st.multiselect("兴趣方向", INTEREST_TAGS,
                                     default=[i for i in p.interests if i in INTEREST_TAGS])
        p.goal = st.text_area("发展目标", value=p.goal, height=70)

        chosen = st.multiselect("技能标签（最多 8 项）", COMMON_SKILLS,
                                default=[s for s in p.skill_names() if s in COMMON_SKILLS],
                                max_selections=8)
        levels = {s["name"]: s["level"] for s in p.skills}
        p.skills = [{"name": n, "level": levels.get(n, 3)} for n in chosen]
        if p.skills:
            st.caption("熟练度：1 认知 ~ 5 精通")
            for s in p.skills:
                s["level"] = st.slider(s["name"], 1, 5, s["level"], key=f"lvl_{s['name']}")

        c1, c2 = st.columns(2)
        if c1.button("保存画像", use_container_width=True):
            save_profile(ss["profile"], DATA_DIR / "profile.json")
            st.toast("画像已保存到本地")
        if c2.button("恢复默认", use_container_width=True):
            ss["profile"] = StudentProfile()
            st.rerun()

    # ---- 模型设置 ----
    with st.expander("大模型设置", expanded=not llm_online):
        provider = st.selectbox("平台预设", list(PROVIDER_PRESETS.keys()))
        if st.button("应用该平台默认地址与模型", use_container_width=True):
            preset = PROVIDER_PRESETS[provider]
            if preset["base_url"]:
                ss["base_url"] = preset["base_url"]
                ss["model"] = preset["model"]
            st.rerun()
        st.text_input("API Key", key="api_key", type="password",
                      help="留空则保持离线演示模式；Key 仅保存在当前会话")
        st.text_input("Base URL（OpenAI 兼容）", key="base_url")
        st.text_input("模型名称", key="model")
        st.slider("Temperature", 0.0, 1.0, key="temperature")

    # ---- 智能体目录 ----
    with st.expander("智能体目录（@名可直连）", expanded=False):
        for a in get_agents():
            st.markdown(f"- **{a.name}**（@{a.en_name}）：{a.role}")

# ---------------- 主区域 ----------------

tab_chat, tab_agents, tab_trace, tab_profile = st.tabs(
    ["对话空间", "智能体网络", "协作追踪", "我的画像"])

# ---- Tab 1：对话空间 ----
with tab_chat:
    if ss.get("direct_agent"):
        agent = get_agent_map()[ss["direct_agent"]]
        st.info(f"正在与 **{agent.name}** 点对点对话，下一条消息将直接交给 TA 处理。"
                f"  （可在下方取消）")
        if st.button("取消指定对话"):
            ss["direct_agent"] = None
            st.rerun()

    if len(ss["messages"]) <= 1:
        cols = st.columns(3)
        for i, ex in enumerate(EXAMPLES):
            if cols[i % 3].button(ex, key=f"ex_{i}", use_container_width=True):
                ss["queued"] = ex
                st.rerun()

    for m in ss["messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("trace"):
                render_inline_trace(m["trace"])

    queued = ss.get("queued")
    user_input = st.chat_input("说说你的需求，UniBrain 会为你编排智能体协作…")
    if queued:
        ss["queued"] = None
        handle_prompt(queued)
    elif user_input:
        handle_prompt(user_input)

# ---- Tab 2：智能体网络 ----
with tab_agents:
    st.subheader("12 位专家智能体 · 三层级架构")
    st.caption("每个智能体独立运行、各司其职；由 UniBrain 按需编排为协作链。点击「指定对话」可点对点咨询。")
    agents_list = get_agents()
    for layer, desc in LAYER_DESC.items():
        st.markdown(f"#### {layer}")
        st.caption(desc)
        layer_agents = [a for a in agents_list if a.layer == layer]
        for r in range(0, len(layer_agents), 3):
            cols = st.columns(3)
            for col, a in zip(cols, layer_agents[r:r + 3]):
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{a.name}** · {a.en_name}")
                        st.caption(a.role)
                        st.markdown(a.description)
                        st.caption("能力：" + "、".join(a.capabilities[:4]))
                        if st.button("指定对话", key=f"pick_{a.id}", use_container_width=True):
                            ss["direct_agent"] = a.id
                            st.toast(f"已指定与 {a.name} 对话，请到「对话空间」输入内容")
                            st.rerun()

# ---- Tab 3：协作追踪 ----
with tab_trace:
    st.subheader("协作追踪")
    st.caption("展示最近一次需求中 UniBrain 的调度决策与每个智能体的完整产出。")
    traces = [m["trace"] for m in ss["messages"] if m.get("trace")]
    if not traces:
        st.info("还没有协作记录，去「对话空间」发起第一个需求吧。")
    else:
        t = traces[-1]
        st.markdown(f"**调度模式**：{t.get('mode_label', '—')}　　**调度理由**：{t.get('reason') or '—'}")
        steps = t.get("steps") or []
        if steps:
            st.text("  ->  ".join(s["name"] for s in steps))
        for i, s in enumerate(steps, 1):
            label = f"第 {i} 步 · {s['name']}（{s['status_label']} · {s['elapsed']}s）"
            with st.expander(label, expanded=(i == 1)):
                st.markdown(f"**产出标题**：{s['title']}")
                st.markdown(s["content"])
                if s.get("refs"):
                    st.caption("知识库参考：" + "；".join(s["refs"]))
                if s.get("note"):
                    st.caption(s["note"])

# ---- Tab 4：我的画像 ----
with tab_profile:
    st.subheader("我的画像")
    st.caption("该画像是 12 位智能体的共享上下文；编辑入口在左侧边栏，保存后本地持久化。")
    p: StudentProfile = ss["profile"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("姓名", p.name)
    c2.metric("专业", p.major)
    c3.metric("年级", p.grade)
    c4.metric("技能数", f"{len(p.skills)} 项")
    st.markdown(f"**兴趣方向**：{'、'.join(p.interests) or '未填写'}")
    st.markdown(f"**发展目标**：{p.goal or '未填写'}")
    if p.skills:
        st.markdown("##### 技能熟练度（Lv1 认知 ~ Lv5 精通）")
        for s in p.skills:
            st.caption(f"{s['name']}：Lv{s['level']}")
            st.progress(s["level"] / 5)
    with st.expander("画像 JSON"):
        from dataclasses import asdict

        st.json(asdict(p))
