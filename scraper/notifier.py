import os
import json
from confluent_kafka import Consumer
from dotenv import load_dotenv
from pathlib import Path
import socket
import requests

current_dir = Path(__file__).resolve().parent
env_path = current_dir.parent / '.env' 
load_dotenv(dotenv_path=env_path)

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
TOPIC_NAME = 'high-value-jobs'

conf = {
    'bootstrap.servers': 'localhost:29092',
    'client.id': socket.gethostname(),
    'group.id': 'job-hunter-notifier-2',
    'auto.offset.reset': 'earliest'
}

#Consume messages and save to database if score is greater than threshold (currently 50)
consumer = Consumer(conf)
consumer.subscribe([TOPIC_NAME])

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

         # Consumes message from high value Kafka topic
        try: 
            high_value_job_data = json.loads(msg.value().decode('utf-8'))
        except json.JSONDecodeError as e:
            print(f"JSON decode error in high-value job message: {e}")
            continue

        # Retrieves relevant fields
        job_title = high_value_job_data.get("title", "N/A")
        company = high_value_job_data.get("company", "N/A")
        url = high_value_job_data.get("url", "N/A")
        score = high_value_job_data.get("score", "N/A")

        payload = {
            "content": f"**High-Value Job Found!**\n**Title:** {job_title}\n**Company:** {company}\n**URL:** {url}\n**Score:** {score}"
        }

        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)

            if response.status_code == 204:
                print(f"Successfully sent notification for job: {job_title}")
            else:
                print(f"Failed to send notification for job: {job_title}, Status Code: {response.status_code}, Response: {response.text}")
        except requests.RequestException as e:
            print(f"Error sending notification for job: {job_title}, Error: {e}")

except KeyboardInterrupt:
    print("Consumer interrupted by user")

finally: 
    consumer.close()
    print("Consumer has been closed")