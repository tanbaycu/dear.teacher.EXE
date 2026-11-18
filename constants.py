"""Hằng số cấu hình, bảng màu tối giản, mốc thời gian và nội dung thiệp cho Dear Teacher.exe."""

import numpy as np

TITLE = "Dear Teacher.exe · 44 Năm Ngày Nhà Giáo Việt Nam 20/11 · TDTU"
CREDIT = "TRƯỜNG ĐẠI HỌC TÔN ĐỨC THẮNG · Đoàn - Hội Khoa CNTT"
DEFAULT_STUDENT_ID = "52600305"

TAU = np.pi * 2
LOOP = 22.0  # Chu kỳ dựng hình và giữ nhịp xoay 3D (giây)

# Mốc thời gian kịch bản dẫn dắt từ lúc khởi động terminal đến khi hoa nở và hiện lời chúc.
T_LAPTOP = (0.2, 2.8)    # Dựng khung laptop 3D từ dưới lên
T_KEYS = (2.0, 3.8)      # Hiệu ứng gõ phím gợn sóng
T_BOOT = (2.3, 4.6)      # Màn hình terminal boot DEAR_TEACHER.EXE
T_STEMS = (3.4, 5.2)     # Cành lá và dải ruy-băng mọc lên
T_BUDS = (4.8, 5.8)      # Các nụ hoa xuất hiện dần
T_OPEN = 5.6             # Bông đầu tiên bắt đầu nở
STAGGER = 0.48           # Độ trễ giữa các bông hoa khi bung cánh
OPEN_DUR = 2.4           # Thời gian mỗi bông hoa nở trọn vẹn
FLASH = 0.6              # Thời gian lóe sáng trắng khi chi tiết mới xuất hiện

T_COMPILE = 10.6         # Khoảnh khắc compile thành công: sóng sáng quét qua và bắn pháo hoa
T_GLEAM = (14.4, 15.8)   # Dải ánh sáng vàng lướt chéo qua tác phẩm
T_FALL = 11.4            # Cánh hoa rơi nhẹ
T_MSG = 11.2             # Bắt đầu gõ từng ký tự thiệp tri ân bên dưới

# Kích thước lưới ASCII (113x105) giữ độ nét cao cho bề mặt 3D và chữ tiếng Việt.
CW, CH, FONT_PX = 7, 10, 11
COLS, ROWS = 113, 105
W, H = COLS * CW, ROWS * CH
TRAIL = 0.45
MONO = "consolas,menlo,dejavusansmono,couriernew,monospace"

# Bảng ký tự theo mật độ sáng tối -> sáng dùng để tô bóng bề mặt 3D.
POOLS = ["1il!;:", "rtfjcvxz=+", "aeoun0{}[]<>", "08B$#&%Q"]
C = lambda ch: ord(ch) - 32
FILL = np.array([[C(p[k % len(p)]) for k in range(12)] for p in POOLS])
SLOPE = np.array([C(c) for c in "-/|\\-"])

# Nhóm tag phân loại điểm 3D để xử lý tô bóng và viền tách lớp riêng biệt.
(
    LAPTOP_BODY,
    LAPTOP_DECK,
    KEYCAP,
    SCREEN_BEZEL,
    SCREEN_BG,
    SCREEN_TEXT,
    STEM,
    LEAF,
    SEPAL,
    PETAL,
    EDGE,
    RIBBON,
    GLINT,
    BLOSSOM,
    GOLD_PART,
    CYAN_PART,
    PINK_PART,
) = range(17)

