"""学生画像：空间内所有智能体共享的个性化上下文，支持本地持久化。"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Union


def _default_skills() -> List[dict]:
    return [
        {"name": "Python", "level": 4},
        {"name": "数据结构", "level": 3},
        {"name": "论文写作", "level": 3},
        {"name": "团队协作", "level": 4},
    ]


@dataclass
class StudentProfile:
    name: str = "李明"
    major: str = "计算机科学与技术"
    grade: str = "大二"
    interests: List[str] = field(default_factory=lambda: ["考研升学", "科研竞赛"])
    goal: str = "夯实专业基础，争取保研，同时积累一段大厂后端开发实习经历"
    skills: List[dict] = field(default_factory=_default_skills)

    def summary(self) -> str:
        interests = "、".join(self.interests) or "暂无"
        skills = "、".join(f"{s['name']}(Lv{s['level']})" for s in self.skills) or "暂无"
        return (
            f"姓名：{self.name}；专业：{self.major}；年级：{self.grade}；"
            f"兴趣方向：{interests}；发展目标：{self.goal or '暂无'}；技能水平：{skills}"
        )

    def skill_names(self) -> List[str]:
        return [s["name"] for s in self.skills]


def load_profile(path: Union[str, Path]) -> StudentProfile:
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        valid = set(StudentProfile.__dataclasses__)
        kwargs = {k: v for k, v in data.items() if k in valid}
        return StudentProfile(**kwargs)
    except Exception:
        return StudentProfile()


def save_profile(profile: StudentProfile, path: Union[str, Path]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(asdict(profile), ensure_ascii=False, indent=2), encoding="utf-8")
