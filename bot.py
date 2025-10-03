import requests
import json
import os
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
import google.generativeai as genai
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from dotenv import load_dotenv 

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")


# Danh sách nguyên liệu ưu tiên
PRIORITY_INGREDIENTS = [
    "tảo chile",
    "sườn non chay",
    "rong biển sấy mè",
    "nấm lộc nhung"
]

# File để lưu lại các công thức đã đăng
POSTED_RECIPES_FILE = "posted_recipes.txt"

# Khởi tạo client OpenAI
genai.configure(api_key=GOOGLE_API_KEY)
# ==============================================================================
# CÁC HÀM CHỨC NĂNG
# ==============================================================================

def load_posted_recipes():
    """Tải danh sách các URL công thức đã đăng từ file."""
    if not os.path.exists(POSTED_RECIPES_FILE):
        return set()
    with open(POSTED_RECIPES_FILE, 'r') as f:
        return set(line.strip() for line in f)

def save_posted_recipe(url):
    """Lưu URL của công thức vừa đăng vào file."""
    with open(POSTED_RECIPES_FILE, 'a') as f:
        f.write(url + '\n')


# HÀM SEARCH_COOKPAD 
def search_cookpad(keyword):
    print(f"Đang tìm công thức với từ khóa: '{keyword}' bằng Selenium...")
    url = f"https://cookpad.com/vn/tim-kiem/{keyword}"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = None
    try:
        service = ChromeService(executable_path='./chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        
        driver.get(url)
        
        # Chờ tối đa 10 giây cho đến khi ÍT NHẤT MỘT công thức xuất hiện.
        wait = WebDriverWait(driver, 10)
        new_selector = "a[href^='/vn/cong-thuc/']"
        print(f"...Đang chờ các công thức xuất hiện ...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, new_selector)))
        # ===============================================

        page_source = driver.page_source # Lấy mã nguồn trang sau khi đã tải xong
        soup = BeautifulSoup(page_source, "html.parser") # Sắp xếp lại bằng BeautifulSoup

        links = []
        # Dùng selector mới để trích xuất link
        for a in soup.select(new_selector):
            href = a.get("href")
            if href and href.startswith("/vn/cong-thuc/"):
                full_link = "https://cookpad.com" + href
                if full_link not in links:
                    links.append(full_link)
        # vòng for này đúng rồi 
        if not links:
            print("Không tìm thấy link nào. Giao diện có thể đã thay đổi.")
        
        return links

    except Exception as e:
        print(f"Lỗi khi tìm kiếm trên Cookpad bằng Selenium: {e}")
        # Chụp man hình để debug nếu có lỗi
        if driver:
            driver.save_screenshot("debug_screenshot.png")
            print("Đã lưu ảnh màn hình lỗi vào file debug_screenshot.png để kiểm tra.")
        return []
    finally:
        if driver:
            driver.quit()

# hàm này đúng ròi
def scrape_recipe_details(url):
    """Lấy chi tiết công thức bằng phương pháp kết hợp:
    - Tên và Nguyên liệu: HTML 
    - Các bước làm và Ảnh: Đọc từ JSON-LD
    """
    print(f"Đang lấy chi tiết từ: {url} ...")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # --- LẤY DỮ LIỆU ---

        # 1. Lấy Tên món 
        title = soup.select_one("h1").get_text(strip=True)

        # 2. Lấy Nguyên liệu 
        ingredients_text = "\n".join([li.get_text(strip=False) for li in soup.select("li[id^='ingredient_']")])
        
        
        # Tìm đúng thẻ script JSON-LD chứa công thức
        script_tags = soup.find_all('script', type='application/ld+json')
        recipe_data = None
        for tag in script_tags:
            try:
                data = json.loads(tag.string)
                if data.get('@type') == 'Recipe':
                    recipe_data = data
                    break
            except (json.JSONDecodeError, AttributeError):
                continue

        if not recipe_data:
            print("Không tìm thấy dữ liệu JSON-LD cho các bước làm và ảnh.")
            steps_text = ""
            image_url = None
        else:
            # 3. Lấy Các bước làm từ JSON-LD
            steps_list = recipe_data.get('recipeInstructions', [])
            steps_items = [f"{i+1}. {step.get('text', '')}" for i, step in enumerate(steps_list)]
            steps_text = "\n".join(steps_items)

            # 4. Lấy Ảnh từ JSON-LD
            image_url = recipe_data.get('image', None)
        

        if not title or not ingredients_text or not steps_text or not image_url:
            print("Thiếu thông tin (tên, nguyên liệu, bước làm hoặc ảnh).")
            return None
        
        print(f"URL ảnh: {image_url}")

        return {
            "title": title,
            "ingredients": ingredients_text,
            "steps": steps_text,
            "image_url": image_url 
        }

    except Exception as e:
        print(f"Lỗi khi lấy chi tiết công thức: {e}")
        return None 

def format_post_with_gemini(recipe_details): 
    """Dùng Gemini để soạn nội dung bài đăng."""
    print("Đang nhờ Gemini biên soạn bài đăng...")
    
    # Chọn model của Gemini
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Bạn là một trợ lý biên tập nội dung cho fanpage ẩm thực chay 'An Thảo'. Nhiệm vụ của bạn là soạn một bài đăng hấp dẫn dựa trên thông tin công thức được cung cấp.

    Dựa vào thông tin công thức dưới đây:
    - Tên món: {recipe_details['title']}
    - Nguyên liệu thô:
    {recipe_details['ingredients']}
    - Các bước làm thô:
    {recipe_details['steps']}

    Hãy biên soạn lại thành một bài đăng hoàn chỉnh theo đúng cấu trúc sau, không thêm bất kỳ ghi chú nào khác:

    [CHUYÊN MỤC NẤU ĂN CÙNG AN THẢO]

    (Một đoạn giới thiệu ngắn, hấp dẫn về món ăn, khoảng 2-3 câu, mở đầu bằng chào cả nhà, ...)

    NGUYÊN LIỆU:
    - (Liệt kê các nguyên liệu và định lượng, định dạng lại cho đẹp mắt)

    CÁCH LÀM:
    1. (Viết lại các bước thực hiện một cách rõ ràng, văn phong thân thiện, dễ hiểu)
    2. ...

    KẾT QUẢ:
    (Mô tả thành phẩm, ví dụ: "Món ăn có màu sắc bắt mắt, hương vị đậm đà, dùng với cơm nóng thì còn gì bằng!")

    Chúc các bạn thành công!
    Mời các bạn tham khảo và ủng hộ các sản phẩm bên mình ạ https://www.facebook.com/share/p/1AU1vXZR2V/
    """
    
    try:
        response = model.generate_content(prompt)
        post_content = response.text.strip()
        return post_content
        # tới đây đúng ròi
    except Exception as e:
        print(f"Lỗi khi gọi API của Gemini: {e}")
        return None

def post_to_facebook(message, image_url):
    """Đăng bài viết kèm ảnh lên Fanpage Facebook."""
    print(f"Đang đăng bài lên Fanpage...")
    post_url = f"https://graph.facebook.com/{FACEBOOK_PAGE_ID}/photos"
    payload = {
        'url': image_url,
        'caption': message,
        'access_token': FACEBOOK_PAGE_ACCESS_TOKEN
    }
    try:
        response = requests.post(post_url, data=payload)
        print("Phản hồi từ Facebook:", response.json())
        response.raise_for_status()
        print("✅ Đăng bài thành công!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi khi đăng bài lên Facebook: {e}")
        print("Phản hồi từ Facebook:", response.json())
        return False

def main():
    print("===================================")
    print("🤖 Bot nấu ăn An Thảo bắt đầu chạy!")
    print("===================================")
    
    posted_recipes = load_posted_recipes()
    print(f"Đã có {len(posted_recipes)} công thức được đăng trước đó.")
    
    recipe_url_to_post = None

    for ingredient in PRIORITY_INGREDIENTS:
        if recipe_url_to_post:
            break
        
        links = search_cookpad(ingredient)
        if not links:
            print(f"Không tìm thấy công thức nào cho '{ingredient}'.")
            continue
            
        for link in links:
            if link not in posted_recipes:
                recipe_url_to_post = link
                print(f"✅ Đã tìm thấy công thức mới chưa đăng: {link}")
                break
    
    if not recipe_url_to_post:
        print("Không tìm thấy công thức nào mới phù hợp. Bot sẽ dừng lại.")
        return

    details = scrape_recipe_details(recipe_url_to_post)
    if not details:
        print("Không thể lấy chi tiết công thức. Bot dừng lại.")
        return

    post_content = format_post_with_gemini(details)
    if not post_content:
        print("Không thể tạo nội dung bài đăng từ Gemini. Bot dừng lại.")
        return

    image_url = details.get("image_url")
    if not image_url:
        print("Không tìm thấy URL ảnh trong chi tiết công thức. Bot dừng lại.")
        return
        
    success = post_to_facebook(post_content, image_url)
    
    if success:
        save_posted_recipe(recipe_url_to_post)
        print(f"Đã lưu công thức '{recipe_url_to_post}' vào danh sách đã đăng.")

    print("===================================")
    print("🤖 Bot đã hoàn thành nhiệm vụ!")
    print("===================================")


if __name__ == "__main__":
    main()