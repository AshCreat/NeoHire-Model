import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import tempfile
import re
from werkzeug.utils import secure_filename
from utils.parser import extract_resume_data
from utils.scorer import score_resume_against_job

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Setup Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key_for_testing")

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'json'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if file was uploaded
    if 'resume' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['resume']
    job_description = request.form.get('job_description', '')
    
    # If user didn't select file
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        try:
            # Save the file temporarily
            filename = secure_filename(file.filename)
            file_extension = filename.rsplit('.', 1)[1].lower()
            
            # Create a temporary file to save the uploaded content
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}')
            file.save(temp_file.name)
            temp_file.close()
            
            # Extract data from the resume
            resume_data = extract_resume_data(temp_file.name, file_extension)
            
            # Score the resume against the job description if provided
            score = 0
            skills_match = {}
            if job_description:
                score, skills_match = score_resume_against_job(resume_data, job_description)
            
            # Clean up the temporary file
            os.unlink(temp_file.name)
            
            # Store result in session
            session['resume_data'] = resume_data
            session['score'] = score
            session['skills_match'] = skills_match
            session['job_description'] = job_description
            
            return redirect(url_for('result'))
            
        except Exception as e:
            logging.error(f"Error processing file: {str(e)}")
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(request.url)
    else:
        flash(f'File type not allowed. Please upload PDF, DOCX, or JSON files.', 'danger')
        return redirect(request.url)

@app.route('/result')
def result():
    # Get results from session
    resume_data = session.get('resume_data', {})
    score = session.get('score', 0)
    skills_match = session.get('skills_match', {})
    job_description = session.get('job_description', '')
    
    if not resume_data:
        flash('No resume data found. Please upload a resume first.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('result.html', 
                          resume_data=resume_data, 
                          score=score, 
                          skills_match=skills_match,
                          job_description=job_description)

@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large. Maximum file size is 16MB.', 'danger')
    return redirect(url_for('index')), 413

@app.errorhandler(500)
def internal_server_error(error):
    flash('An unexpected error occurred. Please try again.', 'danger')
    return redirect(url_for('index')), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
