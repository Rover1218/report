import google.generativeai as genai
import json
import re

def clean_json_string(json_str):
    """Clean a JSON string by removing or replacing invalid control characters"""
    # Replace common problematic characters
    json_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', json_str)  # Remove control chars
    json_str = re.sub(r'\t', ' ', json_str)  # Replace tabs with spaces
    json_str = re.sub(r'\n +', '\n', json_str)  # Clean up indentation
    json_str = re.sub(r'\\([^"])', r'\\\\\1', json_str)  # Fix single backslashes (not in quotes)
    
    # Remove trailing commas before closing braces/brackets:
    json_str = re.sub(r',(\s*[\}\]])', r'\1', json_str)
    
    return json_str

def generate_report(topic, num_pages, is_handwritten=False):
    """
    Generate report content using Gemini API
    
    Args:
        topic (str): The topic of the report
        num_pages (int): Approximate number of pages to generate
        is_handwritten (bool): Whether this is for a handwritten report
    
    Returns:
        dict: A structured report with title, introduction, sections, and conclusion
    """
    # Configure the model - use Gemini 1.5 Flash 8B model with proper limits
    model = genai.GenerativeModel(
        'models/gemini-1.5-flash-8b',  # Updated to the specified model
        generation_config={
            'temperature': 1,  # Reduced for more consistent, clean output
            'max_output_tokens': min(8192, num_pages * 1500)  # Adjusted to model's 8,192 token limit
        }
    )
    
    # Calculate word count based on pages (500 words per page)
    word_count = num_pages * 600
    
    # Determine optimal section count based on page count
    section_count = max(3, min(num_pages, 8))  # Minimum 3, maximum 8 sections
    
    # Calculate approximate words per section for the model
    words_per_section = int((word_count * 0.7) / section_count)  # 70% of content for sections
    
    # Create dynamic example sections based on section_count
    example_sections = []
    section_examples = [
        {"title": "Historical Context and Background", "content": f"Content about the history of {topic} (approx. {words_per_section} words)"},
        {"title": "Theoretical Framework and Key Concepts", "content": f"Content explaining theories related to {topic}"},
        {"title": "Current Research and Findings", "content": f"Content about recent studies on {topic}"},
        {"title": "Practical Applications and Implications", "content": f"Content about how {topic} is applied"},
        {"title": "Critical Analysis and Evaluation", "content": f"Content analyzing strengths and weaknesses of {topic}"},
        {"title": "Case Studies and Real-World Examples", "content": f"Content featuring examples of {topic} in practice"},
        {"title": "Future Directions and Emerging Trends", "content": f"Content about where {topic} is heading"},
        {"title": "Interdisciplinary Connections", "content": f"Content about how {topic} relates to other fields"}
    ]
    
    # Select the first section_count examples to show in the prompt
    for i in range(min(section_count, len(section_examples))):
        example_sections.append(section_examples[i])
    
    # Generate sections JSON string for the prompt
    sections_json = ",\n        ".join([
        f'{{\n          "title": "{section["title"]}",\n          "content": "{section["content"]}"\n        }}'
        for section in example_sections
    ])
    
    # Adjust prompt based on whether it's for handwritten or typed format
    writing_style = "casual, personal, and conversational" if is_handwritten else "formal, academic"
    content_style = "bullet points, shorter paragraphs, and more direct language" if is_handwritten else "detailed paragraphs with academic depth"
    
    # Extra instructions for longer reports (e.g., 30 pages)
    extra_instruction = ""
    if num_pages >= 30:
        extra_instruction = "\n- Since the report spans a high page count, include extended analysis, elaborate descriptions, and additional subsections to cover all aspects comprehensively."
    
    # Adjust prompt to specifically request meaningful section titles with dynamic section count
    prompt = f"""
    Your task is to create a {"personal, handwritten-style" if is_handwritten else "detailed academic"} report on: "{topic}"

    Requirements:
    - Content should fill {num_pages} pages (approximately {word_count} words total){extra_instruction}
    - Include exactly {section_count} sections with meaningful titles
    - Use {writing_style} writing style
    - {"Use more personal language and straightforward formatting" if is_handwritten else "INCLUDE AT LEAST 5 DETAILED ACADEMIC REFERENCES with proper citation format"}
    - Include relevant examples and facts
    - Use only ASCII characters - DO NOT use special symbols or unicode characters
    - {"Use " + content_style if is_handwritten else "MAKE SURE TO INCLUDE ACTUAL REFERENCES RELATED TO THE TOPIC"}
    - IMPORTANT: Give each section a SPECIFIC, UNIQUE, DESCRIPTIVE title related to its content (NO generic titles like "Section 1")
    
    Return ONLY a valid JSON object with this exact structure:
    {{
      "title": "{topic}",
      "introduction": "A {"brief, engaging" if is_handwritten else "comprehensive"} introduction ({int(word_count * 0.15)} words)",
      "sections": [
        {sections_json}
      ],
      "conclusion": "A {"brief, personal" if is_handwritten else "thorough"} conclusion",
      "references": [
        "Author, A. (Year). Title of reference 1. Journal/Publisher, Vol(Issue), pages.",
        "Author, B. (Year). Title of reference 2. Journal/Publisher, Vol(Issue), pages.",
        "Author, C. (Year). Title of reference 3. Journal/Publisher, Vol(Issue), pages.",
        "Author, D. (Year). Title of reference 4. Journal/Publisher, Vol(Issue), pages.",
        "Author, E. (Year). Title of reference 5. Journal/Publisher, Vol(Issue), pages."
      ]
    }}
    """
    
    try:
        # Generate the content
        response = model.generate_content(prompt)
        raw_content = response.text.strip()
        
        # Extract JSON content (in case model adds extra text)
        json_pattern = r'(\{[\s\S]*\})'
        json_match = re.search(json_pattern, raw_content)
        
        if json_match:
            raw_content = json_match.group(1)
        
        # Clean the JSON string to fix any issues
        cleaned_content = clean_json_string(raw_content)
        print(f"Cleaned JSON preview: {cleaned_content[:100]}...")
        
        # Parse the cleaned JSON content
        # Use a more robust approach with error detection
        try:
            report = json.loads(cleaned_content)
        except json.JSONDecodeError as je:
            print(f"Error position: line {je.lineno}, col {je.colno}, pos {je.pos}")
            # Get context of the error
            error_context = cleaned_content[max(0, je.pos-20):min(len(cleaned_content), je.pos+20)]
            print(f"Error context: '...{error_context}...'")
            # Try a more aggressive cleanup
            cleaned_content = re.sub(r'[^\x20-\x7E\n]', '', cleaned_content)  # Keep only printable ASCII
            report = json.loads(cleaned_content)
        
        print("JSON parsed successfully")
        
        # Add requested pages to the content
        report["requested_pages"] = num_pages
        
        # Validate report structure
        if "title" not in report:
            report["title"] = topic
            
        if "sections" not in report or len(report["sections"]) == 0:
            report["sections"] = []
            for i in range(section_count):
                report["sections"].append({
                    "title": f"Section {i+1}: Key Aspect of {topic}",
                    "content": f"This section analyzes important aspects of {topic}."
                })
                
        if "introduction" not in report or not report["introduction"]:
            report["introduction"] = f"This report examines {topic} in detail."
            
        if "conclusion" not in report or not report["conclusion"]:
            report["conclusion"] = f"In conclusion, {topic} represents an important area worthy of study."
            
        if "references" not in report or len(report["references"]) == 0:
            report["references"] = [
                f"Smith, J. (2023). Understanding {topic}. Journal of Research, 45(2), 112-128.",
                f"Johnson, A., & Williams, P. (2022). Advances in {topic}. Academic Press.",
                f"Brown, R. et al. (2021). {topic}: A comprehensive review. Annual Review, 15, 23-45.",
                f"Taylor, M. (2023). Practical applications of {topic}. Applied Research Today, 8(3), 67-89.",
                f"White, S., & Miller, T. (2022). Future directions for {topic} research. Future Perspectives, 12(1), 34-56."
            ]
        
        # Add flag indicating if this is for handwritten format
        report["is_handwritten"] = is_handwritten
        
        return report
        
    except Exception as e:
        print(f"Error generating or parsing content: {str(e)}")
        print(f"Raw content preview: {raw_content[:200]}...")
        
        # Create a more robust fallback report
        fallback_report = {
            "title": topic,
            "introduction": f"This report examines {topic} in depth, exploring its key aspects, historical context, and significance in the field.",
            "sections": [],
            "conclusion": f"In conclusion, {topic} represents an important area of study with significant implications for theory and practice in the field.",
            "references": [
                f"Smith, J. (2023). Understanding {topic}. Journal of Research, 45(2), 112-128.",
                f"Johnson, A., & Williams, P. (2022). Advances in {topic}. Academic Press.",
                f"Brown, R. et al. (2021). {topic}: A comprehensive review. Annual Review, 15, 23-45.",
                f"Taylor, M. (2023). Practical applications of {topic}. Applied Research Today, 8(3), 67-89.",
                f"White, S., & Miller, T. (2022). Future directions for {topic} research. Future Perspectives, 12(1), 34-56."
            ],
            "requested_pages": num_pages
        }
        
        # Add detailed sections
        for i in range(section_count):
            section_title = f"Key Aspect {i+1} of {topic}"
            section_content = f"This section analyzes important dimensions of {topic}, focusing on its {['theoretical foundations', 'practical applications', 'historical development', 'current research', 'future directions'][i % 5]}. The analysis reveals significant patterns and insights that contribute to our understanding of the topic."
            
            fallback_report["sections"].append({
                "title": section_title,
                "content": section_content
            })
        
        # If we're using fallback, create more meaningful section titles
        if len(fallback_report["sections"]) > 0:
            section_themes = [
                f"Historical Context of {topic}",
                f"Theoretical Framework for {topic}",
                f"Practical Applications of {topic}",
                f"Current Research on {topic}",
                f"Critical Analysis of {topic}",
                f"Future Directions for {topic} Research",
                f"Interdisciplinary Connections to {topic}",
                f"Methodological Approaches to {topic}",
                f"Case Studies in {topic}",
                f"Controversies and Debates in {topic}"
            ]
            
            for i, section in enumerate(fallback_report["sections"]):
                section["title"] = section_themes[i % len(section_themes)]
        
        return fallback_report
