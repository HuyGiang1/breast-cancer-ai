#!/bin/bash
# Lấy đường dẫn thư mục hiện tại của file
cd "$(dirname "$0")"

echo "========================================================="
echo "🚀 KHỞI ĐỘNG HỆ THỐNG AI CHẨN ĐOÁN UNG THƯ VÚ"
echo "========================================================="

echo "🔍 Kiểm tra dịch vụ hiện tại..."

BACKEND_ALREADY_RUNNING=0
FRONTEND_ALREADY_RUNNING=0

if lsof -ti:8000 > /dev/null 2>&1; then
	BACKEND_ALREADY_RUNNING=1
fi

if lsof -ti:8080 > /dev/null 2>&1; then
	FRONTEND_ALREADY_RUNNING=1
fi

# Kích hoạt môi trường gốc của AI
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.

echo "🧠 Đang nạp các Mô hình Trí tuệ nhân tạo (Backend)..."
if [ "$BACKEND_ALREADY_RUNNING" -eq 0 ]; then
	cd backend
	mkdir -p ../experiments/results
	uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../experiments/results/backend_startup.log 2>&1 &
	BACKEND_PID=$!
	cd ..
else
	echo "✅ Backend đã chạy sẵn trên port 8000 (không khởi động lại)."
	BACKEND_PID=""
fi

echo "🎨 Đang tải Giao diện Website (Frontend)..."
if [ "$FRONTEND_ALREADY_RUNNING" -eq 0 ]; then
	cd frontend
	python3 -m http.server 8080 --bind 0.0.0.0 > ../experiments/results/frontend_startup.log 2>&1 &
	FRONTEND_PID=$!
	cd ..
else
	echo "✅ Frontend đã chạy sẵn trên port 8080 (không khởi động lại)."
	FRONTEND_PID=""
fi

echo "========================================================="
echo "✅ HỆ THỐNG ĐÃ SẴN SÀNG!"
echo "🌐 Đang tự động mở trang web..."
echo "========================================================="

# Mở FE ngay để người dùng không phải chờ backend load mô hình
open http://localhost:8080

# Theo dõi backend ở nền và thông báo khi sẵn sàng
echo "⏳ Đang kiểm tra backend sẵn sàng (có thể mất 1-3 phút nếu model load nặng)..."
for i in {1..180}; do
	if curl -s --max-time 2 http://localhost:8000/api/v1/models/ > /dev/null; then
		echo "✅ Backend đã sẵn sàng. Bạn có thể chọn model và chạy dự đoán."
		break
	fi
	if (( i % 15 == 0 )); then
		echo "...vẫn đang chờ backend (${i}s)"
	fi
	sleep 1
done

if ! curl -s --max-time 2 http://localhost:8000/api/v1/models/ > /dev/null; then
	echo "⚠️ Backend chưa sẵn sàng sau 180 giây."
	echo "   Xem log: experiments/results/backend_startup.log"
	echo "   FE vẫn đang mở tại http://localhost:8080 và sẽ tự retry kết nối."
fi

echo ""
echo "⚠️ LƯU Ý QUAN TRỌNG:"
echo "- Bạn có thể đóng cửa sổ launcher, backend/frontend vẫn chạy nền để mở lại nhanh."
echo "- Nếu muốn tắt dịch vụ thủ công: lsof -ti:8000 | xargs kill -9 ; lsof -ti:8080 | xargs kill -9"
echo "- Test nhanh API: source venv/bin/activate && python scripts/smoke_test_api.py"
echo ""

# Xử lý khi người dùng ấn Ctrl+C để tắt máy một cách sạch sẽ
trap "echo '🛑 Đóng launcher. Dịch vụ nền vẫn giữ chạy để lần sau mở nhanh hơn.'; exit" INT TERM EXIT
wait
