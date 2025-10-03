# Chương Trình Tự Động Đăng Bài Fanpage

Một chương trình dùng Python được thiết kế để tự động tìm kiếm từ nguồn cho trước , soạn thảo và đăng bài nhờ Gemini để up lên Fanpage Facebook

## Tính năng

- **Tự động tìm kiếm:** Sử dụng Selenium để tìm kiếm công thức trên Cookpad.com dựa trên các từ khóa ưu tiên.
- **Trích xuất dữ liệu thông minh:** Phân tích dữ liệu có cấu trúc (JSON-LD) để lấy thông tin chi tiết của công thức một cách chính xác.
- **Soạn thảo nội dung bằng AI:** Tận dụng API của Gemini để tự động viết lại nội dung công thức thành một bài đăng hấp dẫn theo format chuẩn.
- **Tự động đăng bài:** Sử dụng Facebook Graph API để đăng bài viết kèm hình ảnh trực tiếp lên Fanpage.
- **Chống trùng lặp:** Ghi nhớ các công thức đã đăng vào một file để tránh đăng lại nội dung.

---

## 🛠️ Hướng dẫn Cài đặt

### 1. Tải repository về máy

git clone https://github.com/lengoc-tuyen/Facebook-Fanpage-Auto-Poster.git
cd Facebook-Fanpage-Auto-Poster

2. Tạo và kích hoạt Môi trường ảo

Việc này giúp các thư viện của dự án được tách biệt khỏi hệ thống.


python3.11 -m venv venv
source venv/bin/activate
3. Cài đặt các thư viện cần thiết


pip install -r requirements.txt
4. Tải chromedriver

Kiểm tra phiên bản trình duyệt Chrome trên máy bạn.

Truy cập trang Chrome for Testing để tải về phiên bản chromedriver tương ứng với hệ điều hành của bạn.

Giải nén và đặt file chromedriver vào thư mục gốc của dự án.

⚙️ Cấu hình
Tạo một file mới tên là .env trong thư mục gốc của dự án.

Sao chép nội dung dưới đây vào file .env và thay thế bằng thông tin của bạn. File này được Git bỏ qua và sẽ giữ an toàn cho các mã bí mật của bạn.

GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
FACEBOOK_PAGE_ID="YOUR_FACEBOOK_PAGE_ID"
FACEBOOK_PAGE_ACCESS_TOKEN="YOUR_FACEBOOK_PAGE_ACCESS_TOKEN"

🚀 Cách sử dụng
Sau khi đã hoàn thành các bước cài đặt và cấu hình, bạn chỉ cần chạy bot từ Terminal:


python bot.py
Bot sẽ bắt đầu quy trình làm việc: tìm công thức mới, tạo nội dung và đăng bài lên Fanpage của bạn.

⚠️ Lưu ý Quan trọng
Các "selector" dùng để cào dữ liệu từ Cookpad có thể bị lỗi thời nếu trang web cập nhật giao diện. Nếu bot không tìm hoặc lấy được dữ liệu, bạn có thể cần phải dùng công cụ "Inspect" của trình duyệt để tìm các selector mới và cập nhật lại trong code.
