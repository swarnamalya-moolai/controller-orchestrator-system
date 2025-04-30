import requests
import time
import argparse

# This line will be injected dynamically during build
ORCHESTRATOR_NAME = "Unnamed Orchestrator"

def parse_args():
    parser = argparse.ArgumentParser(description="Orchestrator Heartbeat Sender")
    parser.add_argument('--controller', required=True, help='Controller heartbeat URL')
    parser.add_argument('--interval', type=int, default=60, help='Heartbeat interval in seconds')
    return parser.parse_args()

def send_heartbeat(controller_url):
    try:
        payload = {
            "id": f"orch_{int(time.time())}",
            "name": ORCHESTRATOR_NAME
        }
        headers = {'Content-Type': 'application/json'}
        res = requests.post(controller_url, json=payload, headers=headers, timeout=5)
        print(f"[Heartbeat] {res.status_code}")
    except Exception as e:
        print("[Heartbeat Failed]", e)

def main():
    args = parse_args()
    controller_url = args.controller
    interval = args.interval

    print(f"[INFO] Orchestrator: {ORCHESTRATOR_NAME}")
    print(f"[INFO] Controller: {controller_url}")
    print(f"[INFO] Interval: {interval}s")

    while True:
        send_heartbeat(controller_url)
        time.sleep(interval)

if __name__ == '__main__':
    main()
