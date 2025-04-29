import requests
import time
import argparse

def send_heartbeat(controller_url, interval):
    print(f"[INFO] Target Controller: {controller_url}")
    print(f"[INFO] Heartbeat Interval: {interval} seconds")

    while True:
        try:
            response = requests.post(f"{controller_url}/heartbeat", json={}, timeout=5)
            print(f"[Heartbeat] {response.status_code}")
        except Exception as e:
            print("[Heartbeat Failed]", e)
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller', required=True, help="Controller URL (e.g., http://<IP>:5000)")
    parser.add_argument('--interval', type=int, default=60, help="Heartbeat interval in seconds (default: 60)")
    args = parser.parse_args()

    print("[INFO] Starting Orchestrator")
    send_heartbeat(args.controller, args.interval)
