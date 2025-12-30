import json
import time
import socket
import requests
from bs4 import BeautifulSoup
from confluent_kafka import Producer

# Configurations
KAFKA_TOPIC = 'raw-jobs'
TARGET_URL = "https://weworkremotely.com/categories/remote-back-end-programming-jobs"

# Kafka Config
conf = {
    'bootstrap.servers': 'localhost:29092',
    'client.id': socket.gethostname()
}

producer = Producer(conf)

def delivered_status(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} at offset {msg.offset()}")
        print(f"Message content: {msg.value().decode('utf-8')}")

def scrape_wework_remotely():
    print(f"Scraping: {TARGET_URL}..")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    response = requests.get(TARGET_URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    job_section = soup.find('section', class_='jobs')
    
    if not job_section:
        print("Could not find job section. The HTML structure might have changed.")
        return

    # Find all list items inside that section
    job_items = job_section.find_all('li')

    # print(f"Found {len(job_items)} listing items")
    
    jobs_found = 0
    
    for item in job_items:
        try:
            # Real jobs have the class "feature" or "new-listing-container"
            if 'view-all' in item.get('class', []):
                continue

            title_tag = item.find('h3', class_='new-listing__header__title')
            if not title_tag:
                # Skip if no job title found
                continue 

            title = title_tag.text.strip()

            company_tag = item.find('p', class_='new-listing__company-name')
            company = company_tag.text.strip() if company_tag else "Unknown"

            region_tag = item.find('p', class_='new-listing__company-headquarters')
            region = region_tag.text.strip() if region_tag else "Remote"

            link_tag = item.find('a', class_='listing-link--unlocked')
            if not link_tag:
                continue
            url = "https://weworkremotely.com" + link_tag['href']

            # 3. Build & Send
            job_data = {
                "source": "weworkremotely",
                "title": title,
                "company": company,
                "location": region,
                "url": url,
                "scraped_at": time.time()
            }
            
            producer.produce(
                KAFKA_TOPIC, 
                key=url, 
                value=json.dumps(job_data).encode('utf-8'), 
                callback=delivered_status
            )
            jobs_found += 1
            
        except Exception as e:
            # print(f"Error parsing job: {e}")
            continue

    producer.flush()
    print(f"Finished. Sent {jobs_found} jobs to the pipeline.")

if __name__ == "__main__":
    scrape_wework_remotely()