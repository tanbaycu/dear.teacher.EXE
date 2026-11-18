"""Dear Teacher.exe — Thiệp điện tử ASCII 3D chào mừng 44 năm Ngày Nhà giáo Việt Nam 20/11.

Sản phẩm tham gia hoạt động Dear Teacher.exe — Trường Đại học Tôn Đức Thắng (Đoàn - Hội Khoa CNTT).

Cách chạy nhanh:
    pip install -r requirements.txt
    python dear_teacher.py

Tùy chỉnh tên người nhận / lời chúc / MSSV khi nộp bài:
    python dear_teacher.py --to "Cô Lan" --from "Sinh viên Khoa CNTT" --mssv 52600305

Phím điều khiển:
    Space tạm dừng · R chạy lại · T đổi bộ lời chúc · S lưu ảnh PNG · Esc thoát
"""

import argparse
import os
import sys
import time
from pathlib import Path

import pygame

from constants import DEFAULT_STUDENT_ID, H, LOOP, T_MSG, TITLE, W, WISH_PRESETS
from renderer import Renderer

HERE = Path(__file__).parent


def window_size():
    """Tự co kích thước cửa sổ vừa với màn hình người dùng mà vẫn giữ đúng tỷ lệ dọc."""
    info = pygame.display.Info()
    k = 1.0
    if info.current_w > 0 and info.current_h > 0:
        k = min(1.0, 0.88 * info.current_h / H, 0.95 * info.current_w / W)
    return int(W * k), int(H * k)


def build_presets(recipient=None, sender=None, custom_msg=None):
    """Tạo danh sách lời chúc sạch; chỉ cá nhân hóa phần lời chúc khi người dùng truyền tham số CLI."""
    presets = list(WISH_PRESETS)
    if recipient or sender or custom_msg:
        header = f"DEAR {recipient.upper()} · 20/11 · 44 NĂM TRI ÂN" if recipient else presets[0][0]
        body = custom_msg if custom_msg else (
            f"Kính chúc {recipient} luôn mạnh khỏe, hạnh phúc và nhiệt huyết <3"
            if recipient
            else presets[0][1]
        )
        footer = f"Trân trọng gửi từ {sender}" if sender else presets[0][2]
        presets.insert(0, (header, body, footer))
    return presets


def render_snapshot(seconds, output_path, wish_lines, student_id=DEFAULT_STUDENT_ID):
    """Kết xuất nhanh một thời điểm `seconds` thành file PNG mà không cần mở cửa sổ GUI."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    try:
        renderer = Renderer()
        # Khởi tạo lịch sử vệt sáng bằng vài bước ngắn trước thời điểm chụp để trail tự nhiên.
        for dt in (0.15, 0.10, 0.05, 0.0):
            t_step = max(0.0, seconds - dt)
            surface = renderer.draw(t_step, wish_lines, student_id=student_id)
        pygame.image.save(surface, str(output_path))
    finally:
        pygame.quit()


def parse_args(argv):
    """Phân tích tham số dòng lệnh để cá nhân hóa thiệp hoặc xuất ảnh xem trước."""
    parser = argparse.ArgumentParser(description=TITLE)
    parser.add_argument("--to", dest="recipient", help="Tên Thầy/Cô hoặc đơn vị nhận thiệp")
    parser.add_argument("--from", dest="sender", help="Tên sinh viên / lớp gửi lời chúc")
    parser.add_argument("--mssv", dest="student_id", default=DEFAULT_STUDENT_ID, help="Mã số sinh viên hiển thị ở HUD")
    parser.add_argument("--msg", dest="custom_msg", help="Lời chúc tùy chỉnh hiển thị ở dòng chính")
    parser.add_argument("--loop", action="store_true", help="Tự chạy lại từ đầu sau mỗi chu kỳ (mặc định giữ mở để đọc lời chúc)")
    parser.add_argument("--snapshot", type=float, metavar="SEC", help="Xuất ảnh PNG tại giây SEC rồi thoát")
    parser.add_argument("--out", type=Path, help="Đường dẫn file ảnh khi dùng --snapshot")
    return parser.parse_args(argv)


def main(argv=None):
    """Vòng lặp chính chạy animation ở 30 FPS; giữ cảnh mở sau khi nở hoa để đọc hết lời chúc."""
    args = parse_args(argv)
    presets = build_presets(args.recipient, args.sender, args.custom_msg)

    if args.snapshot is not None:
        out_path = args.out or (HERE / f"dear_teacher_preview_{int(args.snapshot)}s.png")
        render_snapshot(args.snapshot, out_path, presets[0], student_id=args.student_id)
        print(f"Saved snapshot: {out_path}")
        return 0

    pygame.init()
    try:
        size = window_size()
        window = pygame.display.set_mode(size)
        pygame.display.set_caption(TITLE)
        renderer, clock = Renderer(), pygame.time.Clock()
        t, msg_t, paused, wish_idx = 0.0, 0.0, False, 0
        screen = renderer.draw(t, presets[wish_idx], student_id=args.student_id, msg_t=msg_t)
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    return 0
                if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                    paused = not paused
                if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                    t = 0.0
                    msg_t = 0.0
                if e.type == pygame.KEYDOWN and e.key == pygame.K_t:
                    wish_idx = (wish_idx + 1) % len(presets)
                    # Nếu đang ở phần đã nở hoa thì chỉ gõ lại lời chúc mới, không phá nhịp hoa đang đẹp.
                    if t >= T_MSG:
                        msg_t = T_MSG
                    screen = renderer.draw(t, presets[wish_idx], student_id=args.student_id, msg_t=msg_t)
                if e.type == pygame.KEYDOWN and e.key == pygame.K_s:
                    pygame.image.save(screen, str(HERE / f"dear_teacher_{int(time.time())}.png"))
            dt = clock.tick(30) / 1000.0
            if not paused:
                step = min(dt, 1.0 / 15.0)
                t += step
                msg_t += step
                if args.loop and t > LOOP:
                    t = 0.0
                    msg_t = 0.0
                screen = renderer.draw(t, presets[wish_idx], student_id=args.student_id, msg_t=msg_t)
            window.blit(
                screen if size == (W, H) else pygame.transform.smoothscale(screen, size),
                (0, 0),
            )
            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    sys.exit(main())
