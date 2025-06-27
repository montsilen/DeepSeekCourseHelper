# DeepSeek 学习助手
北京大学2025春人工智能基础大作业

## 部署方案
下载源代码并在项目根目录下安装requirements.txt中包含的python库。

```bash
pip install -r requirements.txt
```

然后下载pytesseract依赖的本体Tesseract-OCR引擎，安装并添加到path。

[https://github.com/tesseract-ocr/tesseract/releases](https://github.com/tesseract-ocr/tesseract/releases)

在根目录下创建.env文件，按照格式输入你的DeepSeek Api Key
```
API_KEY=sk-xxxxxxxx
```

运行main_app.py
```bash
python -u main_app.py
```

加载本地向量知识库需要一定时间，运行后等待图形界面出现后即可开始使用本程序。

## 用户手册
在“请输入”框中可以输入您的笔记和有关问题，如果是图片形式的材料，点击“上传图片”中的“选择图片”按钮，即可选择图片文件，自动OCR识别为文本。

输入内容不得包含违禁词。

点击“生成总结、导图与课程推荐”按钮，程序将合并您的输入和OCR识别并提交给DeepSeek，流式地在“知识总结和学习建议”框内给出总结建议。

程序将结合包含所有北京大学课程的数据库，给出推荐学习的课程列表，显示在“课程推荐”框内，以便进一步学习相应的知识。

然后，程序将给出一份直观可交互的知识思维导图，显示在“知识导图”框内

点击“查看历史记录”按钮，可以在新对话框中查看所有的输入内容和大语言模型给出的返回，“清空历史记录”按钮可以清除所有历史记录。