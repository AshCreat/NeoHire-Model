import logging
import re
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def score_resume_against_job(resume_data, job_description):
    """
    Score a resume against a job description
    
    Args:
        resume_data (dict): Parsed resume data
        job_description (str): Job description text
    
    Returns:
        tuple: (score, skills_match)
            - score: int (0-100)
            - skills_match: dict of matching skills and their importance
    """
    logging.debug("Scoring resume against job description")
    
    # Extract skills list from resume
    resume_skills = resume_data.get('skills', [])
    
    # Extract experience from resume
    resume_experience = resume_data.get('experience', [])
    
    # Combine skills and experience into a single text for analysis
    resume_text = " ".join([
        " ".join(resume_skills),
        " ".join(resume_experience)
    ])
    
    # Clean and normalize text
    resume_text = clean_text(resume_text)
    job_description = clean_text(job_description)
    
    # Calculate skill match scores
    skills_match = calculate_skills_match(resume_skills, job_description)
    
    # Calculate content match with TF-IDF
    content_match_score = calculate_content_match(resume_text, job_description)
    
    # Calculate final score (weighted average)
    # 60% for skills match, 40% for content match
    skills_score = sum(skills_match.values()) / max(len(skills_match), 1) * 100
    final_score = int(0.6 * skills_score + 0.4 * content_match_score)
    
    # Ensure score is between 0 and 100
    final_score = max(0, min(100, final_score))
    
    return final_score, skills_match

def clean_text(text):
    """Clean and normalize text for better comparison"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def calculate_skills_match(resume_skills, job_description):
    """
    Calculate how well the resume skills match with job description
    
    Returns:
        dict: Dictionary of skills with match scores (0.0-1.0)
    """
    skills_match = {}
    job_desc_lower = job_description.lower()
    
    for skill in resume_skills:
        skill_lower = skill.lower()
        
        # Check if skill is mentioned in job description
        if skill_lower in job_desc_lower:
            # Calculate importance score based on frequency and position
            # Position: Earlier mentions might be more important
            position_score = 1.0
            first_pos = job_desc_lower.find(skill_lower)
            if first_pos > -1:
                # Normalize position (earlier is better)
                position_score = 1.0 - (first_pos / len(job_desc_lower))
            
            # Frequency: More mentions might indicate importance
            frequency = job_desc_lower.count(skill_lower)
            frequency_score = min(frequency / 3, 1.0)  # Cap at 1.0
            
            # Combine scores (weighted average)
            importance = (0.7 * frequency_score + 0.3 * position_score)
            skills_match[skill] = round(importance, 2)
    
    return skills_match

def calculate_content_match(resume_text, job_description):
    """
    Calculate similarity between resume text and job description using TF-IDF and cosine similarity
    
    Returns:
        float: Similarity score (0-100)
    """
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words='english')
    
    try:
        # Vectorize the texts
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
        
        # Calculate cosine similarity
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        # Convert to percentage
        similarity_score = cosine_sim * 100
        
        return similarity_score
    except Exception as e:
        logging.error(f"Error calculating content match: {str(e)}")
        return 0
