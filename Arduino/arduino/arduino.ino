#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>     // Untuk TLS
#include <PubSubClient.h>
#include <DHT.h>

// ==================== Konfigurasi WiFi ====================
const char* ssid = "Konsol";
const char* password = "20011116";

// ==================== Konfigurasi MQTT (HiveMQ Cloud) ====================
const char* mqtt_server = "6266344797024ee38899455336cb7979.s1.eu.hivemq.cloud";
const int mqtt_port = 8883; // TLS port
const char* mqtt_user = "hivemq.webclient.1751985342943";
const char* mqtt_pass = "g73P#5MkQeuE.F4@$Wyn";

// ==================== Inisialisasi MQTT Client ====================
WiFiClientSecure espClient;
PubSubClient client(espClient);

// ==================== Konfigurasi Sensor dan Aktuator ====================
#define DHTPIN D2           // GPIO4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

#define FLAME_PIN D5        // DO dari sensor api
#define BUZZER_PIN D1       // GPIO5
#define MQ2_PIN A0          // AO dari sensor asap/gas MQ2 (analog)

const float TEMP_THRESHOLD = 45.0;  // Suhu batas kebakaran
const int SMOKE_THRESHOLD = 300;   // Threshold asap (nilai ADC A0)

bool alarmActive = false;

// ==================== Koneksi WiFi ====================
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

// ==================== Reconnect MQTT jika terputus ====================
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("NodeMCUClient", mqtt_user, mqtt_pass)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

// ==================== Publish ke Topik Sensor ====================
void publishSensorData(float temperature, int smokeLevel, int flameValue, bool fireDetected) {
  client.publish("kebakaran/suhu", String(temperature, 1).c_str());
  client.publish("kebakaran/asap", String(smokeLevel).c_str());        // Kirim nilai ADC
  client.publish("kebakaran/api", flameValue == 0 ? "1" : "0");         // 1 = api terdeteksi
  client.publish("kebakaran/status", fireDetected ? "1" : "0");  // Status kebakaran
}

// ==================== Setup Awal ====================
void setup() {
  Serial.begin(115200);
  setup_wifi();

  espClient.setInsecure();  // Nonaktifkan verifikasi TLS untuk testing
  delay(2000);              // Beri waktu agar TLS siap

  client.setServer(mqtt_server, mqtt_port);
  dht.begin();

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(FLAME_PIN, INPUT); // Digital input
}

// ==================== Loop Utama ====================
void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  // Baca sensor
  float temperature = dht.readTemperature();
  int smokeLevel = analogRead(MQ2_PIN);        // Nilai dari 0 - 1023
  int flameValue = digitalRead(FLAME_PIN);     // 0 = api terdeteksi

  bool flameDetected = (flameValue == 0);
  bool smokeDetected = (smokeLevel > SMOKE_THRESHOLD);
  bool tempDetected = (temperature > TEMP_THRESHOLD);

  bool fireDetected = flameDetected || smokeDetected || tempDetected;

  // Kontrol buzzer
  if (fireDetected && !alarmActive) {
    digitalWrite(BUZZER_PIN, HIGH);
    alarmActive = true;
  } else if (!fireDetected && alarmActive) {
    digitalWrite(BUZZER_PIN, LOW);
    alarmActive = false;
  }

  // Kirim data ke MQTT
  publishSensorData(temperature, smokeLevel, flameValue, fireDetected);

  // Debug ke Serial Monitor
  Serial.print("Suhu: "); Serial.print(temperature);
  Serial.print(" | Asap(A0): "); Serial.print(smokeLevel);
  Serial.print(" | Api(DO): "); Serial.print(flameValue);
  Serial.print(" | Kebakaran: "); Serial.println(fireDetected);

  delay(3000);
}
