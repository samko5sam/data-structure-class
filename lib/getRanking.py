from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import re
from dotenv import load_dotenv
import time

load_dotenv()

empty_rank = {
    'rank': 'NA',
    'category': 'NA'
}

# This function will parse the text_content and return structured data
def parse_ranking_info(text_content):
    # Use regex to find the ranking number and category information
    match = re.match(r"#(\d+)\n(.+?) - (.+)", text_content)
    if match:
        rank = int(match.group(1))
        category = match.group(2).strip()
        metric = match.group(3).strip()

        # Return structured data as a dictionary
        return {
            'rank': rank,
            'category': category,
            'metric': metric
        }
    else:
        # Return None or handle error if parsing fails
        return None

def get_ranking(urls = ['https://app.sensortower.com/overview/cyou.sk5s.app.answersai?country=TW'], autoLogin=True):
  data = []
  loginUrl = 'https://app.sensortower.com/users/sign_in'

  edge_options = EdgeOptions()
  if False:
      edge_options.add_argument("--headless")  # Run Chrome in headless mode
  edge_options.add_argument("--force-device-scale-factor=1")
  edge_options.add_argument("--window-size=1000,1350")
  edge_options.add_argument("--disable-pdf-viewer")
  edge_options.add_argument("--window-position=0,0")

  driver = webdriver.Edge(options=edge_options)

  try:
    if autoLogin:
      driver.get(loginUrl)
      driver.implicitly_wait(2)
      email = os.environ.get("SENSORTOWER_EMAIL")
      password = os.environ.get("SENSORTOWER_PASSWORD")
      email_input = driver.find_element(By.ID, "email")
      email_input.send_keys(email)
      email_input.send_keys(Keys.RETURN)
      time.sleep(1)
      password_input = driver.find_element(By.ID, "password")
      password_input.send_keys(password)
      password_input.send_keys(Keys.ENTER)
      time.sleep(1)
    else:
      driver.get(loginUrl)
      input("Press Enter to continue after driver.get is executed...")
    time.sleep(1)
    for url in urls:
      driver.get(url)
      time.sleep(2)
      # Adjust the selector based on the actual HTML structure
      # grid_elements = driver.find_elements(By.CLASS_NAME, "MuiGrid2-root")
      grid_elements = driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
      print(grid_elements)
      if len(grid_elements) == 15:
        seventh_element = grid_elements[13]  # 索引從 0 開始

        try:
            # 在該元素內找到 <a> 標籤
            a_tag = seventh_element.find_element(By.TAG_NAME, "a")

            # 在 <a> 標籤內找到 <div> 並具有 aria-labelledby="app-overview-unified-kpi-category-ranking"
            target_div = a_tag.find_element(By.XPATH, './/div//span[@aria-labelledby="app-overview-unified-kpi-category-ranking"]')

            # 取得文字內容
            text_content = target_div.text
            rank = parse_ranking_info(text_content)
            if rank:
                print(rank)
                data.append(rank)
            else:
                data.append(empty_rank)
        except:
           data.append(empty_rank)
      else:
        print("找不到足夠的 MuiGrid-item 元素")
        data.append(empty_rank)
  except Exception as e:
    print(f"An error occurred: {e}")
    return "Ranking not found"
  finally:
    driver.quit()
    return data

if __name__ == "__main__":
  try:
    rankings = get_ranking(["https://app.sensortower.com/overview/6553973564?country=TW", "https://app.sensortower.com/overview/6590627568?country=TW", "https://app.sensortower.com/overview/cyou.sk5s.app.onea4paperyourlife?country=TW"])
    for rank in rankings:
        print(f"Today's ranking: {rank['rank']}")
  except Exception as e:
    print(f"An error occurred: {e}")
