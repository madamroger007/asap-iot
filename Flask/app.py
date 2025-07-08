from app import create_app, socketio
import threading
from app.src.services.mqtt_service import run_mqtt_service

app = create_app()

def start_background_services():
     threading.Thread(target=lambda: run_mqtt_service(app.app_context()), daemon=True).start()

if __name__ == "__main__":
    start_background_services()
    socketio.run(app, debug=False, host="0.0.0.0", port=5010, use_reloader=False, allow_unsafe_werkzeug=True)
