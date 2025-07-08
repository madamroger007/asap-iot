# app/src/services/notification_service.py
import os
import requests
from app.src.repositories.nohp_repositories import get_all_nomor_hp
from dotenv import load_dotenv
load_dotenv()

def notify_sensor_data_Service(msg, app=None):
    wa_server_url = os.getenv('WA_SERVER_URL')
    session_id = os.getenv('WA_SESSION_ID')
    print("env:", wa_server_url, session_id)
    if not wa_server_url:
        print("❌ WA_SERVER_URL tidak ditemukan di .env")
        return
    if not session_id:
        print("❌ WA_SESSION_ID tidak ditemukan di .env")
        return

    with app:  # ✅ gunakan langsung AppContext
        try:
            numbers = get_all_nomor_hp()

            if not numbers:
                print("⚠️ Tidak ada nomor WA yang ditemukan di database.")
                return

            for record in numbers:
                phone_number = record.nomor_hp if hasattr(record, 'nomor_hp') else record['nomor_hp']

                payload = {
                    "number": phone_number,
                    "message": msg,
                    "sessionId": session_id
                }
                headers = {
                    "Content-Type": "application/json"
                }

                try:
                    response = requests.post(wa_server_url, json=payload, headers=headers)
                    print(f"📤 Mengirim pesan ke {phone_number}...")
                    print(f"Payload: {payload}")
                    response.raise_for_status()
                    res_json = response.json()

                    if res_json.get("status") == "success":
                        print(f"✅ Pesan berhasil dikirim ke {phone_number}")
                    else:
                        print(f"❌ Gagal kirim ke {phone_number}: {res_json}")

                except requests.exceptions.RequestException as err:
                    print(f"❌ Error koneksi ke {phone_number}: {err}")

        except Exception as e:
            print(f"❌ Error saat mengambil nomor dari database: {e}")
