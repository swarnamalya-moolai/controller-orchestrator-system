import requests
import time
import argparse

# ORCHESTRATOR_NAME will be injected here by app.py

def parse_args():
    parser = argparse.ArgumentParser(description="Orchestrator Heartbeat Sender")
    parser.add_argument('--controller', required=True, help='Controller URL')
    parser.add_argument('--interval', type=int, default=60)
    return parser.parse_args()

def send_heartbeat(controller_url, orchestrator_id):
    try:
        payload = {'id': orchestrator_id, 'name': ORCHESTRATOR_NAME}
        headers = {'Content-Type': 'application/json'}
        res = requests.post(controller_url + '/heartbeat', json=payload, headers=headers, timeout=5)
        print(f"[Heartbeat] {res.status_code}")
    except Exception as e:
        print("[Heartbeat Failed]", e)

if __name__ == "__main__":
    args = parse_args()
    orchestrator_id = "orch_" + str(int(time.time()))
    print(f"[INFO] Starting Orchestrator {orchestrator_id} ({ORCHESTRATOR_NAME})")
    while True:
        send_heartbeat(args.controller, orchestrator_id)
        time.sleep(args.interval)
