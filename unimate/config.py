"""UniMate Hub 全局配置。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env")

# ---- 大模型配置（OpenAI 兼容协议）----
LLM_API_KEY = os.getenv("UNIMATE_LLM_API_KEY", "").strip()
LLM_BASE_URL = os.getenv("UNIMATE_LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").strip()
LLM_MODEL = os.getenv("UNIMATE_LLM_MODEL", "qwen-plus").strip()
LLM_TEMPERATURE = float(os.getenv("UNIMATE_LLM_TEMPERATURE", "0.6"))

SPACE_NAME = "UniMate Hub"
SPACE_DESC = "大学生学业与职业发展多智能体协作空间"

# 常见平台预设（均为 OpenAI 兼容接口）
PROVIDER_PRESETS = {
    "离线演示模式（不调用大模型）": {"base_url": "", "model": "mock"},
    "通义千问 DashScope": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "智谱 GLM": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    "DeepSeek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "月之暗面 Kimi": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "OpenAI": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o"},
    "自定义": {"base_url": "", "model": ""},
}

MAJORS = [
    "计算机科学与技术", "软件工程", "人工智能", "数据科学与大数据技术", "电子信息工程",
    "机械工程", "经济学", "金融学", "工商管理", "市场营销", "汉语言文学", "英语", "法学", "其他",
]
GRADES = ["大一", "大二", "大三", "大四", "研一及以上"]
INTEREST_TAGS = ["考研升学", "保研", "出国留学", "求职就业", "科研竞赛", "创业实践", "考公考编", "技能提升"]
COMMON_SKILLS = [
    "Python", "Java", "C/C++", "前端开发", "后端开发", "数据分析", "机器学习",
    "论文写作", "演讲表达", "团队协作", "项目管理", "英语", "设计", "视频剪辑",
]
