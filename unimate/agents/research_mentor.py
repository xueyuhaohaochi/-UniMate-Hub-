"""专业指导层 · 科研启蒙导师 ResearchMentor：论文解读 + 实验室匹配 + 科研入门。"""
from __future__ import annotations

import re
from typing import List

from core.agent_base import BaseAgent, RunContext, get_field, parse_struct_hits
from core.rag import KBHit


class ResearchMentorAgent(BaseAgent):
    id = "research_mentor"
    name = "科研启蒙导师"
    en_name = "ResearchMentor"
    layer = "专业指导层"
    role = "科研入门指导与实验室方向匹配"
    description = "解读学术论文，辅助代码 Debug，介绍校内实验室研究方向，模拟科研助理职位面试。"
    capabilities = ["论文精读框架", "实验室方向匹配", "进组准备与邮件模板", "代码复现排错"]
    keywords = ["科研", "实验室", "导师", "教授", "读论文", "论文解读", "进组", "科研助理", "大创", "论文复现", "学术", "研究生", "夏令营"]
    kb_files = ["labs.txt"]

    def mock(self, task: str, ctx: RunContext, hits: List[KBHit]) -> str:
        items = parse_struct_hits(hits)
        p = ctx.profile
        parts: List[str] = []

        # 1) 实验室匹配：按兴趣/目标/任务与实验室方向的重合度打分
        clue = task + " " + " ".join(p.interests) + " " + (p.goal or "")
        scored = []
        for it in items:
            direction = get_field(it, "方向", "研究方向")
            score = sum(1 for k in re.split(r"[,，、/\s]+", direction) if k and k in clue)
            scored.append((score, it))
        scored.sort(key=lambda x: -x[0])

        parts.append("### 匹配的校内实验室")
        parts.append("")
        if scored:
            for score, it in scored[:3]:
                parts.append(f"#### {it['title']}{'（方向高度匹配，优先联系）' if score >= 2 else ''}")
                direction = get_field(it, "方向", "研究方向")
                tutor = get_field(it, "导师")
                req = get_field(it, "要求", "招生要求")
                result = get_field(it, "成果", "近期成果")
                if direction:
                    parts.append(f"- **研究方向**：{direction}")
                if tutor:
                    parts.append(f"- **导师**：{tutor}")
                if req:
                    parts.append(f"- **招生要求**：{req}")
                if result:
                    parts.append(f"- **近期成果**：{result}")
                parts.append("")
        else:
            parts.append("暂未命中实验室数据，可先明确研究方向关键词（如：大模型 / 计算机视觉 / 机器人）。")
            parts.append("")

        # 2) 按任务意图追加专属模块
        if any(k in task for k in ("debug", "Debug", "报错", "复现", "代码")):
            parts += [
                "### 代码复现排错清单",
                "",
                "1. **环境对齐**：Python / 框架 / CUDA 版本与论文仓库 requirements 完全一致；",
                "2. **随机种子**：固定 seed 后重跑，先排除随机性干扰；",
                "3. **数据路径**：相对路径 vs 绝对路径，数据集 md5 是否校验通过；",
                "4. **显存排查**：batch size 减半试跑，确认是 OOM 还是逻辑错误；",
                "5. **最小复现**：把问题裁到 20 行以内脚本再定位，必要时二分注释。",
                "",
            ]
        if any(k in task for k in ("读论文", "论文解读", "精读", "paper")):
            parts += [
                "### 论文精读五问",
                "",
                "1. 这篇论文要解决的核心问题是什么？现有方法差在哪？",
                "2. 核心创新点用一句话怎么说（方法图复述）？",
                "3. 实验设置是否公平？基线是否足够强？",
                "4. 消融实验证明了每个模块的必要性吗？",
                "5. 如果我来改进，下一个切入点是什么？",
                "",
            ]

        parts += [
            "### 进组准备清单",
            "",
            "- 精读目标实验室近 2 年论文 2~3 篇，准备 2 个有质量的问题；",
            "- 工具底线：Python 熟练 + Git 基本操作 + Linux 常用命令；",
            "- 用一页 PDF 简历呈现：课程成绩、相关项目、可投入时间。",
            "",
            "### 联系导师邮件模板",
            "",
            "> **主题**：【科研助理申请】专业-年级-姓名-意向方向  \n"
            "> 尊敬的 X 老师：您好！我是 XX 专业 X 年级学生 XXX（学号 XXX）。拜读了课题组《XXX》"
            "等工作，对 XX 方向尤其感兴趣，曾完成 XX 项目（一句话成果）。每周可投入 X 小时，"
            "附上简历与成绩单，恳请老师考虑我加入课题组学习和打杂的机会。祝好！——XXX",
            "",
            f"> 已按你的画像（兴趣：{'、'.join(p.interests) or '未填写'}）完成匹配度排序，建议每周联系不超过 2 位老师，保持邮件质量。",
        ]
        return "\n".join(parts)
