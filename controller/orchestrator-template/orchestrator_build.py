import requests
import time
import argparse
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Orchestrator Heartbeat Sender")
    parser.add_argument('--controller', required=True, help='Controller heartbeat URL (e.g., http://localhost:5000/heartbeat)')
    parser.add_argument('--interval', type=int, default=60, help='Heartbeat interval in seconds (default 60s)')
    args = parser.parse_args()
    return args

def send_heartbeat(controller_url, orchestrator_id):
    try:
        payload = {'id': orchestrator_id}
        headers = {'Content-Type': 'application/json'}
        res = requests.post(controller_url, json=payload, headers=headers, timeout=5)
        print(f"[Heartbeat] {res.status_code}")
    except Exception as e:
        print("[Heartbeat Failed]", e)

if __name__ == "__main__":
    args = parse_args()

    ORCHESTRATOR_ID = "orch_" + str(int(time.time()))
    CONTROLLER_URL = args.controller
    INTERVAL = args.interval

    print(f"[INFO] Starting Orchestrator {ORCHESTRATOR_ID}")
    print(f"[INFO] Target Controller: {CONTROLLER_URL}")
    print(f"[INFO] Heartbeat Interval: {INTERVAL} seconds")

    while True:
        send_heartbeat(CONTROLLER_URL, ORCHESTRATOR_ID)
        time.sleep(INTERVAL)

