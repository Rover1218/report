from flask import Flask, render_template, request, send_file, flash, redirect, session
import google.generativeai as genai
from dotenv import load_dotenv
import os
import traceback
import uuid
from werkzeug.utils import secure_filename
from report_generator import generate_report
from pdf_creator import create_typed_pdf, create_handwritten_pdf
from io import BytesIO
import threading
import time

# Load environment variables
load_dotenv()

# Create upload folder
UPLOAD_FOLDER = 'static/uploads'

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For flash messages

# Use a global dictionary to hold generated PDFs
pdf_store = {}

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
        
        # Generate a unique ID for this report generation request
        report_id = str(uuid.uuid4())
        
        # Store report parameters in session
        session['report_params'] = {
            'id': report_id,
            'topic': topic,
            'num_pages': num_pages,
            'report_type': report_type
        }
        
        # Also store parameters in pdf_store to avoid session dependency
        pdf_store[report_id] = {
            'params': {
                'topic': topic,
                'num_pages': num_pages,
                'report_type': report_type
            }
        }
        
        # Render the loading page, which will poll for PDF completion
        return render_template('loading_pdf.html', 
                              pdf_url=f'/download_pdf/{report_id}',
                              topic=topic,
                              type=report_type)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        flash(f"An error occurred: {str(e)}", "error")
        return redirect('/')

@app.route('/create_pdf/<report_id>')
def create_pdf(report_id):
    try:
        # Retrieve parameters from pdf_store instead of session
        pdf_params = pdf_store.get(report_id, {}).get('params')
        if not pdf_params:
            return {'status': 'error', 'message': 'Invalid report ID'}, 400
        
        topic = pdf_params['topic']
        num_pages = pdf_params['num_pages']
        report_type = pdf_params['report_type']
        
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
        
        # Store PDF buffer & filename in pdf_store
        pdf_store[report_id]['buffer'] = pdf_content
        pdf_store[report_id]['filename'] = safe_filename
        
        return {'status': 'success'}, 200
    
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        print(traceback.format_exc())
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/download_pdf/<report_id>', methods=['GET', 'HEAD'])
def download_pdf(report_id):
    if request.method == 'HEAD':
        pdf_data = pdf_store.get(report_id)
        if not pdf_data or 'buffer' not in pdf_data:
            return redirect(f'/create_pdf/{report_id}'), 302
        return '', 200
    
    # For GET requests, retrieve PDF data without popping
    pdf_data = pdf_store.get(report_id)
    if not pdf_data or 'buffer' not in pdf_data:
        return redirect(f'/create_pdf/{report_id}')
    
    pdf_content = pdf_data['buffer']
    pdf_buffer = BytesIO(pdf_content)
    pdf_buffer.seek(0)
    # Remove only session-related data if needed
    session.pop('report_params', None)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=False
    )

# Add a new route for explicitly downloading the PDF after viewing
@app.route('/download_pdf_file/<report_id>')
def download_pdf_file(report_id):
    try:
        # Retrieve PDF data without removing it
        pdf_data = pdf_store.get(report_id)
        
        if not pdf_data:
            flash("Your PDF is no longer available. Please generate a new one.", "error")
            return redirect('/')
        
        # Get PDF data from pdf_store
        pdf_content = pdf_data['buffer']
        filename = pdf_data['filename']
        
        # Create a BytesIO object
        pdf_buffer = BytesIO(pdf_content)
        pdf_buffer.seek(0)
        
        # Don't clean up the session here, as the user might want to view it again
        
        # Return the PDF as a download attachment
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        print(f"Error downloading PDF: {str(e)}")
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
