# controller/app.py
from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import subprocess
import threading
import datetime
import shutil

app = Flask(__name__)
app.secret_key = 'supersecret'

orchestrators = {}

def validate_token(token):
    return token == "dummy_valid_token"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        token = request.form['token']
        if validate_token(token):
            session['user'] = 'authenticated'
            return redirect(url_for('home'))
        else:
            return "Login failed."
    return render_template('index.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return '''
    <h1>I'm Alive - Controller</h1>
    <form action="/generate" method="post">
        <button type="submit">Generate & Download Orchestrator</button>
    </form>
    '''

@app.route('/generate', methods=['POST'])
def generate():
    if 'user' not in session:
        return redirect(url_for('login'))

    create_orchestrator_executable()

    file_path = './orchestrator_dist/orchestrator_build'
    if os.name == 'nt':  # If Windows, add .exe
        file_path += '.exe'

    return send_file(file_path, as_attachment=True)

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    orch_id = data.get('id')
    ip = request.remote_addr
    orchestrators[orch_id] = (ip, datetime.datetime.now())
    return {"status": "received"}

def monitor_heartbeats():
    while True:
        now = datetime.datetime.now()
        for orch, (ip, last_seen) in list(orchestrators.items()):
            if (now - last_seen).seconds > 180:
                print(f"[WARNING] Lost heartbeat from {orch} @ {ip}")
        threading.Event().wait(60)

def create_orchestrator_executable():
    shutil.copyfile('./orchestrator_template/orchestrator.py', './orchestrator_template/orchestrator_build.py')
    subprocess.run([
        "pyinstaller",
        "--onefile",
        "--distpath", "./orchestrator_dist",
        "./orchestrator_template/orchestrator_build.py"
    ])

if __name__ == '__main__':
    threading.Thread(target=monitor_heartbeats, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
