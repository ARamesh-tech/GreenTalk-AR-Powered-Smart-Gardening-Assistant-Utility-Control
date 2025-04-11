// #define BLYNK_TEMPLATE_ID "TMPL3rLB1CbSW"
// #define BLYNK_TEMPLATE_NAME "Led Blink"
// #define BLYNK_AUTH_TOKEN "kGWvdkB1V91FWflMiw24KFLFztnmKPZD"
#define BLYNK_TEMPLATE_ID "TMPL3zlJravNQ"
#define BLYNK_TEMPLATE_NAME "ARGardenAssistant"
#define BLYNK_AUTH_TOKEN "oqVvTjuTCSu7gj4_mOiyvl1ToIfarOtb"

#define BLYNK_PRINT Serial
#include <WiFi.h>
#include <BlynkSimpleEsp32.h>

char ssid[] = "OpenWifi";
char pass[] = "hackers12345";

#define LED_PIN 2         // ESP32 onboard LED
#define SOIL_SENSOR_PIN 15// Soil Moisture Sensor on GPIO5
#define LDR_SENSOR_PIN 22 // LDR Sensor on GPIO21
#define BUZZER_PIN 21      // Buzzer on GPIO5

void setup()
{
    Serial.begin(115200);
    Serial2.begin(9600, SERIAL_8N1, 16, 17); // Serial2: RX=16, TX=17

    pinMode(LED_PIN, OUTPUT);
    pinMode(SOIL_SENSOR_PIN, INPUT);
    pinMode(LDR_SENSOR_PIN, INPUT);
    pinMode(BUZZER_PIN, OUTPUT);
    Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);
    
    delay(1000);
}
    

void loop()
{
    Blynk.run();
    sendSensorData();
}

BLYNK_WRITE(V0)  // Control LED from Blynk
{
    int pinValue = param.asInt();
    digitalWrite(LED_PIN, pinValue ? HIGH : LOW);
    if (pinValue) {
        Serial2.println("ON");
    } else {
        Serial2.println("OFF");
    }
}

void sendSensorData()
{
    int ldrValue = digitalRead(LDR_SENSOR_PIN);
    // Read and send soil moisture data
    int moistureValue = analogRead(SOIL_SENSOR_PIN);
    int moisturePercentage = map(moistureValue, 0, 4095, 100, 0); 
    Blynk.virtualWrite(V1, moistureValue);
    Blynk.virtualWrite(V3, moisturePercentage);
    
    // Read and send LDR sensor data
    
    Blynk.virtualWrite(V2, ldrValue);
    
    Serial.print("Moisture: ");
    Serial.print(moisturePercentage);
    Serial.print("% | LDR: ");
    Serial.println(ldrValue);

    // Control Buzzer based on LDR value
    if (ldrValue ==1) 
    {
        digitalWrite(BUZZER_PIN, HIGH);  // Turn ON buzzer
        Serial.println("Buzzer ON (Dark Environment)");
    }
    else
    {
        digitalWrite(BUZZER_PIN, LOW);   // Turn OFF buzzer
    }

    delay(2000); // Update every 2 seconds
}
