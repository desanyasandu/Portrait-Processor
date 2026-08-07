import cv2
import numpy as np
from PIL import Image, ImageFilter
from rembg import remove, new_session
import time

def generate_pro_portrait(img_pil: Image.Image, blur_radius: int = 35, edge_shift: int = -2, edge_blur: int = 5, model_name: str = "u2net_human_seg") -> Image.Image:
    """
    High Precision Pro Portrait Mode:
    1. Uses human-seg AI model for crisp hair/body outline
    2. Background Inpainting: Fills subject area with background colors before blurring to ELIMINATE DARK HALO / BLEED
    3. Edge Shift / Inset: Slightly shrinks mask inward (-1 to -3px) to remove background bleeding onto subject edges
    4. Smooth Matting: Feathered alpha channel for natural hair/cloth transition
    """
    # Convert PIL to CV2 BGR
    img_np = np.array(img_pil.convert("RGB"))
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    h, w = img_bgr.shape[:2]

    print(f"Running AI segmentation with {model_name}...")
    session = new_session(model_name)
    
    # 1. Get raw mask from rembg
    raw_mask_pil = remove(img_pil, session=session, only_mask=True)
    mask = np.array(raw_mask_pil.convert("L"))

    # 2. Refine mask with Morphological Edge Shift / Inset
    if edge_shift < 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (-edge_shift * 2 + 1, -edge_shift * 2 + 1))
        mask_refined = cv2.erode(mask, kernel, iterations=1)
    elif edge_shift > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (edge_shift * 2 + 1, edge_shift * 2 + 1))
        mask_refined = cv2.dilate(mask, kernel, iterations=1)
    else:
        mask_refined = mask.copy()

    # 3. Create Inpainted Background (Prevents dark halo / subject bleed during blur)
    # Binary mask for subject zone to inpaint
    inpaint_mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (blur_radius // 2 * 2 + 1, blur_radius // 2 * 2 + 1)))
    
    # Fast OpenCV Telea Inpainting to fill subject area with surrounding background colors
    bg_inpainted = cv2.inpaint(img_bgr, inpaint_mask, inpaintRadius=max(5, blur_radius // 3), flags=cv2.INPAINT_TELEA)

    # 4. Apply Blur to Inpainted Background (Now blur has ZERO dark halo/bleed from subject!)
    bg_blurred_bgr = cv2.GaussianBlur(bg_inpainted, (0, 0), sigmaX=blur_radius / 2.0)

    # 5. Smooth Mask for natural soft edge transitions
    if edge_blur > 0:
        mask_float = cv2.GaussianBlur(mask_refined.astype(np.float32), (0, 0), sigmaX=edge_blur / 2.0) / 255.0
    else:
        mask_float = mask_refined.astype(np.float32) / 255.0

    mask_3ch = np.dstack([mask_float] * 3)

    # 6. Composite Sharp Subject over Inpainted & Blurred Background
    final_bgr = (img_bgr.astype(np.float32) * mask_3ch + bg_blurred_bgr.astype(np.float32) * (1.0 - mask_3ch)).astype(np.uint8)
    
    final_rgb = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(final_rgb)

if __name__ == "__main__":
    t0 = time.time()
    img = Image.open("sample_1x.jpg")
    result = generate_pro_portrait(img, blur_radius=30, edge_shift=-2, edge_blur=4, model_name="u2net_human_seg")
    result.save("sample_pro_portrait.jpg", quality=95)
    print(f"Done in {time.time() - t0:.2f}s! Saved to sample_pro_portrait.jpg")
