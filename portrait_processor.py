import os
import argparse
from PIL import Image, ImageFilter, ImageDraw
import numpy as np

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from rembg import remove, new_session
    HAS_REMBG = True
    _SESSIONS = {}
    def get_rembg_session(model_name: str = "u2net_human_seg"):
        global _SESSIONS
        if model_name not in _SESSIONS:
            print(f"[AI Engine] Loading segmentation model '{model_name}'...")
            _SESSIONS[model_name] = new_session(model_name)
        return _SESSIONS[model_name]
except ImportError:
    HAS_REMBG = False

def crop_center_zoom(img: Image.Image, zoom_factor: float = 2.0, crop_box: tuple = None) -> Image.Image:
    """
    Crops the image to simulate optical zoom.
    If crop_box (x, y, w, h) is provided in pixels, crops that exact region.
    Otherwise, crops dead-center based on zoom_factor.
    """
    width, height = img.size
    
    if crop_box is not None:
        x, y, w, h = crop_box
        left = max(0, min(width - 1, int(x)))
        top = max(0, min(height - 1, int(y)))
        right = max(left + 1, min(width, int(x + w)))
        bottom = max(top + 1, min(height, int(y + h)))
        return img.crop((left, top, right, bottom))
    
    crop_width = width / zoom_factor
    crop_height = height / zoom_factor
    
    left = (width - crop_width) / 2
    top = (height - crop_height) / 2
    right = (width + crop_width) / 2
    bottom = (height + crop_height) / 2
    
    return img.crop((left, top, right, bottom))

def apply_ai_portrait_blur(
    img: Image.Image,
    blur_radius: int = 25,
    edge_shift: int = -2,
    edge_blur: int = 4,
    anti_halo: bool = True,
    model_name: str = "u2net_human_seg"
) -> Image.Image:
    """
    Studio Quality AI Portrait Mode:
    1. High-precision human segmentation model (u2net_human_seg / isnet-general-use).
    2. Background Inpainting: Fills subject area with surrounding background colors before blurring to completely ELIMINATE DARK HALO / BLEED.
    3. Edge Inset / Shift: Insets mask slightly (-1 to -3px) to remove background outlines around arms/hair.
    4. Sub-pixel Feathering for ultra-smooth edge blending.
    """
    if not HAS_REMBG:
        print("[Notice] rembg not available, falling back to radial focal blur.")
        return apply_focal_portrait_blur(img, blur_radius)
    
    try:
        session = get_rembg_session(model_name)
        raw_mask = remove(img, session=session, only_mask=True)
        if raw_mask.mode != 'L':
            raw_mask = raw_mask.convert('L')
            
        img_np = np.array(img.convert("RGB"))
        mask_np = np.array(raw_mask)
        
        if HAS_CV2:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            h, w = img_bgr.shape[:2]
            
            # 1. Morphological Edge Shift / Inset
            if edge_shift < 0:
                k_size = abs(edge_shift) * 2 + 1
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
                mask_shifted = cv2.erode(mask_np, kernel, iterations=1)
            elif edge_shift > 0:
                k_size = edge_shift * 2 + 1
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
                mask_shifted = cv2.dilate(mask_np, kernel, iterations=1)
            else:
                mask_shifted = mask_np.copy()

            # 2. Anti-Halo Bleed Filter (Background Inpainting)
            if anti_halo and blur_radius > 3:
                # Expand subject mask to cover potential blur bleed region
                dilate_radius = max(3, blur_radius // 2)
                d_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_radius * 2 + 1, dilate_radius * 2 + 1))
                inpaint_mask = cv2.dilate(mask_np, d_kernel, iterations=1)
                
                # Inpaint subject region using surrounding background colors
                bg_inpainted = cv2.inpaint(img_bgr, inpaint_mask, inpaintRadius=max(5, blur_radius // 3), flags=cv2.INPAINT_TELEA)
            else:
                bg_inpainted = img_bgr

            # 3. Blur Background (No dark halo because subject is inpainted!)
            sigma = max(1.0, blur_radius / 2.0)
            bg_blurred_bgr = cv2.GaussianBlur(bg_inpainted, (0, 0), sigmaX=sigma, sigmaY=sigma)

            # 4. Smooth Alpha Mask Feathering
            if edge_blur > 0:
                mask_float = cv2.GaussianBlur(mask_shifted.astype(np.float32), (0, 0), sigmaX=edge_blur / 2.0) / 255.0
            else:
                mask_float = mask_shifted.astype(np.float32) / 255.0

            mask_3ch = np.dstack([mask_float] * 3)

            # 5. Composite Sharp Subject over Blurred Inpainted Background
            final_bgr = (img_bgr.astype(np.float32) * mask_3ch + bg_blurred_bgr.astype(np.float32) * (1.0 - mask_3ch))
            final_bgr = np.clip(final_bgr, 0, 255).astype(np.uint8)
            final_rgb = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2RGB)
            return Image.fromarray(final_rgb)
        else:
            # Fallback PIL compositing if CV2 is missing
            mask_pil = Image.fromarray(mask_np)
            if edge_blur > 0:
                mask_pil = mask_pil.filter(ImageFilter.GaussianBlur(radius=edge_blur))
            bg_blurred = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            return Image.composite(img, bg_blurred, mask_pil)
            
    except Exception as e:
        print(f"[Warning] AI Portrait Blur failed: {e}. Falling back to radial blur.")
        return apply_focal_portrait_blur(img, blur_radius)

def apply_focal_portrait_blur(img: Image.Image, blur_radius: int = 25) -> Image.Image:
    """
    Creates an optical depth/portrait effect using a smooth center-focused radial gradient mask.
    """
    width, height = img.size
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    
    cx, cy = width // 2, height // 2
    rx, ry = int(width * 0.38), int(height * 0.42)
    
    for r in range(max(rx, ry), 0, -1):
        alpha = int(255 * (1.0 - (r / max(rx, ry)) ** 1.5))
        alpha = max(0, min(255, alpha))
        box = [cx - int(rx * (r / max(rx, ry))),
               cy - int(ry * (r / max(rx, ry))),
               cx + int(rx * (r / max(rx, ry))),
               cy + int(ry * (r / max(rx, ry)))]
        draw.ellipse(box, fill=alpha)
        
    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(15, blur_radius)))
    blurred_img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return Image.composite(img, blurred_img, mask)

