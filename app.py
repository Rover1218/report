from flask import Flask, render_template, request, send_file, flash, redirect
import google.generativeai as genai
from dotenv import load_dotenv
import os
import traceback
import uuid
from werkzeug.utils import secure_filename
from report_generator import generate_report
from pdf_creator import create_typed_pdf, create_handwritten_pdf

# Load environment variables
load_dotenv()

# Create upload folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For flash messages
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        topic = request.form['topic']
        num_pages = int(request.form['pages'])
        report_type = request.form['type']
        
        # Generate content using Gemini with different style based on report type
        content = generate_report(topic, num_pages, is_handwritten=(report_type == 'handwritten'))
        
        # Add page request to content
        content['requested_pages'] = num_pages
        
        # Removed handwriting sample upload handling
        
        # Create PDF based on type
        if report_type == 'typed':
            pdf_path = create_typed_pdf(topic, content)
        else:
            pdf_path = create_handwritten_pdf(topic, content)
        
        # Send file as direct download
        return send_file(pdf_path, as_attachment=True, download_name=f"{topic.replace(' ', '_')}_report.pdf")
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        flash(f"An error occurred: {str(e)}", "error")
        return redirect('/')

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/reports', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    
    # Create fonts directory if it doesn't exist
    os.makedirs('static/fonts', exist_ok=True)
    
    # Download a handwriting font if it doesn't exist
    font_path = os.path.join('static', 'fonts', 'handwriting.ttf')
    if not os.path.exists(font_path):
        try:
            import requests
            # Using Google Font Homemade Apple as a nice handwriting font
            font_url = "https://github.com/google/fonts/raw/main/apache/homemadeapple/HomemadeApple-Regular.ttf"
            response = requests.get(font_url)
            with open(font_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded handwriting font to {font_path}")
        except Exception as e:
            print(f"Could not download font: {e}")
    
    app.run(debug=True)
