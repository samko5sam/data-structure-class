from playwright.sync_api import sync_playwright

def scrapeComments(code):
  # 爬取商品評價資訊
  with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # 顯示瀏覽器
    page = browser.new_page()

    print(f"啟動瀏覽器，進入商品頁面 {code}...")

    #input("Continue...")
    # 進入頁面
    page.goto(f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={code}")
    page.wait_for_timeout(3000)

    # 等待登入完成
    page.screenshot(path="debug_1_after_login.png")
    commentBtn = page.query_selector(".goodsCommendLi")
    commentBtn.click()

    page.wait_for_timeout(1000)

    # 清空檔案內容
    with open("list.txt", "w", encoding="utf-8") as file:
        file.write("")

    # Use query_selector_all to select multiple elements
    page_switcher_elements = page.query_selector_all("div.pageArea ul li")

    page_count = 0
    # Now you can iterate over the collection of elements
    for index, element in enumerate(page_switcher_elements):
        print(f"Element {index}: {element.inner_text()}")  # Example: print the inner text of each element
        page_count += 1

    # 印出每個 'li' 中第二個 'div' 的文字
    with open("list.txt", "a", encoding="utf-8") as file:
        for i in range(page_count):
            li_elements = page.query_selector_all(".reviewCardInner")
            for index, li in enumerate(li_elements):
                file.write(li.inner_text() + "\n---\n")
                print(li.inner_text())  # 打印第二個 div 的文字
            if i != (page_count - 1):
                nextBtn = page.query_selector(f"dd[pageidx='{i+2}']")
                nextBtn.click()
                page.wait_for_timeout(1000)



    # 保持瀏覽器開啟，方便 Debug
    #input("瀏覽器保持開啟，按 Enter 關閉...")

    # 關閉瀏覽器
    browser.close()
    print("瀏覽器已關閉")

if __name__ == '__main__':
    scrapeComments("12334757")