from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

# 讀取 .env 檔案
load_dotenv()
TUTA_EMAIL = os.getenv("TUTA_EMAIL")
TUTA_PASSWORD = os.getenv("TUTA_PASSWORD")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # 顯示瀏覽器
    page = browser.new_page()

    print("啟動瀏覽器，開始登入 Tuta...")

    # 進入 Facebook 登入頁面
    page.goto("https://app.tuta.com/")
    page.wait_for_timeout(20000)

    email_field = page.query_selector("input[autocomplete='email']")
    if not email_field:
        page.wait_for_timeout(10000)
    # 使用 .env 讀取帳號密碼
    email_field = page.query_selector("input[autocomplete='email']")
    if email_field:
        # 填充 email 欄位
        email_field.fill(TUTA_EMAIL)
    else:
        print("未能找到 autocomplete 為 email 的欄位")

    pass_field = page.query_selector("input[autocomplete='current-password']")
    if pass_field:
        # 填充 email 欄位
        pass_field.fill(TUTA_PASSWORD)
    else:
        print("未能找到 autocomplete 為 current-password 的欄位")

    # 按下登入按鈕
    pass_field.press("Enter")

    # 等待登入完成
    page.wait_for_timeout(20000)
    print("登入成功！")
    page.screenshot(path="debug_1_after_login.png")
    input("瀏覽器保持開啟，按 Enter 繼續...")

    # 清空檔案內容
    with open("list.txt", "w", encoding="utf-8") as file:
        file.write("")

    selected_elements_indices = []
    # 印出每個 'li' 中第二個 'div' 的文字
    li_elements = page.query_selector_all("li.list-row")
    for index, li in enumerate(li_elements):
        second_div = li.query_selector("div:nth-of-type(2)")
        if second_div:
            unread_text = second_div.query_selector("div.smaller.text-ellipsis.b")
            if unread_text:
                with open("list.txt", "a", encoding="utf-8") as file:
                    file.write(second_div.inner_text() + "\n---\n")
                print(second_div.inner_text())  # 打印第二個 div 的文字
                selected_elements_indices.append(index)

    # Re-select elements to ensure they are still valid before clicking
    for index in selected_elements_indices:
        try:
            li_elements = page.query_selector_all("li.list-row")
            if index < len(li_elements):
                li_elements[index].click()
                page.wait_for_timeout(4000)
                mailBody = page.query_selector("#mail-body")
                print(mailBody.inner_text())
                ans = input("下一封電子郵件 (q退出)->")
                if ans == 'q':
                    break;
            else:
                print(f"Warning: Element at index {index} is no longer available")
        except Exception as e:
            print(f"Error clicking element at index {index}: {e}")

    # 保持瀏覽器開啟，方便 Debug
    input("瀏覽器保持開啟，按 Enter 關閉...")

    logoutBtn = page.query_selector("button[data-testid='btn:switchAccount_action']")
    logoutBtn.click()

    page.wait_for_timeout(6000)
    # 關閉瀏覽器
    browser.close()
    print("瀏覽器已關閉")
