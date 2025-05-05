import os
import csv
from datetime import datetime
import pandas as pd
from flask import Flask, request, render_template, send_from_directory, jsonify, url_for
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from google import genai
from jinja2 import Template
import pdfkit

# --- Configuration ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    try:
        # Use genai.Client as in the original script
        client = genai.Client(api_key=api_key)
        # You might want to add a simple test call here if needed
        # e.g., list_models to ensure connectivity, but handle potential cost/quota
        print("GenAI Client initialized successfully.")
    except Exception as e:
        print(f"Error initializing GenAI Client: {e}")
        client = None # Ensure client is None if initialization fails
else:
    print("GEMINI_API_KEY not found in environment variables.")
    # Handle missing API key (client remains None)

# Ensure wkhtmltopdf is installed and optionally configure path
# Example for Windows, adjust as necessary:
# config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
# If wkhtmltopdf is in PATH, this might not be needed.

# Define file paths relative to this app's directory
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
RAW_COMMENTS_FILE = os.path.join(APP_ROOT, "list.txt")
CSV_COMMENTS_FILE = os.path.join(APP_ROOT, "list.csv")
HTML_OUTPUT_FILE = os.path.join(APP_ROOT, "output.html")
PDF_OUTPUT_DIR = os.path.join(APP_ROOT, "reports") # Directory to store generated PDFs

# Ensure PDF output directory exists
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)

# --- Helper Functions (Adapted from hw4) ---

