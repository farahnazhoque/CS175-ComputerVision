import os
import subprocess
import uuid
from flask import Flask, request, redirect, url_for, render_template, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'cs175'  

# Configuration
UPLOAD_FOLDER = 'uploads'
BASE_FRAMES = 'frames'
BASE_COLMAP_OUTPUT = 'colmap_output'
MAX_WIDTH = 1080  # Maximum width for scaling (portrait-friendly)
MAX_HEIGHT = 1920  # Maximum height for scaling (portrait-friendly)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

def get_ffmpeg_path():
    """Get local FFmpeg path with platform-specific handling"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    windows_exe = os.path.join(base_dir, 'ffmpeg.exe')
    if os.path.exists(windows_exe):
        return windows_exe
    unix_bin = os.path.join(base_dir, 'ffmpeg')
    if os.path.exists(unix_bin):
        return unix_bin
    raise FileNotFoundError("FFmpeg not found in project directory")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_frames(video_path, output_folder, frame_interval=5):
    """Extract frames from video, scaling to max resolution while maintaining aspect ratio."""
    os.makedirs(output_folder, exist_ok=True)
    try:
        ffmpeg_path = get_ffmpeg_path()
        command = [
            ffmpeg_path,
            '-i', video_path,
            '-vf', f"select=not(mod(n\\,{frame_interval})),scale='min({MAX_WIDTH},iw)':'min({MAX_HEIGHT},ih)':force_original_aspect_ratio=decrease,pad={MAX_WIDTH}:{MAX_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            '-vsync', 'vfr',
            os.path.join(output_folder, 'frame%04d.png')
        ]
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Extraction Error: {str(e)}")
        return False

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            session['status'] = "No file part in the request."
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            session['status'] = "No selected file."
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Create unique ID for this upload
            upload_id = str(uuid.uuid4())[:8]
            filename = secure_filename(file.filename)
            
            # Create session-specific folders
            frames_folder = os.path.join(BASE_FRAMES, upload_id)
            colmap_folder = os.path.join(BASE_COLMAP_OUTPUT, upload_id)
            os.makedirs(frames_folder, exist_ok=True)
            os.makedirs(colmap_folder, exist_ok=True)
            
            # Save uploaded file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_{filename}")
            file.save(filepath)
            
            session['status'] = "File uploaded successfully. Extracting frames..."
            if extract_frames(filepath, frames_folder):
                session['status'] = "Frames extracted successfully. Running COLMAP processing..."
                try:
                    # Run COLMAP processing with standardized camera parameters
                    subprocess.run([
                        'python', 'colmap_sfm.py',
                        '--input', frames_folder,
                        '--output', colmap_folder,
                        '--width', str(MAX_WIDTH),
                        '--height', str(MAX_HEIGHT)
                    ], check=True)
                    session['status'] = "COLMAP processing completed successfully."
                    return redirect(url_for('results', upload_id=upload_id))
                except subprocess.CalledProcessError as e:
                    session['status'] = f"COLMAP processing failed: {str(e)}"
                    return redirect(request.url)
            else:
                session['status'] = "Frame extraction failed - check server logs."
                return redirect(request.url)
    
    # Render the upload page with status feedback
    status = session.pop('status', None)
    return render_template('index.html', status=status)

@app.route('/results/<upload_id>')
def results(upload_id):
    # Display results for specific upload
    frames_folder = os.path.join(BASE_FRAMES, upload_id)
    colmap_folder = os.path.join(BASE_COLMAP_OUTPUT, upload_id)
    try:
        results = {
            'upload_id': upload_id,
            'num_images': len(os.listdir(frames_folder)),
            'colmap_output': os.listdir(colmap_folder),
            'resolution': f"{MAX_WIDTH}x{MAX_HEIGHT}"
        }
    except FileNotFoundError:
        results = {
            'upload_id': upload_id,
            'error': 'Results no longer available'
        }
    return render_template('results.html', results=results)

def create_folders():
    for folder in [UPLOAD_FOLDER, BASE_FRAMES, BASE_COLMAP_OUTPUT]:
        os.makedirs(folder, exist_ok=True)

if __name__ == '__main__':
    create_folders()
    try:
        get_ffmpeg_path()
        app.run(host='0.0.0.0', port=5000, debug=True)
    except FileNotFoundError as e:
        print(f"Critical Error: {str(e)}")
        print("Please place ffmpeg executable in the project folder")