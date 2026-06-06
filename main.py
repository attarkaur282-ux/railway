from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import subprocess
import os
import json
import uuid
import zipfile
import shutil
from datetime import datetime

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load server config
if os.path.exists('server.json'):
    with open('server.json', 'r') as f:
        server_config = json.load(f)
else:
    server_config = {"server": {"name": "Bike File Runner", "port": 8080, "max_connections": 100}}

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bike File Runner | Railway</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #0a0f1e, #0a1a2a);
            color: white;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; margin: 20px 0; color: #ff6600; }
        .card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            margin: 20px 0;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .file-upload-area {
            border: 2px dashed #ff6600;
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .file-upload-area:hover { background: rgba(255,102,0,0.1); }
        .file-list { margin-top: 20px; }
        .file-item {
            background: rgba(0,0,0,0.5);
            padding: 12px 15px;
            margin: 8px 0;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: monospace;
        }
        .run-btn {
            background: #ff6600;
            border: none;
            padding: 8px 20px;
            border-radius: 20px;
            color: white;
            cursor: pointer;
            font-weight: bold;
        }
        .delete-btn {
            background: #ff3333;
            border: none;
            padding: 8px 20px;
            border-radius: 20px;
            color: white;
            cursor: pointer;
            margin-left: 10px;
        }
        .output-area {
            background: #1e1e1e;
            border-radius: 10px;
            padding: 15px;
            font-family: monospace;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
            font-size: 12px;
        }
        .status { padding: 10px; border-radius: 10px; margin: 10px 0; }
        .success { background: #00aa0055; border: 1px solid #00ff00; }
        .error { background: #aa000055; border: 1px solid #ff0000; }
        .loading { background: #ff660055; border: 1px solid #ff6600; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab {
            padding: 10px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            cursor: pointer;
        }
        .tab.active { background: #ff6600; }
        .hidden { display: none; }
        button { font-family: inherit; }
        input, select { padding: 10px; border-radius: 10px; border: none; margin: 5px 0; width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏍️ Bike File Runner</h1>
        <p style="text-align: center">Upload aur Run karo .py, .js, .zip files</p>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('upload')">📤 Upload</div>
            <div class="tab" onclick="showTab('files')">📁 My Files</div>
            <div class="tab" onclick="showTab('login')">🔐 Login</div>
            <div class="tab" onclick="showTab('signup')">📝 Sign Up</div>
        </div>
        
        <!-- Upload Tab -->
        <div id="uploadTab" class="tab-content">
            <div class="card">
                <div class="file-upload-area" onclick="document.getElementById('fileInput').click()">
                    📂 Click ya Drag & Drop karo file<br>
                    <small>(.py, .js, .zip - max 50MB)</small>
                </div>
                <input type="file" id="fileInput" style="display:none" accept=".py,.js,.zip">
                <div id="uploadStatus"></div>
            </div>
        </div>
        
        <!-- Files Tab -->
        <div id="filesTab" class="tab-content hidden">
            <div class="card">
                <h3>📋 Uploaded Files</h3>
                <div id="fileList"></div>
            </div>
        </div>
        
        <!-- Login Tab -->
        <div id="loginTab" class="tab-content hidden">
            <div class="card">
                <h3>🔐 Login</h3>
                <input type="text" id="loginUsername" placeholder="Username">
                <input type="password" id="loginPassword" placeholder="Password">
                <button class="run-btn" onclick="login()">Login</button>
                <div id="loginStatus"></div>
            </div>
        </div>
        
        <!-- Signup Tab -->
        <div id="signupTab" class="tab-content hidden">
            <div class="card">
                <h3>📝 Sign Up</h3>
                <input type="text" id="signupUsername" placeholder="Username">
                <input type="email" id="signupEmail" placeholder="Email">
                <input type="password" id="signupPassword" placeholder="Password">
                <button class="run-btn" onclick="signup()">Sign Up</button>
                <div id="signupStatus"></div>
            </div>
        </div>
        
        <!-- Output Section -->
        <div class="card">
            <h3>📟 Output</h3>
            <div id="outputArea" class="output-area">Ready to run files...</div>
        </div>
    </div>
    
    <script>
        let currentToken = localStorage.getItem('token') || null;
        
        function showTab(tab) {
            document.querySelectorAll('.tab').forEach((t, i) => {
                t.classList.remove('active');
            });
            event.target.classList.add('active');
            
            document.getElementById('uploadTab').classList.add('hidden');
            document.getElementById('filesTab').classList.add('hidden');
            document.getElementById('loginTab').classList.add('hidden');
            document.getElementById('signupTab').classList.add('hidden');
            
            if(tab === 'upload') document.getElementById('uploadTab').classList.remove('hidden');
            if(tab === 'files') {
                document.getElementById('filesTab').classList.remove('hidden');
                loadFiles();
            }
            if(tab === 'login') document.getElementById('loginTab').classList.remove('hidden');
            if(tab === 'signup') document.getElementById('signupTab').classList.remove('hidden');
        }
        
        document.getElementById('fileInput').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if(!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById('uploadStatus').innerHTML = '<div class="status loading">⏳ Uploading...</div>';
            
            const res = await fetch('/upload', { method: 'POST', body: formData });
            const data = await res.json();
            
            if(data.status === 'ok') {
                document.getElementById('uploadStatus').innerHTML = '<div class="status success">✅ Uploaded: ' + data.filename + '</div>';
                loadFiles();
                runFile(data.filepath, data.extension);
            } else {
                document.getElementById('uploadStatus').innerHTML = '<div class="status error">❌ Error: ' + data.error + '</div>';
            }
        });
        
        async function loadFiles() {
            const res = await fetch('/files');
            const data = await res.json();
            
            if(data.files && data.files.length > 0) {
                document.getElementById('fileList').innerHTML = data.files.map(f => `
                    <div class="file-item">
                        <span>📄 ${f}</span>
                        <div>
                            <button class="run-btn" onclick="runFileByName('${f}')">▶ Run</button>
                            <button class="delete-btn" onclick="deleteFile('${f}')">🗑 Delete</button>
                        </div>
                    </div>
                `).join('');
            } else {
                document.getElementById('fileList').innerHTML = '<p>No files uploaded yet.</p>';
            }
        }
        
        async function runFileByName(filename) {
            const res = await fetch('/run-by-name', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: filename })
            });
            const data = await res.json();
            document.getElementById('outputArea').innerHTML = data.output || data.error;
        }
        
        async function runFile(filepath, ext) {
            const res = await fetch('/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filepath: filepath, extension: ext })
            });
            const data = await res.json();
            document.getElementById('outputArea').innerHTML = data.output || data.error;
        }
        
        async function deleteFile(filename) {
            const res = await fetch('/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: filename })
            });
            const data = await res.json();
            if(data.status === 'ok') loadFiles();
        }
        
        async function login() {
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            
            if(data.status === 'ok') {
                currentToken = data.token;
                localStorage.setItem('token', currentToken);
                document.getElementById('loginStatus').innerHTML = '<div class="status success">✅ Login successful!</div>';
                setTimeout(() => showTab('upload'), 1000);
            } else {
                document.getElementById('loginStatus').innerHTML = '<div class="status error">❌ ' + data.error + '</div>';
            }
        }
        
        async function signup() {
            const username = document.getElementById('signupUsername').value;
            const email = document.getElementById('signupEmail').value;
            const password = document.getElementById('signupPassword').value;
            
            const res = await fetch('/api/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });
            const data = await res.json();
            
            if(data.status === 'ok') {
                document.getElementById('signupStatus').innerHTML = '<div class="status success">✅ Account created! Please login.</div>';
                setTimeout(() => showTab('login'), 1500);
            } else {
                document.getElementById('signupStatus').innerHTML = '<div class="status error">❌ ' + data.error + '</div>';
            }
        }
        
        // Drag & drop support
        const dropArea = document.querySelector('.file-upload-area');
        dropArea.addEventListener('dragover', (e) => { e.preventDefault(); dropArea.style.borderColor = '#fff'; });
        dropArea.addEventListener('dragleave', () => { dropArea.style.borderColor = '#ff6600'; });
        dropArea.addEventListener('drop', (e) => {
            e.preventDefault();
            const file = e.dataTransfer.files[0];
            const input = document.getElementById('fileInput');
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
            input.dispatchEvent(new Event('change'));
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    ext = file.filename.split('.')[-1].lower()
    if ext not in ['py', 'js', 'zip']:
        return jsonify({'error': 'Only .py, .js, .zip allowed'}), 400
    
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{unique_id}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return jsonify({
        'status': 'ok',
        'filename': filename,
        'filepath': filepath,
        'extension': ext
    })

@app.route('/run', methods=['POST'])
def run_file():
    data = request.json
    filepath = data.get('filepath')
    ext = data.get('extension')
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        if ext == 'py':
            result = subprocess.run(['python3', filepath], capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
        
        elif ext == 'js':
            result = subprocess.run(['node', filepath], capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
        
        elif ext == 'zip':
            extract_dir = filepath.replace('.zip', '')
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            if os.path.exists(f"{extract_dir}/main.py"):
                result = subprocess.run(['python3', f"{extract_dir}/main.py"], capture_output=True, text=True, timeout=30)
                output = result.stdout + result.stderr
            elif os.path.exists(f"{extract_dir}/index.js"):
                result = subprocess.run(['node', f"{extract_dir}/index.js"], capture_output=True, text=True, timeout=30)
                output = result.stdout + result.stderr
            else:
                output = "ZIP extracted but no main.py or index.js found"
            
            shutil.rmtree(extract_dir, ignore_errors=True)
        else:
            return jsonify({'error': f'Unsupported extension: {ext}'}), 400
        
        return jsonify({'status': 'success', 'output': output})
    
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Execution timeout (30s)'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/run-by-name', methods=['POST'])
def run_by_name():
    data = request.json
    filename = data.get('filename')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    ext = filename.split('.')[-1].lower()
    return run_file_logic(filepath, ext)

def run_file_logic(filepath, ext):
    try:
        if ext == 'py':
            result = subprocess.run(['python3', filepath], capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
        elif ext == 'js':
            result = subprocess.run(['node', filepath], capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
        elif ext == 'zip':
            extract_dir = filepath.replace('.zip', '')
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            if os.path.exists(f"{extract_dir}/main.py"):
                result = subprocess.run(['python3', f"{extract_dir}/main.py"], capture_output=True, text=True, timeout=30)
                output = result.stdout + result.stderr
            elif os.path.exists(f"{extract_dir}/index.js"):
                result = subprocess.run(['node', f"{extract_dir}/index.js"], capture_output=True, text=True, timeout=30)
                output = result.stdout + result.stderr
            else:
                output = "ZIP extracted but no main.py or index.js found"
            shutil.rmtree(extract_dir, ignore_errors=True)
        else:
            return {'error': f'Unsupported extension: {ext}'}
        return {'status': 'success', 'output': output}
    except subprocess.TimeoutExpired:
        return {'error': 'Execution timeout (30s)'}
    except Exception as e:
        return {'error': str(e)}

@app.route('/files', methods=['GET'])
def list_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify({'files': files})

@app.route('/delete', methods=['POST'])
def delete_file():
    data = request.json
    filename = data.get('filename')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/login', methods=['POST'])
def api_login():
    from login import check_login
    data = request.json
    result = check_login(data.get('username'), data.get('password'))
    return jsonify(result)

@app.route('/api/signup', methods=['POST'])
def api_signup():
    from signup import create_account
    data = request.json
    result = create_account(data.get('username'), data.get('email'), data.get('password'))
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)