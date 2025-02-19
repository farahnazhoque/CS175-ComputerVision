import os
import subprocess
import uuid
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config.update({
    'UPLOAD_FOLDER': 'uploads',
    'FRAMES_DIR': 'frames',
    'MAX_WIDTH': 1080,
    'MAX_HEIGHT': 1920,
    'ALLOWED_EXTENSIONS': {'mp4', 'mov', 'avi'}
})

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_ffmpeg():
    ffmpeg = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
    if not os.path.exists(ffmpeg):
        raise FileNotFoundError("FFmpeg not found in working directory")
    return ffmpeg

def extract_frames(video_path, output_dir, interval=5):
    os.makedirs(output_dir, exist_ok=True)
    try:
        subprocess.run([
            get_ffmpeg(), '-i', video_path,
            '-vf', f"select=not(mod(n\\,{interval})),scale=w={app.config['MAX_WIDTH']}:h={app.config['MAX_HEIGHT']}:force_original_aspect_ratio=decrease",
            '-vsync', 'vfr',
            os.path.join(output_dir, 'frame_%04d.png')
        ], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('error.html', message="No file uploaded")
        
        file = request.files['file']
        if not file or not allowed_file(file.filename):
            return render_template('error.html', message="Invalid file type")
        
        upload_id = uuid.uuid4().hex[:8]
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_{secure_filename(file.filename)}")
        file.save(video_path)
        
        frames_dir = os.path.join(app.config['FRAMES_DIR'], upload_id)
        if not extract_frames(video_path, frames_dir):
            return render_template('error.html', message="Frame extraction failed")
        
        return redirect(url_for('upload_success', upload_id=upload_id))
    
    return render_template('upload.html')

@app.route('/success/<upload_id>')
def upload_success(upload_id):
    frames_dir = os.path.join(app.config['FRAMES_DIR'], upload_id)
    if os.path.exists(frames_dir):
        frame_count = len(os.listdir(frames_dir))
    else:
        frame_count = 0
    return render_template('success.html', 
                         upload_id=upload_id,
                         frame_count=frame_count)

if __name__ == '__main__':
    for folder in ['UPLOAD_FOLDER', 'FRAMES_DIR']:
        os.makedirs(app.config[folder], exist_ok=True)
    app.run(host='0.0.0.0', port=5000)