def scrapeComments(code):
    """Scrapes comments for a given product code using Playwright."""
    print(f"Starting scrape for product code: {code}")
    try:
        with sync_playwright() as p:
            # Consider adding browser launch options if needed (e.g., proxy)
            browser = p.chromium.launch(headless=True) # Run headless for server environment
            page = browser.new_page()
            page.goto(f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={code}", timeout=60000) # Increased timeout
            page.wait_for_timeout(3000) # Allow time for dynamic content

            # Click the comments tab/button
            commentBtn = page.query_selector(".goodsCommendLi")
            if not commentBtn:
                print("Comment button not found.")
                browser.close()
                return False
            commentBtn.click()
            page.wait_for_timeout(2000) # Wait for comments section to load

            # Clear previous raw comments
            with open(RAW_COMMENTS_FILE, "w", encoding="utf-8") as file:
                file.write("")

            page_count = 0
            try:
                # Find page switcher elements to determine number of pages
                page_switcher_elements = page.query_selector_all("div.pageArea ul li")
                # Filter out non-page number elements if necessary based on structure
                page_count = len([el for el in page_switcher_elements if el.query_selector('a') and el.inner_text().strip().isdigit()])
                if page_count == 0 and page.query_selector(".reviewCardInner"): # Handle single page case
                    page_count = 1
                print(f"Found {page_count} pages of comments.")
            except Exception as e:
                 print(f"Could not determine page count, assuming 1 page. Error: {e}")
                 page_count = 1 # Default to 1 page if detection fails


            # Scrape comments page by page
            with open(RAW_COMMENTS_FILE, "a", encoding="utf-8") as file:
                for i in range(page_count):
                    print(f"Scraping page {i+1}...")
                    page.wait_for_selector(".reviewCardInner", timeout=10000) # Wait for comments to be present
                    li_elements = page.query_selector_all(".reviewCardInner")
                    if not li_elements:
                         print(f"No comments found on page {i+1}.")
                         continue # Skip if no comments found

                    for index, li in enumerate(li_elements):
                        file.write(li.inner_text() + "\n---\n")

                    # Go to next page if not the last page
                    if i < page_count - 1:
                        try:
                            # Find the correct next page link/button
                            # This selector might need adjustment based on actual site structure
                            next_page_selector = f"div.pageArea a:has-text('{i+2}')" # Example selector
                            nextBtn = page.query_selector(next_page_selector)
                            if nextBtn:
                                nextBtn.click()
                                page.wait_for_timeout(2000) # Wait for next page load
                            else:
                                print(f"Next page button for page {i+2} not found.")
                                break # Stop if next page link isn't found
                        except Exception as e:
                            print(f"Error navigating to next page: {e}")
                            break # Stop pagination on error
            browser.close()
            print("Scraping finished.")
            return True
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        if 'browser' in locals() and browser.is_connected():
            browser.close()
        return False

def tocsv():
    """Converts raw comments from list.txt to list.csv."""
    print("Converting raw comments to CSV...")
    if not os.path.exists(RAW_COMMENTS_FILE):
        print(f"Error: Raw comments file not found at {RAW_COMMENTS_FILE}")
        return False
    try:
        with open(RAW_COMMENTS_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = content.strip().split('---\n')
        data = []

        for block in blocks:
            lines = block.strip().split('\n')
            if not lines or not lines[0]: # Skip empty blocks
                continue

            # Initialize fields with defaults
            user, spec, date, rating, comment = "N/A", "N/A", "N/A", "N/A", ""

            # Basic parsing logic (might need refinement based on actual data variations)
            user = lines[0].strip('*').strip()
            if len(lines) > 2 and "規格" in lines[2]:
                 spec = lines[2].replace("規格 : ", "").strip()
            if len(lines) > 3:
                 date = lines[3].strip() # Assuming date is usually 4th line
            if len(lines) > 4 and "評等" in lines[4]: # Check if rating exists
                 rating = lines[4].strip()
                 comment = ''.join(lines[5:]).strip()
            elif len(lines) > 4: # If no rating, assume comment starts earlier
                 comment = ''.join(lines[4:]).strip()
            else: # Handle very short comments
                 comment = ""


            data.append([user, spec, date, rating, comment])

        with open(CSV_COMMENTS_FILE, "w", newline='', encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["使用者", "規格", "日期", "評分", "留言內容"])
            writer.writerows(data)

        print(f"Conversion complete! Output: {CSV_COMMENTS_FILE}")
        return True
    except Exception as e:
        print(f"An error occurred during CSV conversion: {e}")
        return False

# --- PDF Generation and AI Analysis (Adapted from handlecsv.py) ---

html_template_str = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>商品評論分析報告</title>
    <style>
        body { font-family: 'Arial', 'Microsoft JhengHei', sans-serif; text-align: left; margin: 20px; }
        h2 { text-align: center; }
        .table { width: 100%; margin: 20px 0; border-collapse: collapse; table-layout: fixed; } /* Use fixed layout */
        .table th, .table td { border: 1px solid black; padding: 8px; text-align: left; word-wrap: break-word; } /* Enable word wrap */
        .table th { background-color: #f2f2f2; font-weight: bold; }
        .response-block { margin-bottom: 20px; padding: 15px; border: 1px solid #eee; border-radius: 5px; background-color: #f9f9f9;}
        pre { white-space: pre-wrap; word-wrap: break-word; } /* Ensure preformatted text wraps */
    </style>
</head>
<body>
    <h2>商品評論分析報告</h2>
    {% if table %}
        {{ table | safe }}
    {% else %}
        <div class="response-block">
            <pre>{{ text_content | safe }}</pre>
        </div>
    {% endif %}
</body>
</html>
"""
html_template = Template(html_template_str)

def create_html_table(df: pd.DataFrame):
    """Generates HTML table from DataFrame."""
    if df is None or df.empty:
        return ""
    # Reset index if it's meaningful or drop if not
    # df = df.reset_index(drop=True)
    return df.to_html(index=False, classes="table", border=1) # Added border=1 for clarity

def parse_markdown_table(markdown_text: str) -> pd.DataFrame:
    """Parses Markdown table into DataFrame."""
    lines = markdown_text.strip().splitlines()
    lines = [line.strip() for line in lines if line.strip()]
    table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]

    if not table_lines or len(table_lines) < 3: # Need header, separator, and at least one data row
        return None

    # Extract headers
    header_line = table_lines[0]
    headers = [h.strip() for h in header_line.strip("|").split("|")]

    # Extract data rows
    data = []
    for line in table_lines[2:]: # Skip header and separator
        row = [cell.strip() for cell in line.strip("|").split("|")]
        if len(row) == len(headers):
            data.append(row)
        else:
            print(f"Skipping malformed row: {line}") # Log skipped rows

    if not data:
        return None

    try:
        df = pd.DataFrame(data, columns=headers)
        return df
    except Exception as e:
        print(f"Error creating DataFrame from parsed table: {e}")
        return None


def generate_pdf_report(text_content: str = None) -> str:
    """Generates PDF report from text, attempting to parse Markdown tables."""
    print("Generating PDF report...")
    html_table = None
    final_text_content = text_content if text_content else "No content provided."

    # Attempt to parse Markdown table from the text content
    parsed_df = parse_markdown_table(final_text_content)
    if parsed_df is not None and not parsed_df.empty:
        print("Successfully parsed Markdown table.")
        html_table = create_html_table(parsed_df)
        # Optional: Clear text_content if table is successfully parsed and rendered
        # final_text_content = "See table below."
    else:
        print("No Markdown table found or parsed, rendering raw text.")
        # Keep final_text_content as is

    # Render HTML using the template
    html_content = html_template.render(table=html_table, text_content=final_text_content)

    # Save intermediate HTML (optional, for debugging)
    with open(HTML_OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write(html_content)
    print(f"Intermediate HTML saved to: {HTML_OUTPUT_FILE}")

    # Generate PDF filename
    pdf_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_filepath = os.path.join(PDF_OUTPUT_DIR, pdf_filename)

    try:
        # Specify configuration if needed, especially on Windows or if wkhtmltopdf is not in PATH
        # pdfkit.from_file(HTML_OUTPUT_FILE, pdf_filepath, configuration=config, options={"enable-local-file-access": ""})
        pdfkit.from_file(HTML_OUTPUT_FILE, pdf_filepath, options={"enable-local-file-access": ""}) # Use empty string value
        print(f"PDF report generated successfully: {pdf_filepath}")
        return pdf_filename # Return only the filename for the download route
    except Exception as e:
        print(f"Error generating PDF: {e}")
        # Consider how to report this error back to the user
        return None


def analyze_comments_with_ai(user_prompt: str):
    """Analyzes comments from CSV using GenAI and generates PDF."""
    print("Starting AI analysis...")
    # Check if the client was initialized successfully
    if not client:
        return "Error: GenAI Client not initialized. Check API Key and configuration.", None

    if not os.path.exists(CSV_COMMENTS_FILE):
        return "Error: CSV file not found. Please scrape comments first.", None

    try:
        df = pd.read_csv(CSV_COMMENTS_FILE)
        if df.empty:
            return "CSV file is empty. No comments to analyze.", None

        total_rows = df.shape[0]
        block_size = 20 # Process in blocks of 20
        cumulative_response = ""

        print(f"Processing {total_rows} comments in blocks of {block_size}...")
        # Removed model initialization here, will use client directly

        for i in range(0, total_rows, block_size):
            block = df.iloc[i:min(i+block_size, total_rows)]
            block_csv = block.to_csv(index=False)
            prompt = (f"以下是CSV格式的商品評論資料第 {i+1} 到 {min(i+block_size, total_rows)} 筆：\n"
                      f"```csv\n{block_csv}\n```\n\n"
                      f"請根據以下指示分析這些評論：\n{user_prompt}\n\n"
                      f"請將分析結果整理成Markdown表格格式，包含適當的欄位標題。")

            print(f"Sending prompt for block {i//block_size+1} to AI...")
            # print(prompt) # Uncomment to debug the exact prompt

            try:
                # Use client.models.generate_content as in the original script
                # Using the specific model from hw4
                response = client.models.generate_content(
                    model="gemini-2.5-pro-exp-03-25", # Use the specific model from hw4
                    contents=[prompt] # Pass prompt as contents list
                )
                # Assuming response structure is similar and .text gives the result
                block_response = response.text.strip()
                cumulative_response += f"--- 分析區塊 {i//block_size+1} ---\n{block_response}\n\n"
            except Exception as ai_error:
                 print(f"Error calling GenAI for block {i//block_size+1}: {ai_error}")
                 # Consider adding more specific error details if possible
                 cumulative_response += f"--- 分析區塊 {i//block_size+1} 失敗：{ai_error} ---\n\n"


        print("AI analysis complete.")
        # Generate PDF from the combined responses
        pdf_filename = generate_pdf_report(text_content=cumulative_response)

        if pdf_filename:
            return cumulative_response, pdf_filename
        else:
            return cumulative_response, None # Return text even if PDF fails

    except FileNotFoundError:
        return f"Error: CSV file not found at {CSV_COMMENTS_FILE}.", None
    except pd.errors.EmptyDataError:
         return f"Error: CSV file {CSV_COMMENTS_FILE} is empty.", None
    except Exception as e:
        print(f"An error occurred during AI analysis: {e}")
        return f"An unexpected error occurred during analysis: {e}", None


# --- Flask Routes ---

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape_route():
    """Handles scraping request."""
    goodCode = request.form.get('goodCode')
    if not goodCode:
        return jsonify({"status": "error", "message": "Product ID is required."}), 400

    print(f"Received scrape request for code: {goodCode}")
    scrape_success = scrapeComments(goodCode)
    if not scrape_success:
         return jsonify({"status": "error", "message": "Scraping failed."}), 500

    csv_success = tocsv()
    if not csv_success:
        return jsonify({"status": "error", "message": "CSV conversion failed."}), 500

    return jsonify({"status": "success", "message": f"Successfully scraped and saved comments to {CSV_COMMENTS_FILE}."})


@app.route('/report', methods=['POST'])
def report_route():
    """Handles report generation request."""
    user_prompt = request.form.get('user_prompt')
    if not user_prompt:
        return jsonify({"status": "error", "message": "Analysis prompt is required."}), 400

    print(f"Received report request with prompt: {user_prompt[:100]}...") # Log first 100 chars
    analysis_text, pdf_filename = analyze_comments_with_ai(user_prompt)

    if pdf_filename:
        pdf_url = url_for('download_file', filename=pdf_filename, _external=True)
        return jsonify({
            "status": "success",
            "message": "Report generated successfully.",
            "analysis_summary": analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text, # Send a summary
            "pdf_filename": pdf_filename,
            "pdf_url": pdf_url
        })
    else:
        # Handle case where PDF generation failed but analysis might have text
        return jsonify({
            "status": "error",
            "message": "AI analysis completed, but PDF generation failed.",
            "analysis_summary": analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text
         }), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Serves generated PDF files for download."""
    print(f"Download request for: {filename}")
    safe_path = os.path.join(PDF_OUTPUT_DIR, filename)
    # Basic security check: ensure the path is still within the intended directory
    if not os.path.abspath(safe_path).startswith(os.path.abspath(PDF_OUTPUT_DIR)):
        return "Forbidden", 403
    if not os.path.exists(safe_path):
        return "File not found", 404
    return send_from_directory(PDF_OUTPUT_DIR, filename, as_attachment=True)


if __name__ == '__main__':
    # Use waitress or gunicorn for production
    # For development:
    app.run(debug=True, host='0.0.0.0', port=5001) # Use a different port if 5000 is common
