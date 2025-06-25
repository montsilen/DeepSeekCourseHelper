import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from PIL import Image
import pytesseract
import json
import threading
import os
import requests
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from config import SYSTEM_PROMPT, API_URL, API_KEY, HEADERS, MINDMAP_SCHEMA
from vectorstore_setup import load_vectorstore

retriever = load_vectorstore()
from utils import load_history, save_history
from jsonschema import validate

class KnowledgeApp:
    def __init__(self, root):
        self.root = root
        root.title("\U0001F393 知识总结与导图生成")
        root.geometry("960x1200")

        input_frame = tb.Labelframe(root, text="\U0001F4DD 请输入", padding=10)
        input_frame.pack(fill=X, padx=12, pady=8)
        self.input_text = scrolledtext.ScrolledText(input_frame, height=4, font=("微软雅黑", 11), wrap="word")
        self.input_text.pack(fill=BOTH, expand=True)

        drop_frame = tb.Labelframe(root, text="\U0001F5BC 上传图片", padding=10)
        drop_frame.pack(fill=X, padx=12, pady=8)
        tb.Button(drop_frame, text="\U0001F4E4 选择图片", bootstyle="light", command=self.upload_image).pack(pady=5)

        btn_frame = tb.Frame(root)
        btn_frame.pack(fill=X, padx=12, pady=10)
        tb.Button(btn_frame, text="\u2728 生成总结、导图与课程推荐", bootstyle="light-outline", command=self.generate).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="\U0001F4DC 查看历史记录", bootstyle="light-outline", command=self.show_history).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="\U0001F9F9 清空历史记录", bootstyle="light-outline", command=self.clear_history).pack(side=LEFT, padx=5)

        summary_frame = tb.Labelframe(root, text="\U0001F4D6 知识总结与学习建议", padding=10)
        summary_frame.pack(fill=BOTH, padx=12, pady=8, expand=True)
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=8, font=("微软雅黑", 11), wrap="word")
        self.summary_text.pack(fill=BOTH, expand=True)

        courses_frame = tb.Labelframe(root, text="\U0001F4DA 课程推荐", padding=10)
        courses_frame.pack(fill=BOTH, padx=12, pady=8, expand=True)
        self.courses_text = scrolledtext.ScrolledText(courses_frame, height=6, font=("微软雅黑", 11), wrap="word")
        self.courses_text.pack(fill=BOTH, expand=True)

        tree_frame = tb.Labelframe(root, text="\U0001F333 知识导图", padding=10)
        tree_frame.pack(fill=BOTH, padx=12, pady=8, expand=True)
        self.tree = tb.Treeview(tree_frame, bootstyle="light")
        self.tree.pack(fill=BOTH, expand=True)

        self.ocr_text = ""
        self.dialog_history = load_history()

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("图像文件", "*.png *.jpg *.jpeg")])
        if file_path:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            self.ocr_text = text

    def show_history(self):
        win = tk.Toplevel(self.root)
        win.title("对话历史")
        win.geometry("800x600")
        text = scrolledtext.ScrolledText(win, font=("微软雅黑", 11))
        text.pack(fill=tk.BOTH, expand=True)
        if not self.dialog_history:
            text.insert(tk.END, "暂无历史记录。")
            return
        for i, entry in enumerate(self.dialog_history, 1):
            text.insert(tk.END, f"=== 对话 {i} ===\n")
            text.insert(tk.END, f"用户输入:\n{entry['用户输入']}\n\n")
            text.insert(tk.END, f"图片OCR内容:\n{entry['图片OCR内容']}\n\n")
            text.insert(tk.END, f"模型回答:\n{entry['模型回答']}\n\n\n")
        text.config(state=tk.DISABLED)

    def clear_history(self):
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
            self.dialog_history = []
            save_history(self.dialog_history)

    def insert_tree(self, parent, node):
        title = node.get("title", "无标题")
        node_id = self.tree.insert(parent, "end", text=title)
        for child in node.get("children", []):
            self.insert_tree(node_id, child)

    def generate(self):
        prompt = self.input_text.get("1.0", tk.END).strip()
        ocr = getattr(self, "ocr_text", "").strip()

        if not prompt and not ocr:
            messagebox.showwarning("提示", "请输入内容或上传图片。")
            return

        combined_prompt = f"用户输入内容：\n{prompt}\n\n"
        if ocr:
            combined_prompt += f"【图片OCR内容】：\n{ocr}"

        docs = retriever.invoke(combined_prompt)
        context = "\n\n".join(doc.page_content for doc in docs)

        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, "生成中，请稍候...\n")
        self.tree.delete(*self.tree.get_children())

        self.courses_text.delete("1.0", tk.END)

        buffer = ""

        def update_ui_partial(new_text):
            nonlocal buffer
            buffer += new_text

            summary_start = buffer.find("===Summary===")
            courses_start = buffer.find("===Courses===")
            mindmap_start = buffer.find("===MindMap===")

            if summary_start != -1:
                if courses_start != -1:
                    summary_text = buffer[summary_start + 13 : courses_start].strip()
                elif mindmap_start != -1:
                    summary_text = buffer[summary_start + 13 : mindmap_start].strip()
                else:
                    summary_text = buffer[summary_start + 13 :].strip()
           
                def update_summary():
                    self.summary_text.delete("1.0", tk.END)
                    self.summary_text.insert(tk.END, summary_text)
                    self.summary_text.see(tk.END)
                self.root.after(0, update_summary)

            if courses_start != -1:
                if mindmap_start != -1:
                    courses_text = buffer[courses_start + 13 : mindmap_start].strip()
                else:
                    courses_text = buffer[courses_start + 13 :].strip()
                def update_courses():
                    self.courses_text.delete("1.0", tk.END)
                    self.courses_text.insert(tk.END, courses_text)
                    self.courses_text.see(tk.END)
                self.root.after(0, update_courses)

        def on_finish(full_text):
            try:
                if "===MindMap===" in full_text:
                    mindmap_str = full_text.split("===MindMap===")[-1].strip()
                    mindmap_str = mindmap_str.strip("`json")
                    mindmap_json = json.loads(mindmap_str)
                    validate(instance=mindmap_json, schema=MINDMAP_SCHEMA)
                    self.tree.delete(*self.tree.get_children())
                    self.insert_tree("", mindmap_json)
            except Exception as e:
                self.tree.insert("", "end", text=f"[MindMap 解析失败]: {e}")

            self.dialog_history.append({"用户输入": prompt, "图片OCR内容": ocr, "模型回答": full_text})
            save_history(self.dialog_history)
            self.ocr_text = ""

        def query():
            payload = {
                "model": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 1500,
                "presence_penalty": 0.6,
                "frequency_penalty": 0.3,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT + context},
                    {"role": "user", "content": combined_prompt}
                ],
                "stream": True
            }

            try:
                with requests.post(API_URL, headers=HEADERS, json=payload, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    for line in r.iter_lines():
                        if line:
                            line = line.decode("utf-8").replace("data: ", "")
                            if line.strip() == "[DONE]":
                                break
                            content = json.loads(line)["choices"][0]["delta"].get("content", "")
                            if content:
                                update_ui_partial(content)  
                    on_finish(buffer)
            except Exception as e:
                def show_error():
                    self.summary_text.insert(tk.END, f"\n[错误] 接口调用失败: {e}")
                    self.summary_text.see(tk.END)
                self.root.after(0, show_error)

        threading.Thread(target=query, daemon=True).start()

if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    root = tb.Window(themename="darkly")
    app = KnowledgeApp(root)
    root.mainloop()
