from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
import os
import subprocess
import threading
import datetime
import shutil
import zipfile

app = Flask(__name__)
app.secret_key = 'supersecret'

DUMMY_USERNAME = "admin"
DUMMY_PASSWORD = "password123"

orchestrators = {}
orchestrator_names = {}  # Maps IP to orchestrator name

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

@app.route('/home', methods=['GET'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/generate', methods=['POST'])
def generate():
    if 'user' not in session:
        return redirect(url_for('login'))

    name = request.form.get('name')
    if not name:
        return "Name is required.", 400

    session['orchestrator_name'] = name

    create_orchestrator_executable(name)

    file_path = './orchestrator_dist/orchestrator_build.zip'
    return send_file(file_path, as_attachment=True)

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    orch_id = data.get('id')
    orch_name = data.get('name')
    ip = request.remote_addr
    orchestrators[ip] = (orch_id, datetime.datetime.utcnow())
    orchestrator_names[ip] = orch_name
    print(f"[Heartbeat] Received from {orch_id} ({orch_name}) @ {ip} at {datetime.datetime.utcnow()}")
    return {"status": "received"}

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/heartbeat_status')
def heartbeat_status():
    if 'user' not in session:
        return jsonify([])

    now = datetime.datetime.utcnow()
    data = []
    for ip, (orch_id, last_seen) in orchestrators.items():
        status = "Online" if (now - last_seen).total_seconds() <= 30 else "Offline"
        name = orchestrator_names.get(ip, orch_id)
        data.append({
            "name": name,
            "ip": ip,
            "last_seen": "",
            "status": status
        })
    return jsonify(data)

def monitor_heartbeats():
    while True:
        now = datetime.datetime.utcnow()
        for ip, (orch_id, last_seen) in list(orchestrators.items()):
            if (now - last_seen).total_seconds() > 60:
                print(f"[WARNING] Lost heartbeat from {orch_id} @ {ip}")
        threading.Event().wait(15)

def create_orchestrator_executable(name):
    os.makedirs("./orchestrator_dist", exist_ok=True)

    # Copy base file and inject name at the top
    shutil.copyfile('./orchestrator-template/orchestrator.py', './orchestrator-template/orchestrator_build.py')
    with open('./orchestrator-template/orchestrator_build.py', 'r+') as f:
        content = f.read()
        f.seek(0)
        f.write(f'ORCHESTRATOR_NAME = "{name}"\n' + content)

    subprocess.run([
        "pyinstaller",
        "--onefile",
        "--distpath", "./orchestrator_dist",
        "--clean",
        "--name", "orchestrator_build",
        "--noconsole",
        "./orchestrator-template/orchestrator_build.py"
    ])

    build_filename = "orchestrator_build"
    build_path = os.path.join("./orchestrator_dist", build_filename)
    zip_path = "./orchestrator_dist/orchestrator_build.zip"

    if not os.path.exists(build_path):
        raise FileNotFoundError(f"{build_filename} not found!")

    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(build_path, arcname=build_filename)

    print(f"[INFO] Successfully created zipped orchestrator at {zip_path}")

if __name__ == '__main__':
    threading.Thread(target=monitor_heartbeats, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)