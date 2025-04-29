import requests
import time
import argparse

ORCHESTRATOR_NAME = "Unnamed Orchestrator"  # Will be overridden dynamically

parser = argparse.ArgumentParser()
parser.add_argument('--controller', required=True, help='Controller URL')
parser.add_argument('--interval', type=int, default=60, help='Heartbeat interval in seconds')
args = parser.parse_args()

ORCHESTRATOR_ID = f"orch_{int(time.time())}"
CONTROLLER_URL = args.controller
INTERVAL = args.interval

def send_heartbeat():
    try:
        payload = {'id': ORCHESTRATOR_ID, 'name': ORCHESTRATOR_NAME}
        res = requests.post(f"{CONTROLLER_URL}/heartbeat", json=payload, timeout=5)
        print(f"[Heartbeat] {res.status_code}")
    except Exception as e:
        print("[Heartbeat Failed]", e)

if __name__ == "__main__":
    print(f"[INFO] Starting Orchestrator {ORCHESTRATOR_ID}")
    print(f"[INFO] Target Controller: {CONTROLLER_URL}")
    print(f"[INFO] Heartbeat Interval: {INTERVAL} seconds")
    while True:
        send_heartbeat()
        time.sleep(INTERVAL)
