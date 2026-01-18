import paho.mqtt.client as mqtt
import re
from datetime import datetime
from google.cloud import firestore

# --- CONFIGURATION ---
MQTT_BROKER = "localhost"
MQTT_TOPIC = "iot"
KEY_FILE = "fair-veld-481702-a1-d0ee1466211f.json"  # Ensure this file is in the same folder
DB_ID = "cpc357-assignment2"  # Your specific Firestore Database ID

# Initialize Firestore Client with your specific database ID
try:
    db = firestore.Client.from_service_account_json(KEY_FILE, database=DB_ID)
    print(f"Connected to Firestore Database: {DB_ID}")
except Exception as e:
    print(f"Failed to connect to Firestore: {e}")
    exit()

def parse_sensor_data(payload):
    """Extracts CO and Moisture values from: 'CO: 949 ppm | Moisture: 94%'"""
    try:
        numbers = re.findall(r'\d+', payload)
        if len(numbers) >= 2:
            return {
                "timestamp": datetime.now(),
                "co_ppm": int(numbers[0]),
                "moisture": int(numbers[1])
            }
    except Exception as e:
        print(f"Parsing error: {e}")
    return None

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    data = parse_sensor_data(payload)
    
    if data:
        try:
            # Save to 'sensor_readings' collection
            db.collection("sensor_readings").add(data)
            print(f" [DB STORED] CO: {data['co_ppm']} | Moisture: {data['moisture']}")
        except Exception as e:
            print(f"Firestore Storage Error: {e}")

# Setup MQTT Client
client = mqtt.Client()
client.on_message = on_message

print(f"Connecting to MQTT broker at {MQTT_BROKER}...")
client.connect(MQTT_BROKER, 1883, 60)
client.subscribe(MQTT_TOPIC)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("Subscriber stopped by user.")
