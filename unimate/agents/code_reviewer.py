"""专业指导层 · 代码审查专家 CodeReviewer：静态检查 + 复杂度评估 + 重构建议（离线可用）。"""
from __future__ import annotations

import re
from typing import List, Optional

from core.agent_base import BaseAgent, RunContext
from core.rag import KBHit

_FENCE = re.compile(r"```[\w+#.-]*\s*\n(.*?)```", re.S)
_CODE_HINTS = ("def ", "class ", "import ", "from ", "#include", "print(", "function", "const ", "public static")
_CODE_FILE = re.compile(r"\.(py|java|c|cpp|js|ts|go|rs)\b")

# (问题, 正则, 级别, 建议)
CHECKS = [
    ("裸 except：会吞掉 KeyboardInterrupt 等系统异常", r"except\s*:", "高",
     "捕获具体异常类型，或 except Exception as e 并记录日志"),
    ("可变对象作为默认参数", r"def\s+\w+\s*\([^)]*=\s*(\[\]|\{\})", "高",
     "默认值改为 None，函数体内再创建新列表 / 字典"),
    ("使用 eval，存在代码注入风险", r"\beval\s*\(", "高",
     "解析字面量改用 ast.literal_eval；确需动态执行必须白名单 + 沙箱"),
    ("用 == / != 与 None 比较", r"==\s*None|!=\s*None", "中",
     "PEP8 要求使用 is None / is not None"),
    ("print 调试输出残留", r"print\s*\(", "中",
     "服务与长期维护代码改用 logging 分级记录（一次性脚本可忽略）"),
    ("from ... import * 污染命名空间", r"from\s+\w+\s+import\s+\*", "中",
     "显式导入所需符号，利于阅读与静态检查"),
    ("open 后未用 with 管理文件句柄", r"(?<!with )open\s*\(", "中",
     "统一使用 with open(...) as f，避免句柄泄漏"),
    ("TODO / FIXME / XXX 待办未跟踪", r"TODO|FIXME|XXX", "低",
     "转入任务清单并标注负责人与期限"),
    ("使用 global 声明全局变量", r"\bglobal\s+", "低",
     "通过参数传入 / 返回值传出，或封装为类"),
]
LEVEL_ORDER = {"高": 0, "中": 1, "低": 2}


class CodeReviewerAgent(BaseAgent):
    id = "code_reviewer"
    name = "代码审查专家"
    en_name = "CodeReviewer"
    layer = "专业指导层"
    role = "代码错误、风格与复杂度审查"
    description = "针对 CS 专业：不仅检查代码错误，还评估代码风格与复杂度，给出可执行的优化建议。"
    capabilities = ["静态缺陷扫描", "代码风格规范", "复杂度评估", "重构路线建议"]
    keywords = ["代码", "code", "报错", "bug", "Debug", "重构", "审查", "优化", "编程", "运行异常"]
    kb_files = []  # 纯本地静态分析，不依赖知识库

    @staticmethod
    def _extract_code(task: str) -> Optional[str]:
        m = _FENCE.search(task)
        if m:
            return m.group(1)
        if any(h in task for h in _CODE_HINTS) or _CODE_FILE.search(task):
            return task
        return None

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        code = self._extract_code(task)
        if not code:
            return (
                "请把需要审查的代码粘贴进来（支持 Markdown 代码块），我将从四个维度出具报告：\n\n"
                "1. **正确性**：异常处理、边界条件、资源管理；\n"
                "2. **安全性**：注入风险、敏感信息硬编码；\n"
                "3. **风格**：命名、行宽、导入规范（PEP8）；\n"
                "4. **复杂度**：函数长度、职责单一性、可测试性。\n\n"
                "示例格式：\n\n```python\ndef load(path=[]):\n    try:\n        return open(path).read()\n    except:\n        print('fail')\n```"
            )

        lines = code.splitlines()
        issues: List[tuple] = []
        for no, line in enumerate(lines, 1):
            for problem, pattern, level, advice in CHECKS:
                if pattern and re.search(pattern, line):
                    issues.append((level, no, problem, advice, line.strip()[:60]))
            if len(line) > 100:
                issues.append(("低", no, f"行长度 {len(line)} 超过 100 字符", "拆分长表达式，遵循 PEP8 行宽约定", line.strip()[:60]))

        level_rank = {"高": 0, "中": 1, "低": 2}
        issues.sort(key=lambda x: (level_rank[x[0]], x[1]))
        high = sum(1 for i in issues if i[0] == "高")
        mid = sum(1 for i in issues if i[0] == "中")
        low = sum(1 for i in issues if i[0] == "低")
        score = high * 3 + mid * 2 + low
        grade = "优秀" if score <= 2 else ("良好" if score <= 6 else "待改进")

        n_funcs = len(re.findall(r"\bdef\s+\w+|\bfunction\b|public\s+static", code))
        func_lens = []
        starts = [i for i, l in enumerate(lines) if re.search(r"\bdef\s+\w+|function\s+\w+", l)]
        for idx, s in enumerate(starts):
            e = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
            func_lens.append(e - s)
        longest = max(func_lens) if func_lens else 0

        table = ["| 级别 | 行号 | 问题 | 修改建议 |", "| --- | --- | --- | --- |"]
        for level, no, problem, advice, _snip in issues[:12]:
            table.append(f"| **{level}** | L{no} | {problem} | {advice} |")
        if not issues:
            table.append("| - | - | 未检出常见静态问题 | 仍建议补充单元测试与文档字符串 |")

        refactor = [
            "- **单一职责**：每个函数只做一件事，超过 50 行的函数优先拆分；" if longest > 50 else "- **函数长度**：当前最长函数约 "
            f"{longest} 行，粒度健康，继续保持；",
            "- **命名规范**：Python 统一 snake_case，类名 PascalCase，布尔量用 is_/has_ 前缀；",
            "- **类型注解**：为公开函数补充类型注解，让 IDE 与 mypy 提前拦截低级错误；",
            "- **防御性测试**：为核心函数补 2~3 个 pytest 用例（正常值 / 边界值 / 异常值）。",
        ]

        return (
            f"### 代码审查报告\n\n"
            f"**概览**：总 {len(lines)} 行，识别出 {n_funcs} 个函数；最长函数约 {longest} 行；"
            f"检出问题 高×{high} / 中×{mid} / 低×{low}，综合评级：**{grade}**。\n\n"
            + "\n".join(table)
            + "\n\n### 重构与优化建议\n\n" + "\n".join(refactor)
            + "\n\n> 本报告基于内置静态规则引擎（离线可用）。接入大模型后可追加架构级点评与逐行讲解。"
        )
