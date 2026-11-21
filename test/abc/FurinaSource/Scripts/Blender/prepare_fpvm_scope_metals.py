"""Prepare the four texture maps used by the Unreal scope materials."""
from pathlib import Path
import sys
from zipfile import ZipFile

from PIL import Image


def main(archives):
    output = Path(__file__).resolve().parents[2] / 'Textures' / 'FPVM' / 'Metals'
    output.mkdir(parents=True, exist_ok=True)
    for path in archives:
        number = path.name.split('_')[0]
        assert number in ('Metal063', 'Metal038'), path
        with ZipFile(path) as source:
            for role in ('Color', 'NormalDX', 'Metalness', 'Roughness'):
                with source.open(f'{number}_4K-PNG_{role}.png') as stream, Image.open(stream) as image:
                    mode = 'RGB' if role in ('Color', 'NormalDX') else 'L'
                    converted = image.convert(mode)
                    converted.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
                    converted.save(output / f'T_FPVM_{number}_{role}.png')


if __name__ == '__main__':
    main([Path(arg) for arg in sys.argv[1:]])
