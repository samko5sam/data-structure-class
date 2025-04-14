import csv

def tocsv():
  print("開始讀檔")
  # 讀入原始檔案
  with open("list.txt", "r", encoding="utf-8") as f:
      content = f.read()

  # 分割每筆留言（--- 為分隔線）
  blocks = content.strip().split('---\n')

  # 儲存結構化資料
  data = []

  for block in blocks:
      lines = block.strip().split('\n')
      if len(lines) < 5:
          continue  # 跳過格式不完整的區塊

      user = lines[0].strip('*').strip()
      spec = lines[2].replace("規格 : ", "").strip()
      date = lines[3].strip()
      rating = lines[4].strip()
      comment = ''.join(lines[5:]).strip()

      data.append([user, spec, date, rating, comment])

  # 輸出成 CSV
  with open("list.csv", "w", newline='', encoding="utf-8-sig") as csvfile:
      writer = csv.writer(csvfile)
      writer.writerow(["使用者", "規格", "日期", "評分", "留言內容"])
      writer.writerows(data)

  print("轉換完成！已輸出為 list.csv")

if __name__ == '__main__':
    tocsv()