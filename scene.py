"""Tổng hợp khung hình 3D -> lưới ASCII 2D: chiếu phối cảnh, tô bóng, viền tách lớp và thiệp tri ân."""

import numpy as np

from constants import (
    BLOSSOM,
    C,
    COLORS,
    CYAN,
    EDGE,
    FILL,
    FLASH,
    GLINT,
    GOLD,
    ICE_SILVER,
    KEYCAP,
    LAPTOP_DECK,
    LOOP,
    LOVE_RED,
    MUTED_SLATE,
    OPEN_DUR,
    PETAL,
    SCREEN_BG,
    SCREEN_TEXT,
    SEPAL,
    SOFT_SILVER,
    T_BOOT,
    T_COMPILE,
    T_GLEAM,
    T_KEYS,
    T_MSG,
    TAU,
    WARM_CREAM,
    WHITE,
)
from effects import (
    FALL_POSES,
    compile_sparks,
    falling_petals,
    lang_tokens,
    rays,
    rose_pops,
    stars,
)
from geometry import (
    HEART_GAIN,
    N_ROSES,
    ROSE_STEPS,
    SCR_COLS,
    SCR_ROWS,
    build_bouquet_layout,
    build_laptop,
    rose_instance,
    smooth,
    spin_y,
)

# Ngưỡng chiếu phối cảnh và phát hiện nếp gấp giữa các lớp 3D để kẻ viền ASCII sắc nét.
FOCAL = 3.1
MIDDLE = 0.42
FOLD = 0.11
STAR_FLARES = 5

EYE = np.array([0.0, 1.40, 4.35], dtype=np.float32)
TARGET = np.array([0.0, -0.12, 0.0], dtype=np.float32)
_FWD = (TARGET - EYE) / np.linalg.norm(TARGET - EYE)
_RIGHT = np.cross(_FWD, np.array([0.0, 1.0, 0.0], dtype=np.float32))
_RIGHT /= np.linalg.norm(_RIGHT)
_UP = np.cross(_RIGHT, _FWD)
VIEW = (-_FWD).astype(np.float32)

