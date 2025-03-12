import os
import subprocess
import uuid
import sys
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Get the absolute path to the current directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config.update({
    'UPLOAD_FOLDER': os.path.join(BASE_DIR, 'uploads'),
    'FRAMES_DIR': os.path.join(BASE_DIR, 'frames'),
    'POSTSHOT_DIR': os.path.join(BASE_DIR, 'postshot_projects'),
    'SPLAT_DIR': os.path.join(BASE_DIR, 'splat_files'),
    'MAX_WIDTH': 1080,
    'MAX_HEIGHT': 1920,
    'ALLOWED_EXTENSIONS': {'mp4', 'mov', 'avi'},
    'POSTSHOT_CLI': r'C:\Program Files\Jawset Postshot\bin\postshot-cli.exe'
})

# Create required directories
for dir_key in ['UPLOAD_FOLDER', 'FRAMES_DIR', 'POSTSHOT_DIR', 'SPLAT_DIR']:
    os.makedirs(app.config[dir_key], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_frames(video_path, output_dir, interval=10):
    try:
        subprocess.run([
            'ffmpeg', '-i', video_path,
            '-vf', f"select=not(mod(n\\,{interval})),scale=w={app.config['MAX_WIDTH']}:h={app.config['MAX_HEIGHT']}:force_original_aspect_ratio=decrease",
            '-vsync', 'vfr',
            os.path.join(output_dir, 'frame_%04d.png')
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Frame extraction failed: {e}")
        return False

def run_postshot_training(frames_dir, project_id):
    try:
        # Use absolute paths consistently
        abs_frames_dir = os.path.abspath(frames_dir)
        project_path = os.path.join(app.config['POSTSHOT_DIR'], f"{project_id}.psht")
        ply_path = os.path.join(app.config['POSTSHOT_DIR'], f"{project_id}.ply")
        splat_path = os.path.join(app.config['SPLAT_DIR'], f"{project_id}.splat")
        
        # Ensure paths are absolute
        project_path = os.path.abspath(project_path)
        ply_path = os.path.abspath(ply_path)
        splat_path = os.path.abspath(splat_path)
        
        print(f"Training with frames from: {abs_frames_dir}")
        print(f"Project path: {project_path}")
        print(f"PLY path: {ply_path}")
        print(f"SPLAT path: {splat_path}")
        
        # First: Train the model with PLY export in one command
        train_process = subprocess.run([
            app.config['POSTSHOT_CLI'],
            'train',
            '--import', abs_frames_dir,
            '--output', project_path,
            '--export-splat-ply', ply_path,
            '--profile', 'Splat MCMC',
            '--train-steps-limit', '10',
        ], check=True, capture_output=True, text=True)
        
        print("Training output:", train_process.stdout)
        
        # Verify the PLY file exists
        if not os.path.exists(ply_path):
            print(f"PLY file not created at {ply_path}, trying separate export command...")
            
            # Try exporting separately
            export_process = subprocess.run([
                app.config['POSTSHOT_CLI'],
                'export',
                project_path,
                '--export-splat-ply', ply_path
            ], check=True, capture_output=True, text=True)
            
            print("Export output:", export_process.stdout)
        
        # Verify PLY exists after potential second attempt
        if not os.path.exists(ply_path):
            print(f"ERROR: PLY file still not created at {ply_path}")
            return None
        
        print(f"PLY file exists at {ply_path}, size: {os.path.getsize(ply_path)} bytes")
        
        # Use our convert.py script to convert PLY to SPLAT format
        convert_script = os.path.join(BASE_DIR, 'convert.py')
        print(f"Converting PLY to SPLAT using script: {convert_script}")
        
        convert_process = subprocess.run([
            sys.executable, 
            convert_script, 
            ply_path,
            splat_path
        ], check=True, capture_output=True, text=True)
        
        print("Convert script output:", convert_process.stdout)
        
        # Verify the SPLAT file was created
        if os.path.exists(splat_path):
            print(f"SPLAT file created successfully at {splat_path}, size: {os.path.getsize(splat_path)} bytes")
            return splat_path
        else:
            print(f"ERROR: Failed to create SPLAT file at {splat_path}")
            return None
                
    except subprocess.CalledProcessError as e:
        print(f"Processing failed: {e}")
        if hasattr(e, 'stdout'):
            print(f"STDOUT: {e.stdout}")
        if hasattr(e, 'stderr'):
            print(f"STDERR: {e.stderr}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if not file or not allowed_file(file.filename):
        return "Invalid file type", 400

    upload_id = uuid.uuid4().hex[:8]
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_{secure_filename(file.filename)}")
    file.save(video_path)

    frames_dir = os.path.join(app.config['FRAMES_DIR'], upload_id)
    os.makedirs(frames_dir, exist_ok=True)
    if not extract_frames(video_path, frames_dir):
        return "Frame extraction failed", 500

    splat_path = run_postshot_training(frames_dir, upload_id)
    if not splat_path or not os.path.exists(splat_path):
        return "SPLAT conversion failed", 500

    return redirect(url_for('view_model', model_id=upload_id))

@app.route('/view/<model_id>')
def view_model(model_id):
    splat_url = url_for('serve_splat', model_id=model_id, _external=True)
    return render_template('viewer.html', splat_url=splat_url)

@app.route('/splat/<model_id>.splat')
def serve_splat(model_id):
    splat_path = os.path.join(app.config['SPLAT_DIR'], f"{model_id}.splat")
    
    # Check if the splat file exists
    if not os.path.exists(splat_path):
        return "SPLAT file not found", 404
    
    # Serve the SPLAT file with proper CORS headers
    response = send_from_directory(app.config['SPLAT_DIR'], f"{model_id}.splat")
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/models')
def list_models():
    """List all available models"""
    models = []
    for filename in os.listdir(app.config['SPLAT_DIR']):
        if filename.endswith('.splat'):
            model_id = filename.replace('.splat', '')
            models.append({
                'id': model_id,
                'url': url_for('view_model', model_id=model_id)
            })
    return render_template('models.html', models=models)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)