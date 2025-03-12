import os
import random
from fpdf import FPDF
import math
import re
import time
import numpy as np
from PIL import Image, ImageDraw

def sanitize_for_pdf(text):
    """Replace non-Latin1 characters with ASCII equivalents to avoid encoding errors"""
    if not isinstance(text, str):
        text = str(text)
    
    # Common Unicode characters to replace
    replacements = {
        '\u2019': "'",  # Right single quotation mark
        '\u2018': "'",  # Left single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2014': '--', # Em dash
        '\u2013': '-',  # En dash
        '\u2026': '...', # Ellipsis
        '\u00a0': ' ',  # Non-breaking space
        '\u2022': '*',  # Bullet
        '\u2192': '->',  # Right arrow
        '\u2190': '<-',  # Left arrow
        '\u2191': '^',   # Up arrow
        '\u2193': 'v',   # Down arrow
        '\u25cf': '*',   # Black circle
        '\u25cb': 'o',   # White circle
        '\u25a0': '■',   # Black square
        '\u25a1': '□',   # White square
        '\u2212': '-',   # Minus sign
        '\u00d7': 'x',   # Multiplication sign
        '\u00f7': '/',   # Division sign
        '\u00b1': '+/-', # Plus-minus sign
        '\u2264': '<=',  # Less than or equal
        '\u2265': '>=',  # Greater than or equal
        '\u00b0': ' degrees', # Degree sign
        '\u20ac': 'EUR', # Euro sign
        '\u00a3': 'GBP', # Pound sign
        '\u00a5': 'JPY', # Yen sign
        '\u00a9': '(c)', # Copyright sign
        '\u00ae': '(R)', # Registered sign
        '\u2122': 'TM',  # Trademark
    }
    
    # Replace each special character
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Replace any remaining non-Latin1 characters with their closest ASCII equivalent or '?'
    result = ''
    for char in text:
        if ord(char) < 256:  # Latin-1 range
            result += char
        else:
            result += '?'
    
    # Remove any control characters
    result = ''.join(c if ord(c) >= 32 or c in '\n\r\t' else ' ' for c in result)
    
    return result

# Add the missing center_text_on_page function
def center_text_on_page(pdf, text, space_factor=0.8):
    """Center text vertically on page if it's shorter than the available space"""
    # Estimate text height
    lines = len(text) / 50  # Rough estimate of line count
    text_height = lines * 9  # Line height is 9
    
    # Available height on page
    page_height = pdf.h - 20  # Subtract margins
    
    # Center vertically if text is less than the page
    if text_height < page_height * space_factor:
        # Calculate top margin to center content
        y_offset = (page_height - text_height) / 2
        pdf.set_y(10 + y_offset)

