import os
import subprocess
import uuid
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
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
        # Run ffmpeg command and capture output
        result = subprocess.run([
            get_ffmpeg(), '-i', video_path,
            '-vf', f"select=not(mod(n\\,{interval})),scale=w={app.config['MAX_WIDTH']}:h={app.config['MAX_HEIGHT']}:force_original_aspect_ratio=decrease",
            '-vsync', 'vfr',
            os.path.join(output_dir, 'frame_%04d.png')
        ], check=True, capture_output=True, text=True)
        
        # Check if any frames were actually created
        frames = os.listdir(output_dir)
        if not frames:
            print("No frames were extracted. FFmpeg output:", result.stderr)
            return False
            
        print(f"Successfully extracted {len(frames)} frames")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error during frame extraction: {str(e)}")
        return False

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        upload_id = uuid.uuid4().hex[:8]
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_{secure_filename(file.filename)}")
        file.save(video_path)
        
        frames_dir = os.path.join(app.config['FRAMES_DIR'], upload_id)
        if not extract_frames(video_path, frames_dir):
            return jsonify({'error': 'Frame extraction failed'}), 500
        
        frame_count = len(os.listdir(frames_dir))
        if frame_count == 0:
            return jsonify({'error': 'No frames were extracted from the video'}), 500
            
        return jsonify({
            'message': f'Upload successful. Extracted {frame_count} frames.',
            'upload_id': upload_id,
            'frame_count': frame_count
        })
        
    except Exception as e:
        print(f"Error processing upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    for folder in ['UPLOAD_FOLDER', 'FRAMES_DIR']:
        os.makedirs(app.config[folder], exist_ok=True)
    app.run(host='0.0.0.0', port=5500)