import subprocess
import os
import zipfile
import shutil
import json

def run_python_file(filepath):
    result = subprocess.run(['python3', filepath], capture_output=True, text=True, timeout=30)
    return result.stdout + result.stderr

def run_js_file(filepath):
    result = subprocess.run(['node', filepath], capture_output=True, text=True, timeout=30)
    return result.stdout + result.stderr

def run_zip_file(filepath):
    extract_dir = filepath.replace('.zip', '')
    with zipfile.ZipFile(filepath, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    output = ""
    if os.path.exists(f"{extract_dir}/main.py"):
        result = subprocess.run(['python3', f"{extract_dir}/main.py"], capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
    elif os.path.exists(f"{extract_dir}/index.js"):
        result = subprocess.run(['node', f"{extract_dir}/index.js"], capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
    else:
        output = "ZIP extracted but no main.py or index.js found"
    
    shutil.rmtree(extract_dir, ignore_errors=True)
    return output

def run_file(filepath, extension):
    if extension == 'py':
        return run_python_file(filepath)
    elif extension == 'js':
        return run_js_file(filepath)
    elif extension == 'zip':
        return run_zip_file(filepath)
    else:
        return f"Unsupported extension: {extension}"