COLORS = np.array(
    [
        [168, 182, 206],  # LAPTOP_BODY: nhôm xám bạc dịu mắt
        [44, 54, 74],     # LAPTOP_DECK: mặt bàn phím tối tạo độ tương phản
        [108, 214, 240],  # KEYCAP: phím sáng cyan dịu
        [184, 198, 222],  # SCREEN_BEZEL: viền màn hình sáng gọn
        [14, 30, 54],     # SCREEN_BG: nền terminal xanh đêm sâu
        [124, 242, 218],  # SCREEN_TEXT: chữ hiển thị trên màn hình 3D
        [72, 188, 108],   # STEM: cành hoa xanh dịu
        [54, 168, 92],    # LEAF: lá xanh trầm
        [82, 196, 114],   # SEPAL: đài hoa
        [235, 52, 82],    # PETAL: cánh hoa mặc định
        [255, 168, 184],  # EDGE: viền cánh hoa
        [246, 198, 104],  # RIBBON: dải ruy-băng vàng champagne
        [255, 255, 255],  # GLINT: tia lóe trắng
        [248, 244, 236],  # BLOSSOM: hoa bi trắng nhỏ
        [246, 208, 122],  # GOLD_PART: hạt sáng vàng dịu
        [126, 220, 246],  # CYAN_PART: hạt sáng cyan dịu
        [242, 148, 180],  # PINK_PART: hạt sáng hồng dịu
    ],
    dtype=np.float32,
) / 255.0

WHITE = np.array([1.0, 0.98, 0.95], dtype=np.float32)
GOLD = np.array([0.98, 0.83, 0.46], dtype=np.float32)
CYAN = np.array([0.48, 0.88, 0.98], dtype=np.float32)
LOVE_RED = np.array([0.96, 0.24, 0.36], dtype=np.float32)
WARM_CREAM = np.array([0.98, 0.92, 0.80], dtype=np.float32)
ICE_SILVER = np.array([0.74, 0.86, 0.98], dtype=np.float32)
MUTED_SLATE = np.array([0.66, 0.70, 0.78], dtype=np.float32)
SOFT_SILVER = np.array([0.88, 0.90, 0.94], dtype=np.float32)

# Bảng màu tối giản đồng bộ cho 7 bông hồng: bông trung tâm vàng champagne, xung quanh đỏ thắm & hồng phấn.
ROSE_SHADES = np.array(
    [
        [[246, 192, 92], [255, 236, 178]],   # Vàng champagne (trung tâm)
        [[230, 38, 68], [255, 134, 152]],    # Đỏ thắm
        [[236, 98, 136], [255, 186, 208]],   # Hồng trầm
        [[216, 48, 76], [252, 146, 162]],    # Đỏ ruby
        [[244, 134, 162], [255, 206, 220]],  # Hồng phấn dịu
        [[234, 72, 92], [255, 164, 176]],    # Đỏ san hô dịu
        [[224, 54, 88], [252, 154, 176]],    # Đỏ hồng
    ],
    dtype=np.float32,
) / 255.0

# Màu HUD tối giản (RGB 0..255)
DIM = (114, 122, 138)
ACCENT = (124, 218, 246)
SIGN = (206, 192, 168)
HINT = "Space tạm dừng · R chạy lại · T đổi lời chúc · S lưu ảnh · Esc thoát"

# Các bộ lời chúc tối giản, trang nhã cho Ngày Nhà giáo Việt Nam 20/11 (nhấn T để chuyển đổi).
WISH_PRESETS = [
    (
        "DEAR TEACHER.EXE · 44 NĂM NGÀY NHÀ GIÁO VIỆT NAM",
        "Cảm ơn Thầy Cô Khoa CNTT đã 'compile' ước mơ chúng em <3",
        "Kính chúc Quý Thầy Cô luôn bình an, hạnh phúc và nhiệt huyết",
    ),
    (
        "KỶ NIỆM 44 NĂM NGÀY NHÀ GIÁO VIỆT NAM · 20/11",
        "Chúc Quý Thầy Cô luôn mạnh khỏe, giữ vững ngọn lửa đam mê <3",
        "Gửi trọn lòng biết ơn sâu sắc đến Quý Thầy Cô Khoa CNTT",
    ),
    (
        "TỪ NHỮNG DÒNG CODE TRI ÂN · 20/11",
        "Mỗi dòng code hôm nay đều mang dấu ấn bài giảng của Thầy Cô <3",
        "Trân trọng từng bài học và sự tận tâm của Quý Thầy Cô",
    ),
]

# Các ngôn ngữ lập trình tiêu biểu trôi nhẹ hai bên khung hình, đặt C nổi bật ở vị trí đầu.
LANG_TOKENS = [
    "C",
    "Python",
    "C++",
    "Java",
    "JS",
    "HTML",
    "C#",
    "Go",
    "SQL",
    "TS",
    "{ }",
    "</>",
]
