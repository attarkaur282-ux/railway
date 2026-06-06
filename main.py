from flask import Flask, request, jsonify, render_template_string
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
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================== HTML TEMPLATE ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>Bike File Runner | Railway</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0f1e 0%, #0a1a2a 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        h1 {
            text-align: center;
            margin: 20px 0;
            font-size: 2.5rem;
            background: linear-gradient(135deg, #ffaa44, #ff6600);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .subtitle {
            text-align: center;
            margin-bottom: 30px;
            opacity: 0.8;
        }

        /* Tabs */
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            justify-content: center;
        }

        .tab {
            padding: 12px 24px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
        }

        .tab:hover {
            background: rgba(255, 102, 0, 0.5);
        }

        .tab.active {
            background: #ff6600;
            box-shadow: 0 0 15px rgba(255, 102, 0, 0.5);
        }

        /* Cards */
        .card {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            margin: 20px 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .card h3 {
            margin-bottom: 15px;
            color: #ffaa44;
        }

        /* Upload Area */
        .upload-area {
            border: 2px dashed #ff6600;
            border-radius: 20px;
            padding: 50px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }

        .upload-area:hover {
            background: rgba(255, 102, 0, 0.1);
            border-color: #ffaa44;
        }

        /* File List */
        .file-item {
            background: rgba(0, 0, 0, 0.5);
            padding: 12px 15px;
            margin: 8px 0;
            border-radius: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }

        .file-name {
            font-family: monospace;
            word-break: break-all;
            flex: 1;
        }

        .btn {
            background: #ff6600;
            border: none;
            padding: 8px 20px;
            border-radius: 25px;
            color: white;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.2s;
        }

        .btn:hover {
            transform: scale(1.02);
            background: #ff8833;
        }

        .btn-danger {
            background: #dc2626;
        }

        .btn-danger:hover {
            background: #ef4444;
        }

        /* Inputs */
        input, textarea {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border-radius: 10px;
            border: none;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-family: inherit;
        }

        input::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }

        /* Output */
        .output-area {
            background: #0a0a0a;
            border-radius: 12px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #333;
        }

        /* Status Messages */
        .status {
            padding: 10px;
            border-radius: 10px;
            margin: 10px 0;
        }

        .success {
            background: rgba(0, 170, 0, 0.3);
            border: 1px solid #00aa00;
        }

        .error {
            background: rgba(170, 0, 0, 0.3);
            border: 1px solid #ff0000;
        }

        .loading {
            background: rgba(255, 102, 0, 0.3);
            border: 1px solid #ff6600;
        }

        .hidden {
            display: none;
        }

        footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            opacity: 0.6;
            font-size: 12px;
        }

        @media (max-width: 600px) {
            h1 { font-size: 1.8rem; }
            .tab { padding: 8px 16px; font-size: 14px; }
            .file-item { flex-direction: column; align-items: stretch; }
            .btn { width: 100%; text-align: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏍️ BIKE FILE RUNNER</h1>
        <div class="subtitle">Upload | Run | Execute .py .js .zip files</div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('upload')">📤 UPLOAD</div>
            <div class="tab" onclick="showTab('files')">📁 MY FILES</div>
            <div class="tab" onclick="showTab('login')">🔐 LOGIN</div>
            <div class="tab" onclick="showTab('signup')">📝 SIGN UP</div>
        </div>

        <!-- Upload Tab -->
        <div id="uploadTab" class="tab-content">
            <div class="card">
                <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                    📂 Click to Upload or Drag & Drop<br>
                    <small>(.py, .js, .zip | Max 50MB)</small>
                </div>
                <input type="file" id="fileInput" style="display:none" accept=".py,.js,.zip">
                <div id="uploadStatus"></div>
            </div>
        </div>

        <!-- Files Tab -->
        <div id="filesTab" class="tab-content hidden">
            <div class="card">
                <h3>📋 Uploaded Files</h3>
                <div id="fileList">
                    <div class="status loading">Loading files...</div>
                </div>
            </div>
        </div>

        <!-- Login Tab -->
        <div id="loginTab" class="tab-content hidden">
            <div class="card">
                <h3>🔐 Login to Account</h3>
                <input type="text" id="loginUsername" placeholder="Username">
                <input type="password" id="loginPassword" placeholder="Password">
                <button class="btn" onclick="login()">Login</button>
                <div id="loginStatus"></div>
            </div>
        </div>

        <!-- Signup Tab -->
        <div id="signupTab" class="tab-content hidden">
            <div class="card">
                <h3>📝 Create New Account</h3>
                <input type="text" id="signupUsername" placeholder="Username">
                <input type="email" id="signupEmail" placeholder="Email">
                <input type="password" id="signupPassword" placeholder="Password (min 6 chars)">
                <button class="btn" onclick="signup()">Sign Up</button>
                <div id="signupStatus"></div>
            </div>
        </div>

        <!-- Output Section -->
        <div class="card">
            <h3>📟 OUTPUT</h3>
            <div id="outputArea" class="output-area">⚡ Ready to run files... Click RUN on any file.</div>
        </div>
    </div>

    <footer>
        Bike File Runner v1.0 | Hosted on Railway
    </footer>

    <script>
        let currentToken = localStorage.getItem('token') || null;

        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            document.getElementById('uploadTab').classList.add('hidden');
            document.getElementById('filesTab').classList.add('hidden');
            document.getElementById('loginTab').classList.add('hidden');
            document.getElementById('signupTab').classList.add('hidden');
            
            if(tabName === 'upload') document.getElementById('uploadTab').classList.remove('hidden');
            if(tabName === 'files') {
                document.getElementById('filesTab').classList.remove('hidden');
                loadFiles();
            }
            if(tabName === 'login') document.getElementById('loginTab').classList.remove('hidden');
            if(tabName === 'signup') document.getElementById('signupTab').classList.remove('hidden');
        }

        // File upload
        document.getElementById('fileInput').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if(!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById('uploadStatus').innerHTML = '<div class="status loading">⏳ Uploading...</div>';
            
            try {
                const res = await fetch('/upload', { method: 'POST', body: formData });
                const data = await res.json();
                
                if(data.status === 'ok') {
                    document.getElementById('uploadStatus').innerHTML = '<div class="status success">✅ Uploaded: ' + data.filename + '</div>';
                    loadFiles();
                    runFile(data.filepath, data.extension);
                } else {
                    document.getElementById('uploadStatus').innerHTML = '<div class="status error">❌ Error: ' + data.error + '</div>';
                }
            } catch(err) {
                document.getElementById('uploadStatus').innerHTML = '<div class="status error">❌ Upload failed</div>';
            }
        });

        // Load files list
        async function loadFiles() {
            try {
                const res = await fetch('/files');
                const data = await res.json();
                
                if(data.files && data.files.length > 0) {
                    document.getElementById('fileList').innerHTML = data.files.map(f => `
                        <div class="file-item">
                            <span class="file-name">📄 ${f}</span>
                            <div style="display: flex; gap: 8px;">
                                <button class="btn" onclick="runFileByName('${f}')">▶ RUN</button>
                                <button class="btn btn-danger" onclick="deleteFile('${f}')">🗑 DELETE</button>
                            </div>
                        </div>
                    `).join('');
                } else {
                    document.getElementById('fileList').innerHTML = '<p>📭 No files uploaded yet. Go to Upload tab.</p>';
                }
            } catch(err) {
                document.getElementById('fileList').innerHTML = '<div class="status error">Error loading files</div>';
            }
        }

        async function runFileByName(filename) {
            document.getElementById('outputArea').innerHTML = '⏳ Running ' + filename + '...';
            try {
                const res = await fetch('/run-by-name', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: filename })
                });
                const data = await res.json();
                document.getElementById('outputArea').innerHTML = data.output || data.error || 'No output';
            } catch(err) {
                document.getElementById('outputArea').innerHTML = '❌ Error running file';
            }
        }

        async function runFile(filepath, ext) {
            try {
                const res = await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filepath: filepath, extension: ext })
                });
                const data = await res.json();
                document.getElementById('outputArea').innerHTML = data.output || data.error;
            } catch(err) {
                document.getElementById('outputArea').innerHTML = '❌ Execution failed';
            }
        }

        async function deleteFile(filename) {
            try {
                const res = await fetch('/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: filename })
                });
                const data = await res.json();
                if(data.status === 'ok') {
                    loadFiles();
                }
            } catch(err) {
                alert('Delete failed');
            }
        }

        async function login() {
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            
            if(!username || !password) {
                document.getElementById('loginStatus').innerHTML = '<div class="status error">Please fill all fields</div>';
                return;
            }
            
            document.getElementById('loginStatus').innerHTML = '<div class="status loading">Logging in...</div>';
            
            try {
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
            } catch(err) {
                document.getElementById('loginStatus').innerHTML = '<div class="status error">❌ Login failed</div>';
            }
        }

        async function signup() {
            const username = document.getElementById('signupUsername').value;
            const email = document.getElementById('signupEmail').value;
            const password = document.getElementById('signupPassword').value;
            
            if(!username || !email || !password) {
                document.getElementById('signupStatus').innerHTML = '<div class="status error">Please fill all fields</div>';
                return;
            }
            
            if(password.length < 6) {
                document.getElementById('signupStatus').innerHTML = '<div class="status error">Password must be at least 6 characters</div>';
                return;
            }
            
            document.getElementById('signupStatus').innerHTML = '<div class="status loading">Creating account...</div>';
            
            try {
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
            } catch(err) {
                document.getElementById('signupStatus').innerHTML = '<div class="status error">❌ Signup failed</div>';
            }
        }

        // Drag and Drop
        const dropArea = document.querySelector('.upload-area');
        if(dropArea) {
            dropArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropArea.style.background = 'rgba(255,102,0,0.2)';
            });
            dropArea.addEventListener('dragleave', () => {
                dropArea.style.background = 'transparent';
            });
            dropArea.addEventListener('drop', (e) => {
                e.preventDefault();
                dropArea.style.background = 'transparent';
                const file = e.dataTransfer.files[0];
                const input = document.getElementById('fileInput');
                const dt = new DataTransfer();
                dt.items.add(file);
                input.files = dt.files;
                input.dispatchEvent(new Event('change'));
            });
        }
    </script>
</body>
</html>
'''

# ==================== ROUTES ====================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/run', methods=['POST'])
def run_file():
    try:
        data = request.json
        filepath = data.get('filepath')
        ext = data.get('extension')
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
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
    try:
        data = request.json
        filename = data.get('filename')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        ext = filename.split('.')[-1].lower()
        
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
        
        return jsonify({'output': output})
    
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Execution timeout (30s)'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/files', methods=['GET'])
def list_files():
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete', methods=['POST'])
def delete_file():
    try:
        data = request.json
        filename = data.get('filename')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'status': 'ok'})
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        from login import check_login
        data = request.json
        result = check_login(data.get('username'), data.get('password'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/signup', methods=['POST'])
def api_signup():
    try:
        from signup import create_account
        data = request.json
        result = create_account(data.get('username'), data.get('email'), data.get('password'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# ==================== MAIN ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