def apply_simple_gaussian_blur(img: Image.Image, blur_radius: int = 15) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

def process_portrait(
    image_path: str,
    output_path: str = None,
    zoom_factor: float = 2.0,
    blur_radius: int = 25,
    mode: str = "ai",
    crop_box: tuple = None,
    edge_shift: int = -2,
    edge_blur: int = 4,
    anti_halo: bool = True,
    model_name: str = "u2net_human_seg"
):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at path: {image_path}")
        
    img = Image.open(image_path).convert("RGB")
    cropped = crop_center_zoom(img, zoom_factor=zoom_factor, crop_box=crop_box)
    
    if mode == "ai":
        result = apply_ai_portrait_blur(
            cropped,
            blur_radius=blur_radius,
            edge_shift=edge_shift,
            edge_blur=edge_blur,
            anti_halo=anti_halo,
            model_name=model_name
        )
    elif mode == "focal":
        result = apply_focal_portrait_blur(cropped, blur_radius=blur_radius)
    else:
        result = apply_simple_gaussian_blur(cropped, blur_radius=blur_radius)
        
    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_portrait_2x{ext}"
        
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    result.save(output_path, quality=95)
    print(f"[Success] Processed image saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="iPhone 1x to 2x Studio Portrait Converter")
    parser.add_argument("input", help="Path to input 1x photo")
    parser.add_argument("-o", "--output", help="Path to output portrait photo", default=None)
    parser.add_argument("-z", "--zoom", type=float, default=2.0, help="Zoom factor")
    parser.add_argument("-b", "--blur", type=int, default=25, help="Blur radius")
    parser.add_argument("-m", "--mode", choices=["ai", "focal", "simple"], default="ai", help="Blur mode")
    parser.add_argument("--model", default="u2net_human_seg", help="AI Model: u2net_human_seg, isnet-general-use, u2netp")
    parser.add_argument("--edge-shift", type=int, default=-2, help="Mask edge inset/shift in px (default -2)")
    parser.add_argument("--edge-blur", type=int, default=4, help="Mask edge feathering blur in px (default 4)")
    parser.add_argument("--no-anti-halo", action="store_true", help="Disable anti-halo bleed filter")
    
    args = parser.parse_args()
    process_portrait(
        args.input,
        args.output,
        zoom_factor=args.zoom,
        blur_radius=args.blur,
        mode=args.mode,
        edge_shift=args.edge_shift,
        edge_blur=args.edge_blur,
        anti_halo=not args.no_anti_halo,
        model_name=args.model
    )
