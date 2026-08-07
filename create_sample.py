from PIL import Image, ImageDraw, ImageFont
import os

def generate_sample_photo(filepath="sample_1x.jpg"):
    # Create 1200x1600 portrait photo
    w, h = 1200, 1600
    img = Image.new("RGB", (w, h), "#1e293b")
    draw = ImageDraw.Draw(img)
    
    # Background patterns (trees/decorations)
    for x in range(50, w, 150):
        for y in range(50, h, 150):
            draw.ellipse([x, y, x+80, y+80], fill="#334155")
            draw.polygon([(x+40, y-30), (x, y+40), (x+80, y+40)], fill="#0f766e")
            
    # Center Subject (Person portrait simulation)
    cx, cy = w // 2, h // 2
    # Head
    draw.ellipse([cx - 140, cy - 260, cx + 140, cy + 20], fill="#f87171")
    # Face features
    draw.ellipse([cx - 50, cy - 140, cx - 10, cy - 100], fill="#38bdf8") # Left eye
    draw.ellipse([cx + 10, cy - 140, cx + 50, cy - 100], fill="#38bdf8") # Right eye
    draw.arc([cx - 60, cy - 60, cx + 60, cy - 20], start=0, end=180, fill="#ffffff", width=8) # Smile
    
    # Shoulders / Body
    draw.polygon([(cx - 320, cy + 500), (cx - 180, cy + 20), (cx + 180, cy + 20), (cx + 320, cy + 500)], fill="#6366f1")
    
    # Text overlay
    try:
        draw.text((cx - 180, cy + 300), "iPhone 14 Photo (1x)", fill="#ffffff")
    except Exception:
        pass
        
    img.save(filepath, quality=95)
    print(f"Sample image created at {filepath}")

if __name__ == "__main__":
    generate_sample_photo()
