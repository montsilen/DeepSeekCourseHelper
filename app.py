import tkinter as tk
from tkinter import scrolledtext, messagebox,filedialog
from PIL import Image
import pytesseract
import requests
import json
import threading
import os
from PIL import Image
from jsonschema import validate
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-base-zh-v1.5")
vectorstore = FAISS.load_local(
    "course_vector_store",
    embedding,
    allow_dangerous_deserialization=True
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

HISTORY_FILE = "dialog_history.json"

API_URL = "https://api.deepseek.com/chat/completions"
API_KEY = "sk-b1177a26a6614347adfe0c642a32022a" 
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}


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

class KnowledgeApp:
    def __init__(self, root):
        self.root = root
        root.title("🎓 知识总结与导图生成")
        root.geometry("960x1200")

        input_frame = tb.Labelframe(root, text="📝 请输入", padding=10)
        input_frame.pack(fill=X, padx=12, pady=8)
        self.input_text = scrolledtext.ScrolledText(input_frame, height=4, font=("微软雅黑", 11), wrap="word")
        self.input_text.pack(fill=BOTH, expand=True)

        drop_frame = tb.Labelframe(root, text="🖼 上传图片", padding=10)
        drop_frame.pack(fill=X, padx=12, pady=8)
        tb.Button(drop_frame, text="📤 选择图片", bootstyle="light", command=self.upload_image).pack(pady=5)

        btn_frame = tb.Frame(root)
        btn_frame.pack(fill=X, padx=12, pady=10)
        tb.Button(btn_frame, text="✨ 生成总结、导图与课程推荐", bootstyle="light-outline", command=self.generate).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="📜 查看历史记录", bootstyle="light-outline", command=self.show_history).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="🧹 清空历史记录", bootstyle="light-outline", command=self.clear_history).pack(side=LEFT, padx=5)

        summary_frame = tb.Labelframe(root, text="📖 知识总结与学习建议", padding=10)
        summary_frame.pack(fill=BOTH, padx=12, pady=8, expand=True)
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=8, font=("微软雅黑", 11), wrap="word")
        self.summary_text.pack(fill=BOTH, expand=True)

        courses_frame = tb.Labelframe(root, text="📚 课程推荐", padding=10)
        courses_frame.pack(fill=BOTH, padx=12, pady=8, expand=True)
        self.courses_text = scrolledtext.ScrolledText(courses_frame, height=6, font=("微软雅黑", 11), wrap="word")
        self.courses_text.pack(fill=BOTH, expand=True)


        tree_frame = tb.Labelframe(root, text="🌳 知识导图", padding=10)
        tree_frame.pack(fill=BOTH, padx=12, pady=8, expand=True)
        self.tree = tb.Treeview(tree_frame, bootstyle="light")
        self.tree.pack(fill=BOTH, expand=True)

        self.ocr_text = ""
        self.dialog_history = self.load_history()

    def upload_image(self):
        from PIL import Image
        import pytesseract
        file_path = filedialog.askopenfilename(filetypes=[("图像文件", "*.png *.jpg *.jpeg")])
        if file_path:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            self.ocr_text = text

   
    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.dialog_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史失败: {e}")

    def add_history(self, user_input, ocr_input, assistant_output):
        entry = {
            "用户输入": user_input,
            "图片OCR内容": ocr_input,
            "模型回答": assistant_output
        }
        self.dialog_history.append(entry)
        self.save_history()

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
            self.save_history()

    def drop_event(self, event):
        files = self.root.tk.splitlist(event.data)
        new_texts = []
        try:
            for file_path in files:
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                new_texts.append(text)
        
            combined_text = "\n\n".join(new_texts)
            self.ocr_text += "\n\n" + combined_text if self.ocr_text else combined_text
        
            self.ocr_display.delete("1.0", tk.END)
            self.ocr_display.insert(tk.END, self.ocr_text)

            messagebox.showinfo("OCR结果", f"拖入 {len(files)} 张图片，提取文字长度: {len(combined_text)} 字符")
        except Exception as e:
            messagebox.showerror("错误", f"OCR识别失败: {e}")

    def query_deepseek_stream(self, prompt, on_stream_end, on_summary_update, system_context=""):
        payload = {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 1500,
            "presence_penalty": 0.6,#惩罚重复话题
            "frequency_penalty": 0.3,#惩罚重复用词
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT + system_context},
                {"role": "user", "content": prompt},
            ],
            "stream": True
        }
        try:
            with requests.post(API_URL, headers=HEADERS, json=payload, stream=True, timeout=60) as r:
                r.raise_for_status()
                buffer_total = ""
                buffer_summary = ""
                mindmap_triggered = False
                for line in r.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data: "):
                            line_str = line_str[6:]
                        if line_str.strip() == "[DONE]":
                            break
                        data = json.loads(line_str)
                        delta = data['choices'][0]['delta'].get("content", "")
                        if delta:
                            buffer_total += delta
                            if not mindmap_triggered:
                                buffer_summary += delta
                                if "===MindMap===" in buffer_summary:
                                    buffer_summary = buffer_summary.split("===MindMap===")[0].strip()
                                    mindmap_triggered = True
                                on_summary_update(buffer_summary)
            on_stream_end(buffer_total)
        except Exception as e:
            on_summary_update(f"\n[错误] 接口调用失败: {e}")
            on_stream_end("")

    def generate(self):
        ocr_text_input = getattr(self, "ocr_text", "").strip()
        prompt = self.input_text.get("1.0", tk.END).strip()
        if not prompt and not self.ocr_text:
            messagebox.showwarning("提示", "请输入内容或拖入图片进行OCR识别。")
            return

        prompt = prompt.replace("\u3000", " ").replace("\xa0", " ").strip()
        ocr_text_input = ocr_text_input.replace("\u3000", " ").replace("\xa0", " ").strip()

        sensitive_words = ["暴力","恐怖","屠杀","爆炸","枪支","贩毒","色情","自杀","邪教"]
        combined_input = prompt + "\n" + ocr_text_input
        for word in sensitive_words:
            if word in combined_input:
                messagebox.showwarning("警告", f"输入中包含敏感词：'{word}''，请修改后再试。")
                return
        
        combined_prompt = "用户输入内容：\n" + prompt + "\n\n"
        if ocr_text_input:
            combined_prompt += "【图片OCR内容】：\n" + ocr_text_input
        retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
        docs = retriever.invoke(combined_prompt)
        context = "\n\n".join(doc.page_content for doc in docs)
        
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, "生成中，请稍候...\n")
        self.tree.delete(*self.tree.get_children())
        def update_summary(text):
            summary_start = text.find("===Summary===")
            courses_start = text.find("===Courses===")
            mindmap_start = text.find("===MindMap===")

            summary_text = ""
            courses_text = ""

            if summary_start != -1:
                if courses_start != -1:
                    summary_text = text[summary_start + 13 : courses_start]
                elif mindmap_start != -1:
                    summary_text = text[summary_start + 13 : mindmap_start]
                else:
                    summary_text = text[summary_start + 13 :]

            if courses_start != -1:
                if mindmap_start != -1:
                    courses_text = text[courses_start + 13 : mindmap_start]
                else:
                    courses_text = text[courses_start + 13 :]

            self.summary_text.delete("1.0", tk.END)
            self.summary_text.insert(tk.END, summary_text.strip())
            self.summary_text.see(tk.END)

            self.courses_text.delete("1.0", tk.END)
            self.courses_text.insert(tk.END, courses_text.strip())
            self.courses_text.see(tk.END)

            self.root.update_idletasks()
        def on_complete(full_text):
            summary_part = ""
            course_part = ""

            if "===Courses===" in full_text:
                parts = full_text.split("===Courses===")
                summary_part = parts[0].replace("===Summary===", "").strip()
                if "===MindMap===" in parts[1]:
                    course_part = parts[1].split("===MindMap===")[0].strip()
                else:
                    course_part = parts[1].strip()
            else:
                summary_part = full_text

            self.summary_text.delete("1.0", tk.END)
            self.summary_text.insert(tk.END, summary_part)

            self.courses_text.delete("1.0", tk.END)
            self.courses_text.insert(tk.END, course_part)

            if "===MindMap===" in full_text:
                mindmap_str = full_text.split("===MindMap===")[1].strip()
                print(mindmap_str)
                try:
                    mindmap_json = json.loads(mindmap_str)
                    self.tree.delete(*self.tree.get_children())
                    self.insert_tree("", mindmap_json)
                    validate(instance=mindmap_json, schema=MINDMAP_SCHEMA)
                except Exception as e:
                    self.tree.delete(*self.tree.get_children())
                    self.tree.insert("", "end", text=f"[JSON解析错误]: {e}")
            else:
                self.tree.delete(*self.tree.get_children())
                self.tree.insert("", "end", text="[未检测到导图JSON内容]")
            self.add_history(prompt, ocr_text_input, full_text)
            self.ocr_text = ""

        threading.Thread(
            target=lambda: self.query_deepseek_stream(combined_prompt, on_complete, update_summary, context),
            daemon=True
        ).start()
        
    def insert_tree(self, parent, node):
        title = node.get("title", "无标题")
        node_id = self.tree.insert(parent, "end", text=title)
        for child in node.get("children", []):
            self.insert_tree(node_id, child)


if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = KnowledgeApp(root)
    root.mainloop()
