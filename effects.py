"""Hiệu ứng hạt 3D, ngôi sao nền, cánh hoa rơi, pháo hoa compile và nhãn ngôn ngữ lập trình."""

import numpy as np

from constants import (
    C,
    CYAN_PART,
    GLINT,
    GOLD_PART,
    LANG_TOKENS,
    OPEN_DUR,
    PINK_PART,
    ROSE_SHADES,
    T_COMPILE,
    T_FALL,
    TAU,
)
from geometry import N_ROSES, smooth

N_STARS = 300
_STARS = np.random.default_rng(21).random((N_STARS, 6))
_POPS = np.random.default_rng(13).random((N_ROSES, 14, 4))

# Pháo hoa tinh tế tại mốc compile thành công T_COMPILE.
N_SPARKS = 120
_SPARK_RNG = np.random.default_rng(44)
_SPARK_A = _SPARK_RNG.uniform(0, TAU, N_SPARKS)
_SPARK_EL = _SPARK_RNG.uniform(-0.25, 1.15, N_SPARKS)
_SPARK_SPD = _SPARK_RNG.uniform(0.60, 1.55, N_SPARKS)
_SPARK_LIFE = _SPARK_RNG.uniform(1.0, 1.7, N_SPARKS)
_SPARK_KIND = _SPARK_RNG.integers(0, 3, N_SPARKS)

# Cánh hoa rơi nhẹ xung quanh sau khi hoa nở.
N_FALL = 12
_FALL = np.random.default_rng(17).random((N_FALL, 8))
FALL_PERIOD = 5.4
FALL_POSES = [("(", ")"), ("/", ""), ("-", ""), ("\\", ""), ("{", "}"), ("<", ">")]
FALL_TURN = [0, 1, 2, 3, 4, 3, 2, 1]

# Nhãn các ngôn ngữ lập trình phân bố đều hai bên lề, giữ khoảng cách gọn gàng khỏi tâm cảnh 3D và mép màn hình.
_TOKEN_RNG = np.random.default_rng(2011)
_TOKEN_SIDE = np.array([-1 if i % 2 == 0 else 1 for i in range(len(LANG_TOKENS))], dtype=np.float32)
_TOKEN_LANE = _TOKEN_RNG.uniform(0.0, 0.08, len(LANG_TOKENS))


def stars(t):
    """Tạo trường sao thưa dịu lấp lánh chậm rãi làm nền tối giản."""
    g = _STARS
    x = 2.6 * g[:, 0] - 1.3 + 0.04 * np.sin(t * 0.5 + g[:, 5] * TAU)
    y = -1.35 + 2.8 * ((g[:, 1] + t * 0.006 * (0.5 + g[:, 3])) % 1.0)
    z = -1.4 + 2.3 * g[:, 2]
    beat = 2.8 + 4.5 * g[:, 3]
    peak = np.clip(1.0 - np.abs((t / beat + g[:, 4]) % 1.0 - 0.5) * beat / 0.24, 0.0, 1.0)
    glow = 0.20 + 0.26 * g[:, 5] + peak ** 1.5
    kind = np.select(
        [g[:, 2] % 0.25 < 0.04, g[:, 2] % 0.25 < 0.08, g[:, 2] % 0.25 < 0.11],
        [PINK_PART, CYAN_PART, GOLD_PART],
        GLINT,
    )
    return np.stack([x, y, z], 1).astype(np.float32), glow.astype(np.float32), kind


def rose_pops(layout, t):
    """Tia sáng nhỏ bắn ra mỗi khi từng bông hồng vừa bung nở hoàn toàn."""
    pts, strength, tags = [], [], []
    for k in range(N_ROSES):
        age = t - (layout["starts"][k] + 0.85 * OPEN_DUR)
        if not 0.0 < age < 1.3:
            continue
        g = _POPS[k]
        a, up = g[:, 0] * TAU, 0.4 + 0.7 * g[:, 1]
        speed = 0.38 + 0.42 * g[:, 2]
        vel = np.stack([np.cos(a) * speed, up, np.sin(a) * speed], 1)
        head = layout["pos"][k] + layout["dir"][k] * 0.10
        pts.append(head + vel * age - np.array([0.0, 0.85, 0.0]) * age ** 2)
        strength.append((1.0 - age / 1.3) ** 1.2 * (0.70 + 0.45 * g[:, 3]))
        tags.append(np.where(g[:, 3] > 0.5, GLINT, GOLD_PART))
    if not pts:
        return np.zeros((0, 3), np.float32), np.zeros(0, np.float32), np.zeros(0, int)
    return np.concatenate(pts).astype(np.float32), np.concatenate(strength).astype(np.float32), np.concatenate(tags)


