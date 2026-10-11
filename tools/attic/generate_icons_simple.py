from PIL import Image, ImageDraw
import os

sizes = [72, 96, 128, 144, 152, 192, 384, 512]
output_dir = 'frontend/assets/icons/'

os.makedirs(output_dir, exist_ok=True)

for size in sizes:
    # Create a new image with gradient background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle background with gradient
    # Since we can't easily do gradients in PIL, use solid color
    radius = size // 5  # ~20% radius
    draw.rounded_rectangle([0, 0, size, size], radius=radius//5, fill=(0, 102, 204, 255))
    
    # Draw swim icon (simplified)
    center = size // 2
    icon_size = size // 2
    
    # Draw water waves
    wave_color = (255, 255, 255, 100)
    for i in range(3):
        y = center - icon_size//4 + i * (icon_size//4)
        draw.arc([size//8, y, size*7//8, y + icon_size//2], 0, 180, fill=(255,255,255,80), width=max(2, size//64))
    
    # Draw plus sign in center (simplified swim coach logo)
    center_x, center_y = size // 2, size // 2
    cross_size = size // 8
    line_width = max(3, size // 64)
    
    # Vertical line
    draw.line([center_x, center_y - cross_size, center_x, center_y + cross_size], fill='white', width=line_width)
    # Horizontal line
    draw.line([center_x - cross_size, center_y, center_x + cross_size, center_y], fill='white', width=line_width)
    
    # Small circle in center
    circle_r = size // 16
    draw.ellipse([center_x - circle_r, center_y - circle_r, center_x + circle_r, center_y + circle_r], fill=(0, 102, 204))
    
    output_path = os.path.join(output_dir, f'icon-{size}.png')
    img.save(output_path, 'PNG')
    print(f'Generated icon-{size}.png')

# Also create 512 maskable version
print('All icons generated!')