"""UniMate Hub 智能体注册表：12 个独立专家智能体，按三层级组织。"""
from agents.alumni_connector import AlumniConnectorAgent
from agents.career_pathfinder import CareerPathfinderAgent
from agents.code_reviewer import CodeReviewerAgent
from agents.course_planner import CoursePlannerAgent
from agents.event_scout import EventScoutAgent
from agents.exam_prep_coach import ExamPrepCoachAgent
from agents.library_guide import LibraryGuideAgent
from agents.life_admin_bot import LifeAdminBotAgent
from agents.mindful_pal import MindfulPalAgent
from agents.research_mentor import ResearchMentorAgent
from agents.skill_builder import SkillBuilderAgent
from agents.thesis_advisor import ThesisAdvisorAgent

# 注册顺序即协作执行顺序（信息 → 分析 → 规划）
AGENT_CLASSES = [
    # 基础服务层
    CoursePlannerAgent,
    LibraryGuideAgent,
    ExamPrepCoachAgent,
    LifeAdminBotAgent,
    # 专业指导层
    ResearchMentorAgent,
    CodeReviewerAgent,
    ThesisAdvisorAgent,
    # 成长拓展层
    CareerPathfinderAgent,
    SkillBuilderAgent,
    MindfulPalAgent,
    AlumniConnectorAgent,
    EventScoutAgent,
]

LAYER_DESC = {
    "基础服务层": "解决日常高频需求：选课、文献、备考、行政事务",
    "专业指导层": "解决深度发展需求：科研、代码、论文写作",
    "成长拓展层": "解决未来就业与身心需求：职业、技能、心理、校友、活动",
}


def build_agents():
    return [cls() for cls in AGENT_CLASSES]
