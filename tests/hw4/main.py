import gradio as gr
from dotenv import load_dotenv
from scrape import scrapeComments
from tocsv import tocsv
from handlecsv import gradio_handler

# 讀取 .env 檔案
load_dotenv()

# HW4

# 爬取評論資料、轉換成CSV檔案
def getCsv(goodCode):
    scrapeComments(goodCode)
    tocsv()

# 讓各Agent討論，標記評論後生成PDF報告
def report_handler(user_prompt):
    gradio_handler(user_prompt) # 生成PDF

default_prompt = """請根據以下的評分項目將每個評論進行審核：

"商品優點",
"商品缺點",
"商品品質",
"購物體驗",
"無意義",
"備註"

並將所有題目進行整理後產出報表。"""

with gr.Blocks() as demo:
    gr.Markdown("# EOEO 商品評論分析報告")
    with gr.Row():
        goodCode = gr.Textbox(label="請輸入商品ID", lines=1, value='12334757')
        scrapeBtn = gr.Button("爬取商品評論資料")
        scrapeBtn.click(fn=getCsv, inputs=[goodCode])
    output_text = gr.Textbox(label="回應內容", interactive=False)
    user_input = gr.Textbox(label="請輸入分析指令", lines=10, value=default_prompt)
    output_pdf = gr.File(label="下載 PDF 報表")
    submit_button = gr.Button("生成報表")
    submit_button.click(fn=report_handler, inputs=[user_input],
                        outputs=[output_text, output_pdf])

demo.launch()