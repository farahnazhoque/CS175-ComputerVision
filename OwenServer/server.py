import os
import subprocess
import uuid
import shutil
import time
from flask import Flask, request, redirect, url_for, render_template, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config.update({
    'UPLOAD_FOLDER': 'uploads',
    'FRAMES_DIR': 'frames',
    'COLMAP_DIR': 'colmap_output',
    'DATASETS_DIR': 'datasets',
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

def prepare_dataset(upload_id):
    # Path setup
    colmap_dir = os.path.join(app.config['COLMAP_DIR'], upload_id)
    dataset_dir = os.path.join(app.config['DATASETS_DIR'], upload_id)
    frames_dir = os.path.join(app.config['FRAMES_DIR'], upload_id)
    
    # Create dataset structure
    os.makedirs(dataset_dir, exist_ok=True)
    shutil.move(frames_dir, os.path.join(dataset_dir, 'images'))
    
    # Convert COLMAP output to JSON
    subprocess.run([
        'python', 'colmap_to_json.py',
        '--colmap_dir', colmap_dir,
        '--output_json', os.path.join(dataset_dir, 'transforms.json')
    ], check=True)
    
    # Downsample point cloud
    dense_ply = os.path.join(colmap_dir, 'dense/fused.ply')
    output_ply = os.path.join(dataset_dir, 'points3D_downsample2.ply')
    subprocess.run([
        'python', 'scripts/downsample_point.py',
        dense_ply, output_ply
    ], check=True)
    
    return dataset_dir

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('error.html', message="No file uploaded")
        
        file = request.files['file']
        if not file or not allowed_file(file.filename):
            return render_template('error.html', message="Invalid file type")
        
        # Create session ID
        upload_id = uuid.uuid4().hex[:8]
        session['upload_id'] = upload_id
        session['status'] = []
        
        # Create directories
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_{secure_filename(file.filename)}")
        file.save(video_path)
        
        # Step 1: Extract frames
        frames_dir = os.path.join(app.config['FRAMES_DIR'], upload_id)
        if not extract_frames(video_path, frames_dir):
            return render_template('error.html', message="Frame extraction failed")
        
        # Step 2: Run COLMAP
        colmap_dir = os.path.join(app.config['COLMAP_DIR'], upload_id)
        try:
            subprocess.run([
                'python', 'colmap_sfm.py',
                '--input', frames_dir,
                '--output', colmap_dir,
                '--width', str(app.config['MAX_WIDTH']),
                '--height', str(app.config['MAX_HEIGHT'])
            ], check=True)
        except subprocess.CalledProcessError:
            return render_template('error.html', message="COLMAP processing failed")
        
        # Step 3: Prepare 4DG dataset
        try:
            dataset_dir = prepare_dataset(upload_id)
        except Exception as e:
            return render_template('error.html', message=f"Dataset prep failed: {str(e)}")
        
        # Step 4: Launch training
        log_file = os.path.join(dataset_dir, 'training.log')
        subprocess.Popen([
            'python', 'train.py',
            '-s', dataset_dir,
            '--port', '6017',
            '--expname', f'custom/{upload_id}',
            '--configs', 'arguments/hypernerf/default.py'
        ], stdout=open(log_file, 'w'), stderr=subprocess.STDOUT)
        
        return redirect(url_for('training_status', upload_id=upload_id))
    
    return render_template('upload.html')

@app.route('/status/<upload_id>')
def training_status(upload_id):
    log_path = os.path.join(app.config['DATASETS_DIR'], upload_id, 'training.log')
    try:
        with open(log_path) as f:
            log = f.read().splitlines()[-20:]  # Get last 20 lines
    except FileNotFoundError:
        log = ["No log available yet"]
    
    return render_template('status.html', 
                         upload_id=upload_id,
                         log=log)

if __name__ == '__main__':
    for folder in ['UPLOAD_FOLDER', 'FRAMES_DIR', 'COLMAP_DIR', 'DATASETS_DIR']:
        os.makedirs(app.config[folder], exist_ok=True)
    app.run(host='0.0.0.0', port=5000)