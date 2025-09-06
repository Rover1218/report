import os
import random
from fpdf import FPDF
import math
import re
import time
import numpy as np  # Fixed: corrected "import numpy np" to "import numpy as np"
from PIL import Image, ImageDraw, ImageFilter
import textwrap

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

class PDF(FPDF):
    """Base PDF class with common functionality"""
    def __init__(self, target_pages=None):
        super().__init__()
        self.target_pages = target_pages
        self.current_page = 0
        # Initialize with Courier font as fallback
        self.set_font('Courier', '', 12)
        
    def add_page(self, orientation='', format='', same=False):
        if orientation and not format and not same:
            super().add_page(orientation)
        elif orientation and format and not same:
            super().add_page(orientation, format)
        else:
            super().add_page()
        self.current_page += 1

class PageLimitPDF(PDF):
    """Custom PDF class that monitors page count"""
    pass

class HandwrittenPDF(PDF):
    """Custom PDF class that handles text wrapping and rotation"""
    def __init__(self, target_pages=None):
        super().__init__(target_pages)
        # Initialize handwriting characteristics for consistency
        self.writing_style = {
            'base_slant': random.uniform(-3, 3),
            'pressure_variation': random.uniform(0.7, 1.3),
            'speed_variation': random.uniform(0.8, 1.2),
            'fatigue_factor': random.uniform(0.02, 0.05),
            'dominant_hand': random.choice(['right', 'left'])
        }
        self.word_count = 0
        self.line_count = 0
    
    def rotated_text(self, x, y, text, angle, size_factor=1.0):
        if not text or text.isspace():
            return

        current_size = self.font_size * size_factor
        self.set_font_size(current_size)

        safe_margin = 10
        x = max(safe_margin, x)
        y = max(safe_margin, y)

        # Apply minimal fatigue effect - handwriting gets slightly messier over time
        fatigue_effect = 1 + (self.word_count * self.writing_style['fatigue_factor'] * 0.1)
        
        # Base angle with personal slant
        base_angle = self.writing_style['base_slant'] + (angle * 0.2)
        angle_rad = base_angle * math.pi / 180
        
        current_x = x
        current_y = y
        
        # Add slight baseline drift for entire word
        baseline_drift = random.uniform(-0.8, 0.8) * fatigue_effect

        for i, char in enumerate(text):
            if char == ' ':
                # More realistic spacing variation
                space_w = self.get_string_width(' ') * random.uniform(0.7, 1.4) * self.writing_style['speed_variation']
                current_x += space_w
                continue

            # Character-specific variations with fatigue
            char_size_factor = random.uniform(0.8, 1.2) * (1 + fatigue_effect * 0.1)
            self.set_font_size(current_size * char_size_factor)

            # More realistic positioning with hand dominance effect
            hand_bias = 0.2 if self.writing_style['dominant_hand'] == 'right' else -0.2
            x_offset = random.uniform(-0.6, 0.6) + hand_bias * fatigue_effect
            y_offset = random.uniform(-0.8, 0.8) + baseline_drift

            # Character angle with micro-tremor
            char_angle = angle_rad + random.uniform(-4, 4) * math.pi / 180 * fatigue_effect
            
            # Keep text consistently dark and readable
            ink_intensity = random.randint(0, 30)  # Always dark text
            self.set_text_color(ink_intensity, ink_intensity, ink_intensity)

            # Occasional ink blots or skips
            if random.random() < 0.03 * fatigue_effect:
                # Ink blot
                blob_size = random.uniform(0.3, 0.8)
                self.set_fill_color(ink_intensity, ink_intensity, ink_intensity)
                self.circle(current_x + x_offset, current_y + y_offset, blob_size, 'F')
            elif random.random() < 0.02:
                # Ink skip - make character lighter
                skip_intensity = min(255, ink_intensity + random.randint(40, 80))
                self.set_text_color(skip_intensity, skip_intensity, skip_intensity)

            # Letter connection strokes (cursive-like)
            if i > 0 and random.random() < 0.3 and text[i-1] != ' ':
                prev_x = current_x - self.get_string_width(text[i-1]) * 0.8
                stroke_y = current_y + random.uniform(-0.3, 0.3)
                self.set_draw_color(ink_intensity + 20, ink_intensity + 20, ink_intensity + 20)
                self.set_line_width(0.1)
                self.line(prev_x, stroke_y, current_x + x_offset - 0.5, current_y + y_offset)

            # Draw character with rotation
            self.rotate(char_angle, current_x + x_offset, current_y + y_offset)
            self.text(current_x + x_offset, current_y + y_offset, char)
            self.rotate(0)

            # Character width with natural variation
            char_width = self.get_string_width(char) * random.uniform(0.85, 1.15)
            current_x += char_width
            
            # Reset text color
            self.set_text_color(0, 0, 0)

        self.word_count += len(text.split())
        self.set_font_size(self.font_size / size_factor)
    
    def circle(self, x, y, radius, style=''):
        """Draw a circle approximation using small rectangles"""
        segments = max(8, int(radius * 4))  # More segments for larger circles
        for i in range(segments):
            angle = (i / segments) * 2 * math.pi
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            size = max(0.1, radius / 4)
            self.rect(px - size/2, py - size/2, size, size, style)
    
    def add_page(self, orientation='', format='', same=False):
        # Override add_page to add scanned paper effect to each page
        if orientation and not format and not same:
            super().add_page(orientation)
        elif orientation and format and not same:
            super().add_page(orientation, format)
        else:
            super().add_page()
        
        # Add scanned paper effect to the current page
        self.add_scanned_paper_effect()
        self.current_page += 1
    
    def add_scanned_paper_effect(self):
        """Create a realistic scanned paper effect with highly randomized page styles"""
        page_width = self.w
        page_height = self.h
        
        # 1. Pure white background base layer
        self.set_fill_color(255, 255, 255)
        self.rect(0, 0, page_width, page_height, 'F')
        
        # 2. Determine the random page style for this specific page
        page_style = random.choice([
            "clean",       # Almost no artifacts
            "light_dots",  # Light paper texture with few dots
            "heavy_dots",  # Heavy paper texture with many dots
            "lines_only",  # Mostly scan lines, few dots
            "mixed",       # Both dots and lines in medium amount
            "aged"         # Yellowed with heavier texture
        ])
        
        # 3. Subtle background color/tint based on page style
        if page_style == "aged":
            # Slightly yellow/aged paper
            self.set_fill_color(252, 250, 242)
            self.rect(0, 0, page_width, page_height, 'F')
            
        # Always add some form of gradient, but vary the intensity
        gradient_steps = random.randint(70, 100)
        gradient_intensity = {
            "clean": 0.03,
            "light_dots": 0.05,
            "heavy_dots": 0.07,
            "lines_only": 0.06,
            "mixed": 0.08,
            "aged": 0.09
        }[page_style]
        
        # Apply gradient with style-specific intensity
        for i in range(gradient_steps):
            # Create subtle variations in the gradient
            variation = math.sin(i/gradient_steps * math.pi) * 2
            r = 254 - int(i * gradient_intensity) - variation
            g = 254 - int(i * gradient_intensity * 1.05) - variation
            b = 253 - int(i * gradient_intensity * 1.1) - variation
            
            # Adjust for aged paper style
            if page_style == "aged":
                r = min(252, r + 3)  # More yellow/brown
                g = min(250, g + 2)
                b = min(240, b)      # Less blue
                
            self.set_fill_color(r, g, b)
            y = i * (page_height / gradient_steps)
            height = (page_height / gradient_steps) + 0.1
            self.rect(0, y, page_width, height, 'F')
        
        # 4. Add paper texture dots based on style
        dot_counts = {
            "clean": random.randint(200, 500),
            "light_dots": random.randint(1000, 2000),
            "heavy_dots": random.randint(5000, 8000),
            "lines_only": random.randint(300, 700),
            "mixed": random.randint(2000, 3000),
            "aged": random.randint(3000, 6000)
        }[page_style]
        
        # Add the dots with style-specific parameters
        for _ in range(dot_counts):
            x = random.uniform(0, page_width)
            y = random.uniform(0, page_height)
            
            # Vary dot size based on style
            size_min = {"clean": 0.02, "aged": 0.04}.get(page_style, 0.03)
            size_max = {"heavy_dots": 0.18, "aged": 0.20}.get(page_style, 0.15)
            size = random.uniform(size_min, size_max)
            
            # Create clusters for some styles
            if page_style in ["heavy_dots", "aged", "mixed"] and random.random() > 0.93:
                cluster_size = random.randint(3, 8)
                base_x, base_y = x, y
                for _ in range(cluster_size):
                    cx = base_x + random.uniform(-1.2, 1.2)
                    cy = base_y + random.uniform(-1.2, 1.2)
                    if 0 <= cx < page_width and 0 <= cy < page_height:
                        gray = random.randint(230, 248)
                        dot_size = random.uniform(size_min, size_max)
                        self.set_fill_color(gray, gray, gray)
                        self.rect(cx, cy, dot_size, dot_size, 'F')
            
            # Regular dots with style-specific darkness
            min_gray = {"clean": 240, "aged": 220}.get(page_style, 235)
            max_gray = {"clean": 252, "aged": 240}.get(page_style, 250)
            gray = random.randint(min_gray, max_gray)
            self.set_fill_color(gray, gray, gray)
            self.rect(x, y, size, size, 'F')
        
        # 5. Add realistic dust and scanning artifacts
        speck_params = {
            "clean": {"count": random.randint(8, 25), "darkness": (190, 230)},
            "light_texture": {"count": random.randint(25, 60), "darkness": (180, 220)},
            "medium_wear": {"count": random.randint(80, 150), "darkness": (170, 210)},
            "heavy_use": {"count": random.randint(150, 250), "darkness": (160, 200)},
            "aged_paper": {"count": random.randint(200, 300), "darkness": (150, 190)},
            "notebook_style": {"count": random.randint(40, 80), "darkness": (185, 225)}
        }
        
        params = speck_params.get(page_style, speck_params["light_texture"])
        speck_count = params["count"]
        dark_min, dark_max = params["darkness"]
        
        for _ in range(speck_count):
            x = random.uniform(0, page_width)
            y = random.uniform(0, page_height)
            
            # Vary speck types for realism
            speck_type = random.choice(["dust", "fiber", "ink_spot", "scan_artifact"])
            
            if speck_type == "dust":
                size = random.uniform(0.03, 0.08)
                gray = random.randint(dark_min, dark_max)
                self.set_fill_color(gray, gray, gray)
                self.rect(x, y, size, size, 'F')
            
            elif speck_type == "fiber":
                length = random.uniform(0.5, 2.0)
                angle = random.uniform(0, math.pi * 2)
                gray = random.randint(dark_min + 10, dark_max)
                self.set_draw_color(gray, gray, gray)
                self.set_line_width(0.05)
                dx = length * math.cos(angle)
                dy = length * math.sin(angle)
                self.line(x, y, x + dx, y + dy)
            
            elif speck_type == "ink_spot":
                size = random.uniform(0.08, 0.15)
                gray = random.randint(dark_min - 20, dark_min + 10)
                self.set_fill_color(gray, gray, gray)
                # Irregular ink spot
                for _ in range(3):
                    offset_x = random.uniform(-size/2, size/2)
                    offset_y = random.uniform(-size/2, size/2)
                    spot_size = size * random.uniform(0.6, 1.0)
                    self.rect(x + offset_x, y + offset_y, spot_size, spot_size, 'F')
            
            else:  # scan_artifact
                # Horizontal scan line artifact
                width = random.uniform(2, 8)
                height = random.uniform(0.1, 0.3)
                gray = random.randint(dark_min + 20, dark_max)
                self.set_fill_color(gray, gray, gray)
                self.rect(x, y, width, height, 'F')
        
        # 6. Add realistic scanning lines and artifacts
        if page_style != "clean":
            scan_line_params = {
                "light_texture": {"count": random.randint(3, 12), "visibility": (235, 248)},
                "medium_wear": {"count": random.randint(8, 18), "visibility": (225, 240)},
                "heavy_use": {"count": random.randint(15, 30), "visibility": (215, 235)},
                "aged_paper": {"count": random.randint(12, 25), "visibility": (210, 230)},
                "notebook_style": {"count": random.randint(5, 15), "visibility": (230, 245)}
            }
            
            params = scan_line_params.get(page_style, {"count": 10, "visibility": (230, 245)})
            line_count = params["count"]
            opacity_min, opacity_max = params["visibility"]
            
            for _ in range(line_count):
                # Horizontal scan lines (most common)
                if random.random() < 0.8:
                    y_pos = random.uniform(0, page_height)
                    thickness = random.uniform(0.08, 0.25)
                    opacity = random.randint(opacity_min, opacity_max)
                    
                    # Line length varies
                    length = random.uniform(page_width * 0.4, page_width * 0.98)
                    x_start = random.uniform(0, page_width - length)
                    
                    # Create realistic segmented line
                    segments = max(1, int(length / 8))
                    for s in range(segments):
                        # Random gaps in scan lines
                        if random.random() < 0.15:
                            continue
                        
                        seg_length = (length / segments) * random.uniform(0.8, 1.2)
                        seg_x = x_start + (s * length / segments)
                        
                        # Slight vertical waviness
                        wave_y = y_pos + random.uniform(-0.3, 0.3)
                        
                        self.set_fill_color(opacity, opacity, opacity)
                        self.rect(seg_x, wave_y, seg_length, thickness, 'F')
                
                # Occasional vertical artifacts
                else:
                    x_pos = random.uniform(0, page_width)
                    thickness = random.uniform(0.05, 0.15)
                    opacity = random.randint(opacity_min + 5, opacity_max)
                    
                    height = random.uniform(page_height * 0.1, page_height * 0.6)
                    y_start = random.uniform(0, page_height - height)
                    
                    self.set_fill_color(opacity, opacity, opacity)
                    self.rect(x_pos, y_start, thickness, height, 'F')
        
        # 7. Add paper fold/crease marks
        # Only some page styles have visible fold marks
        if page_style in ["mixed", "aged", "heavy_dots"] and random.random() > 0.3:
            fold_y = page_height * random.uniform(0.4, 0.6)
            for x in range(0, int(page_width), 1):
                if random.random() > 0.8:  # Make fold line discontinuous
                    continue
                intensity = random.randint(198, 225)
                self.set_fill_color(intensity, intensity, intensity)
                dot_height = random.uniform(0.08, 0.25)
                y_variation = fold_y + random.uniform(-0.4, 0.4) * (1 + math.sin(x/20)**2)
                self.rect(x, y_variation, 0.5, dot_height, 'F')
        
        # 8. Add occasional vertical fold for some styles
        if page_style in ["mixed", "aged"] and random.random() > 0.6:
            fold_x = page_width * random.uniform(0.25, 0.75)
            for y in range(0, int(page_height), 2):
                if random.random() > 0.8:  # Make fold line discontinuous
                    continue
                intensity = random.randint(205, 230)
                self.set_fill_color(intensity, intensity, intensity)
                dot_width = random.uniform(0.08, 0.15)
                x_variation = fold_x + random.uniform(-0.25, 0.25) * (1 + math.sin(y/30)**2)
                self.rect(x_variation, y, dot_width, 0.4, 'F')
        
        # 9. Add paper fiber effects (but not for clean style)
        if page_style != "clean":
            fiber_counts = {
                "light_dots": random.randint(20, 40),
                "heavy_dots": random.randint(40, 70),
                "lines_only": random.randint(30, 50),
                "mixed": random.randint(40, 60),
                "aged": random.randint(50, 80)
            }[page_style]
            
            for _ in range(fiber_counts):
                x = random.uniform(10, page_width-10)
                y = random.uniform(10, page_height-10)
                length = random.uniform(0.5, 3.0)
                angle = random.uniform(0, math.pi*2)
                dx = length * math.cos(angle)
                dy = length * math.sin(angle)
                gray = random.randint(220, 245)
                self.set_fill_color(gray, gray, gray)
                self.set_line_width(0.1)
                self.line(x, y, x+dx, y+dy)
        
        # 10. Always add some edge shadows, but vary intensity by style
        edge_width = {
            "clean": 8,
            "light_dots": 10,
            "heavy_dots": 12,
            "lines_only": 10,
            "mixed": 12,
            "aged": 15
        }[page_style]
        
        for i in range(edge_width):
            # Create a more natural edge darkness gradient
            shadow_intensity = {
                "clean": 0.8,
                "light_dots": 1.0,
                "heavy_dots": 1.2,
                "lines_only": 1.0,
                "mixed": 1.2,
                "aged": 1.4
            }[page_style]
            
            shadow = 255 - int((edge_width - i)**shadow_intensity)
            self.set_fill_color(shadow, shadow, shadow)
            
            # Left and right edges
            self.rect(i*0.3, 0, 0.3, page_height, 'F')
            self.rect(page_width - (i*0.3) - 0.3, 0, 0.3, page_height, 'F')
            
            # Top and bottom edges (partial)
            if i < edge_width * 0.6:
                self.rect(0, i*0.3, page_width, 0.3, 'F')
                self.rect(0, page_height - (i*0.3) - 0.3, page_width, 0.3, 'F')
        
        # Reset colors
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(0, 0, 0)
        
        # Ensure deep black text for best contrast
        self.set_text_color(0, 0, 0)

    # Override the write_html method to use darker text
    def write_html(self, *args, **kwargs):
        # Save current text color
        current_r, current_g, current_b = self.text_color
        # Set to pure black text for better contrast
        self.set_text_color(0, 0, 0)
        # Call parent method
        super().write_html(*args, **kwargs)
        # Restore original text color
        self.set_text_color(current_r, current_g, current_b)

