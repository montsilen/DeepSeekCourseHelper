import pytesseract
from dotenv import load_dotenv
import os

load_dotenv()

API_URL = "https://api.deepseek.com/chat/completions"
API_KEY = os.getenv("API_KEY")
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

HISTORY_FILE = "dialog_history.json"

VECTORSTORE_PATH = "course_vector_store"
EMBEDDING_MODEL = "BAAI/bge-base-zh-v1.5"

MINDMAP_SCHEMA = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MindMap Schema",
  "type": "object",
  "required": ["title"],
  "properties": {
    "title": {
      "type": "string",
      "description": "节点标题"
    },
    "children": {
      "type": "array",
      "description": "子节点数组",
      "items": {
        "$ref": "#"
      },
      "default": []
    }
  },
  "additionalProperties": True
}

SYSTEM_PROMPT = (
    "你是知识总结和知识导图专家。请根据用学生输入的知识内容和图片OCR内容，生成：\n\n"
    "请严格按照以下格式返回，不要包含多余的说明文字"
    "生成数学公式时严格使用Latex格式,一定要严格使用，在生成树状图时也要注意格式正确"
    "对知识点的总结尽量详细全面，让用户容易理解"
    "===Summary===\n"
    "- 知识总结和学习建议（用中文，条理清晰）\n\n"
    "===Courses===\n"
    "- 课程推荐，从列表中选择2-3节最合适的课程"
    "给出课程编号，中英文名称和学分数，并给出相应原因\n"
    "===MindMap===\n"
    "一定要用标准JSON格式描述知识导图，格式如下：\n"
    '{\n'
    '  "title": "主题",\n'
    '  "children": [\n'
    '    {"title": "知识点1", "children": [...]},\n'
    '    {"title": "知识点2", "children": [...]}\n'
    '  ]\n'
    '}\n'
    "请保证JSON格式正确。不要添加任何额外内容\n"
    "所推荐的课程从以下课程中选择：\n"
)
