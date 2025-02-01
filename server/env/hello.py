from flask import Flask, request, render_template, send_from_directory
import os
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mov', 'mp4', 'avi', 'mkv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # ensure the folder exists

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])  # <--- 'methods' must be plural
def upload_file():
    if request.method == 'POST':
        # If no file part in the request
        if 'file' not in request.files:
            return "No file part in request"
        
        file = request.files['file']
        email = request.form.get('email')  # if you’re sending an email field, too

        # If user didn't select a file
        if file.filename == '':
            return "No selected file"

        # Allowed file?
        if file and allowed_file(file.filename):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            return f"File '{file.filename}' uploaded successfully, email: {email}"
        else:
            return "File type not allowed"
    # If GET request
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    print("Starting Flask...")
    app.run(debug=True, port=5000)
