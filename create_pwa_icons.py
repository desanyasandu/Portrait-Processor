import os
from PIL import Image, ImageDraw

def generate_icons():
    icon_dir = os.path.join(os.path.dirname(__file__), 'static', 'icons')
    os.makedirs(icon_dir, exist_ok=True)
    
    sizes = [180, 192, 512]
    
    for size in sizes:
        img = Image.new("RGBA", (size, size), (15, 23, 42, 255))
        draw = ImageDraw.Draw(img)
        
        # Rounded background box
        margin = int(size * 0.08)
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=int(size * 0.2), fill="#6366f1")
        
        # Inner camera lens accent
        cx, cy = size // 2, size // 2
        r1 = int(size * 0.28)
        draw.ellipse([cx - r1, cy - r1, cx + r1, cy + r1], fill="#38bdf8")
        
        r2 = int(size * 0.18)
        draw.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill="#0f172a")
        
        r3 = int(size * 0.07)
        draw.ellipse([cx - r3 + int(size*0.05), cy - r3 - int(size*0.05), cx + r3 + int(size*0.05), cy + r3 - int(size*0.05)], fill="#ffffff")
        
        # Save icon
        filename = f"icon-{size}.png" if size != 180 else "apple-touch-icon.png"
        filepath = os.path.join(icon_dir, filename)
        img.save(filepath, "PNG")
        print(f"Saved icon: {filepath}")

if __name__ == "__main__":
    generate_icons()
