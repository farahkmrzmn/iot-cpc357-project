#include <WiFi.h>
#include <PubSubClient.h>

// ---------- WiFi ----------
const char* WIFI_SSID = "Farah";
const char* WIFI_PASSWORD = "12345678";

// ---------- MQTT ----------
const char* MQTT_SERVER = "34.57.126.65";
const char* MQTT_TOPIC  = "iot";
const int   MQTT_PORT   = 1883;

// ---------- Maker Feather ESP32 ADC Pins ----------
#define MQ_PIN A0        // Smoke sensor
#define MOISTURE_PIN A3  // Soil moisture sensor

// ---------- Moisture Calibration ----------
#define DRY_VALUE 3500
#define WET_VALUE 1200

// ---------- Objects ----------
WiFiClient espClient;
PubSubClient client(espClient);
char buffer[128];

// ---------- WiFi ----------
void setup_wifi() {
  Serial.print("Connecting to ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

// ---------- MQTT ----------
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("FeatherESP32-Sensors")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying...");
      delay(5000);
    }
  }
}

// ---------- Setup ----------
void setup() {
  Serial.begin(115200);

  pinMode(MQ_PIN, INPUT);
  pinMode(MOISTURE_PIN, INPUT);

  setup_wifi();
  client.setServer(MQTT_SERVER, MQTT_PORT);
}

// ---------- Loop ----------
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  delay(5000);

  // ---------- Read sensors ----------
  int smokeRaw = analogRead(MQ_PIN);
  int moistureRaw = analogRead(MOISTURE_PIN);

  // ---------- Convert values ----------
  int smokePPM = map(smokeRaw, 200, 4095, 0, 1000);
  smokePPM = constrain(smokePPM, 0, 1000);

  int moisturePercent = map(moistureRaw, DRY_VALUE, WET_VALUE, 0, 100);
  moisturePercent = constrain(moisturePercent, 0, 100);

  // ---------- Publish ----------
  snprintf(
    buffer,
    sizeof(buffer),
    "CO: %d ppm | Moisture: %d%%",
    smokePPM,
    moisturePercent
  );

  client.publish(MQTT_TOPIC, buffer);
  Serial.println(buffer);
}
