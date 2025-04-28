from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
import os
import subprocess
import threading
import datetime
import shutil
import zipfile

app = Flask(__name__)
app.secret_key = 'supersecret'

# Hardcoded Dummy User Credentials
DUMMY_USERNAME = "admin"
DUMMY_PASSWORD = "password123"

# Dictionary to store orchestrator heartbeats
orchestrators = {}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == DUMMY_USERNAME and password == DUMMY_PASSWORD:
            session['user'] = 'authenticated'
            return redirect(url_for('home'))
        else:
            return "Login failed. Invalid credentials."
    return render_template('index.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return '''
    <h1>I'm Alive - Controller</h1>
    <a href="/dashboard" class="btn btn-primary">Go to Dashboard</a>
    <form action="/generate" method="post" style="margin-top: 20px;">
        <button type="submit">Generate & Download Orchestrator</button>
    </form>
    '''

@app.route('/generate', methods=['POST'])
def generate():
    if 'user' not in session:
        return redirect(url_for('login'))

    create_orchestrator_executable()

    file_path = './orchestrator_dist/orchestrator_build.zip'
    return send_file(file_path, as_attachment=True)

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    orch_id = data.get('id')
    ip = request.remote_addr
    orchestrators[orch_id] = (ip, datetime.datetime.now())
    print(f"[Heartbeat] Received from {orch_id} @ {ip} at {datetime.datetime.now()}")
    return {"status": "received"}

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/heartbeat_status')
def heartbeat_status():
    if 'user' not in session:
        return jsonify({})
    
    data = []
    now = datetime.datetime.now()

    for orch_id, (ip, last_seen) in orchestrators.items():
        status = "Online" if (now - last_seen).seconds <= 120 else "Offline"
        data.append({
            "id": orch_id,
            "ip": ip,
            "last_seen": last_seen.strftime('%Y-%m-%d %H:%M:%S'),
            "status": status
        })
    return jsonify(data)

def monitor_heartbeats():
    while True:
        now = datetime.datetime.now()
        for orch, (ip, last_seen) in list(orchestrators.items()):
            if (now - last_seen).seconds > 180:
                print(f"[WARNING] Lost heartbeat from {orch} @ {ip}")
        threading.Event().wait(60)

def create_orchestrator_executable():
    os.makedirs("./orchestrator_dist", exist_ok=True)

    shutil.copyfile('./orchestrator-template/orchestrator.py', './orchestrator-template/orchestrator_build.py')

    subprocess.run([
        "pyinstaller",
        "--onefile",
        "--distpath", "./orchestrator_dist",
        "--clean",
        "--name", "orchestrator_build",
        "--noconsole",
        "./orchestrator-template/orchestrator_build.py"
    ], env={
        **os.environ,
        "WINEARCH": "win32",
        "WINEPREFIX": "/root/.wine"
    })

    # Always package the .exe file
    build_path = "./orchestrator_dist/orchestrator_build.exe"
    zip_path = "./orchestrator_dist/orchestrator_build.zip"

    if not os.path.exists(build_path):
        raise FileNotFoundError("Windows executable not found!")

    # Create zip
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(build_path, arcname="orchestrator_build.exe")

    print(f"[INFO] Successfully created zipped orchestrator at {zip_path}")


if __name__ == '__main__':
    threading.Thread(target=monitor_heartbeats, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
