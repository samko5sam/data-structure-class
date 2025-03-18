import os
import json
import time
import pandas as pd
import sys
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError

# 載入 .env 中的 GEMINI_API_KEY
load_dotenv()

# 定義評分項目（依據原始 xlsx 編碼規則）
ITEMS = [
    "生活化",
    "粗俗用語",
    "延伸討論",
    "連結生活經驗",
    "無意義",
    "簡體字",
    "備註"
]

def parse_response(response_text):
    """
    嘗試解析 Gemini API 回傳的 JSON 格式結果。
    如果回傳內容被 markdown 的反引號包圍，則先移除這些標記。
    若解析失敗，則回傳所有項目皆為空的字典。
    """
    cleaned = response_text.strip()
    # 如果回傳內容以三個反引號開始，則移除第一行和最後一行
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    
    try:
        result = json.loads(cleaned)
        for item in ITEMS:
            if item not in result:
                result[item] = ""
        return result
    except Exception as e:
        print(f"解析 JSON 失敗：{e}")
        print("原始回傳內容：", response_text)
        return {item: "" for item in ITEMS}

def process_batch_question(client, questions: list, delimiter="-----"):
    """
    將多筆逐字稿合併成一個批次請求。
    提示中要求模型對每筆逐字稿產生 JSON 格式回覆，
    並以指定的 delimiter 分隔各筆結果。
    """
    prompt = (
        "你是一位遊戲題目審核專家，請根據以下編碼規則評估每個題目的字詞是否合標準，\n"
        + "\n".join(ITEMS) +
        "\n\n請依據評估結果，對每個項目：若觸及則標記為 1，否則留空。"
        " 請對每筆逐字稿產生 JSON 格式回覆，並在各筆結果間用下列分隔線隔開：\n"
        f"{delimiter}\n"
        "例如：\n"
        "```json\n"
        "{\n  \"生活化\": \"1\",\n  \"粗俗用語\": \"\",\n  ...\n}\n"
        f"{delimiter}\n"
        "{{...}}\n```"
    )
    batch_text = f"\n{delimiter}\n".join([",".join(question) for question in questions])
    content = prompt + "\n\n" + batch_text

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=content
        )
    except ServerError as e:
        print(f"API 呼叫失敗：{e}")
        return [{item: "" for item in ITEMS} for _ in questions]
    
    print("批次 API 回傳內容：", response.text)
    parts = response.text.split(delimiter)
    results = []
    for part in parts:
        part = part.strip()
        if part:
            results.append(parse_response(part))
    # 若結果數量多於原始筆數，僅取前面對應筆數；若不足則補足空結果
    if len(results) > len(questions):
        results = results[:len(questions)]
    elif len(results) < len(questions):
        results.extend([{item: "" for item in ITEMS}] * (len(questions) - len(results)))
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python Qreview.py <path_to_csv>")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    # Extract the file name without extension to generate output file name
    input_filename = os.path.basename(input_csv)
    file_root, _ = os.path.splitext(input_filename)
    output_csv = f"{file_root}_processed.csv"
    if os.path.exists(output_csv):
        os.remove(output_csv)
    
    df = pd.read_csv(input_csv, header=0)
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("請設定環境變數 GEMINI_API_KEY")
    client = genai.Client(api_key=gemini_api_key)
    
    batch_size = 10
    total = len(df)
    for start_idx in range(0, total, batch_size):
        end_idx = min(start_idx + batch_size, total)
        batch = df.iloc[start_idx:end_idx]
        word1s = batch["字詞1"].tolist()
        word2s = batch["字詞2"].tolist()
        questions = [[w1, w2] for w1, w2 in zip(word1s, word2s)]
        batch_results = process_batch_question(client, questions)
        batch_df = batch.copy()
        for item in ITEMS:
            batch_df[item] = [res.get(item, "") for res in batch_results]
        if start_idx == 0:
            batch_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        else:
            batch_df.to_csv(output_csv, mode='a', index=False, header=False, encoding="utf-8-sig")
        print(f"已處理 {end_idx} 筆 / {total}")
        time.sleep(1)
    
    print("全部處理完成。最終結果已寫入：", output_csv)

if __name__ == "__main__":
    main()