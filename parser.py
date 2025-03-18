import re
import json
import logging
import spacy
from PyPDF2 import PdfReader
import docx
import os

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If model isn't downloaded, use a simpler approach
    logging.warning("Spacy model not found. Using basic NLP processing.")
    nlp = spacy.blank("en")

def extract_resume_data(file_path, file_extension):
    """
    Extract data from resume file
    
    Args:
        file_path (str): Path to the resume file
        file_extension (str): File extension (pdf, docx, json)
    
    Returns:
        dict: Dictionary containing extracted data
    """
    logging.debug(f"Extracting data from {file_path} with extension {file_extension}")
    
    if file_extension == 'pdf':
        text = extract_text_from_pdf(file_path)
    elif file_extension == 'docx':
        text = extract_text_from_docx(file_path)
    elif file_extension == 'json':
        return extract_data_from_json(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}")
    
    # Extract structured data from text
    return extract_structured_data_from_text(text)

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        pdf_reader = PdfReader(file_path)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        raise

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        logging.error(f"Error extracting text from DOCX: {str(e)}")
        raise

def extract_data_from_json(file_path):
    """Extract data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Ensure we have the required fields even if they're not in the JSON
        result = {
            'name': data.get('name', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', data.get('phone_number', '')),
            'skills': data.get('skills', []),
            'experience': data.get('experience', [])
        }
        
        # Convert experience to standard format if it's not already a list
        if not isinstance(result['experience'], list):
            result['experience'] = [str(result['experience'])]
        
        # Convert skills to standard format if it's not already a list
        if not isinstance(result['skills'], list):
            if isinstance(result['skills'], str):
                result['skills'] = [s.strip() for s in result['skills'].split(',')]
            else:
                result['skills'] = [str(result['skills'])]
        
        return result
    except Exception as e:
        logging.error(f"Error extracting data from JSON: {str(e)}")
        raise

def extract_structured_data_from_text(text):
    """
    Extract structured data from plain text using NLP
    
    Args:
        text (str): Plain text from resume
    
    Returns:
        dict: Dictionary with structured data
    """
    # Process the text with spaCy
    doc = nlp(text)
    
    # Extract basic information
    name = extract_name(doc, text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(doc, text)
    experience = extract_experience(doc, text)
    
    return {
        'name': name,
        'email': email,
        'phone': phone,
        'skills': skills,
        'experience': experience
    }

def extract_name(doc, text):
    """Extract name from text"""
    # Try to find name using spaCy entities
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # Return the first PERSON entity as the name
            return ent.text
    
    # Fallback to looking for a name at the beginning of the document
    # This assumes the resume starts with the person's name
    lines = text.split('\n')
    for line in lines[:5]:  # Check the first 5 lines
        line = line.strip()
        if line and len(line.split()) <= 5:  # Names typically have 5 or fewer words
            return line
    
    return ""

def extract_email(text):
    """Extract email from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ""

def extract_phone(text):
    """Extract phone number from text"""
    # Match various phone number formats
    phone_patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 123-456-7890
        r'\b\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}\b',  # (123) 456-7890
        r'\b\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'  # +1 123-456-7890
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return ""

def extract_skills(doc, text):
    """Extract skills from text"""
    # Common technical skills and keywords
    common_skills = [
        "python", "java", "javascript", "html", "css", "sql", "c++", "c#", "ruby",
        "php", "swift", "kotlin", "rust", "go", "typescript", "react", "angular",
        "vue", "django", "flask", "spring", "node.js", "express", "asp.net",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
        "git", "machine learning", "data science", "artificial intelligence", "ai",
        "nlp", "data analysis", "data visualization", "tableau", "power bi",
        "excel", "word", "powerpoint", "project management", "agile", "scrum",
        "leadership", "communication", "problem-solving", "teamwork", "creativity",
        "devops", "ci/cd", "database", "mongodb", "postgresql", "mysql", "oracle",
        "sqlserver", "networking", "security", "linux", "windows", "macos",
        "mobile development", "web development", "fullstack", "frontend", "backend"
    ]
    
    # Look for skills keywords
    skills = []
    
    # Try to find "Skills" section and extract
    skills_section = extract_section(text, ["skills", "technical skills", "core competencies"])
    if skills_section:
        # Extract skills from the skills section
        for skill in common_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', skills_section, re.IGNORECASE):
                skills.append(skill.title())
    
    # If we didn't find enough skills, search the whole document
    if len(skills) < 5:
        for skill in common_skills:
            if skill not in [s.lower() for s in skills] and re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                skills.append(skill.title())
    
    return skills

def extract_experience(doc, text):
    """Extract work experience from text"""
    # Try to find "Experience" section
    experience_section = extract_section(text, ["experience", "work experience", "employment history", "work history"])
    
    if not experience_section:
        # If no experience section found, return empty list
        return []
    
    # Split the experience section into parts based on common job title keywords
    job_indicators = [
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}',  # Month Year
        r'\b\d{4}\s*-\s*(?:\d{4}|Present|Current)',  # Year - Year/Present
        r'\bSenior\b', r'\bJunior\b', r'\bLead\b', r'\bManager\b', r'\bDirector\b',
        r'\bEngineer\b', r'\bDeveloper\b', r'\bArchitect\b', r'\bAnalyst\b',
        r'\bConsultant\b', r'\bSpecialist\b', r'\bAssociate\b', r'\bIntern\b'
    ]
    
    pattern = '|'.join(job_indicators)
    parts = re.split(f"({pattern})", experience_section)
    
    # Reassemble parts into job descriptions
    job_descriptions = []
    current_job = ""
    
    for i, part in enumerate(parts):
        current_job += part
        if i < len(parts) - 1 and re.match(pattern, parts[i+1]):
            job_descriptions.append(current_job.strip())
            current_job = ""
    
    if current_job:
        job_descriptions.append(current_job.strip())
    
    # If we couldn't split properly, just return the whole section
    if not job_descriptions:
        # Split by lines and filter out empty lines
        lines = [line.strip() for line in experience_section.split('\n') if line.strip()]
        return lines[:5]  # Return up to 5 lines
    
    # Limit to the first 5 job descriptions or less
    return job_descriptions[:5]

def extract_section(text, section_names):
    """
    Extract text from a specific section of the resume
    
    Args:
        text (str): Full resume text
        section_names (list): Possible names for the section
    
    Returns:
        str: Text from the section or empty string if not found
    """
    lines = text.split('\n')
    section_content = ""
    in_section = False
    
    for i, line in enumerate(lines):
        # Check if this line is a section header
        for name in section_names:
            if re.search(r'\b' + re.escape(name) + r'\b', line, re.IGNORECASE) and len(line) < 50:
                in_section = True
                break
        
        # If we're in the target section, add to content
        if in_section:
            # Check if we've reached the next section (headers are usually short)
            if i > 0 and line.strip() and len(line) < 50 and line.strip().endswith(':'):
                # Check if this is a new section header
                is_new_section = False
                for name in ["education", "projects", "skills", "experience", "achievements", "certifications"]:
                    if re.search(r'\b' + re.escape(name) + r'\b', line, re.IGNORECASE):
                        is_new_section = True
                        break
                
                if is_new_section:
                    break
            
            section_content += line + "\n"
    
    return section_content.strip()
