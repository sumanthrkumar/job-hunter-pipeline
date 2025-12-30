# Job Hunter AI Automation System

This project is an automated job-hunting pipeline designed to discover, evaluate, and notify users about remote job opportunities relevant to their skills. It leverages web scraping, Apache Kafka for a robust data pipeline, AI-powered resume matching (via Google Gemini), and PostgreSQL for storing high-value job postings. Relevant job alerts are sent via Discord webhooks.

## Features

*   **Web Scraping**: Automatically scrapes remote job postings from target websites (e.g., WeWorkRemotely) and publishes them to a Kafka topic.
*   **Kafka-based Data Pipeline**: Utilizes Apache Kafka for reliable, asynchronous processing of job data, ensuring scalable and decoupled components.
*   **AI-Powered Resume Scoring**: Integrates with Google Gemini to analyze job postings against a candidate's resume, assigning a relevance score and providing an explanation for the fit.
*   **PostgreSQL Persistence**: Stores high-scoring job postings (above a configurable threshold) in a PostgreSQL database, allowing for persistent storage and future analysis.
*   **Discord Notifications**: Sends real-time alerts to a configured Discord channel for newly identified high-value job opportunities, including job details and a direct link.
*   **Modular Design**: Separates concerns into distinct, independent components (scraper, AI scorer, consumer, notifier) for easier maintenance and development.
*   **Configurable**: Relies on environment variables for API keys, database credentials, and Kafka topics, making it flexible for different environments.

## Project Structure

*   `scraper/ai_scorer.py`: Contains the logic for loading a resume PDF and using the Google Gemini API to score job postings.
*   `scraper/consumer.py`: The core processing unit. Consumes raw jobs from Kafka, uses `ai_scorer` to score them, stores high-value jobs in PostgreSQL, and publishes them to a `high-value-jobs` Kafka topic.
*   `scraper/notifier.py`: Consumes high-value jobs from Kafka and sends detailed notifications to a Discord webhook.
*   `scraper/reset_db.py`: A utility script to clear all data from the `job_postings` table in the PostgreSQL database.
*   `scraper/scraper_and_producer.py`: Scrapes job listings from WeWorkRemotely and produces them to the `raw-jobs` Kafka topic.
*   `scraper/test_producer.py`: A simple script to send a test message to the `raw-jobs` Kafka topic for development and testing purposes.
*   `resources/Resume.pdf`: Placeholder for the candidate's resume, which is used for AI scoring.

## Prerequisites

Before you begin, ensure you have the following installed and configured:

*   **Python 3.8+**: The project is developed in Python.
*   **Docker & Docker Compose**: Recommended for easily setting up Kafka and PostgreSQL.
*   **Google Gemini API Key**: Obtain a key from [Google AI Studio](https://makersuite.google.com/app/apikey).
*   **Discord Webhook URL**: Create a webhook in your Discord server settings to receive notifications.
*   **A Resume PDF file**: Named `Resume.pdf` and placed in the `resources/` directory.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/job-hunter-ai.git
    cd job-hunter-ai
    ```
    (Replace `your-username/job-hunter-ai` with the actual repository path if different.)

2.  **Set up Environment Variables**:
    Create a `.env` file in the project's root directory (`job-hunter-ai/.env`) and populate it with your credentials:

    ```dotenv
    GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
    DISCORD_WEBHOOK_URL="YOUR_DISCORD_WEBHOOK_URL"

    DB_USER="your_db_user"
    DB_PASSWORD="your_db_password"
    DB_HOST="localhost"
    DB_PORT="5432"
    DB_NAME="job_hunter"
    ```
    *   Ensure `DB_USER` and `DB_PASSWORD` match the PostgreSQL setup.
    *   `DB_HOST` should be `localhost` if running PostgreSQL via Docker Compose on the same machine.

3.  **Place Your Resume**:
    Ensure your resume PDF file is located at `resources/Resume.pdf`. The AI scorer will use this file to evaluate job fit.

4.  **Install Python Dependencies**:
    It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
    Create `requirements.txt` with the following content:
    ```
    google-generativeai
    pypdf
    python-dotenv
    confluent-kafka
    SQLAlchemy
    requests
    beautifulsoup4
    ```

5.  **Set up Kafka and PostgreSQL with Docker Compose**:
    Create a `docker-compose.yml` file in the project's root directory:

    ```yaml
    version: '3'
    services:
      zookeeper:
        image: confluentinc/cp-zookeeper:7.3.0
        hostname: zookeeper
        container_name: zookeeper
        ports:
          - "2181:2181"
        environment:
          ZOOKEEPER_CLIENT_PORT: 2181
          ZOOKEEPER_TICK_TIME: 2000

      broker:
        image: confluentinc/cp-kafka:7.3.0
        hostname: broker
        container_name: broker
        ports:
          - "29092:29092"
          - "9092:9092"
        environment:
          KAFKA_BROKER_ID: 1
          KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
          KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_INTERNAL:PLAINTEXT
          KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:29092,PLAINTEXT_INTERNAL://broker:9092
          KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
          KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
          KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
          KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
        depends_on:
          - zookeeper

      db:
        image: postgres:13
        hostname: job_hunter_db
        container_name: job_hunter_db
        environment:
          POSTGRES_DB: ${DB_NAME}
          POSTGRES_USER: ${DB_USER}
          POSTGRES_PASSWORD: ${DB_PASSWORD}
        ports:
          - "5432:5432"
        volumes:
          - postgres_data:/var/lib/postgresql/data

    volumes:
      postgres_data:
    ```
    Then, start the services:
    ```bash
    docker-compose up -d
    ```
    This will start Zookeeper, Kafka, and PostgreSQL. The PostgreSQL database will be created with the credentials from your `.env` file.

## Usage

Once all prerequisites are met and services are running:

1.  **Initialize or Reset the Database (Optional)**:
    The `consumer.py` script will automatically create the `job_postings` table on its first run. If you need to clear all existing job data, run:
    ```bash
    python scraper/reset_db.py
    ```

2.  **Start the AI Scorer and Database Consumer**:
    This component listens for raw job postings, scores them against your resume, and stores relevant ones in the database.
    ```bash
    python scraper/consumer.py
    ```
    Keep this running in a dedicated terminal.

3.  **Start the Discord Notifier**:
    This component listens for high-value job postings and sends notifications to your configured Discord webhook.
    ```bash
    python scraper/notifier.py
    ```
    Keep this running in another dedicated terminal.

4.  **Run the Job Scraper**:
    This script scrapes job listings from the target website and feeds them into the Kafka pipeline.
    ```bash
    python scraper/scraper_and_producer.py
    ```
    You can run this manually whenever you want to check for new jobs, or set up a task scheduler (like `cron` on Linux/macOS or Task Scheduler on Windows) to run it periodically.

### Testing (Optional)

To send a test job message to the `raw-jobs` Kafka topic without performing a full scrape:

```bash
python scraper/test_producer.py
```
This can be useful for verifying your Kafka and consumer setup.
