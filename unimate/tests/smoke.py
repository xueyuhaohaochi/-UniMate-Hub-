"""UniMate Hub 离线冒烟测试：验证调度、12 个智能体与协作链路（Mock 模式，无需 API Key）。

运行：python tests/smoke.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents import build_agents  # noqa: E402
from core.memory import StudentProfile  # noqa: E402
from core.orchestrator import UniBrain  # noqa: E402
from core.rag import KnowledgeBase  # noqa: E402

PROFILE = StudentProfile()
KB = KnowledgeBase(ROOT / "knowledge")
BRAIN = UniBrain(build_agents())

COLLAB_CASES = [
    "我想参加互联网+大赛，但还没组队，也不知道怎么写商业计划书",
    "我想申请计算机系的研究生，现在该做什么准备？",
    "这学期想提升数据分析能力并找一份相关实习",
]
SINGLE_CASES = [
    "下学期课表怎么选？给分好的课有哪些？",
    "最近备考数据结构，帮我制定复习计划",
    "帮我找深度学习在医疗影像方向的最新综述",
    "奖学金申请时间节点是什么时候？",
    "推荐几个值得参加的竞赛活动",
    "最近压力大睡不好，总是焦虑内耗",
    "报销竞赛经费的流程是什么",
    "帮我看看这段代码：\ndef f(x=[]):\n    try:\n        print(x)\n    except:\n        pass",
    "毕业论文怎么选题？引用格式有哪些规范",
    "想认识互联网行业的学长学姐，了解真实的职场",
    "@备考教练 高数期末怎么复习",
]
CHITCHAT_CASES = ["你好", "今天天气怎么样"]


def check(msg, expect_mode):
    plan = BRAIN.plan(msg, PROFILE, None, [])
    label = plan.mode_label
    assert plan.mode == expect_mode, f"[{msg}] 期望 {expect_mode}，实际 {plan.mode}（{plan.reason[:60]}）"
    if expect_mode == "chitchat":
        assert plan.intro, "闲聊应答为空"
        print(f"PASS [{label}] {msg}")
        return
    final, trace, results = BRAIN.execute(plan, msg, PROFILE, KB, None, [])
    names = [s["name"] for s in trace["steps"]]
    assert len(final) > 200, f"[{msg}] 最终答复过短: {len(final)}"
    for s in trace["steps"]:
        assert s["content"], f"[{msg}] {s['name']} 输出为空"
        assert len(s["content"]) > 100, f"[{msg}] {s['name']} 输出过短"
    print(f"PASS [{label}] {msg}")
    print(f"     链路({'->'.join(names)})  final={len(final)}字")


print("== 协作场景（多智能体） ==")
for c in COLLAB_CASES:
    check(c, "collab")

print("\n== 单体场景（含 @直连） ==")
for c in SINGLE_CASES:
    check(c, "single" if not c.startswith("@") else "direct")

print("\n== 闲聊导览 ==")
for c in CHITCHAT_CASES:
    check(c, "chitchat")

print("\n== 12 个智能体完整性 ==")
agents = build_agents()
assert len(agents) == 12, f"智能体数量应为 12，实际 {len(agents)}"
assert len({a.id for a in agents}) == 12, "智能体 id 存在重复"
for a in agents:
    assert a.name and a.role and a.layer and a.keywords, f"{a.id} 元信息不完整"
    print(f"PASS {a.name}（{a.en_name}）· {a.layer}")

print("\nALL SMOKE TESTS PASSED")
