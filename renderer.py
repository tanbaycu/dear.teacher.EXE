"""Bộ dựng khung hình pygame-ce: vẽ atlas ký tự ASCII, vệt chuyển động, hiệu ứng glow 2 tầng và HUD."""

import numpy as np
import pygame

from constants import (
    ACCENT,
    CH,
    COLS,
    CREDIT,
    CW,
    DEFAULT_STUDENT_ID,
    DIM,
    FONT_PX,
    HINT,
    MONO,
    ROWS,
    SIGN,
    TRAIL,
)
from geometry import N_ROSES
from scene import frame

GREYS = [(i, i, i) for i in range(256)]
_ATLAS = {}
_BIG_FONTS = {}


def glyph_atlas(cw, ch, font_px):
    """Tạo bảng bitmap độ xám cho toàn bộ ký tự ASCII in được (32..126) để blitting nhanh."""
    key = (cw, ch, font_px)
    if key not in _ATLAS:
        pygame.font.init()
        font = pygame.font.SysFont(MONO, font_px)
        cells = []
        for code in range(32, 127):
            s = pygame.Surface((cw, ch))
            g = font.render(chr(code), True, (255, 255, 255))
            s.blit(g, ((cw - g.get_width()) // 2, (ch - g.get_height()) // 2))
            cells.append(pygame.surfarray.array3d(s).transpose(1, 0, 2)[..., 0])
        _ATLAS[key] = np.stack(cells)
    return _ATLAS[key]


def _big_font(size):
    """Cache font monospace hỗ trợ Unicode tiếng Việt theo từng kích cỡ chữ."""
    if size not in _BIG_FONTS:
        _BIG_FONTS[size] = pygame.font.SysFont(MONO, size, bold=True)
    return _BIG_FONTS[size]


class Renderer:
    """Quản lý surface vẽ, lớp trail chuyển động, blur phát sáng và lớp chữ thiệp tri ân."""

    def __init__(self, cols=COLS, rows=ROWS, cw=CW, ch=CH, font_px=FONT_PX, hud_px=13, hint=True):
        pygame.font.init()
        self.cols, self.rows, self.cw, self.ch = cols, rows, cw, ch
        self.w, self.h = cols * cw, rows * ch
        self.atlas = glyph_atlas(cw, ch, font_px)
        self.art = pygame.Surface((self.w, self.h))
        self.trail = pygame.Surface((self.w, self.h))
        self.out = pygame.Surface((self.w, self.h))
        self.tint = pygame.Surface((cols, rows))
        self.moving = pygame.Surface((self.w, self.h))
        self.still = pygame.Surface((self.w, self.h))
        self.small = pygame.font.SysFont(MONO, hud_px)
        self.hud_gap = int(hud_px * 1.42)
        self.hint = hint
        self.last_t = None

    @staticmethod
    def blur(src, size, radius):
        """Thu nhỏ và làm mờ Gaussian để tạo quầng sáng mượt không tốn CPU."""
        small = pygame.transform.smoothscale(src, size)
        if hasattr(pygame.transform, "gaussian_blur"):
            small = pygame.transform.gaussian_blur(small, max(1, radius))
        return small

    def glow(self, src):
        """Áp dụng 2 tầng phát sáng (quầng hẹp sắc nét + quầng rộng dịu) bằng cộng sáng BLEND_ADD."""
        w, h = self.w, self.h
        tight = self.blur(src, (w // 4, h // 4), 2)
        wide = self.blur(tight, (w // 8, h // 8), 3)
        for layer, amount in ((tight, 0.72), (wide, 0.42)):
            layer = pygame.transform.smoothscale(layer, (w, h))
            layer.fill((int(255 * amount),) * 3, special_flags=pygame.BLEND_MULT)
            self.out.blit(layer, (0, 0), special_flags=pygame.BLEND_ADD)

    def tinted(self, col, into):
        """Phủ màu RGB lên bitmap ký tự trắng bằng BLEND_MULT."""
        pygame.surfarray.blit_array(self.tint, (np.clip(col, 0, 1) * 255).astype(np.uint8).transpose(1, 0, 2))
        pygame.transform.scale(self.tint, (self.w, self.h), into)
        into.blit(self.art, (0, 0), special_flags=pygame.BLEND_MULT)
        return into

    def draw(self, t, wish_lines, student_id=DEFAULT_STUDENT_ID, msg_t=None):
        """Vẽ một khung hình hoàn chỉnh tại thời điểm `t` với bộ lời chúc `wish_lines`."""
        w, h = self.w, self.h
        char, col, steady, info = frame(t, self.cols, self.rows, self.cw, self.ch, wish_lines, msg_t=msg_t)
        grey = pygame.image.frombuffer(self.atlas[char].transpose(0, 2, 1, 3).tobytes(), (w, h), "P")
        grey.set_palette(GREYS)
        self.art.blit(grey, (0, 0))

        if self.last_t is None or t < self.last_t:
            self.trail.fill((0, 0, 0))
        self.last_t = t

        self.trail.fill((int(TRAIL * 255),) * 3, special_flags=pygame.BLEND_MULT)
        self.trail.blit(self.tinted(col * ~steady[..., None], self.moving), (0, 0), special_flags=pygame.BLEND_MAX)
        self.out.blit(self.trail, (0, 0))
        self.out.blit(self.tinted(col * steady[..., None], self.still), (0, 0), special_flags=pygame.BLEND_MAX)

        # Vẽ chữ lời chúc tiếng Việt TRƯỚC bước glow() để câu chúc cũng tỏa hào quang đồng bộ.
        for block in info["messages"]:
            fnt = _big_font(block["size"])
            for letter, x, rgb in block["letters"]:
                glyph = fnt.render(letter, True, tuple(int(255 * v) for v in rgb))
                self.out.blit(glyph, (int(x - glyph.get_width() / 2), int(block["y"] - glyph.get_height() / 2)))

        self.glow(self.out)

        # HUD gọn ở góc dưới trái và đồng hồ nhấp nháy ở góc trên phải.
        status_line = (
            f"MSSV {student_id}   build {info['grown'] * 100:5.1f}%   roses {info['open']}/{N_ROSES}   glyphs {info['letters']:,}"
        )
        lines = [status_line]
        if self.hint:
            lines.append(HINT)
        gap = self.hud_gap
        for i, text in enumerate(lines):
            self.out.blit(self.small.render(text, True, DIM), (24, h - 14 - gap * (len(lines) - i)))
        self.out.blit(self.small.render(CREDIT, True, SIGN), (24, h - 14 - gap * (len(lines) + 1) - gap // 3))

        top_badge = self.small.render("TDTU · DEAR TEACHER.EXE · 20/11", True, SIGN)
        self.out.blit(top_badge, (24, 16))
        clock_text = self.small.render(f"{'●' if int(t * 2) % 2 == 0 else ' '} t {t:05.2f}s", True, ACCENT)
        self.out.blit(clock_text, (w - 24 - clock_text.get_width(), 16))
        return self.out
