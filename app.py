from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import uuid
from PIL import Image
from portrait_processor import process_portrait

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
PROCESSED_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'processed')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'photo' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    zoom_factor = float(request.form.get('zoom', 2.0))
    blur_radius = int(request.form.get('blur', 25))
    mode = request.form.get('mode', 'ai')
    
    edge_shift = int(request.form.get('edge_shift', -2))
    edge_blur = int(request.form.get('edge_blur', 4))
    anti_halo = request.form.get('anti_halo', 'true').lower() in ['true', 'on', '1']
    model_name = request.form.get('model_name', 'u2net_human_seg')
    
    crop_box = None
    if 'crop_x' in request.form and 'crop_y' in request.form and 'crop_w' in request.form and 'crop_h' in request.form:
        try:
            cx = float(request.form.get('crop_x'))
            cy = float(request.form.get('crop_y'))
            cw = float(request.form.get('crop_w'))
            ch = float(request.form.get('crop_h'))
            if cw > 0 and ch > 0:
                crop_box = (cx, cy, cw, ch)
        except ValueError:
            crop_box = None
    
    unique_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        ext = '.jpg'
        
    upload_name = f"orig_{unique_id}{ext}"
    processed_name = f"portrait_{unique_id}{ext}"
    
    upload_path = os.path.join(UPLOAD_FOLDER, upload_name)
    processed_path = os.path.join(PROCESSED_FOLDER, processed_name)
    
    file.save(upload_path)
    
    try:
        process_portrait(
            upload_path,
            processed_path,
            zoom_factor=zoom_factor,
            blur_radius=blur_radius,
            mode=mode,
            crop_box=crop_box,
            edge_shift=edge_shift,
            edge_blur=edge_blur,
            anti_halo=anti_halo,
            model_name=model_name
        )
        
        # Get dimensions
        with Image.open(upload_path) as orig_img:
            orig_size = orig_img.size
        with Image.open(processed_path) as proc_img:
            proc_size = proc_img.size
            
        return jsonify({
            'success': True,
            'original_url': f'/static/uploads/{upload_name}',
            'processed_url': f'/static/processed/{processed_name}',
            'orig_size': orig_size,
            'proc_size': proc_size
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"Starting iPhone 14 2x Portrait Web App (PWA Supported) on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
