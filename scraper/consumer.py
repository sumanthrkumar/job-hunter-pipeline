import os
import json
from confluent_kafka import Consumer, Producer
import socket
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, declarative_base


current_dir = Path(__file__).resolve().parent
env_path = current_dir.parent / '.env' 
load_dotenv(dotenv_path=env_path)

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'job_hunter')

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base = declarative_base()
engine = create_engine(DB_URL)
Session = sessionmaker(bind = engine)
CONSUMER_TOPIC = 'raw-jobs'
PRODUCER_TOPIC = 'high-value-jobs'

conf = {
    'bootstrap.servers': 'localhost:29092',
    'client.id': socket.gethostname(),
    'group.id': 'job-hunter-consumer5',
    'auto.offset.reset': 'earliest'
}

# DAO for Job Posting
class JobPosting(Base):
    __tablename__ = 'job_postings'
    id = Column(Integer, primary_key = True)
    title = Column(String)
    company = Column(String)
    url = Column(String, unique = True)
    score = Column(Integer)

# Function to assign scores to jobs based on keywords
def analyze_job(job_data):
    title = job_data.get("title", "N/A").lower()

    if "java" in title or "backend" in title or "back-end" in title:
        return 100
    if  "python" in title or "full stack" in title: 
        return 80
    else:
        return 0
    
# Function to handle delivery status of high-value job messages
def delivered_status(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} at offset {msg.offset()}")
        print(f"Message content: {msg.value().decode('utf-8')}")

# Create tables if they don't exist
Base.metadata.create_all(engine)

#Consume messages and save to database if score is greater than threshold (currently 50)
consumer = Consumer(conf)
consumer.subscribe([CONSUMER_TOPIC])

producer = Producer(conf)

try: 
    while True:
        producer.poll(0)
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        # Consumes message from Kafka
        try: 
            job_data = json.loads(msg.value().decode('utf-8'))

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            continue

        # Retrieves relevant fields
        job_title = job_data.get("title", "N/A")
        company = job_data.get("company", "N/A")
        url = job_data.get("url", "N/A")
        score = analyze_job(job_data)
        job_data["score"] = score

        # If score is greater than threshold, save to DB and produce to high-value topic
        if score > 50: 
            print(f"Match: job_title='{job_title} - {url}' with a score of {score}")

            try:
                session = Session()
                new_job = JobPosting(
                    title = job_title,
                    company = company,
                    url = url,
                    score = score
                )
                session.add(new_job)
                session.commit()
                print(f"Inserted job into database: {job_title} at {company}")

                # Produce to high-value jobs topic
                producer.produce(
                    PRODUCER_TOPIC, 
                    key=url, 
                    value=json.dumps(job_data).encode('utf-8'), 
                    callback=delivered_status
                )

            except IntegrityError:
                session.rollback()
                print(f"Job already exists in database: {job_title} at {company}")
            except Exception as e:
                session.rollback()
                print(f"Database error: {e}")
            finally:
                session.close()

        else: 
            print(f"Ignoring job: '{job_title}'")

except KeyboardInterrupt:
    print("Consumer interrupted by user")

finally: 
    consumer.close()
    print("Consumer has been closed")
    producer.flush()
    print("Producer has been flushed")