# Font pixel 5x7 tối giản cho màn hình terminal 3D hiển thị "20/11", "44" và "<3".
_GLYPHS_5X7 = {
    "2": ["11110", "00001", "00001", "01110", "10000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "4": ["10010", "10010", "10010", "11111", "00010", "00010", "00010"],
    "<": ["00010", "00100", "01000", "10000", "01000", "00100", "00010"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
}

_LAPTOP = build_laptop()
_BOUQUET = build_bouquet_layout()
_STATIC_CACHE = {}


def look(pts):
    """Biến đổi tọa độ thế giới sang hệ tọa độ camera."""
    rel = pts - EYE
    return rel @ _RIGHT, rel @ _UP, rel @ _FWD


def sway(t):
    """Dao động xoay trái-phải nhẹ nhàng để người xem thấy rõ chiều sâu 3D của laptop và bó hoa."""
    return 0.34 * np.sin(TAU * t / LOOP) * smooth(t / 1.5)


def outline_letter(gx, gy):
    """Chọn nét -, |, /, \\ phù hợp với hướng biên của vật thể trên màn hình."""
    ax, ay = np.abs(gx), np.abs(gy)
    c = np.where(
        ax > 2 * ay,
        C("|"),
        np.where(ay > 2 * ax, np.where(gy > 0, C("_"), C("-")), np.where(gx * gy > 0, C("/"), C("\\"))),
    )
    return np.where((ax + ay) == 0, C("+"), c)


def _paint_screen_bitmap(t):
    """Tạo mặt nạ bitmap cho màn hình 3D (boot code -> '20/11' và '44 <3'), co giãn khớp SCR_ROWS x SCR_COLS."""
    base_r, base_c = 20, 48
    grid = np.zeros((base_r, base_c), dtype=int)  # 0: nền tối, 1: cyan code, 2: vàng 20/11, 3: đỏ tim
    grid[1, 3:-3] = 1
    grid[-2, 3:-3] = 1
    if t < T_BOOT[1]:
        u = np.clip((t - T_BOOT[0]) / max(0.1, T_BOOT[1] - T_BOOT[0]), 0.0, 1.0)
        for row, start, span in ((4, 5, 22), (6, 5, 30), (8, 8, 24), (10, 5, 28)):
            filled = int(span * np.clip(u * 1.4 - (row - 4) * 0.08, 0.0, 1.0))
            if filled > 0:
                grid[row, start:start + filled] = 1
        bar_len = int((base_c - 12) * u)
        if bar_len > 0:
            grid[14:16, 6:6 + bar_len] = 2
    else:
        def draw_word(word, r0, c0, code):
            col = c0
            for ch in word:
                glyph = _GLYPHS_5X7.get(ch)
                if glyph:
                    for dr, line in enumerate(glyph):
                        for dc, px in enumerate(line):
                            if px == "1" and 0 <= r0 + dr < base_r and 0 <= col + dc < base_c:
                                grid[r0 + dr, col + dc] = code
                    col += 6
                else:
                    col += 3

        draw_word("20/11", 3, 10, 2)
        draw_word("44", 11, 10, 1)
        draw_word("<3", 11, 27, 3)

    # Chiếu gần nhất (nearest-neighbor) từ lưới logic 20x48 sang lưới vật lý SCR_ROWS x SCR_COLS.
    rr = (np.arange(SCR_ROWS) * base_r // SCR_ROWS)[:, None]
    cc = (np.arange(SCR_COLS) * base_c // SCR_COLS)[None, :]
    return grid[rr, cc]


def _assemble(rose_states):
    """Gộp phần tĩnh (laptop + cành lá) và 7 bông hoa tại trạng thái hiện tại, có cache theo trạng thái."""
    if _STATIC_CACHE.get("key") == rose_states:
        return _STATIC_CACHE["value"]
    lap, bq = _LAPTOP, _BOUQUET
    pts = [lap["p"], bq["p"]]
    nrms = [lap["n"], bq["n"]]
    tags = [lap["tag"], bq["tag"]]
    parts = [lap["part"], bq["part"]]
    tones = [COLORS[lap["tag"]], COLORS[bq["tag"]]]
    appears = [lap["appear"], bq["appear"]]
    pops = [np.zeros(len(lap["p"]), dtype=bool), bq["pop"]]
    centres = [lap["p"], bq["centre"]]
    whiten = [np.zeros(len(lap["p"]), dtype=np.float32), np.zeros(len(bq["p"]), dtype=np.float32)]
    gains = [np.ones(len(lap["p"]), dtype=np.float32), np.ones(len(bq["p"]), dtype=np.float32)]

    for k, open_, flash in rose_states:
        rp, rn, rt, rtone, rk = rose_instance(bq, k, open_, flash)
        pts.append(rp)
        nrms.append(rn)
        tags.append(rt)
        parts.append(rk)
        tones.append(rtone)
        appears.append(np.full(len(rp), bq["bud_pop"][k], dtype=np.float32))
        pops.append(np.ones(len(rp), dtype=bool))
        centres.append(np.broadcast_to(bq["pos"][k], rp.shape))
        whiten.append(np.where(rt == SEPAL, 0.0, 0.72 * flash).astype(np.float32))
        gains.append(np.concatenate([HEART_GAIN, np.ones(len(rp) - len(HEART_GAIN), dtype=np.float32)]))

    data = {
        "P": np.concatenate(pts),
        "N": np.concatenate(nrms),
        "T": np.concatenate(tags),
        "K": np.concatenate(parts),
        "tone": np.concatenate(tones).astype(np.float32),
        "appear": np.concatenate(appears),
        "pop": np.concatenate(pops),
        "centre": np.concatenate(centres).astype(np.float32),
        "W": np.concatenate(whiten),
        "gain": np.concatenate(gains),
        "scr_slice": lap["scr_slice"],
        "key_ids": lap["key_id"],
        "n_lap": len(lap["p"]),
    }
    data["lit"] = np.flatnonzero(data["W"] > 0)
    _STATIC_CACHE.update(key=rose_states, value=data)
    return data


def _scene_points(t):
    """Tính toàn bộ tọa độ, ánh sáng, hiệu ứng gõ phím, màn hình 3D và sóng compile tại thời điểm `t`."""
    bq = _BOUQUET
    op = smooth((t - bq["starts"]) / OPEN_DUR)
    op = op * (1.32 - 0.32 * op)
    states = []
    heads = []
    for k in range(N_ROSES):
        flash = np.clip(1.0 - (t - bq["starts"][k]) / FLASH, 0.0, 1.0) ** 2 if t >= bq["starts"][k] else 0.0
        states.append((k, round(float(op[k]) * ROSE_STEPS) / ROSE_STEPS, round(float(flash), 1)))
        heads.append((bq["pos"][k] + bq["dir"][k] * 0.09 * (0.5 + op[k]), float(flash)))

    v = _assemble(tuple(states))
    P = v["P"].copy()
    T = v["T"].copy()
    rgb = v["tone"].copy()

    # Hiệu ứng nảy phồng nhẹ khi nụ hoa hay ruy-băng mới xuất hiện
    age = t - v["appear"]
    pf = np.flatnonzero(v["pop"] & (age >= 0.0) & (age < FLASH))
    if len(pf):
        g = smooth(age[pf] / 0.2) * (1.0 + 0.30 * np.clip(1.0 - age[pf] / FLASH, 0.0, 1.0) ** 2)
        P[pf] = v["centre"][pf] + (P[pf] - v["centre"][pf]) * g[:, None].astype(np.float32)

    # Tô nội dung terminal lên lưới 3D màn hình laptop
    scr = _paint_screen_bitmap(t).ravel()
    sl = v["scr_slice"]
    if t >= T_BOOT[0]:
        active = scr > 0
        T[sl] = np.where(active, SCREEN_TEXT, SCREEN_BG)
        scr_rgb = np.broadcast_to(COLORS[SCREEN_BG], (len(scr), 3)).copy()
        scr_rgb[scr == 1] = CYAN
        scr_rgb[scr == 2] = GOLD
        ph = (t - T_BOOT[1]) % 1.05
        beat = float(np.exp(-(ph / 0.07) ** 2) + 0.5 * np.exp(-((ph - 0.25) / 0.07) ** 2))
        scr_rgb[scr == 3] = np.clip(LOVE_RED * (1.0 + 0.55 * beat), 0.0, 1.0)
        rgb[sl] = scr_rgb

    # Nháy phím ngẫu nhiên mô phỏng đang gõ code gửi Thầy Cô
    n_lap = v["n_lap"]
    k_ids = v["key_ids"]
    if t >= T_KEYS[0]:
        active_key = int(t * 9.0) % 48
        typing = np.zeros(len(P), dtype=bool)
        typing[:n_lap] = (k_ids == active_key) | (k_ids == (active_key + 17) % 48)
        rgb[typing] = WHITE

    # Ánh sáng 2 nguồn (key + sheen chuyển động)
    yaw = sway(t)
    Ry = spin_y(yaw)
    P_rot = P @ Ry.T
    N_rot = v["N"] @ Ry.T
    heads_rot = [(hp @ Ry.T, fl) for hp, fl in heads]

    key = np.array([0.45, 0.80, 0.55], dtype=np.float32)
    key /= np.linalg.norm(key)
    sheen = np.array([0.85 * np.sin(t * 0.55), 0.35, 0.65], dtype=np.float32)
    sheen /= np.linalg.norm(sheen)
    half_k = (key + VIEW) / np.linalg.norm(key + VIEW)
    half_s = (sheen + VIEW) / np.linalg.norm(sheen + VIEW)

    back = N_rot @ VIEW < 0.0
    side = np.where(back, np.float32(-1.0), np.float32(1.0))
    diff = np.clip(side * (N_rot @ key), 0.0, 1.0)
    a2 = np.clip(side * (N_rot @ half_k), 0.0, 1.0) ** 2
    b2 = np.clip(side * (N_rot @ half_s), 0.0, 1.0) ** 2
    shade = (0.58 + 0.56 * diff + 0.35 * (a2 ** 4 + 0.65 * b2 ** 4)) * v["gain"]

    # Điều chỉnh độ sáng riêng cho nền màn hình tối và chữ phát sáng trên laptop
    is_scr_bg = T == SCREEN_BG
    is_scr_txt = T == SCREEN_TEXT
    shade[is_scr_bg] = 0.28
    shade[is_scr_txt] = 1.32
    shade[T == LAPTOP_DECK] *= 0.72
    shade[T == KEYCAP] *= 1.15
    shade[T == PETAL] += 0.12
    shade[T == EDGE] += 0.15

    # Hoa chớp trắng khi bắt đầu bung cánh
    lit = v["lit"]
    if len(lit):
        w = v["W"][lit]
        rgb[lit] += (WHITE - rgb[lit]) * w[:, None]
        shade[lit] += 0.8 * w

    # Sóng compile chạy từ đáy laptop lên đỉnh bó hoa tại mốc T_COMPILE
    if T_COMPILE <= t <= T_COMPILE + 1.1:
        front_y = -0.82 + 1.85 * (t - T_COMPILE) / 0.9
        wave = np.exp(-((P_rot[:, 1] - front_y) / 0.09) ** 2)
        shade += 1.35 * wave
        rgb += (CYAN - rgb) * (0.65 * wave)[:, None]

    # Vệt sáng vàng kim lướt chéo qua toàn bộ tác phẩm, lặp lại dịu dàng mỗi 9 giây sau khi hoàn thiện
    if t >= T_GLEAM[0]:
        gleam_span = T_GLEAM[1] - T_GLEAM[0]
        g_age = (t - T_GLEAM[0]) % 9.0
        if g_age < gleam_span + 0.3:
            u_gleam = P_rot[:, 0] + 0.45 * P_rot[:, 1]
            at = -1.0 + 2.2 * g_age / gleam_span
            gl = np.exp(-((u_gleam - at) / 0.11) ** 2)
            shade += 1.05 * gl
            rgb += (WHITE - rgb) * (0.55 * gl)[:, None]

    # Phần đang mọc lên có viền lóe trắng
    fresh = (~v["pop"]) & (age >= 0.0) & (age < 0.16)
    T[fresh] = GLINT
    shade[fresh] = 1.25
    rgb[fresh] = WHITE
    hot = v["pop"] & (age >= 0.0) & (age < FLASH)
    f = (np.clip(1.0 - age[hot] / FLASH, 0.0, 1.0) ** 2).astype(np.float32)
    rgb[hot] += (WHITE - rgb[hot]) * f[:, None]
    shade[hot] += 1.1 * f

    seen = age >= 0.0
    P_out, shade_out, rgb_out, T_out, K_out = P_rot[seen], shade[seen], rgb[seen], T[seen], v["K"][seen]

    # Gom các hạt bay (hoa bi, pháo hoa hoa nở, pháo hoa compile, sao nền)
    sp_r, ss_r, st_r = rose_pops(bq, t)
    sp_c, ss_c, st_c = compile_sparks(t)
    lit_bloss = np.clip(1.0 - (t - bq["blossom_appear"]) / FLASH, 0.0, 1.0) ** 2 * (t >= bq["blossom_appear"])
    bs = (0.55 + 0.35 * np.clip(np.sin(t * 1.4 + bq["blossom_phase"] * 30), 0, 1) ** 4 + 0.85 * lit_bloss) * (
        t >= bq["blossom_appear"]
    )
    fx_local = np.concatenate([bq["blossoms"], sp_r]) @ Ry.T
    gp, gs, gt = stars(t)
    fx_p = np.concatenate([fx_local, sp_c @ Ry.T, gp])
    fx_s = np.concatenate([bs, ss_r, ss_c, gs])
    fx_t = np.concatenate([np.full(len(bq["blossoms"]), BLOSSOM), st_r, st_c, gt])

    return (
        (P_out, shade_out, rgb_out, T_out, K_out),
        (fx_p, fx_s, fx_t),
        heads_rot,
        [(p @ Ry.T, col, pose, fd) for p, col, pose, fd in falling_petals(bq, t)],
        lang_tokens(t),
        {"open": int((op > 0.96).sum()), "grown": float(np.clip((t - 0.2) / 9.2, 0.0, 1.0))},
    )


def _message_layout(char, col, t, cw, ch, wish_lines):
    """Tính vị trí và bảng màu tối giản cho 3 dòng thiệp tiếng Việt gõ từng chữ ở bên dưới laptop."""
    if t < T_MSG:
        return []
    rows, cols = char.shape
    max_w = cols * cw - 44
    specs = [
        (0, T_MSG, 14, 22.0, 0.806, ICE_SILVER, WHITE),
        (1, T_MSG + 0.9, 15, 24.0, 0.848, WARM_CREAM, GOLD),
        (2, T_MSG + 2.2, 13, 26.0, 0.890, MUTED_SLATE, SOFT_SILVER),
    ]
    out = []
    # Xóa sạch sao nền trong dải chữ thiệp để lời chúc hiển thị rõ nét tuyệt đối.
    r_lo = max(0, int(0.77 * rows))
    r_hi = min(rows, int(0.92 * rows))
    char[r_lo:r_hi, :] = 0
    col[r_lo:r_hi, :] = 0

    for idx, t0, base_px, cps, y_ratio, c_base, c_hi in specs:
        if t < t0 or idx >= len(wish_lines) or not wish_lines[idx]:
            continue
        text = wish_lines[idx]
        # Tự thu nhỏ cỡ chữ nếu người dùng truyền lời chúc dài qua CLI để không tràn khung.
        size = max(10, round(base_px * (cols * cw) / 791))
        while len(text) * (0.60 * size) > max_w and size > 9:
            size -= 1
        advance = 0.60 * size
        x0 = (cols * cw - advance * len(text)) / 2.0
        shown = min(len(text), int((t - t0) * cps))
        love_at = text.find("<3")
        ph = (t - t0) % 1.05
        beat = float(np.exp(-(ph / 0.06) ** 2) + 0.55 * np.exp(-((ph - 0.24) / 0.06) ** 2))
        letters = []
        for i, ch_txt in enumerate(text[:shown]):
            if ch_txt == " ":
                continue
            new = float(np.clip(1.0 - ((t - t0) * cps - i) / 3.0, 0.0, 1.0))
            if love_at >= 0 and i >= love_at and i < love_at + 2:
                tint = (LOVE_RED + (WHITE - LOVE_RED) * new) * (1.0 + 0.55 * beat)
            else:
                shimmer = float(np.clip(np.sin(t * 2.8 - i * 0.45), 0.0, 1.0) ** 5)
                tint = c_base + (c_hi - c_base) * max(new, 0.8 * shimmer)
            letters.append((ch_txt, x0 + advance * (i + 0.5), np.clip(tint, 0.0, 1.0)))
        out.append({"size": size, "y": y_ratio * (rows * ch), "letters": letters})
    return out


def frame(t, cols, rows, cw, ch, wish_lines, msg_t=None):
    """Dựng hoàn chỉnh ma trận ký tự `char`, màu `col`, lớp tĩnh `steady` và dữ liệu overlay."""
    if msg_t is None:
        msg_t = t
    (P, shade, rgb, T, K), (fx_p, fx_s, fx_t), heads, fall, tokens, info = _scene_points(t)
    aspect = (cols * cw) / (rows * ch)
    x, y, z = look(P)
    zz = np.maximum(z, 0.2)
    sx = (0.5 + x / zz * FOCAL * 0.5 / aspect) * cols
    sy = (MIDDLE - y / zz * FOCAL * 0.5) * rows
    order = np.argsort(-z)
    ix, iy = sx[order].astype(int), sy[order].astype(int)
    ok = (ix >= 0) & (ix < cols) & (iy >= 0) & (iy < rows) & (z[order] > 0.2)
    o, ix, iy = order[ok], ix[ok], iy[ok]

    part = np.full((rows, cols), -1)
    depth = np.full((rows, cols), 99.0)
    lum = np.zeros((rows, cols), dtype=np.float32)
    tag = np.zeros((rows, cols), dtype=int)
    tint = np.zeros((rows, cols, 3), dtype=np.float32)
    part[iy, ix], depth[iy, ix], lum[iy, ix], tag[iy, ix], tint[iy, ix] = K[o], z[o], shade[o], T[o], rgb[o]
    body = part >= 0

    # Phát hiện biên vật thể và nếp gấp để thay bằng nét - / | \ thay vì ký tự đặc.
    pp = np.pad(part, 1, constant_values=-1)
    pd = np.pad(depth, 1, constant_values=99.0)
    edge = np.zeros_like(body)
    gx, gy = np.zeros((rows, cols), dtype=np.float32), np.zeros((rows, cols), dtype=np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == dy == 0:
                continue
            nb = pp[1 + dy:rows + 1 + dy, 1 + dx:cols + 1 + dx]
            nz = pd[1 + dy:rows + 1 + dy, 1 + dx:cols + 1 + dx]
            other_rose = (nb // 100 != part // 100) & (nb >= 1000) & (part >= 1000) & (nz >= depth)
            out = body & ((nb < 0) | ((nb != part) & (nz > depth + FOLD)) | other_rose)
            gx += dx * out
            gy += dy * out
            if dx == 0 or dy == 0:
                edge |= out

    r, c = np.mgrid[0:rows, 0:cols]
    h = (r * 7919 + c * 104729) % 9973
    level = np.clip((lum * 3.1).astype(int), 0, 3)
    inside = FILL[level, (h + (t * 4.0 + h % 11).astype(int)) % 12]
    char = np.where(body, np.where(edge, outline_letter(gx, gy), inside), 0)
    char = np.where(body & (tag == GLINT), C("*"), char)
    char = np.where(body & (tag == SCREEN_TEXT), C("#"), char)
    char = np.where(body & (tag == SCREEN_BG), np.where((h % 11) == 0, C("."), 0), char)
    light = np.where(body, np.where(edge, np.maximum(0.85, lum), np.clip(0.45 + 0.55 * lum / 0.9, 0.40, 1.35)), 0.0)
    col = tint * light[..., None]
    steady = body.copy()

    # Chiếu hạt sao, hoa bi và pháo hoa lên lưới nếu nằm phía trước vật thể.
    if len(fx_p):
        px, py, pz = look(fx_p)
        qx = ((0.5 + px / np.maximum(pz, 0.2) * FOCAL * 0.5 / aspect) * cols).astype(int)
        qy = ((MIDDLE - py / np.maximum(pz, 0.2) * FOCAL * 0.5) * rows).astype(int)
        m = (qx >= 0) & (qx < cols) & (qy >= 0) & (qy < rows) & (fx_s > 0.04) & (pz > 0.2)
        qx, qy, pz, s, k = qx[m], qy[m], pz[m], fx_s[m], fx_t[m]
        front = ~body[qy, qx] | ((pz < depth[qy, qx] - 0.04) & ((k == BLOSSOM) | (s > 0.55)))
        qx, qy, s, k = qx[front], qy[front], s[front], k[front]
        bloss = k == BLOSSOM
        char[qy, qx] = np.where(
            bloss,
            np.where(s > 0.8, C("*"), C("o")),
            np.where(s > 0.72, C("*"), np.where(s > 0.36, C("+"), C("."))),
        )
        col[qy, qx] = COLORS[k] * np.clip(np.where(bloss, s, 0.25 + s), 0.0, 1.3)[:, None]
        steady[qy, qx] = bloss
        hot = np.flatnonzero(~bloss & (s > 0.82))
        for j in hot[np.argsort(-s[hot])[:STAR_FLARES]]:
            rays(char, col, int(qy[j]), int(qx[j]), int(1 + 4 * min(s[j], 1.3) ** 2 / 1.3), COLORS[k[j]], 0.7 * min(s[j], 1.2))

    # Nhãn các ngôn ngữ lập trình (C, Python, C++, Java, JS, HTML...) trôi nhịp nhàng với tông màu dịu.
    token_colors = (ICE_SILVER, GOLD * 0.86, CYAN * 0.82)
    for pos, text, fade, c_idx in tokens:
        tx, ty, tz = look(pos[None])
        cx = int((0.5 + tx[0] / np.maximum(tz[0], 0.2) * FOCAL * 0.5 / aspect) * cols)
        cy = int((MIDDLE - ty[0] / np.maximum(tz[0], 0.2) * FOCAL * 0.5) * rows)
        for j, ch_tok in enumerate(text):
            xx = cx + j - len(text) // 2
            if 0 <= cy < rows and 0 <= xx < cols and not body[cy, xx]:
                char[cy, xx] = C(ch_tok)
                col[cy, xx] = token_colors[c_idx] * (0.95 * fade)
                steady[cy, xx] = True  # giữ chữ ngôn ngữ sắc nét, không bị nhòe bóng đôi khi trôi

    # Cánh hoa rơi
    for pos, rose_col, pose, fd in fall:
        fx_, fy_, fz_ = look(pos[None])
        cx = int((0.5 + fx_[0] / np.maximum(fz_[0], 0.2) * FOCAL * 0.5 / aspect) * cols)
        cy = int((MIDDLE - fy_[0] / np.maximum(fz_[0], 0.2) * FOCAL * 0.5) * rows)
        for j, letter in enumerate(FALL_POSES[pose]):
            x_ = cx + j
            if letter and 0 <= cy < rows and 0 <= x_ < cols and (not body[cy, x_] or fz_[0] < depth[cy, x_]):
                char[cy, x_] = C(letter)
                col[cy, x_] = rose_col * (1.15 * fd)
                steady[cy, x_] = False

    # Tia lóe sáng ở tâm các bông hoa vừa nở và tại điểm nhấn compile
    for hp, fl in heads:
        if fl > 0.15:
            hx, hy, hz = look(hp[None])
            cx = int((0.5 + hx[0] / np.maximum(hz[0], 0.2) * FOCAL * 0.5 / aspect) * cols)
            cy = int((MIDDLE - hy[0] / np.maximum(hz[0], 0.2) * FOCAL * 0.5) * rows)
            rays(char, col, cy, cx, int(2 + 5 * fl), WHITE, 0.55 + 0.6 * fl)

    if T_COMPILE <= t < T_COMPILE + 0.6:
        g_c = (1.0 - (t - T_COMPILE) / 0.6) ** 2
        cx, cy, cz = look(np.array([[0.0, 0.10, -0.18]], dtype=np.float32))
        rays(
            char,
            col,
            int((MIDDLE - cy[0] / cz[0] * FOCAL * 0.5) * rows),
            int((0.5 + cx[0] / cz[0] * FOCAL * 0.5 / aspect) * cols),
            int(3 + 7 * g_c),
            GOLD,
            0.7 + 0.7 * g_c,
        )

    info["messages"] = _message_layout(char, col, msg_t, cw, ch, wish_lines)
    info["letters"] = int((char > 0).sum())
    return char, col, steady, info
