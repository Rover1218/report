import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

def check_gemini_api():
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "GEMINI_API_KEY not found in .env"
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")
        return f"Gemini API: WORKING - {api_key[:10]}..."
    except Exception as e:
        return f"Gemini API: EXPIRED/INVALID - {str(e)}"

if __name__ == "__main__":
    print(check_gemini_api())
    print(f"Groq API key present: {bool(os.getenv('GROQ_API_KEY'))}")