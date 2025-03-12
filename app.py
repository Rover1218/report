from flask import Flask, render_template, request, send_file, flash, redirect
import google.generativeai as genai
from dotenv import load_dotenv
import os
import traceback
import uuid
from werkzeug.utils import secure_filename
from report_generator import generate_report
from pdf_creator import create_typed_pdf, create_handwritten_pdf
from io import BytesIO

# Load environment variables
load_dotenv()

# Create upload folder
UPLOAD_FOLDER = 'static/uploads'

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For flash messages

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        topic = request.form['topic']
        num_pages = int(request.form['pages'])
        report_type = request.form['type']
        
        # Limit pages to a reasonable number for Vercel deployment
        num_pages = min(num_pages, 10)  # Cap at 10 pages to prevent timeouts
        
        # Generate the report content
        content = generate_report(topic, num_pages, is_handwritten=(report_type == 'handwritten'))
        
        # Validate the report structure before proceeding
        if not isinstance(content, dict):
            raise ValueError("Invalid report structure: not a dictionary")
        
        required_keys = ['title', 'introduction', 'sections', 'conclusion', 'references']
        missing_keys = [key for key in required_keys if key not in content]
        
        if missing_keys:
            raise ValueError(f"Invalid report structure: missing keys {missing_keys}")
            
        content['requested_pages'] = num_pages

        # Create the PDF in memory
        if report_type == 'typed':
            pdf_content = create_typed_pdf(topic, content)
        else:
            pdf_content = create_handwritten_pdf(topic, content)
        
        # Create a BytesIO object from the PDF content
        pdf_buffer = BytesIO(pdf_content)
        pdf_buffer.seek(0)
        
        # Generate a safe filename
        safe_filename = secure_filename(f"{topic.replace(' ', '_')}_report.pdf")
        
        # Return the PDF directly
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=safe_filename
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        flash(f"An error occurred: {str(e)}", "error")
        return redirect('/')

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/reports', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/fonts', exist_ok=True)
    
    # Download font if it doesn't exist
    font_path = os.path.join('static', 'fonts', 'hc.ttf')
    if not os.path.exists(font_path):
        try:
            import requests
            font_url = "https://github.com/google/fonts/raw/main/apache/homemadeapple/HomemadeApple-Regular.ttf"
            response = requests.get(font_url, timeout=10)
            if response.status_code == 200:
                with open(font_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded handwriting font to {font_path}")
            else:
                print("Failed to download font, using fallback")
        except Exception as e:
            print(f"Could not download font: {e}")
    
    app.run(debug=True)
