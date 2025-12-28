import json
from confluent_kafka import Producer
import socket

conf = {
    'bootstrap.servers': 'localhost:29092',
    'client.id': socket.gethostname()
}

producer = Producer(conf)

def produced(err, msg):
    if err is not None:
        print(f"Failed to deliver message: {err}")
    else:
        print(f"Message produced: {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

topic = 'raw-jobs'
data = {"title": "Test Job", "salary": "100k"}

print ("Sending Message...")
producer.produce(topic, json.dumps(data).encode('utf-8'), callback=produced)
producer.flush()
