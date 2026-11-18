"""Hình học 3D dạng đám mây điểm (point-cloud) cho laptop mở nắp, bàn phím, màn hình và bó hoa hồng."""

import numpy as np

from constants import (
    BLOSSOM,
    COLORS,
    EDGE,
    KEYCAP,
    LAPTOP_BODY,
    LAPTOP_DECK,
    LEAF,
    OPEN_DUR,
    PETAL,
    RIBBON,
    ROSE_SHADES,
    SCREEN_BEZEL,
    SCREEN_BG,
    SEPAL,
    STAGGER,
    STEM,
    T_BUDS,
    T_KEYS,
    T_LAPTOP,
    T_OPEN,
    T_STEMS,
    TAU,
)

# Hằng số bố cục không gian 3D giữa chiếc laptop và bó hoa tri ân mọc lên phía trên màn hình.
HINGE_Y, HINGE_Z = -0.70, -0.36
LID_TILT = np.radians(16.0)
LID_UP = np.array([0.0, np.cos(LID_TILT), -np.sin(LID_TILT)], dtype=np.float32)
LID_FWD = np.array([0.0, np.sin(LID_TILT), np.cos(LID_TILT)], dtype=np.float32)
LID_W, LID_H = 0.72, 0.82

SCR_U_MIN, SCR_U_MAX = -0.62, 0.62
SCR_V_MIN, SCR_V_MAX = 0.09, 0.74
# Lấy mẫu dày (96x42) cho lưới màn hình 3D để không lọt điểm mặt sau xuyên qua nền terminal.
SCR_COLS, SCR_ROWS = 96, 42

DOME = np.array([0.0, 0.35, -0.14], dtype=np.float32)
WAIST = np.array([0.0, 0.14, -0.22], dtype=np.float32)
ROSE_SIZE = 0.21
N_ROSES = len(ROSE_SHADES)

SPIRAL, ACROSS = 260, 10
ANGLE, ALONG = np.meshgrid(np.linspace(2.2 * np.pi, 20 * np.pi, SPIRAL), np.linspace(0, 1, ACROSS))
INWARD = (ANGLE - ANGLE.min()) / (ANGLE.max() - ANGLE.min())
PETAL_ID = (np.floor(3.6 * ANGLE / TAU).astype(int) - int(np.floor(3.6 * ANGLE.min() / TAU))).ravel()
OUTER = (1.0 - INWARD.ravel()).astype(np.float32)
HEART_GAIN = (0.68 + 0.32 * OUTER ** 0.8).astype(np.float32)
ROSE_STEPS = 44

_PETALS = {}
_SEPALS = {}


def smooth(x):
    """Hàm làm mượt Hermite bậc 3 trên đoạn [0, 1]."""
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def unit(v):
    """Chuẩn hóa vector theo trục cuối, tránh chia cho 0."""
    v = np.asarray(v, dtype=np.float32)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-8)


