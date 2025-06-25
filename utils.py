import os
import json
from tkinter import messagebox

HISTORY_FILE = "dialog_history.json"
SENSITIVE_WORDS = ["暴力", "恐怖", "屠杀", "爆炸", "枪支", "贩毒", "色情", "自杀", "邪教"]


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def save_history(dialog_history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(dialog_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存历史失败: {e}")


def add_history(dialog_history, user_input, ocr_input, assistant_output):
    entry = {
        "用户输入": user_input,
        "图片OCR内容": ocr_input,
        "模型回答": assistant_output
    }
    dialog_history.append(entry)
    save_history(dialog_history)


def contains_sensitive_words(text):
    for word in SENSITIVE_WORDS:
        if word in text:
            messagebox.showwarning("警告", f"输入中包含敏感词：'{word}'，请修改后再试。")
            return True
    return False
