import json
import requests
import argparse

from datetime import datetime
from pathlib import Path
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# PROJECT_ID = "testpelm-db8d6"
# PARAMETER_KEY = "testParam"

BACKUP_DIR = Path("backups")  # cartella dove salvare i backup

# -- command line arguments params
parser = argparse.ArgumentParser("firebase-key-updater.py")
parser.add_argument("env", help="A string representing the environment (e.g.: test, prod). ")
parser.add_argument("firebaseProjectId", help="A string representing Firebase project ID (e.g.: abcde-123ef). ")
parser.add_argument("remoteConfigKey", help="A string representing the Firebase Property to be updated (e.g.: iosSdkWorkaround). ")

args = parser.parse_args()

env = args.env
print(f"[INFO] env: {env}")

firebaseProjectId = args.firebaseProjectId
print(f"[INFO] firebaseProjectId: {firebaseProjectId}")

remoteConfigKey = args.remoteConfigKey
print(f"[INFO] remoteConfigKey: {remoteConfigKey}")

# -- Firebase connection params
RC_URL = f"https://firebaseremoteconfig.googleapis.com/v1/projects/{firebaseProjectId}/remoteConfig"
CREDENTIALS_FILE = f"env/{env}-credentials.json"
print(f"[INFO] CREDENTIALS_FILE: {CREDENTIALS_FILE}")
SCOPES = ["https://www.googleapis.com/auth/firebase.remoteconfig"]

def backup_remote_config():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    token = get_access_token()
    resp = requests.get(
        RC_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept-Encoding": "gzip",
        },
        timeout=30,
    )
    if resp.status_code == 200:
        template = resp.json()
        etag = resp.headers.get("ETag", "")
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = BACKUP_DIR / f"{firebaseProjectId}-{env}-remoteconfigBK-{ts}.json"
        latest_path = BACKUP_DIR / f"{firebaseProjectId}-{env}-remoteconfigBK-latest.json"
        # Salva payload e metadati ETag
        payload = {
            "_metadata": {
                "project_id": firebaseProjectId,
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
                "etag": etag,
            },
            "template": template,
        }
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"Backup Remote Config salvato: {backup_path}")
        return template, etag
    elif resp.status_code == 404:
        print("Nessun template trovato (404) — il progetto potrebbe non avere una versione pubblicata.")
        return {"parameters": {}, "conditions": []}, None
    else:
        raise RuntimeError(f"GET template failed: {resp.status_code} {resp.text}")
    
def get_access_token():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    creds.refresh(Request())
    return creds.token

def update_remote_config_once():
    token = get_access_token()

    # 1) Backup e get del template corrente
    template, etag = backup_remote_config()
    
    # 2) Aggiorna/crea il parametro con timestamp
    now = datetime.now().strftime("last update %d.%m.%Y %H:%M")
    template.setdefault("parameters", {})
    template["parameters"][remoteConfigKey] = {
        "defaultValue": {"value": now},
        "valueType": "STRING"
    }

    # 3) PUT con If-Match (usa ETag se presente, altrimenti '*' per creare)
    put_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; UTF-8",
        "If-Match": etag if etag else "*"
    }
    put_resp = requests.put(RC_URL, headers=put_headers, data=json.dumps(template))
    if put_resp.status_code == 200:
        print(f"Aggiornato {remoteConfigKey} = {now}")
    else:
        raise RuntimeError(f"[ERROR] PUT failed: {put_resp.status_code} {put_resp.text}")

if __name__ == "__main__":
    try:
        update_remote_config_once()
    except Exception as e:
        print(f"Errore: {e}")