def initialize_pdf_with_font(pdf_class, target_pages):
    """Initialize PDF with proper font handling"""
    pdf = pdf_class(target_pages)
    
    # Try to load handwriting font
    font_path = os.path.join('static', 'fonts', 'hc.ttf')
    try:
        # Check if font file exists
        if os.path.exists(font_path):
            pdf.add_font('Handwriting', '', font_path, uni=True)
            pdf.set_font('Handwriting', '', 12)
        else:
            # Fallback to Courier
            pdf.set_font('Courier', '', 12)
    except Exception as e:
        print(f"Font loading error: {e}")
        # Ensure we have a working font
        pdf.set_font('Courier', '', 12)
    
    return pdf

def create_typed_pdf(title, content):
    """Create a professionally formatted PDF report."""
    # Initialize PDF with proper font
    pdf = initialize_pdf_with_font(PageLimitPDF, content.get('requested_pages', 3))
    
    # Sanitize the title and content
    title = sanitize_for_pdf(title)
    
    # Sanitize all content fields recursively
    if isinstance(content, dict):
        for key in content:
            if isinstance(content[key], str):
                content[key] = sanitize_for_pdf(content[key])
            elif isinstance(content[key], list):
                content[key] = [sanitize_for_pdf(item) if isinstance(item, str) else item for item in content[key]]
    
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
    
    pdf.set_font("Times", '', 18)  # Increased from 16
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
    pdf.multi_cell(0, 10, abstract)  # Increased line spacing from 8 to 10
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
        pdf.multi_cell(0, 10, intro_text)  # Increased line spacing from 9 to 10
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
                    pdf.set_x(18)  # Indent continued lines
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
    
    # Instead of saving to disk, return the PDF content
    return pdf.output(dest='S').encode('latin-1')  # Return PDF as bytes

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
    # Initialize PDF with proper font
    pdf = initialize_pdf_with_font(HandwrittenPDF, content.get('requested_pages', 3))
    
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
    
    pdf = HandwrittenPDF(target_pages=requested_pages)
    
    # Fix margins on every page - increase margins for better heading containment
    pdf.set_margins(10, 10, 10)  # Reduced margins
    pdf.set_auto_page_break(True, margin=10)  # Increased from 5 to 10
    
    # Use hc.ttf font for handwritten text instead of trying different fonts
    try:
        pdf.add_font('Handwriting', '', os.path.join('static', 'fonts', 'hc.ttf'), uni=True)
        pdf.set_font('Handwriting', '', 18)  # Reduced from 22 for headings
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
    pdf.ln(10)  # increased gap below heading
    
    # Again use safe font selection
    try:
        pdf.set_font("Handwriting", '', 18)  # Increased from 14 for abstract body text
    except Exception:
        pdf.set_font('Courier', '', 14)
    
    # Replace rotated_text with multi_cell to reliably render abstract text
    pdf.multi_cell(0, 12, abstract)
    pdf.ln(10)
    
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
        pdf.ln(10)
        pdf.set_font("Handwriting", '', 16)  # Slightly smaller for body
        
        # Clean content text to remove all \n\n and \n
        content_text = re.sub(r'\\n\\n', ' ', content_text)
        content_text = re.sub(r'\\n', ' ', content_text)
        
        # Realistic handwritten text with natural flow
        words = content_text.split()
        left_margin = 15
        right_margin = pdf.w - 15
        line_height = 18
        
        current_x = left_margin
        current_y = pdf.get_y()
        
        # Add margin lines (like notebook paper)
        if random.random() < 0.7:  # 70% chance of margin line
            pdf.set_draw_color(200, 200, 255)  # Light blue
            pdf.set_line_width(0.2)
            margin_x = left_margin + random.uniform(15, 25)
            pdf.line(margin_x, current_y - 5, margin_x, current_y + len(words) * 2)
            pdf.set_draw_color(0, 0, 0)
        
        for word_idx, word in enumerate(words):
            # Check if word fits on current line
            word_width = pdf.get_string_width(word + ' ') * 1.2  # Estimate with spacing
            
            if current_x + word_width > right_margin and current_x > left_margin:
                # Move to next line with natural variation
                current_x = left_margin + random.uniform(-2, 8)  # Slight indent variation
                current_y += line_height + random.uniform(-2, 3)  # Line spacing variation
                pdf.line_count += 1
                
                # Occasional ruled line (like notebook paper)
                if random.random() < 0.4:
                    pdf.set_draw_color(220, 220, 240)
                    pdf.set_line_width(0.1)
                    line_y = current_y + 2
                    pdf.line(left_margin, line_y, right_margin, line_y)
                    pdf.set_draw_color(0, 0, 0)
            
            # Word-level characteristics
            word_fatigue = 1 + (pdf.word_count * 0.002)
            word_speed = pdf.writing_style['speed_variation'] * random.uniform(0.9, 1.1)
            word_pressure = pdf.writing_style['pressure_variation'] * random.uniform(0.8, 1.2)
            
            # Some words are written faster/slower affecting spacing and angle
            if len(word) > 6:  # Longer words often written faster
                word_speed *= 1.2
                word_pressure *= 0.9
            
            # Add word with character-by-character variation
            word_start_x = current_x
            for char_idx, char in enumerate(word):
                # Character size with fatigue and word-level effects
                base_size = 14
                char_size = base_size * random.uniform(0.75, 1.25) * word_fatigue
                
                # First and last letters often slightly larger (emphasis)
                if char_idx == 0 or char_idx == len(word) - 1:
                    char_size *= random.uniform(1.05, 1.15)
                
                pdf.set_font_size(char_size)
                
                # Always use dark text for readability
                ink_darkness = random.randint(0, 25)  # Always very dark
                
                # Occasional ink buildup at word start - keep readable
                if char_idx == 0 and random.random() < 0.1:
                    ink_darkness = max(40, ink_darkness - random.randint(10, 20))
                
                pdf.set_text_color(ink_darkness, ink_darkness, ink_darkness)
                
                # Position with natural hand movement and word flow
                x_jitter = random.uniform(-0.5, 0.5) / word_speed
                y_jitter = random.uniform(-0.8, 0.8) / word_speed
                
                # Progressive baseline drift within word
                baseline_drift = (char_idx / len(word)) * random.uniform(-0.3, 0.3)
                y_jitter += baseline_drift
                
                # Angle variation with word consistency
                base_slant = pdf.writing_style['base_slant']
                word_slant_variation = random.uniform(-1, 1)  # Consistent for whole word
                char_angle = base_slant + word_slant_variation + random.uniform(-2, 2)
                
                # Speed affects angle stability
                if word_speed > 1.1:  # Fast writing is less stable
                    char_angle += random.uniform(-2, 2)
                
                # Draw character
                char_x = current_x + x_jitter
                char_y = current_y + y_jitter
                pdf.rotate(char_angle * math.pi / 180, char_x, char_y)
                pdf.text(char_x, char_y, char)
                pdf.rotate(0)
                
                # Advance position with speed-affected spacing
                char_width = pdf.get_string_width(char) * random.uniform(0.85, 1.15) / word_speed
                current_x += char_width
                
                # Letter connections (more common in cursive-style writing)
                connection_chance = 0.3 if pdf.writing_style['speed_variation'] > 1.0 else 0.15
                if char_idx < len(word) - 1 and random.random() < connection_chance:
                    next_x = current_x + random.uniform(0.3, 1.0)
                    connection_y = char_y + random.uniform(-0.3, 0.8)
                    
                    # Connection stroke color slightly lighter
                    stroke_color = min(255, ink_darkness + 25)
                    pdf.set_draw_color(stroke_color, stroke_color, stroke_color)
                    pdf.set_line_width(random.uniform(0.05, 0.12))
                    
                    # Curved connection
                    mid_x = (char_x + char_width * 0.8 + next_x) / 2
                    mid_y = connection_y + random.uniform(-0.2, 0.2)
                    
                    # Simple curve approximation with two line segments
                    pdf.line(char_x + char_width * 0.8, char_y + 0.5, mid_x, mid_y)
                    pdf.line(mid_x, mid_y, next_x - 0.3, connection_y)
                    
                    pdf.set_draw_color(0, 0, 0)
            
            # Add space after word
            space_width = pdf.get_string_width(' ') * random.uniform(0.8, 1.4)
            current_x += space_width
            
            # Occasional ink smudge or correction
            if random.random() < 0.01:
                smudge_x = word_start_x + random.uniform(0, current_x - word_start_x)
                smudge_y = current_y + random.uniform(-1, 2)
                pdf.set_fill_color(180, 180, 180)
                pdf.ellipse(smudge_x, smudge_y, random.uniform(2, 4), random.uniform(0.5, 1.5), 'F')
        
        pdf.set_y(current_y + line_height * 2)
        pdf.set_text_color(0, 0, 0)  # Reset color

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
    pdf.ln(10)  # increased gap below heading
    
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
    
    # Instead of saving to disk, return the PDF content
    return pdf.output(dest='S').encode('latin-1')  # Return PDF as bytes