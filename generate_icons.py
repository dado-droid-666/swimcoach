import cairosvg
import os

sizes = [72, 96, 128, 144, 152, 192, 384, 512]
input_svg = 'frontend/assets/icons/icon.svg'
output_dir = 'frontend/assets/icons/'

os.makedirs(output_dir, exist_ok=True)

for size in sizes:
    output_path = os.path.join(output_dir, f'icon-{size}.png')
    cairosvg.svg2png(
        url='frontend/assets/icons/icon.svg',
        write_to=output_path,
        output_width=size,
        output_height=size
    )
    print(f'Generated icon-{size}.png')

# Also create a maskable version for 512
cairosvg.svg2png(
    url='frontend/assets/icons/icon.svg',
    write_to=os.path.join(output_dir, 'icon-512-maskable.png'),
    output_width=512,
    output_height=512
)

print('All icons generated!')