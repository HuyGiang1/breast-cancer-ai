# Deploy Guide

## Mục tiêu

Triển khai theo mô hình:

- `api`: FastAPI + ML/DL models
- `web`: Nginx phục vụ frontend tĩnh và reverse proxy `/api` + `/results`

Frontend đã được chỉnh để gọi API qua cùng domain, nên không cần mở riêng port `8000` ra internet.

## 1. Chuẩn bị server

Yêu cầu tối thiểu:

- Ubuntu 22.04 hoặc 24.04
- Docker Engine
- Docker Compose plugin
- RAM nên từ 4GB trở lên nếu dùng DL

Cài Docker:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Đăng xuất rồi đăng nhập lại sau khi thêm user vào group `docker`.

## 2. Clone dự án

```bash
git clone <repo-url>
cd breast-cancer-ai
```

## 3. Tạo file môi trường

Copy từ mẫu:

```bash
cp .env.example .env
```

Thiết lập tối thiểu để deploy an toàn hơn:

```env
AI_ADVISOR_PROVIDER=local
APP_MAIL_MODE=file
APP_FRONTEND_URL=https://ten-mien-cua-ban
DL_PRELOAD_ON_STARTUP=false
```

Nếu muốn dùng Gemini/OpenAI hoặc SMTP thì điền thêm key thật vào `.env`.

## 4. Khởi chạy

```bash
mkdir -p backend/data frontend/results
docker compose up -d --build
```

Kiểm tra trạng thái:

```bash
docker compose ps
docker compose logs -f api
docker compose logs -f web
```

## 5. Kiểm tra sau deploy

Mở trên trình duyệt:

- `http://SERVER_IP/`
- `http://SERVER_IP/api/v1/models/`
- `http://SERVER_IP/docs`

Nếu API chạy nhưng web lỗi, kiểm tra `web` container trước.

## 6. Gắn domain và SSL

Cách đơn giản:

- Trỏ `A record` của domain về IP server
- Dùng Nginx ngoài host hoặc Cloudflare Tunnel để cấp HTTPS

Nếu bạn đã có Nginx trên host, reverse proxy domain về `http://127.0.0.1:80`.

## 7. Cập nhật phiên bản mới

```bash
git pull
docker compose up -d --build
```

## 8. Dữ liệu cần backup

Các thư mục/file quan trọng:

- `backend/data/app.db`
- `models/`
- `.env`

## 9. Lỗi thường gặp

### Frontend gọi sai API

Frontend hiện dùng `window.location.origin`, nên web và API phải đi qua cùng domain/nginx.

### DL load chậm hoặc fail khi startup

Tạm đặt:

```env
DL_PRELOAD_ON_STARTUP=false
```

Rồi warmup sau khi hệ thống đã lên.

### Reset password không gửi mail

Nếu `APP_MAIL_MODE=file`, token reset sẽ được ghi vào:

```text
backend/data/outbox/password_reset.jsonl
```
