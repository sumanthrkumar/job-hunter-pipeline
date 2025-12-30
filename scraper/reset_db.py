import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# Load Env
current_dir = Path(__file__).resolve().parent
env_path = current_dir.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Connection Details
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'job_hunter')

# Connect
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

try:
    with engine.connect() as connection:
        print("Clearing all data from job_postings...")
        
        connection.execute(text("TRUNCATE TABLE job_postings RESTART IDENTITY;"))
        connection.commit()
        print("Database cleared successfully.")
except Exception as e:
    print(f"Error: {e}")