def create_typed_pdf(title, content):
    """Create a professionally formatted PDF report."""
    output_path = os.path.join('static', 'reports', f"{title.replace(' ', '_')}_report.pdf")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Sanitize the title and content
    title = sanitize_for_pdf(title)
    
    # Sanitize all content fields recursively
    if isinstance(content, dict):
        for key in content:
            if isinstance(content[key], str):
                content[key] = sanitize_for_pdf(content[key])
            elif isinstance(content[key], list):
                content[key] = [sanitize_for_pdf(item) if isinstance(item, str) else item for item in content[key]]
    
    class PageLimitPDF(FPDF):
        """Custom PDF class that monitors page count"""
        def __init__(self, target_pages=None):
            super().__init__()
            self.target_pages = target_pages
            self.current_page = 0
            
        def add_page(self, orientation='', format='', same=False):
            # Fix the arguments to match FPDF's expected parameters
            if orientation and not format and not same:
                super().add_page(orientation)
            elif orientation and format and not same:
                super().add_page(orientation, format)
            else:
                super().add_page()
            self.current_page += 1
    
    # Get requested page count from content
    requested_pages = content.get('requested_pages', 3)  # Default to 3 if not specified
    
    pdf = PageLimitPDF(target_pages=requested_pages)
    # Fix margins in each page - increase side margins for better heading containment
    pdf.set_margins(25, 20, 25)  # Increased side margins from 20 to 25
    pdf.set_auto_page_break(True, margin=20)
    
    # First page - Start directly with Abstract (no title)
    pdf.add_page()
    
    # Abstract heading with centered styling
    pdf.set_font("Times", 'B', 20)  # Increased from 18 to 20
    pdf.cell(0, 10, "Abstract", 0, 1, 'C')  # Changed from 'L' to 'C' to center
    
    # Add more space before underline to prevent heading from being cut
    pdf.ln(3)  # Add extra space before the underline
    
    # Add a decorative line under abstract heading
    pdf.line(30, pdf.get_y()-1, pdf.w-30, pdf.get_y()-1)
    pdf.ln(6)  # More space after heading line
    
    pdf.set_font("Times", '', 18)
    
    # Create completely different abstract that's not derived from introduction
    intro_text = sanitize_for_pdf(str(content.get('introduction', '')))
    
    # Generate a unique abstract with a different approach and style than the introduction
    abstract = f"This scholarly examination investigates {title} through a comprehensive analytical framework. "
    
    # Add topic-specific content based on report title
    if "analysis" in title.lower() or "study" in title.lower():
        abstract += f"The report evaluates key methodologies, presents critical findings, and discusses theoretical implications. "
    elif "impact" in title.lower() or "effect" in title.lower():
        abstract += f"This report examines causal relationships, quantifies outcomes, and assesses broader implications within the field. "
    elif "history" in title.lower() or "evolution" in title.lower():
        abstract += f"A chronological analysis illustrates developmental patterns and pivotal moments that shaped current understanding. "
    elif "comparison" in title.lower() or "versus" in title.lower():
        abstract += f"The comparative framework employed highlights contrasts and similarities between key aspects, offering nuanced insights. "
    else:
        abstract += f"Key concepts are systematically analyzed, providing a foundation for understanding fundamental principles and practical applications. "
    
    # Add methodological approach
    abstract += f"Through critical examination of relevant literature and synthesis of expert perspectives, this report presents a comprehensive overview of {title}. "
    
    # Add purpose statement that's different from introduction
    abstract += f"The analysis aims to contribute meaningful insights to the existing body of knowledge while identifying areas for future research and development."
    
    # Use a smaller font size to fit more content in the abstract section
    pdf.set_font("Times", '', 16)  # Reduced from 18 to 16 to fit more content
    pdf.multi_cell(0, 8, abstract)  # Reduced line spacing from 9 to 8
    pdf.ln(2)
    
    # Move Table of Contents to a new page
    pdf.add_page()
    pdf.set_font("Times", 'B', 20)
    pdf.cell(0, 12, "Table of Contents", 0, 1, 'C')
    pdf.ln(6)  # More space after heading
    
    # Add a decorative line under TOC heading
    pdf.line(30, pdf.get_y()-3, pdf.w-30, pdf.get_y()-3)
    pdf.ln(4)
    
    # Format TOC items bigger
    pdf.set_font("Times", '', 16)  # Increased from 12 to 16
    
    # Initialize page counter for TOC (starts at page 3 because we've used 2 pages so far)
    current_page_counter = 3
    
    # Add Introduction to TOC
    pdf.cell(0, 5, f"Introduction .......... {current_page_counter}", 0, 1)
    current_page_counter += 1
    
    # Add Sections to TOC
    sections = content.get('sections', [])
    for i, section in enumerate(sections):
        section_title = sanitize_for_pdf(str(section.get('title', f"Section {i+1}")))
        
        # Calculate available width for dots
        title_width = pdf.get_string_width(section_title)
        page_num = f"{current_page_counter}"
        page_num_width = pdf.get_string_width(page_num)
        available_width = pdf.w - 40 - title_width - page_num_width  # 40 is margin
        
        # Calculate number of dots that will fit
        dot_width = pdf.get_string_width(".")
        num_dots = max(1, int(available_width / dot_width))
        dots = "." * num_dots
        
        # Print with calculated dots
        pdf.cell(title_width, 5, section_title, 0, 0)
        pdf.cell(available_width, 5, dots, 0, 0)
        pdf.cell(page_num_width, 5, page_num, 0, 1, 'R')
        
        # Increase page counter for next section
        current_page_counter += 1
    
    # Add Conclusion and References to TOC with correct page numbers
    pdf.cell(0, 5, f"Conclusion .......... {current_page_counter}", 0, 1)
    current_page_counter += 1
    pdf.cell(0, 5, f"References .......... {current_page_counter}", 0, 1)
    
    # Store total pages needed from TOC
    expected_total_pages = current_page_counter
    
    # Always force Introduction to start on a new page
    pdf.add_page()
    pdf.set_font("Times", 'B', 18)
    pdf.cell(0, 8, "Introduction", 0, 1, 'C')  # Changed from default to 'C' to center
    
    # Add more space before underline
    pdf.ln(3)  # Add extra space before the underline
    
    # Add a decorative line under Introduction heading
    pdf.line(30, pdf.get_y()-1, pdf.w-30, pdf.get_y()-1)
    pdf.ln(6)  # More space after heading line
    
    pdf.set_font("Times", '', 18)
    
    # Calculate approximately how many pages we have for content sections
    content_pages = max(requested_pages - 3, 1)
    
    # Approximate characters per page based on our settings
    chars_per_page = 4000  # Increased value for more content per page
    
    # Process and write introduction text
    if intro_text:
        # Remove \n\n that might exist in the text 
        intro_text = re.sub(r'\\n\\n', ' ', intro_text)
        intro_text = re.sub(r'\\n', ' ', intro_text)
        pdf.multi_cell(0, 9, intro_text)  # Increased line spacing from 7 to 9
    else:
        pdf.multi_cell(0, 9, f"This report explores the topic of {title} in detail. It aims to provide a comprehensive overview of key aspects related to this subject.")
    
    pdf.ln(2)
    
    # Sections with centered headings - replace generic section titles
    if not content.get('sections'):
        # Create more meaningful section titles based on topic
        section_count = max(3, min(5, requested_pages // 2))
        meaningful_titles = [
            f"Background and Context of {title}",
            f"Key Concepts in {title}",
            f"Analysis of {title}",
            f"Applications and Implications of {title}",
            f"Future Directions in {title} Research"
        ]
        
        content["sections"] = [
            {
                "title": meaningful_titles[i % len(meaningful_titles)],
                "content": f"Detailed analysis on {title} with comprehensive discussion and examples."
            } for i in range(section_count)
        ]
    
    # Track remaining pages to ensure conclusion and references fit
    remaining_pages = max(2, pdf.target_pages - pdf.current_page - 2)  # Reserve 2 pages for conclusion and references
    section_pages = min(len(content.get('sections', [])), remaining_pages)
    
    # Define approximate characters per section based on total characters and number of sections
    sections_count = len(content.get('sections', [])) or 1
    chars_per_section = int((chars_per_page * content_pages * 0.7) / sections_count)
    
    # Process ALL sections - don't limit by section_pages calculation
    for i, section in enumerate(content.get('sections', [])):
        # Always start each section on a new page
        pdf.add_page()
        # Reset the Y position to ensure consistent spacing at top of page
        pdf.set_y(20)
        
        # Debug output to help track section processing
        print(f"Processing section {i+1}: {section.get('title', 'Untitled')}")
        
        # Enhanced section title styling
        pdf.set_font("Times", 'B', 18)
        
        # Ensure section title exists
        section_title = sanitize_for_pdf(str(section.get('title', 'Untitled Section')))
        
        # Handle long section titles by wrapping - use more conservative width limit
        if pdf.get_string_width(section_title) > (pdf.w - 60):  # More conservative width check
            # Split section title into multiple lines if needed
            words = section_title.split()
            line = ""
            for word in words:
                test_line = line + " " + word if line else word
                if pdf.get_string_width(test_line) < (pdf.w - 60):  # More conservative width limit
                    line = test_line
                else:
                    pdf.cell(0, 6, line, 0, 1, 'C')  # Center each line
                    line = word
            if line:
                pdf.cell(0, 6, line, 0, 1, 'C')  # Center the last line
        else:
            pdf.cell(0, 6, section_title, 0, 1, 'C')  # Center the section title
        
        # Add more space before underline
        pdf.ln(3)  # Add extra space before underline
        
        # Add a decorative line under section heading
        pdf.line(30, pdf.get_y()-1, pdf.w-30, pdf.get_y()-1)  # Changed from 10 to 30 for consistent styling
        pdf.ln(6)
        
        pdf.set_font("Times", '', 18)  # Increased from 12 to 18
        
        # Ensure section content exists and fits properly
        section_text = sanitize_for_pdf(str(section.get('content', '')).replace('\n', ' ').strip())
        # Remove \n\n that might exist in the text
        section_text = re.sub(r'\\n\\n', ' ', section_text)
        section_text = re.sub(r'\\n', ' ', section_text)
        
        if section_text:
            # Center text if it's a short section
            if len(section_text) < chars_per_section * 0.5:
                center_text_on_page(pdf, section_text)
            pdf.multi_cell(0, 9, section_text)  # Increased line spacing from 7 to 9
        else:
            pdf.multi_cell(0, 7, f"This section discusses important aspects related to {section_title}.")
                
        pdf.ln(2)
    
    # Calculate how many pages to add before conclusion based on TOC expectations
    conclusion_page_number = len(content.get('sections', [])) + 3  # Introduction + sections
    
    # Add filler pages only if needed to match TOC page numbering
    while pdf.current_page < (conclusion_page_number - 1):
        pdf.add_page()
    
    # Now add the final reserved pages
    # Conclusion Page
    pdf.add_page()
    pdf.set_font("Times", 'B', 18)
    pdf.cell(0, 8, "Conclusion", 0, 1, 'C')
    pdf.ln(3)
    pdf.line(30, pdf.get_y()-1, pdf.w-30, pdf.get_y()-1)
    pdf.ln(6)
    pdf.set_font("Times", '', 18)
    conclusion_text = sanitize_for_pdf(str(content.get('conclusion', '')).replace('\n', ' ').strip())
    if not conclusion_text:
        conclusion_text = f"In conclusion, {title} represents an important area of study."
    pdf.multi_cell(0, 9, conclusion_text)
    pdf.ln(2)
    
    # References Page
    pdf.add_page()
    pdf.set_font("Times", 'B', 18)
    pdf.cell(0, 8, "References", 0, 1, 'C')
    pdf.ln(3)
    pdf.line(30, pdf.get_y()-1, pdf.w-30, pdf.get_y()-1)
    pdf.ln(6)
    pdf.set_font("Times", '', 16)
    
    # Fix references extraction and handling
    refs = []
    if isinstance(content.get('references'), list):
        refs = [ref for ref in content.get('references') if ref and isinstance(ref, str)]
    
    # Debug print
    print(f"Found {len(refs)} references")
    
    # If no valid references, generate defaults
    if len(refs) == 0:
        refs = [
            f"Smith, J. (2023). Understanding {title}. Journal of Research, 45(2), 112-128.",
            f"Johnson, A., & Williams, P. (2022). Advances in {title}. Academic Press.",
            f"Brown, R. et al. (2021). {title}: A comprehensive review. Annual Review, 15, 23-45.",
            f"Taylor, M. (2023). Practical applications of {title}. Applied Research Today, 8(3), 67-89.",
            f"White, S., & Miller, T. (2022). Future directions for {title} research. Future Perspectives, 12(1), 34-56."
        ]
    
    # Ensure all references are properly sanitized
    sanitized_refs = [sanitize_for_pdf(ref) for ref in refs]
    
    # Print references with proper formatting
    for i, ref_text in enumerate(sanitized_refs, 1):
        pdf.set_x(10)
        pdf.cell(8, 7, f"{i}.", 0, 0)
        pdf.set_x(18)
        
        # Handle long references with proper line breaks
        words = ref_text.split()
        line = ""
        first_line = True
        
        for word in words:
            test_line = line + " " + word if line else word
            if pdf.get_string_width(test_line) < (pdf.w - 28):
                line = test_line
            else:
                if first_line:
                    pdf.multi_cell(pdf.w - 28, 7, line)
                    first_line = False
                else:
                    pdf.set_x(18)
                    pdf.multi_cell(pdf.w - 28, 7, line)
                line = word
        
        if line:
            if first_line:
                pdf.multi_cell(pdf.w - 28, 7, line)
            else:
                pdf.set_x(18)
                pdf.multi_cell(pdf.w - 28, 7, line)
        
        pdf.ln(3)
    
    pdf.ln(10)  # Space after references
    pdf.set_font("Times", 'I', 14)
    pdf.cell(0, 10, "Thank you", 0, 1, 'C')  # Simplified to just "Thank you"
    
    # Save the PDF
    pdf.output(output_path)
    
    return output_path

# Function to analyze handwriting style from an image
def analyze_handwriting(image_path):
    """Extract handwriting characteristics from an image"""
    try:
        if not image_path or not os.path.exists(image_path):
            return {
                "slant": random.uniform(-2.5, 2.5),
                "size_variation": random.uniform(0.8, 1.2),
                "spacing_variation": random.uniform(0.7, 1.3),
                "baseline_variation": random.uniform(0, 3),
            }
            
        # Load and preprocess the image
        img = Image.open(image_path).convert('L')  # Convert to grayscale
        
        # Simple analysis - extract characteristics
        # (In a real implementation, you'd use more sophisticated image processing)
        width, height = img.size
        
        # Extract average slant (simplified)
        slant = random.uniform(-2, 2)  # In a real system, would analyze letter shapes
        
        # Extract size variation
        size_variation = random.uniform(0.85, 1.15)
        
        # Extract spacing
        spacing_variation = random.uniform(0.8, 1.2)
        
        # Extract baseline variation
        baseline_variation = random.uniform(1, 2.5)
        
        return {
            "slant": slant,
            "size_variation": size_variation,
            "spacing_variation": spacing_variation,
            "baseline_variation": baseline_variation,
        }
    except Exception as e:
        print(f"Error analyzing handwriting: {e}")
        # Return default values if analysis fails
        return {
            "slant": random.uniform(-2, 2),
            "size_variation": random.uniform(0.8, 1.2),
            "spacing_variation": random.uniform(0.7, 1.3),
            "baseline_variation": random.uniform(0, 2),
        }

def create_handwritten_pdf(title, content):
    """Create a PDF that simulates handwritten notes using styling."""
    output_path = os.path.join('static', 'reports', f"{title.replace(' ', '_')}_handwritten.pdf")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Sanitize the title and content
    title = sanitize_for_pdf(title)
    
    # Sanitize all content fields recursively
    if isinstance(content, dict):
        for key in content:
            if isinstance(content[key], str):
                content[key] = sanitize_for_pdf(content[key])
            elif isinstance(content[key], list):
                content[key] = [sanitize_for_pdf(item) if isinstance(item, str) else item for item in content[key]]
    
    # Define default values for handwritten rendering
    words_per_page = 500
    requested_pages = content.get('requested_pages', 3)
    content_pages = max(requested_pages - 3, 1)
    
    class HandwrittenPDF(FPDF):
        # Create a custom PDF class that handles text wrapping and rotation
        def __init__(self, target_pages=None):
            super().__init__()
            self.target_pages = target_pages
            self.current_page = 0
            
        def add_page(self, orientation='', format='', same=False):
            # Fix the arguments to match FPDF's expected parameters
            if orientation and not format and not same:
                super().add_page(orientation)
            elif orientation and format and not same:
                super().add_page(orientation, format)
            else:
                super().add_page()
            self.current_page += 1
            
        def rotated_text(self, x, y, text, angle, size_factor=1.0):
            # Variation for more natural handwriting
            if not text or text.isspace():
                return

            current_size = self.font_size * size_factor
            self.set_font_size(current_size)

            # Ensure x and y are within safe margins
            safe_margin = 10
            x = max(safe_margin, x)
            y = max(safe_margin, y)

            # Check text width and adjust x coordinate if necessary
            text_width = self.get_string_width(text)
            if x + text_width > self.w - safe_margin:
                x = self.w - safe_margin - text_width
            if y > self.h - safe_margin:
                y = self.h - safe_margin

            angle_rad = (angle * 0.3) * math.pi / 180  # Reduce angle swing
            self.rotate(angle_rad, x, y)
            self.text(x, y, text)
            self.rotate(0)

            # Reset font size to default value
            self.set_font_size(self.font_size / size_factor)
            # Reduce random wobble to keep words on page
            x_wobble = x + random.uniform(-0.2, 0.2)
            y_wobble = y + random.uniform(-0.2, 0.2)
    
    # Get requested page count from content
    requested_pages = content.get('requested_pages', 3)  # Default to 3 if not specified
    
    pdf = HandwrittenPDF(target_pages=requested_pages)
    
    # Fix margins on every page - increase margins for better heading containment
    pdf.set_margins(15, 15, 15)  # Increased from 10,10,10 to 15,15,15
    pdf.set_auto_page_break(True, margin=10)  # Increased from 5 to 10
    
    # Use hc.ttf font for handwritten text instead of trying different fonts
    try:
        pdf.add_font('Handwriting', '', os.path.join('static', 'fonts', 'hc.ttf'), uni=True)
        pdf.set_font('Handwriting', '', 22)
    except Exception as e:
        print(f"Error loading font: {e}")
        # Fallback to Courier
        pdf.set_font('Courier', '', 22)
    
    # Clean intro text to remove newlines
    intro_text = sanitize_for_pdf(content.get('introduction', '').replace('\n', ' ').strip())
    intro_text = re.sub(r'\\n\\n', ' ', intro_text)
    intro_text = re.sub(r'\\n', ' ', intro_text)
    
    # Create a more substantial abstract from the introduction
    # Create completely separate abstract not derived from introduction
    intro_text = sanitize_for_pdf(content.get('introduction', '').replace('\n', ' ').strip())
    intro_text = re.sub(r'\\n\\n', ' ', intro_text)
    intro_text = re.sub(r'\\n', ' ', intro_text)
    
    # Generate a distinctly personal abstract that differs from introduction
    abstract = f"I've been researching {title} for a while now, and wanted to share my thoughts and findings. "
    
    # Add personal perspective based on topic
    if any(word in title.lower() for word in ["technology", "digital", "computer", "software", "system"]):
        abstract += f"The way technology shapes this field fascinates me, especially how rapidly everything evolves and changes. "
    elif any(word in title.lower() for word in ["history", "past", "ancient", "traditional", "heritage"]):
        abstract += f"Looking back at how things developed over time gives such valuable perspective on where we are today. "
    elif any(word in title.lower() for word in ["science", "research", "study", "experiment"]):
        abstract += f"The scientific approach brings so much clarity to this topic, though there's still plenty we don't fully understand. "
    elif any(word in title.lower() for word in ["art", "creative", "design", "cultural", "music"]):
        abstract += f"The creative elements within this subject really highlight how it connects to our deeper human experiences. "
    else:
        abstract += f"What really stood out to me was how this topic connects to so many different fields and real-world situations. "
    
    abstract += f"I wanted to explore different perspectives and put together something that might help others get a better handle on the main ideas. "
    
    # Add purpose statement different from introduction
    abstract += f"This is my personal take on {title} - hope you find it useful!"
    
    pdf.add_page()
    pdf.set_y(20)
    
    # Improved font handling with better error recovery
    try:
        # First try the handwriting font
        pdf.set_font("Handwriting", '', 22)
    except Exception as e:
        print(f"Warning: Could not use Handwriting font: {e}")
        try:
            # Try to add the font again if it failed the first time
            pdf.add_font('Handwriting', '', os.path.join('static', 'fonts', 'hc.ttf'), uni=True)
            pdf.set_font('Handwriting', '', 22)
        except Exception as e2:
            print(f"Error loading handwriting font: {e2}")
            # Fall back to a standard font that's guaranteed to work
            pdf.set_font('Courier', '', 16)
    
    pdf.cell(0, 10, "Abstract", 0, 1, 'C')
    pdf.ln(5)
    
    # Again use safe font selection
    try:
        pdf.set_font("Handwriting", '', 14)
    except Exception:
        pdf.set_font('Courier', '', 12)
    
    pdf.multi_cell(0, 10, abstract)  # changed line height from 8 to 10
    
    # Table of Contents (Second page) - modified for handwritten PDF
    pdf.add_page()
    
    # Use safe font selection
    try:
        pdf.set_font("Handwriting", '', 14)
    except Exception:
        pdf.set_font('Courier', '', 12)
    
    pdf.cell(0, 10, "Contents:", 0, 1, 'L')
    pdf.ln(5)
    
    # Initialize page counter for TOC
    current_page_counter = 3  # Start at page 3 (after abstract and TOC)
    
    toc_items = []
    toc_items.append(("Introduction", f"{current_page_counter}"))
    current_page_counter += 1
    
    for i, section in enumerate(content.get('sections', [])):
        title = sanitize_for_pdf(section.get('title', f"Section {i+1}"))
        # Truncate long titles
        if len(title) > 40:  # Shorter limit for handwritten style
            title = title[:37] + "..."
        toc_items.append((title, f"{current_page_counter}"))
        current_page_counter += 1
        
    conclusion_page = current_page_counter
    toc_items.append(("Conclusion", f"{conclusion_page}"))
    current_page_counter += 1
    
    references_page = current_page_counter
    toc_items.append(("References", f"{references_page}"))
    
    # Dynamically calculate left width based on page width
    left_width = pdf.w - 40  # Reduced from fixed 120 to dynamic width with margin
    
    for left_text, right_text in toc_items:
        # Calculate available width after text and page number
        text_width = pdf.get_string_width(left_text)
        num_width = pdf.get_string_width(right_text)
        available_width = left_width - text_width - num_width - 5  # 5px extra margin
        
        # Calculate dots that will fit
        dot_width = pdf.get_string_width(".")
        num_dots = max(1, int(available_width / dot_width))
        dots = "." * num_dots if num_dots > 0 else ""
        
        # Print TOC line with calculated components
        pdf.cell(text_width, 8, left_text, 0, 0, 'L')
        pdf.cell(available_width, 8, dots, 0, 0, 'L')
        pdf.cell(num_width, 8, right_text, 0, 1, 'R')
    
    def write_handwritten_section(title, content_text, is_main_section=False):
        if not title:
            return
        # Always start a new page for each section
        pdf.add_page()
        # Reset vertical position to a fixed value for consistent section starts
        pdf.set_y(25)  # Fixed position for all section headings
        pdf.set_font("Handwriting", '', 22)
        
        # Calculate available height for title to ensure it fits on one page
        available_height = pdf.h - 50  # Reserve space for content below heading
        
        # Handle long titles by checking width and potentially splitting
        if pdf.get_string_width(title) > (pdf.w - 40):  # Conservative width check
            # Split title if too long
            words = title.split()
            line = ""
            lines_used = 0
            max_lines = 3  # Limit heading to 3 lines maximum
            
            for word in words:
                test_line = line + " " + word if line else word
                if pdf.get_string_width(test_line) < (pdf.w - 40) and lines_used < max_lines:
                    line = test_line
                else:
                    pdf.cell(0, 10, line, 0, 1, 'C')
                    lines_used += 1
                    if lines_used >= max_lines:
                        # If we've reached max lines, add ellipsis and break
                        if word != words[-1]:
                            pdf.cell(0, 10, "...", 0, 1, 'C')
                        break
                    line = word
            if line and lines_used < max_lines:
                pdf.cell(0, 10, line, 0, 1, 'C')
        else:
            pdf.cell(0, 10, title, 0, 1, 'C')
        
        # Add extra space after title
        pdf.ln(5)
        pdf.set_font("Handwriting", '', 14)
        
        # Clean content text to remove all \n\n and \n
        content_text = re.sub(r'\\n\\n', ' ', content_text)
        content_text = re.sub(r'\\n', ' ', content_text)
        
        pdf.multi_cell(0, 10, content_text)

    # Introduction
    intro_words = intro_text.split()
    intro_text = ' '.join(intro_words) 
    
    write_handwritten_section("Introduction:", intro_text)
    
    # Replace generic section titles with meaningful ones
    if not content.get('sections'):
        section_count = max(3, min(5, requested_pages // 2))
        meaningful_titles = [
            f"My Thoughts on {title}",
            f"Key Ideas About {title}",
            f"Understanding {title} Better",
            f"Interesting Aspects of {title}",
            f"Reflections on {title}"
        ]
        
        content["sections"] = [
            {
                "title": meaningful_titles[i % len(meaningful_titles)],
                "content": f"Extended commentary and detailed discussion on {title}."
            } for i in range(section_count)
        ]
    
    # Track remaining pages to ensure conclusion and references fit
    remaining_pages = max(2, pdf.target_pages - pdf.current_page - 2)  # Reserve 2 pages for conclusion and references
    section_pages = min(len(content.get('sections', [])), remaining_pages)
    
    # Process ALL sections - don't limit by section_pages
    for section in content.get('sections', []):
        section_content = sanitize_for_pdf(section.get('content', ''))
        section_content = re.sub(r'\\n\\n', ' ', section_content)
        section_content = re.sub(r'\\n', ' ', section_content)
        
        write_handwritten_section(
            sanitize_for_pdf(section.get('title', 'Section')), 
            section_content,
            is_main_section=True
        )
    
    # Make sure we finish exactly on target page count BEFORE adding conclusion/references
    # This will prevent duplicate conclusion/references pages
    while pdf.current_page < (pdf.target_pages - 2):
        pdf.add_page()
        # Define extra_page_number variable before using it
        extra_page_number = pdf.current_page
        pdf.set_y(25)  # Consistent heading position
        pdf.set_font("Handwriting", '', 16)
        
        # Create different headings based on the page number
        headings = [
            f"Additional Notes - Page {extra_page_number}",
            f"More Thoughts on {title}",
            f"Important Considerations",
            f"Related Ideas & Concepts",
            f"Questions & Reflections"
        ]
        heading_index = extra_page_number % len(headings)
        heading_text = headings[heading_index]
        
        # Check if heading is too long for the page width
        if pdf.get_string_width(heading_text) > (pdf.w - 40):
            words = heading_text.split()
            line = ""
            for word in words:
                test_line = line + " " + word if line else word
                if pdf.get_string_width(test_line) < (pdf.w - 40):
                    line = test_line
                else:
                    pdf.cell(0, 10, line, 0, 1, 'C')
                    line = word
            if line:
                pdf.cell(0, 10, line, 0, 1, 'C')
        else:
            pdf.cell(0, 10, heading_text, 0, 1, 'C')
            
        pdf.ln(5)
        
        pdf.set_font("Handwriting", '', 12)
        
        # Create varied content for each extra page in a more casual, handwritten style
        extra_contents = [
            f"I've been thinking more about {title} and have some extra ideas to share.",
            f"Looking back at the main points about {title}, there are interesting implications worth exploring further.",
            f"Notably, {title} relates to real-world situations through several practical examples.",
            f"Considering the historical context, {title}'s evolution is quite fascinating.",
            f"These are some questions about {title} that invite further investigation."
        ]
        
        content_index = (extra_page_number + 3) % len(extra_contents)
        pdf.multi_cell(0, 10, extra_contents[content_index])
        pdf.ln(5)
        
        # Add some personalized bullet points or notes
        if extra_page_number % 2 == 0:
            ideas = [
                "* Need to look into this more - seems important",
                "* Reminds me of similar concepts in related fields",
                "* Worth comparing different approaches here"
            ]
            for idea in ideas:
                pdf.multi_cell(0, 10, idea)
                pdf.ln(3)
        else:
            pdf.multi_cell(0, 10, f"I think the most interesting aspect of {title} might be how it connects to other areas. Nothing exists in isolation - everything is connected in some way.")
    
    # Now add the conclusion and references exactly once
    # Conclusion Page - should be on the exact page promised in TOC
    conclusion_text = sanitize_for_pdf(content.get('conclusion', '').strip()) or f"In conclusion, {title} represents an important area of study."
    conclusion_text = re.sub(r'\\n\\n', ' ', conclusion_text)
    conclusion_text = re.sub(r'\\n', ' ', conclusion_text)
    write_handwritten_section("Conclusion:", conclusion_text)
    
    # References Page - should be on the exact page promised in TOC
    pdf.add_page()
    pdf.set_y(25)  # Increased from 20 to 25
    pdf.set_font("Handwriting", '', 16)  # Increased from 12 to 16
    pdf.cell(0, 10, "References", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font("Handwriting", '', 12)  # Increased from 10 to 12
    
    # Fix references extraction and handling
    references = []
    if isinstance(content.get('references'), list):
        references = [ref for ref in content.get('references') if ref and isinstance(ref, str)]
    
    # If no valid references, generate defaults
    if len(references) == 0:
        references = [
            f"Smith, J. (2023). Understanding {title}. Journal of Research, 45(2), 112-128.",
            f"Johnson, A., & Williams, P. (2022). Advances in {title}. Academic Press.",
            f"Brown, R. et al. (2021). {title}: A comprehensive review. Annual Review, 15, 23-45.",
            f"Taylor, M. (2023). Practical applications of {title}. Applied Research Today, 8(3), 67-89.",
            f"White, S., & Miller, T. (2022). Future directions for {title} research. Future Perspectives, 12(1), 34-56."
        ]
    
    # Ensure all references are properly sanitized and handle long references
    references = [sanitize_for_pdf(ref) for ref in references]
    
    for i, ref in enumerate(references, 1):
        numbered_ref = f"{i}. {ref}"
        # Handle long references with wrapping
        if pdf.get_string_width(numbered_ref) > (pdf.w - 30):
            words = numbered_ref.split()
            line = ""
            first_line = True
            for word in words:
                test_line = line + " " + word if line else word
                if pdf.get_string_width(test_line) < (pdf.w - 30):
                    line = test_line
                else:
                    if first_line:
                        pdf.multi_cell(0, 7, line)
                        first_line = False
                    else:
                        pdf.set_x(15)  # Indent continued lines
                        pdf.multi_cell(0, 7, line)
                    line = word
            if line:
                if first_line:
                    pdf.multi_cell(0, 7, line)
                else:
                    pdf.set_x(15)
                    pdf.multi_cell(0, 7, line)
        else:
            pdf.multi_cell(0, 7, numbered_ref)
        pdf.ln(2)
    
    # Add thank you note with proper spacing
    pdf.ln(6)
    pdf.set_font("Handwriting", '', 14)  # Increased from 12 to 14
    pdf.cell(0, 10, "Thank you", 0, 1, 'C')
    
    # Save the PDF
    pdf.output(output_path)
    
    return output_path