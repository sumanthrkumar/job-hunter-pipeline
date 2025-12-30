import os
import json
import google.generativeai as genai
from pypdf import PdfReader
from pathlib import Path
from dotenv import load_dotenv

current_dir = Path(__file__).resolve().parent
env_path = current_dir.parent / '.env' 
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("API key not found in environment variables.")

genai.configure(api_key = GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def load_resume_pdf(pdf_path):
    if pdf_path.exists():
        print("Loading resume..")

        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
        
    else: 
        print("Resume PDF not found.")
        return ""
    
def score_job(job_title, company, resume_content, description = ""):
    job_content = f"Job Title: {job_title}\nCompany: {company}\n"
    if description:
        job_content += f"Description: {description}\n"

    
    prompt = f"""
    You are an expert technical recrutier. 

    Here is the candidate's resume: {resume_content}.

    Here is the job posting: {job_content}.

    Task:
    1. Analyze the candidate's resume against the job posting.
    2. Assign a score from 0 to 100 indicating how well the candidate fits the job requirements.
    3. Be strict. 100 is a perfect fit. 50 is a partial fit. < 20 is irrelevant

    Output format: 
    Return ONLY a raw JSON object with no markdown formatting as follows:
    {{"score": <integer>, "explanation": "<brief explanation>"}}

    """

    try:
        scored_response = model.generate_content(prompt)
        clean_text = scored_response.text.strip().replace("```json", "").replace("```", "")
        result = json.loads(clean_text)

        return result.get("score", 0), result.get("reason", "No reason provided.")
    except Exception as e:
        print(f"Error scoring job: {e}")
        return 0, "AI scoring failed."