def spin_y(angle):
    """Ma trận xoay quanh trục Y đứng."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=np.float32)


def turn_to(direction):
    """Tìm ma trận xoay đưa trục +Y về hướng `direction` để từng bông hoa hướng về phía người xem."""
    y = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    d = unit(direction)
    v = np.cross(y, d)
    c = float(y @ d)
    if np.linalg.norm(v) < 1e-7:
        return np.eye(3, dtype=np.float32)
    k = np.array([[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]], dtype=np.float32)
    return (np.eye(3, dtype=np.float32) + k + k @ k / (1.0 + c)).astype(np.float32)


def normals_of(p, axis_u, axis_v, outward):
    """Tính pháp tuyến bề mặt lưới tham số và lật hướng ra ngoài theo `outward`."""
    n = np.cross(np.gradient(p, axis=axis_u), np.gradient(p, axis=axis_v))
    n = n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-8)
    sign = np.sign((n * outward).sum(-1, keepdims=True) + 1e-8)
    return (n * sign).astype(np.float32)


def _laptop_appear(y, x):
    """Thời gian dựng khung laptop từ đáy lên trên kết hợp lan nhẹ ra hai bên."""
    u = np.clip((y - (-0.77)) / (0.14 - (-0.77)), 0.0, 1.0)
    side = np.abs(x) / 0.75 * 0.14
    return (T_LAPTOP[0] + (T_LAPTOP[1] - T_LAPTOP[0]) * (0.86 * u + side)).astype(np.float32)


def build_laptop():
    """Tạo đám mây điểm 3D cho thân máy, mặt phím, từng phím bấm, bàn di chuột và nắp màn hình."""
    pts, nrms, tags, parts, appears, key_ids = [], [], [], [], [], []

    def push(p, n, tag, part, appear=None, key_id=-1):
        p = np.asarray(p, dtype=np.float32).reshape(-1, 3)
        n = np.broadcast_to(np.asarray(n, dtype=np.float32), p.shape).copy()
        m = len(p)
        pts.append(p)
        nrms.append(n)
        tags.append(np.full(m, tag, dtype=int))
        parts.append(np.full(m, part, dtype=int))
        appears.append(
            _laptop_appear(p[:, 1], p[:, 0])
            if appear is None
            else np.broadcast_to(np.asarray(appear, dtype=np.float32), (m,)).copy()
        )
        key_ids.append(np.full(m, key_id, dtype=int))

    # Mặt bàn phím phẳng được lấy mẫu đủ dày để không hở nền đen bên dưới.
    gx, gz = np.meshgrid(np.linspace(-0.72, 0.72, 76), np.linspace(HINGE_Z, 0.44, 42))
    deck = np.stack([gx, np.full_like(gx, HINGE_Y), gz], -1)
    push(deck, [0.0, 1.0, 0.0], LAPTOP_DECK, 2)

    # Cạnh trước và hai bên hông tạo độ dày khối cho đế laptop.
    fx, fy = np.meshgrid(np.linspace(-0.72, 0.72, 72), np.linspace(-0.75, HINGE_Y, 6))
    push(np.stack([fx, fy, np.full_like(fx, 0.44)], -1), [0.0, 0.15, 1.0], LAPTOP_BODY, 1)
    for sx in (-1.0, 1.0):
        sz, sy = np.meshgrid(np.linspace(HINGE_Z, 0.44, 40), np.linspace(-0.75, HINGE_Y, 6))
        push(np.stack([np.full_like(sz, sx * 0.72), sy, sz], -1), [sx, 0.15, 0.0], LAPTOP_BODY, 1)

    # Các phím bấm nổi trên bàn phím; giữ chung part=2 trên mặt phím để không nhiễu nét gạch.
    k_idx = 0
    for row in range(4):
        z0 = -0.27 + row * 0.105
        for col in range(12):
            x0 = -0.56 + col * 0.102
            kx, kz = np.meshgrid(np.linspace(x0 - 0.032, x0 + 0.032, 4), np.linspace(z0 - 0.028, z0 + 0.028, 3))
            kp = np.stack([kx, np.full_like(kx, HINGE_Y + 0.015), kz], -1)
            t_k = T_KEYS[0] + (T_KEYS[1] - T_KEYS[0]) * ((col + row * 1.4) / 16.0)
            push(kp, [0.0, 1.0, 0.0], KEYCAP, 2, appear=t_k, key_id=k_idx)
            k_idx += 1

    # Bàn di chuột phía trước
    tx, tz = np.meshgrid(np.linspace(-0.18, 0.18, 22), np.linspace(0.20, 0.37, 10))
    push(np.stack([tx, np.full_like(tx, HINGE_Y + 0.010), tz], -1), [0.0, 1.0, 0.0], KEYCAP, 3, appear=T_KEYS[0] + 0.6, key_id=999)

    # Khung viền nắp màn hình và mặt lưng phía sau (dày 96x46 để đồng bộ với màn hình).
    hinge = np.array([0.0, HINGE_Y, HINGE_Z], dtype=np.float32)
    lu, lv = np.meshgrid(np.linspace(-LID_W, LID_W, 96), np.linspace(0.0, LID_H, 46))
    is_screen = (np.abs(lu) <= SCR_U_MAX) & (lv >= SCR_V_MIN) & (lv <= SCR_V_MAX)
    lid_p = hinge + np.stack([lu, np.zeros_like(lu), np.zeros_like(lu)], -1) + lv[..., None] * LID_UP
    push(lid_p[~is_screen], LID_FWD, SCREEN_BEZEL, 4)
    push(lid_p - 0.035 * LID_FWD, -LID_FWD, SCREEN_BEZEL, 40)

    # Lưới điểm màn hình terminal nằm phía trước khung, lấy mẫu dày 96x42 để hiển thị "20/11" sắc nét.
    su, sv = np.meshgrid(
        np.linspace(SCR_U_MIN, SCR_U_MAX, SCR_COLS),
        np.linspace(SCR_V_MAX, SCR_V_MIN, SCR_ROWS),
    )
    scr_p = hinge + np.stack([su, np.zeros_like(su), np.zeros_like(su)], -1) + sv[..., None] * LID_UP + 0.008 * LID_FWD
    scr_start = len(np.concatenate(pts))
    push(scr_p, LID_FWD, SCREEN_BG, 5)

    return {
        "p": np.concatenate(pts),
        "n": np.concatenate(nrms),
        "tag": np.concatenate(tags),
        "part": np.concatenate(parts),
        "appear": np.concatenate(appears),
        "key_id": np.concatenate(key_ids),
        "scr_slice": slice(scr_start, scr_start + SCR_COLS * SCR_ROWS),
    }


def petals(open_):
    """Sinh bề mặt cánh hoa hồng xoắn tham số theo độ nở `open_` ∈ [0, 1] và cache lại."""
    key = round(float(open_) * ROSE_STEPS) / ROSE_STEPS
    if key not in _PETALS:
        spread = 1.4 + 4.1 * key
        lean = (np.pi / 2.0) * np.exp(-ANGLE / (spread * np.pi))
        width = 1.0 - 0.5 * (1.25 * (1.0 - np.mod(3.6 * ANGLE, TAU) / np.pi) ** 2 - 0.25) ** 2
        cup = 1.95653 * ALONG ** 2 * (1.27689 * ALONG - 1.0) ** 2 * np.sin(lean)
        r = width * (ALONG * np.sin(lean) + cup * np.cos(lean))
        y = width * (ALONG * np.cos(lean) - cup * np.sin(lean))
        p = np.stack([r * np.sin(ANGLE), y, r * np.cos(ANGLE)], -1) * 0.8
        wrap = smooth(key / 0.7)
        p[..., [0, 2]] *= 0.72 + 0.28 * wrap
        p[..., 1] *= 0.66 + 0.34 * wrap
        out = np.stack([np.sin(ANGLE), np.full_like(ANGLE, 0.3), np.cos(ANGLE)], -1)
        n = normals_of(p, 1, 0, out)
        _PETALS[key] = (
            p.reshape(-1, 3).astype(np.float32),
            n.reshape(-1, 3).astype(np.float32),
            (ALONG > 0.92).ravel(),
        )
    return _PETALS[key]


def sepals(open_):
    """Sinh 5 lá đài xanh ôm dưới bông hoa."""
    key = round(float(open_) * 10) / 10
    if key in _SEPALS:
        return _SEPALS[key]
    sl, sw = np.meshgrid(np.linspace(0.0, 1.0, 9), np.linspace(-1.0, 1.0, 3))
    pts, nrms = [], []
    reach, droop = 0.24 + 0.06 * key, 0.10 + 0.14 * key
    for i in range(5):
        a = TAU * i / 5.0 + 0.6
        out = np.array([np.sin(a), 0.0, np.cos(a)])
        side = np.array([np.cos(a), 0.0, -np.sin(a)])
        b0 = np.array([0.0, 0.03, 0.0]) + 0.03 * out
        b1 = 0.16 * out + np.array([0.0, 0.10 - 0.10 * key, 0.0])
        b2 = reach * out - np.array([0.0, droop, 0.0])
        u = sl[..., None]
        mid = (1 - u) ** 2 * b0 + 2 * (1 - u) * u * b1 + u ** 2 * b2
        half = 0.05 * np.sin(np.pi * np.minimum(sl * 1.5, 1.0) / 2.0) * (1.0 - sl) ** 0.7
        p = mid + side * (half * sw)[..., None]
        pts.append(p.reshape(-1, 3))
        nrms.append(normals_of(p, 1, 0, np.array([0.0, 1.0, 0.0])).reshape(-1, 3))
    _SEPALS[key] = (np.concatenate(pts).astype(np.float32), np.concatenate(nrms).astype(np.float32))
    return _SEPALS[key]


def _tube(curve, radius, around=6):
    """Tạo ống tròn dọc theo đường cong 3D để dựng cành hoa."""
    d = np.gradient(curve, axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-8
    side = np.cross(d, [0.0, 0.0, 1.0])
    side /= np.linalg.norm(side, axis=1, keepdims=True) + 1e-8
    up = np.cross(side, d)
    a = np.linspace(0, TAU, around, endpoint=False)
    n = np.cos(a)[None, :, None] * side[:, None] + np.sin(a)[None, :, None] * up[:, None]
    return (curve[:, None] + radius * n).reshape(-1, 3), n.reshape(-1, 3)


def _leaf(base, d, length):
    """Tạo lá cây thon nhọn uốn cong nhẹ và có gân gập chữ V ở giữa."""
    s, w = np.meshgrid(np.linspace(0, 1, 24), np.linspace(-1, 1, 9))
    d = unit(d)
    wide = unit(np.cross(d, [0.0, 1.0, 0.0]))
    up = np.cross(wide, d)
    half = 0.30 * length * np.sqrt(s) * (1 - s) ** 0.8 * 1.9 * (1 + 0.06 * np.sin(s * 40))
    p = base + d * (s * length)[..., None] + wide * (w * half)[..., None] + up * (0.10 * length * w ** 2 - 0.28 * length * s ** 1.8)[..., None]
    return p.reshape(-1, 3), normals_of(p, 1, 0, up).reshape(-1, 3), s.ravel()


def build_bouquet_layout():
    """Xếp 7 bông hồng thành vòm hướng về người xem phía trên màn hình laptop để từng bông tách bạch."""
    # Đặt từng bông hoa dạng bó xòe hướng mặt về phía camera (+Y/+Z) thay vì úp ra sau lưng.
    offsets = np.array(
        [
            [0.00, 0.28, 0.04],   # 0: bông vàng trung tâm ở đỉnh bó hoa
            [-0.27, 0.20, 0.10],  # 1: hàng trên trái
            [0.27, 0.20, 0.10],   # 2: hàng trên phải
            [-0.44, 0.03, 0.04],  # 3: cánh ngoài trái
            [0.44, 0.03, 0.04],   # 4: cánh ngoài phải
            [-0.17, 0.02, 0.22],  # 5: tầng trước trái
            [0.17, 0.02, 0.22],   # 6: tầng trước phải
        ],
        dtype=np.float32,
    )
    aims = np.array(
        [
            [0.00, 0.90, 0.44],
            [-0.36, 0.80, 0.48],
            [0.36, 0.80, 0.48],
            [-0.64, 0.56, 0.52],
            [0.64, 0.56, 0.52],
            [-0.22, 0.62, 0.75],
            [0.22, 0.62, 0.75],
        ],
        dtype=np.float32,
    )
    lean = [unit(v) for v in aims]
    pos = [DOME + off for off in offsets]
    rng = np.random.default_rng(11)
    turns = [turn_to(d) @ spin_y(float(rng.uniform(0, TAU))) for d in lean]

    order = [0, 5, 6, 1, 2, 3, 4]
    starts = np.empty(N_ROSES, dtype=np.float32)
    starts[order] = T_OPEN + STAGGER * np.arange(N_ROSES)
    bud_pop = T_BUDS[0] + (T_BUDS[1] - T_BUDS[0]) * rng.random(N_ROSES).astype(np.float32)

    pts, nrms, tags, parts, appears, pops, centres = [], [], [], [], [], [], []

    def add(p, n, tag, part, appear, pop=False, centre=None):
        p = np.asarray(p, dtype=np.float32).reshape(-1, 3)
        n = np.asarray(n, dtype=np.float32).reshape(-1, 3)
        m = len(p)
        pts.append(p)
        nrms.append(n)
        tags.append(np.full(m, tag, dtype=int))
        parts.append(np.full(m, part, dtype=int))
        appears.append(np.broadcast_to(np.asarray(appear, dtype=np.float32), (m,)).copy())
        pops.append(np.full(m, pop, dtype=bool))
        centres.append(p.copy() if centre is None else np.broadcast_to(np.asarray(centre, dtype=np.float32), (m, 3)).copy())

    # Cành hoa uốn mềm từ cổ bó hoa phía trên màn hình tới đáy từng bông hoa
    for k in range(N_ROSES):
        base = pos[k] - lean[k] * 0.04
        start = WAIST + np.array([0.025 * np.sin(1.4 * k), -0.06, 0.02 * np.cos(1.4 * k)], dtype=np.float32)
        bend = np.array([0.35 * base[0], 0.5 * (start[1] + base[1]), 0.4 * base[2] - 0.08], dtype=np.float32)
        u = np.linspace(0, 1, 24)[:, None]
        sp, sn = _tube((1 - u) ** 2 * start + 2 * (1 - u) * u * bend + u ** 2 * base, 0.010, 5)
        ap = T_STEMS[0] + (T_STEMS[1] - T_STEMS[0]) * np.clip((sp[:, 1] - start[1]) / max(0.15, base[1] - start[1]), 0, 1)
        add(sp, sn, STEM, 10 + k, ap)

    # Lá xanh tỏa nhẹ ở hai bên và phía sau viền bó hoa
    for j, ang in enumerate((-1.35, -0.95, -0.50, 0.50, 0.95, 1.35, -2.1, 2.1)):
        base = WAIST + np.array([0.14 * np.sin(ang), 0.11, 0.06 * np.cos(ang)], dtype=np.float32)
        d = np.array([np.sin(ang), 0.25, 0.45 * np.cos(ang)], dtype=np.float32)
        lp, ln, along = _leaf(base, d, 0.26)
        add(lp, ln, LEAF, 20 + j, T_STEMS[0] + 0.5 + 0.08 * j + 0.45 * along)

    # Dải ruy-băng vàng kim và nơ 2 cánh buộc ngay cổ bó hoa (WAIST)
    ra, rw = np.meshgrid(np.linspace(0, TAU, 72, endpoint=False), np.linspace(-1, 1, 5))
    band = WAIST + np.stack([0.095 * np.sin(ra), 0.020 * rw + 0.04, 0.095 * np.cos(ra)], -1)
    add(band, np.stack([np.sin(ra), np.zeros_like(ra), np.cos(ra)], -1), RIBBON, 30, T_STEMS[1] - 0.1, pop=True, centre=WAIST + [0, 0.04, 0])
    knot = WAIST + np.array([0.0, 0.04, 0.10], dtype=np.float32)
    for side, pid in ((-1, 31), (1, 32)):
        u, q = np.meshgrid(np.linspace(0, TAU, 60), np.linspace(0, 1, 7))
        rx, ry = 0.025 + 0.045 * q, 0.010 + 0.028 * q
        bx, by = side * (0.018 + rx + rx * np.cos(u + np.pi)), ry * np.sin(u)
        tip = side * 0.26
        bx, by = bx * np.cos(tip) - by * np.sin(tip), bx * np.sin(tip) + by * np.cos(tip)
        bz = 0.022 * np.sin(u / 2.0) ** 2 + 0.010 * q
        bp = knot + np.stack([bx, by, bz], -1)
        add(bp, normals_of(bp, 1, 0, np.array([0.0, 0.25, 1.0])), RIBBON, pid, T_STEMS[1] - 0.05, pop=True, centre=knot)

    # Hoa bi trắng nhỏ điểm xuyết giữa các bông hồng
    bl = np.random.default_rng(33).random((46, 3))
    ba = (bl[:, 1] - 0.5) * 2.5
    blossoms = DOME + np.stack([0.52 * np.sin(ba) * (0.5 + 0.5 * bl[:, 0]), -0.04 + 0.34 * bl[:, 0], 0.18 + 0.12 * np.cos(ba)], 1)
    blossom_appear = (T_BUDS[0] + 0.2 + 0.8 * bl[:, 2]).astype(np.float32)

    return {
        "pos": pos,
        "dir": lean,
        "turn": turns,
        "starts": starts,
        "bud_pop": bud_pop,
        "p": np.concatenate(pts),
        "n": np.concatenate(nrms),
        "tag": np.concatenate(tags),
        "part": np.concatenate(parts),
        "appear": np.concatenate(appears),
        "pop": np.concatenate(pops),
        "centre": np.concatenate(centres),
        "blossoms": blossoms.astype(np.float32),
        "blossom_appear": blossom_appear,
        "blossom_phase": bl[:, 2].astype(np.float32),
    }


_ROSES, _ROSE_LOOKS = {}, {}


def rose_instance(layout, k, open_, flash):
    """Tạo và cache geometry cho bông hồng thứ `k` tại độ mở `open_` và độ chớp `flash`."""
    key = (open_, flash)
    if k not in _ROSES or _ROSES[k][0] != key:
        p, n, rim = petals(open_)
        sp, sn = sepals(open_)
        if k not in _ROSE_LOOKS:
            _ROSE_LOOKS[k] = (
                np.concatenate([np.where(rim, EDGE, PETAL), np.full(len(sp), SEPAL)]),
                np.concatenate(
                    [
                        np.where(rim[:, None], ROSE_SHADES[k, 1], ROSE_SHADES[k, 0]),
                        np.broadcast_to(COLORS[SEPAL], (len(sp), 3)),
                    ]
                ),
                np.concatenate([1000 + 100 * k + PETAL_ID, np.full(len(sp), 40 + k)]),
            )
        size = np.float32(ROSE_SIZE * (1.0 + 0.12 * flash))
        rot = layout["turn"][k]
        _ROSES[k] = (
            key,
            (
                layout["pos"][k] + (np.concatenate([p, sp]) * size) @ rot.T,
                np.concatenate([n, sn]) @ rot.T,
            )
            + _ROSE_LOOKS[k],
        )
    return _ROSES[k][1]
