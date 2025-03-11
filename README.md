# AI Report Generator

This application uses Google's Gemini AI model to generate detailed reports on any topic. The reports can be downloaded as either professionally formatted PDFs or as PDFs that simulate handwritten notes.

## Features

- Generate reports on any topic
- Specify the desired report length
- Choose between typed and handwritten styles
- Reports include title, introduction, sections, conclusion, and references

## Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file and add your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_key_here
   ```
4. Create required directories:
   ```
   mkdir -p static/reports static/fonts
   ```
5. Add a handwriting font (optional):
   - Download a handwriting-style font and place it at `static/fonts/handwriting.ttf`
   - If no font is provided, the system will use Comic Sans or Courier as fallback

6. Run the application:
   ```
   python app.py
   ```
7. Open your browser and navigate to `http://localhost:5000`

## How it Works

1. User enters a topic, number of pages, and selects the report style
2. The application uses Gemini AI to generate detailed content on the topic
3. The content is processed and structured into a report format
4. For handwritten style, the text is rendered with random tilts, offsets, and spacing for a realistic handwritten look
5. A PDF is generated and provided to the user for download

## Requirements

- Python 3.7+
- Flask
- Google Generative AI Python library
- FPDF
- NumPy
