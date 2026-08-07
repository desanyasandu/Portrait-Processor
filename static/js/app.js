document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const filePreviewInfo = document.getElementById('filePreviewInfo');
    const fileName = document.getElementById('fileName');
    const btnClearFile = document.getElementById('btnClearFile');
    const dropContent = dropZone.querySelector('.drop-zone-content');
    
    const cropperWrapper = document.getElementById('cropperWrapper');
    const cropperImage = document.getElementById('cropperImage');
    const cropXInput = document.getElementById('cropX');
    const cropYInput = document.getElementById('cropY');
    const cropWInput = document.getElementById('cropW');
    const cropHInput = document.getElementById('cropH');
    
    const zoomRange = document.getElementById('zoomRange');
    const zoomVal = document.getElementById('zoomVal');
    const blurRange = document.getElementById('blurRange');
    const blurVal = document.getElementById('blurVal');
    
    const uploadForm = document.getElementById('uploadForm');
    const btnProcess = document.getElementById('btnProcess');
    const btnText = btnProcess.querySelector('.btn-text');
    const spinner = btnProcess.querySelector('.spinner');
    
    const resultsSection = document.getElementById('resultsSection');
    const imgOriginal = document.getElementById('imgOriginal');
    const imgProcessed = document.getElementById('imgProcessed');
    const metaOriginal = document.getElementById('metaOriginal');
    const metaProcessed = document.getElementById('metaProcessed');
    const btnDownload = document.getElementById('btnDownload');

    let cropper = null;

    // Range slider updates
    zoomRange.addEventListener('input', (e) => {
        const zoom = parseFloat(e.target.value);
        zoomVal.textContent = zoom.toFixed(1) + 'x';
        
        if (cropper && cropper.imageData) {
            const imgData = cropper.getImageData();
            const targetW = imgData.naturalWidth / zoom;
            const targetH = imgData.naturalHeight / zoom;
            const cropBoxData = cropper.getCropBoxData();
            
            cropper.setCropBoxData({
                left: cropBoxData.left + (cropBoxData.width - targetW * (imgData.width / imgData.naturalWidth)) / 2,
                top: cropBoxData.top + (cropBoxData.height - targetH * (imgData.height / imgData.naturalHeight)) / 2,
                width: targetW * (imgData.width / imgData.naturalWidth),
                height: targetH * (imgData.height / imgData.naturalHeight)
            });
        }
    });

    blurRange.addEventListener('input', (e) => {
        blurVal.textContent = e.target.value + 'px';
    });

    if (edgeShiftRange) {
        edgeShiftRange.addEventListener('input', (e) => {
            edgeShiftVal.textContent = e.target.value + 'px';
        });
    }

    if (edgeBlurRange) {
        edgeBlurRange.addEventListener('input', (e) => {
            edgeBlurVal.textContent = e.target.value + 'px';
        });
    }

    // Radio card active state toggle
    document.querySelectorAll('.radio-card input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            document.querySelectorAll('.radio-card').forEach(card => card.classList.remove('active'));
            e.target.closest('.radio-card').classList.add('active');
        });
    });

    // Drag and Drop handlers
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFilePreview(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            updateFilePreview(e.target.files[0]);
        }
    });

    btnClearFile.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.value = '';
        dropContent.style.display = 'block';
        filePreviewInfo.style.display = 'none';
        cropperWrapper.style.display = 'none';
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
    });

    function updateFilePreview(file) {
        fileName.textContent = file.name + ` (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
        dropContent.style.display = 'none';
        filePreviewInfo.style.display = 'flex';

        const reader = new FileReader();
        reader.onload = (evt) => {
            cropperImage.src = evt.target.result;
            cropperWrapper.style.display = 'block';

            if (cropper) {
                cropper.destroy();
            }

            const currentZoom = parseFloat(zoomRange.value);
            cropper = new Cropper(cropperImage, {
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 1 / currentZoom,
                restore: false,
                guides: true,
                center: true,
                highlight: true,
                crop(event) {
                    cropXInput.value = Math.round(event.detail.x);
                    cropYInput.value = Math.round(event.detail.y);
                    cropWInput.value = Math.round(event.detail.width);
                    cropHInput.value = Math.round(event.detail.height);
                }
            });
        };
        reader.readAsDataURL(file);
    }

    // Form Submission via Fetch API
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!fileInput.files.length) {
            alert('කරුණාකර පළමුව Photos එකක් තෝරන්න (Select a photo first)');
            return;
        }

        const formData = new FormData(uploadForm);
        
        // If cropper data is ready, ensure crop box details are appended
        if (cropper) {
            const data = cropper.getData(true);
            formData.set('crop_x', data.x);
            formData.set('crop_y', data.y);
            formData.set('crop_w', data.width);
            formData.set('crop_h', data.height);
        }
        
        // Show loading state
        btnProcess.disabled = true;
        btnText.textContent = 'Processing Selected 2x Portrait Region...';
        spinner.style.display = 'inline-block';

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                imgOriginal.src = data.original_url + '?t=' + Date.now();
                imgProcessed.src = data.processed_url + '?t=' + Date.now();
                
                metaOriginal.textContent = `Original Size: ${data.orig_size[0]} x ${data.orig_size[1]} px`;
                metaProcessed.textContent = `Selected 2x Portrait Size: ${data.proc_size[0]} x ${data.proc_size[1]} px`;
                
                btnDownload.href = data.processed_url;
                btnDownload.setAttribute('download', 'portrait_2x.jpg');
                
                resultsSection.style.display = 'block';
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            } else {
                alert('Error: ' + (data.error || 'Processing failed'));
            }
        } catch (err) {
            alert('Network or Server Error: ' + err.message);
        } finally {
            btnProcess.disabled = false;
            btnText.textContent = '✨ Generate 2x Portrait Photo';
            spinner.style.display = 'none';
        }
    });
});
