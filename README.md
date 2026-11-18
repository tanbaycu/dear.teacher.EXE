# Dear Teacher.exe

Thiệp điện tử ASCII 3D chào mừng **Kỷ niệm 44 năm Ngày Nhà giáo Việt Nam (20/11)** — Trường Đại học Tôn Đức Thắng (Đoàn – Hội Khoa Công nghệ thông tin).

## Kịch bản hiển thị

1. **Khởi động Terminal (`0.2s → 4.6s`)**: Khung laptop 3D dựng lên từ dưới lên cùng bàn phím phát sáng và thanh tiến trình khởi động `DEAR_TEACHER.EXE`.
2. **Hoa nở từ những dòng code (`3.4s → 9.8s`)**: Màn hình 3D hiển thị dấu mốc **`20/11 · 44 <3`**, đồng thời cành lá, nơ vàng và 7 bông hồng 3D lần lượt nở phía trên nắp máy.
3. **Compile thành công (`10.6s`)**: Làn sóng sáng quét qua toàn bộ tác phẩm, bắn tỏa hạt sáng và cánh hoa rơi nhẹ; xung quanh là các ngôn ngữ lập trình (`C`, `Python`, `C++`, `Java`, `JS`, `HTML`, `C#`, `Go`, `SQL`, `TS`, ...) trôi nhẹ hai bên.
4. **Thông điệp Tri ân (`11.2s → giữ mở`)**: Ba dòng thiệp tiếng Việt tối giản gõ từng chữ bên dưới kèm biểu tượng `<3` đập theo nhịp. Thiệp giữ nguyên trạng thái nở hoa để người xem đọc trọn vẹn lời chúc.

## Cấu trúc mã nguồn

- `dear_teacher.py`: Điểm khởi chạy chính, xử lý vòng lặp 30 FPS, phím điều khiển và CLI.
- `constants.py`: Bảng màu tối giản, mốc thời gian, danh sách ngôn ngữ và bộ lời chúc.
- `geometry.py`: Sinh point-cloud 3D cho laptop, bàn phím, màn hình và 7 bông hồng xoắn tham số.
- `effects.py`: Trường sao nền, pháo hoa compile, cánh hoa rơi, tia lóe 4 cánh và nhãn ngôn ngữ.
- `scene.py`: Chiếu phối cảnh 3D sang lưới ASCII 2D, tô bóng, viền tách lớp và bố cục chữ tiếng Việt.
- `renderer.py`: Kết xuất `pygame-ce`, trail chuyển động, quầng sáng Gaussian 2 tầng và HUD.

## Cài đặt & chạy

Yêu cầu **Python 3.10+** (`numpy>=1.24`, `pygame-ce>=2.5`):

```bash
pip install -r requirements.txt
python dear_teacher.py
```

### Tham số tùy chọn

```bash
# Cá nhân hóa người nhận và người gửi
python dear_teacher.py --to "Cô Lan" --from "Sinh viên Khoa CNTT"

# Tùy chỉnh MSSV hiển thị ở HUD
python dear_teacher.py --mssv 52600305

# Xuất ảnh PNG tại thời điểm SEC (giây) không cần mở cửa sổ GUI
python dear_teacher.py --snapshot 16 --out preview.png
```

### Phím điều khiển

- `Space`: Tạm dừng / tiếp tục
- `R`: Chạy lại từ đầu
- `T`: Đổi và gõ lại bộ lời chúc
- `S`: Lưu ảnh chụp màn hình PNG
- `Esc`: Thoát

## Giấy phép

Phát hành theo giấy phép [MIT License](LICENSE).
