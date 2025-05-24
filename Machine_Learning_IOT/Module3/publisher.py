from time import sleep
import paho.mqtt.client as mqtt
import psutil
import uuid
import time
from datetime import datetime
import json

mac_address = hex(uuid.getnode())

# Create a new MQTT client
client = mqtt.Client()

# Connect to the MQTT broker
client.connect('mqtt.eclipseprojects.io', 1883)



while True:
    # Collect 10 consecutive records
    events = []
    for i in range(10):
        timestamp = time.time()
        battery_level = psutil.sensors_battery().percent
        power_plugged = int(psutil.sensors_battery().power_plugged)
    
        # Create an event dictionary
        event_data = {"timestamp": int(timestamp * 1000), "battery_level": battery_level, "power_plugged": power_plugged}
    
        # Append the event to the list
        events.append(event_data)
    
        sleep(1)

    # Create the final JSON payload with the collected events

    json_payload = {
        "mac_address": mac_address,
        "events": events
    }

    # Publish the JSON payload to the MQTT broker

    client.publish('s307798', json.dumps(json_payload,sort_keys = False,indent = 4))
