"""Copy the maps supplied for the three cartridge render materials."""
from pathlib import Path
import sys
from zipfile import ZipFile

from PIL import Image

DATA = Path(__file__).resolve().parents[2] / 'Textures' / 'FPVM' / 'PistolMetals'


def main(source):
    DATA.mkdir(parents=True, exist_ok=True)
    for metal in ('Metal048B', 'Metal058A'):
        with ZipFile(source / (metal + '_2K-PNG.zip')) as archive:
            for role in ('Color', 'NormalDX', 'Metalness', 'Roughness'):
                with archive.open(f'{metal}_2K-PNG_{role}.png') as stream, Image.open(stream) as image:
                    write(image, metal, role)
    with ZipFile(source / '9mm_Bullets_3D0020_LOD0.zip') as archive:
        for label in ('BaseColor', 'Normal', 'OcclusionRoughnessMetallic'):
            with archive.open(f'TEXTURES/Nine_MM_Bullet/PBR-Unreal/Nine_MM_Bullet_{label}.jpg') as stream, Image.open(stream) as image:
                if label == 'OcclusionRoughnessMetallic':
                    _, rough, metallic = image.convert('RGB').split()
                    write(rough, 'NineMM', 'Roughness')
                    write(metallic, 'NineMM', 'Metalness')
                else:
                    write(image, 'NineMM', 'Color' if label == 'BaseColor' else 'NormalDX')


def write(image, material, role):
    converted = image.convert('RGB' if role in ('Color', 'NormalDX') else 'L')
    converted.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    converted.save(DATA / f'T_FPVM_{material}_{role}.png')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
