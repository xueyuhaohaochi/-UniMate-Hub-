"""专业指导层 · 论文写作顾问 ThesisAdvisor：选题 / 结构 / 引用格式 / BP 辅导（强调辅助而非代写）。"""
from __future__ import annotations

from typing import List

from core.agent_base import BaseAgent, RunContext
from core.rag import KBHit

_ETHICS = (
    "\n---\n> **学术规范声明**：本智能体严格遵循学术诚信要求，仅提供选题咨询、结构反馈、"
    "引用格式检查与语言润色建议，**不代写、不生成可直接提交的学术成果**。"
)


class ThesisAdvisorAgent(BaseAgent):
    id = "thesis_advisor"
    name = "论文写作顾问"
    en_name = "ThesisAdvisor"
    layer = "专业指导层"
    role = "学术写作与商业计划书结构辅导"
    description = "辅助选题、检查引用格式（GB/T 7714、APA、MLA）、润色摘要、审查逻辑结构；强调辅助而非代写。"
    capabilities = ["选题可行性评估", "论文结构与大纲", "引用格式审查", "摘要润色与 BP 大纲"]
    keywords = ["论文写作", "开题", "选题", "摘要", "引用", "参考文献", "毕业论文", "毕业设计", "大纲", "润色",
                "查重", "商业计划书", "计划书", "BP", "路演"]
    kb_files = ["writing.txt"]

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        t = task
        p = ctx.profile

        if any(k in t for k in ("商业计划书", "计划书", "BP", "路演")):
            body = self._bp(t, p)
        elif "摘要" in t:
            body = self._abstract(t)
        elif any(k in t for k in ("引用", "参考文献", "格式", "文献标注")):
            body = self._citation()
        else:
            body = self._topic_outline(t, p)
        return body + _ETHICS

    @staticmethod
    def _topic_outline(task: str, p) -> str:
        focus = "商业计划书" if "计划书" in task else task[:20] or "你的选题"
        return (
            "### 选题四维评估法\n\n"
            "| 维度 | 自评问题 | 达标线 |\n| --- | --- | --- |\n"
            "| 兴趣度 | 愿意为它连续投入 3 个月吗 | 4/5 |\n"
            "| 资料可得性 | 能找到 15+ 篇核心文献 / 数据吗 | 4/5 |\n"
            "| 创新空间 | 有没有前人没做透的切口 | 3/5 |\n"
            "| 可行性 | 现有方法、数据、算力能闭环吗 | 4/5 |\n\n"
            "低于达标线的维度先补救再开题，避免中途换题。\n\n"
            "### 标准五章大纲（借阅与实证通用）\n\n"
            "1. **绪论**：研究背景 → 问题提出 → 研究意义（每段都要指向「缺口」）；\n"
            "2. **文献综述与理论基础**：按主题而非按作者组织，结尾落到研究假设；\n"
            "3. **研究设计 / 方法**：数据来源、变量定义、模型设定，保证可复现；\n"
            "4. **实证 / 实现与分析**：结果呈现 + 稳健性检验；\n"
            "5. **结论与建议**：回答绪论提出的问题，坦承局限。\n\n"
            "### 开题报告要素清单\n\n"
            "- 一句话研究问题（不超过 30 字）；\n- 3 个研究问题 / 假设（H1、H2、H3）；\n"
            "- 技术路线图一张；\n- 12 周甘特图；\n- 核心参考文献 10 篇（近 5 年占比 ≥ 60%）。\n\n"
            f"> 已结合你的专业（{p.major}）。可以把具体选题发给我做四维打分：如「@论文写作顾问 我的题目是 XXX」。"
        )

    @staticmethod
    def _abstract(task: str) -> str:
        return (
            "### 摘要四句式结构\n\n"
            "1. **背景缺口**：针对 XX 问题，现有研究 / 方法在 XX 上存在不足；\n"
            "2. **本文工作**：本文提出 / 构建 / 设计了 XX，用于 XX；\n"
            "3. **方法与过程**：基于 XX 数据 / 实验，采用 XX 方法验证；\n"
            "4. **结论价值**：结果表明 XX，为 XX 提供 XX 参考。\n\n"
            "### 润色自查清单\n\n"
            "- 字数 250~350，一段成文，不出现「本文第一章」等结构性语句；\n"
            "- 删除空泛词（进行了一定的研究 → 改为具体动作与对象）；\n"
            "- 定量结果进摘要：提升 X% / 覆盖 N 条数据 / 误差 ≤ X；\n"
            "- 关键词 3~5 个，按「领域 → 方法 → 对象」排序，与全文高频词一致。\n\n"
            "把你的摘要草稿发给我（@论文写作顾问 + 正文），我将逐句给出修改理由。"
        )

    @staticmethod
    def _citation() -> str:
        return (
            "### 常用引用格式速查\n\n"
            "**GB/T 7714-2015（国内学位论文常用）**\n\n"
            "> [1] 作者. 题名[J]. 刊名, 年, 卷(期): 起止页码.  \n"
            "> [2] 作者. 书名[M]. 版本. 出版地: 出版社, 年: 页码.  \n"
            "> [3] 作者. 题名[EB/OL]. (发布日期)[引用日期]. URL.\n\n"
            "**APA 7th（英文社科常用）**\n\n"
            "> Author, A. A. (Year). Title of article. *Journal Name, Volume*(Issue), pages. https://doi.org/xxx\n\n"
            "**MLA 9th（人文常用）**\n\n"
            "> Author. \"Title of Article.\" *Journal Name*, vol. X, no. X, Year, pp. XX-XX.\n\n"
            "### 格式自查清单\n\n"
            "- 全文标注风格统一（顺序编码制 vs 著者-出版年制 二选一）；\n"
            "- 文内引用与文末条目一一对应，无「幽灵文献」；\n"
            "- 网络资源必须有 [引用日期] 与可访问 URL；\n"
            "- 用 Zotero / EndNote 管理并自动生成，投稿前人工核对标点与斜体。"
        )

    @staticmethod
    def _bp(task: str, p) -> str:
        role_hint = ""
        skills = p.skill_names()
        if any(k in " ".join(skills) for k in ("开发", "Python", "Java", "C/", "机器学习", "数据")):
            role_hint = "从你的技能画像看，你适合承担团队中的**技术与产品模块**，BP 中「产品与技术方案」一章可由你主笔。"
        return (
            "### 商业计划书（BP）黄金结构\n\n"
            "1. **执行摘要**：一页讲清「为谁、解决什么、凭什么是我们」（最后再写）；\n"
            "2. **痛点与机会**：真实场景 + 数据佐证，避免「伪需求」；\n"
            "3. **产品与服务**：Demo 截图 / 原型图说话，突出核心使用流程；\n"
            "4. **技术方案与壁垒**：架构图 + 与竞品的差异化指标；\n"
            "5. **市场分析**：TAM-SAM-SOM 三层测算，标注测算口径；\n"
            "6. **商业模式**：谁付费、定价逻辑、单位经济模型（CAC / LTV）；\n"
            "7. **竞争分析**：竞品矩阵表，说明可持续优势而非「没有竞品」；\n"
            "8. **营销与运营计划**：冷启动路径 + 前 3 个月里程碑；\n"
            "9. **团队介绍**：分工照片化呈现，导师 / 顾问背书；\n"
            "10. **财务预测**：三年损益表，关键假设单列；\n"
            "11. **融资计划**：金额、用途、出让比例、里程碑承诺。\n\n"
            "### 逻辑自查六问\n\n"
            "1. 痛点是「刚需高频」还是「锦上添花」？2. 方案比现有替代品好 10 倍在哪？\n"
            "3. 市场规模测算的每个数字有来源吗？4. 收入能否覆盖获客成本？\n"
            "5. 团队配置与项目短板是否互补？6. 融资用途是否对应可验证的里程碑？\n\n"
            f"{role_hint}\n\n> 小技巧：评委平均 8 分钟看一份 BP，第 1、2、6 章决定生死，先打磨这三章。"
        )
