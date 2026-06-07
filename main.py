from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bike File Runner</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                background: linear-gradient(135deg, #0a0f1e, #0a1a2a);
                font-family: Arial, sans-serif;
                color: white;
                text-align: center;
                padding: 50px;
            }
            h1 { color: #ff6600; font-size: 3rem; }
            .status {
                background: #00aa0055;
                border: 1px solid #00ff00;
                border-radius: 10px;
                padding: 20px;
                display: inline-block;
            }
            button {
                background: #ff6600;
                border: none;
                padding: 15px 30px;
                border-radius: 30px;
                color: white;
                font-size: 1rem;
                cursor: pointer;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>🏍️ BIKE FILE RUNNER</h1>
        <div class="status">
            ✅ SERVER IS RUNNING SUCCESSFULLY ✅
        </div>
        <p>Railway deployment is working fine.</p>
        <button onclick="alert('Working!')">Click to Test</button>
        <p><small>Full file runner system is being added...</small></p>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