def compile_sparks(t):
    """Đợt pháo hoa hạt sáng tỏa ra tại khoảnh khắc compile thành công (chịu lực cản và trọng lực)."""
    age = t - T_COMPILE
    if not 0.0 <= age < 1.8:
        return np.zeros((0, 3), np.float32), np.zeros(0, np.float32), np.zeros(0, int)
    alive = age < _SPARK_LIFE
    drag = 2.3
    gone = (1.0 - np.exp(-drag * age)) / drag
    vx = np.cos(_SPARK_EL) * np.cos(_SPARK_A) * _SPARK_SPD
    vy = np.sin(_SPARK_EL) * _SPARK_SPD
    vz = np.cos(_SPARK_EL) * np.sin(_SPARK_A) * _SPARK_SPD
    origin = np.array([0.0, 0.14, -0.18], dtype=np.float32)
    pos = origin + np.stack([vx * gone, vy * gone - 0.55 * age * age, vz * gone], 1)
    fade = np.clip(1.0 - age / _SPARK_LIFE[alive], 0.0, 1.0) ** 1.15
    tag_map = np.array([GOLD_PART, CYAN_PART, PINK_PART])
    tag = np.where(age < 0.25, GLINT, tag_map[_SPARK_KIND[alive]])
    return pos[alive].astype(np.float32), (1.25 * fade).astype(np.float32), tag


def falling_petals(layout, t):
    """Các cánh hoa rơi chầm chậm xung quanh bó hoa sau khi nở."""
    out = []
    for k, (a, b, c, d, e, f, g, h) in enumerate(_FALL):
        since = t - T_FALL - k * FALL_PERIOD / N_FALL
        if since < 0.0:
            continue
        age = since % FALL_PERIOD
        rose_k = int(a * N_ROSES) % N_ROSES
        start = layout["pos"][rose_k] + layout["turn"][rose_k] @ (
            np.array([np.cos(b * TAU), 0.10, np.sin(b * TAU)], dtype=np.float32) * 0.08
        )
        drift = np.array(
            [
                0.24 * (c - 0.5) * age + 0.06 * np.sin(age * (2 + 2 * d) + e * TAU),
                -0.28 * age,
                0.20 * age * f + 0.05 * np.cos(age * (2 + g) + h * TAU),
            ],
            dtype=np.float32,
        )
        pose = FALL_TURN[int(age * (3 + 3 * d) + e * 8) % len(FALL_TURN)]
        fade = smooth(age / 0.3) * smooth((FALL_PERIOD - age) / 0.6)
        out.append((start + drift, ROSE_SHADES[rose_k, 0], pose, float(fade)))
    return out


def lang_tokens(t):
    """Các nhãn ngôn ngữ lập trình (C, Python, C++, Java, JS, HTML...) trôi nhịp nhàng hai bên lề."""
    if t < 2.2:
        return []
    out = []
    n = len(LANG_TOKENS)
    period = 12.0
    for i, text in enumerate(LANG_TOKENS):
        # Chia đều pha ban đầu để cùng lúc luôn có 8–10 ngôn ngữ phân tầng rõ ràng ở hai bên.
        age = (t - 2.2 + i * (period / n)) % period
        u = age / period
        side = float(_TOKEN_SIDE[i])
        x = side * (0.86 + _TOKEN_LANE[i] + 0.02 * np.sin(t * 0.8 + i))
        y = -0.52 + 1.38 * u
        z = 0.0
        fade = smooth(u / 0.14) * smooth((1.0 - u) / 0.18) * smooth((t - 2.2) / 0.8)
        if fade > 0.08:
            out.append((np.array([x, y, z], dtype=np.float32), text, float(fade), i % 3))
    return out


def rays(char, col, cy, cx, reach, rgb, strength=1.0, over=1.0):
    """Vẽ tia lóe sáng 4 cánh bằng ký tự -, |, /, \\ quanh điểm sáng nhất."""
    rows, cols = char.shape
    for dist in range(1, reach + 1):
        fade = (1.0 - dist / (reach + 1)) * strength
        arms = [(0, 1, "-"), (0, -1, "-"), (1, 0, "|"), (-1, 0, "|")]
        if dist <= reach // 2:
            arms += [(1, 1, "\\"), (-1, -1, "\\"), (1, -1, "/"), (-1, 1, "/")]
        for dy, dx, stroke in arms:
            yy, xx = cy + dy * dist, cx + dx * dist * (2 if dy == 0 else 1)
            k = fade * (0.7 if dx and dy else 1.0)
            if 0 <= yy < rows and 0 <= xx < cols and col[yy, xx].max() < k * over:
                char[yy, xx] = C(stroke)
                col[yy, xx] = rgb * k
    if 0 <= cy < rows and 0 <= cx < cols:
        char[cy, cx] = C("*")
        col[cy, cx] = rgb * 1.3 * strength
