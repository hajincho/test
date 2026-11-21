"""Draw original alpha masks for the three game optics."""
import math
from pathlib import Path
import struct
import zlib


SIZE = 1024
OUT = Path(__file__).resolve().parents[2] / 'Textures' / 'FPVM'
STYLES = {
    'ZF39': (.42, .026, .002, .013),
    'ZF41': (.34, .036, .0015, .010),
    'ZF4': (.41, .025, .0017, .011),
}


def chunk(kind, value):
    return struct.pack('!I', len(value)) + kind + value + struct.pack('!I', zlib.crc32(kind + value))


def mask(shape):
    radius, gap, line, post = shape
    rgb = bytes((7, 8, 10))
    rows = []
    coords = [(pixel + .5) / SIZE - .5 for pixel in range(SIZE)]
    for y in coords:
        row = bytearray(b'\0')
        for x in coords:
            r = math.hypot(x, y)
            outside = min(1., max(0., (r - radius) * SIZE + .5))
            glass_edge = min(.6, max(0., (r - (radius - .065)) * 7.5))
            horizontal = abs(x) > gap and abs(y) < line
            vertical = y > 0 and abs(x) < post * min(1., y / .065)
            alpha = 1. if horizontal or vertical else max(outside, glass_edge)
            row.extend(rgb + bytes((round(alpha * 255),)))
        rows.append(row)
    header = struct.pack('!IIBBBBB', SIZE, SIZE, 8, 6, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(b''.join(rows), 9)) + chunk(b'IEND', b'')


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for name, shape in STYLES.items():
        (OUT / f'T_FPVM_View_{name}.png').write_bytes(mask(shape))
