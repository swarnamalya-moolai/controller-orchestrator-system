import requests
import time

ORCHESTRATOR_ID = "orch_" + str(int(time.time()))
CONTROLLER_URL = "http://your_controller_ip:5000/heartbeat"

def send_heartbeat():
    try:
        payload = {'id': ORCHESTRATOR_ID}
        res = requests.post(CONTROLLER_URL, json=payload, timeout=5)
        print(f"[Heartbeat] {res.status_code}")
    except Exception as e:
        print("[Heartbeat Failed]", e)

if __name__ == "__main__":
    while True:
        send_heartbeat()
        time.sleep(60)
