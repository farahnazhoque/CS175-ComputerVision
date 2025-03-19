# CS175-ComputerVision

# Project Setup Instructions

## 1. Prerequisites

1. **Python 3.x** (3.8 or higher recommended)  
2. **Node.js and npm** (Node 18+ recommended)  
3. **Git** (to clone this repository)

Make sure you have enough free disk space—some dependencies can be large (especially Node modules).

---

## 2. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

**Tip:** If you don’t have Git installed, you can [download it here](https://git-scm.com/downloads).

---

## 3. Set Up the Python Backend (Flask)

1. **Change directory** to the `server` (or backend) folder (if applicable):
   ```bash
   cd server
   ```
2. **Create a virtual environment** (recommended to keep dependencies isolated):
   ```bash
   python -m venv env
   ```
3. **Activate** the virtual environment:

   - **macOS / Linux**:
     ```bash
     source env/bin/activate
     ```
   - **Windows (Command Prompt)**:
     ```bash
     env\Scripts\activate
     ```
   - **Windows (PowerShell)**:
     ```powershell
     .\env\Scripts\Activate.ps1
     ```

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   If you don’t have a `requirements.txt` file, install Flask or other dependencies manually:
   ```bash
   pip install flask flask-cors  # for example
   ```

5. **Run and install postshot.exe**:
   The exe file is included inside the server folder and should correctly install the cli interface.


6. **Run the Flask server**:
   ```bash
   python hello.py
   ```
   (Whatever your main entry point is.)

   By default, Flask serves on `http://127.0.0.1:5000`.

---

## 4. Set Up the Front-End (Vue)

1. **Change directory** to the Vue frontend folder:
   ```bash
   cd ../frontend
   ```
   (Adjust the path if your frontend folder is elsewhere.)
2. **Install node modules**:
   ```bash
   npm install
   ```
3. **Install tailwindcss modules**:
   ```bash
   npm install tailwindcss @tailwindcss/vite
   ```
4. **Run the development server**:
   ```bash
   npm run dev
   ```
   This usually starts the app at `http://127.0.0.1:5173` (or a different port).

5. **Optional:** If you want a production build:
   ```bash
   npm run build
   ```
   This creates a `/dist` folder with optimized production files. You can then serve those from Flask or a static hosting service, depending on your deployment setup.

---

## 5. How to Use / Testing

- **Open** your browser and navigate to the **Vue dev server** URL (e.g., `http://127.0.0.1:5173`), which proxies API calls to the Flask server (if you’ve set up a Vite proxy or used CORS).  
- **Or**, directly hit `http://127.0.0.1:5000` if you want to see any Flask routes (like `http://127.0.0.1:5000/api/...`).

---

## 6. Backups

If you need to backup or share data:

1. **Uploads Folder**: If your application uploads files to a folder (e.g., `server/uploads`), be sure to:
   - Include it in `.gitignore` if it should not be stored in version control.
   - Regularly **zip** and back it up externally, or push it to cloud storage (AWS S3, Google Drive, etc.) if needed.
2. **Database**: If you have a database (e.g., SQLite, PostgreSQL), back up the `.db` file or export SQL dumps as needed.
3. **Git**: Pushing changes to a remote Git repository also provides version control backups of your code base.

---

## 7. Common Issues

- **ENOSPC (No Space Left on Device)**: Make sure you have enough disk space before installing Node modules.  
- **Wrong Node Version**: If you see errors like `structuredClone` not defined, upgrade to **Node 18+**.  
- **CORS Errors**: If you see “Cross-Origin Request Blocked,” either enable [flask-cors](https://pypi.org/project/Flask-Cors/) or use a dev-server proxy in `vite.config.js`.

---

## 8. Contributing

1. **Fork** the repository on GitHub.  
2. **Create a branch** from `main` (e.g., `feature/new-stuff`).  
3. **Commit** and **push** your changes to your forked repo.  
4. **Open a Pull Request** to the main repository once your feature/fix is ready.  

---
