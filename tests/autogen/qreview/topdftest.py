import pandas as pd
from jinja2 import Template
import pdfkit

text = """
區塊 1:
好的，這是一份根據您提供的 CSV 資料和評分項目所產出的題目審核報表：

**題目審核分析報表**

| Submission ID | 字詞1        | 字詞2        | 生活化 | 粗俗用語 | 延伸討論 | 連結生活經驗 | 無意義 | 簡體字 | 備註                                                                                                |
| :------------ | :----------- | :----------- | :----- | :------- | :------- | :----------- | :----- | :----- | :-------------------------------------------------------------------------------------------------- |
| 7Aqepa        | 臭豆腐       | 狗屎         | 是     | 是       | 中       | 是           | 否     | 否     | 包含粗俗用語「狗屎」。使用者註記：「狗屎寫作咗個｛屎｝字（糞）」。建議不採用。                          |
| JPOAVX        | 低音長號     | 低音號       | 低     | 否       | 低       | 低           | 否     | 否     | 詞彙較專業（樂器），可能對不熟悉音樂的玩家較困難，生活化程度低。                                        |
| oPGB1O        | 草莓         | 番茄         | 是     | 否       | 是       | 是           | 否     | 否     | 使用者建議將原題目中的「鳳梨」改成「番茄」，認為與「草莓」的關聯性或對比性更佳。此為合理建議。                 |
| r4PG6v        | 櫻花         | 薰衣草       | 是     | 否       | 是       | 是           | 否     | 否     | 建議將原題目「喉糖/口香糖」改為「櫻花/薰衣草」。此組詞彙生活化且具討論空間。使用者註記與題目內容無關。          |
| vZ4qG4        | 你／妳是平民 | 你／妳是臥底 | 否     | 否       | 否       | 否           | 是     | 否     | 此組詞彙描述的是遊戲角色身份，而非一般詞語，不適合做為題目本身。可能使用者誤解了題目的性質。              |
| qrYkG9        | 電腦         | 筆電         | 是     | 否       | 是       | 是           | 否     | 否     | 使用者建議將「電腦」改為「桌機」，以與「筆電」做出更明確的區別。這是個不錯的優化建議。                     |
| WWl25N        | 宋雨綺       | 葉舒華       | 中     | 否       | 中       | 低           | 否     | 否     | 建議將原題目「乒乓球/羽毛球」改為特定人物名稱（偶像團體成員）。可能較為粉絲向，對一般玩家的普適性較低。 |
| Ag5N6l        | 高中         | 國中         | 是     | 否       | 是       | 是           | 否     | 否     | 詞彙本身合適。使用者註記反應的是遊戲過程遇到的問題（重複詞彙），而非針對「高中/國中」這組詞彙的建議。        |
| gE2z6J        | 輔導老師     | 班導師       | 是     | 否       | 是       | 是           | 否     | 否     | 使用者認為這兩個詞彙「太像了」，可能導致遊戲難度過高或不易區分。此為有效的遊戲性回饋。                    |

**說明：**

*   **生活化**：評估詞彙是否常見於日常生活中。
*   **粗俗用語**：評估詞彙是否包含不雅、冒犯性或粗俗的字眼。
*   **延伸討論**：評估詞彙是否能在遊戲過程中引發有趣的描述、聯想或區別討論。
*   **連結生活經驗**：評估詞彙是否容易讓玩家連結到自身的經驗或知識。
*   **無意義**：評估詞彙組合是否邏輯不通、過於抽象或無法進行有意義的描述/區別（例如直接使用遊戲角色身份）。
*   **簡體字**：檢查是否使用了簡體中文。在此樣本中皆為否。
*   **備註**：包含使用者提供的具體說明、審核者的額外觀察或建議。

此報表已根據您提供的規則，對每一筆提交的題目（以 `字詞1` 和 `字詞2` 為主）進行了分析和整理。
"""

# 定義 HTML 模板
html_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataFrame PDF</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin: 20px; }
        .table { width: 80%; margin: auto; border-collapse: collapse; }
        .table th, .table td { border: 1px solid black; padding: 8px; text-align: center; }
        .table th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h2>DataFrame 轉 PDF 範例</h2>
    {{ table | safe }}
</body>
</html>
"""

def create_table(df: pd.DataFrame):
    html_table = df.to_html(index=False, classes="table table-bordered")
    return html_table

def parse_markdown_table(markdown_text: str) -> pd.DataFrame:
    """
    從 Markdown 格式的表格文字提取資料，返回一個 pandas DataFrame。
    例如，輸入：
      | start | end | text | 分類 |
      |-------|-----|------|------|
      | 00:00 | 00:01 | 開始拍攝喔 | 備註 |
    會返回包含該資料的 DataFrame。
    """
    lines = markdown_text.strip().splitlines()
    # 過濾掉空行
    lines = [line.strip() for line in lines if line.strip()]
    # 找到包含 '|' 的行，假設這就是表格
    table_lines = [line for line in lines if line.startswith("|")]
    if not table_lines:
        return None
    # 忽略第二行（分隔線）
    header_line = table_lines[0]
    headers = [h.strip() for h in header_line.strip("|").split("|")]
    data = []
    for line in table_lines[2:]:
        row = [cell.strip() for cell in line.strip("|").split("|")]
        if len(row) == len(headers):
            data.append(row)
    df = pd.DataFrame(data, columns=headers)
    return df

def generate_pdf(text: str = None, df: pd.DataFrame = None) -> str:
    print("開始生成 PDF")
    html_table=""
    if df is not None:
        html_table = create_table(df)
    elif text is not None:
        # 嘗試檢查 text 是否包含 Markdown 表格格式
        if "|" in text:
            # 找出可能的表格部分（假設從第一個 '|' 開始到最後一個 '|'）
            table_part = "\n".join([line for line in text.splitlines() if line.strip().startswith("|")])
            parsed_df = parse_markdown_table(table_part)
            if parsed_df is not None:
                html_table = create_table(parsed_df)
            else:
                print(text)
        else:
            print(text)
    else:
        print("沒有可呈現的內容")

    template = Template(html_template)
    html_content = template.render(table=html_table)
    
    pdf_filename = f"report_test.pdf"
    html_file = "output.html"
    with open(html_file, "w", encoding="utf-8") as file:
        file.write(html_content)
    print("輸出 PDF 至檔案：", pdf_filename)
    pdfkit.from_file("output.html", "test.pdf", verbose=True, options={"enable-local-file-access": True})

    return pdf_filename

if __name__ == "__main__":
    generate_pdf(text)