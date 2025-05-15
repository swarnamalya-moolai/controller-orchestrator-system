ORCHESTRATOR_NAME = "Test"
import requests
import time
import argparse

# This line will be overwritten dynamically by controller during build
ORCHESTRATOR_NAME = "Unnamed Orchestrator"

def parse_args():
    parser = argparse.ArgumentParser(description="Orchestrator Heartbeat Sender")
    parser.add_argument('--controller', required=True, help='Controller base URL (e.g. http://<ip>:5000)')
    parser.add_argument('--interval', type=int, default=60, help='Heartbeat interval in seconds')
    return parser.parse_args()

def send_heartbeat(controller_url, orchestrator_id):
    try:
        payload = {
            "id": orchestrator_id,
            "name": ORCHESTRATOR_NAME
        }
        headers = {'Content-Type': 'application/json'}
        res = requests.post(f"{controller_url}/heartbeat", json=payload, headers=headers, timeout=5)
        print(f"[Heartbeat] {res.status_code}")
    except Exception as e:
        print("[Heartbeat Failed]", e)

def main():
    args = parse_args()
    orchestrator_id = f"orch_{int(time.time())}"

    print(f"[INFO] Orchestrator: {ORCHESTRATOR_NAME}")
    print(f"[INFO] Controller: {args.controller}")
    print(f"[INFO] Interval: {args.interval}s")

    while True:
        send_heartbeat(args.controller, orchestrator_id)
        time.sleep(args.interval)

if __name__ == '__main__':
    main()
