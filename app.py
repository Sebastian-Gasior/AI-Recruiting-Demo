"""
AI Recruiting Demo - Flask Application
Automatische CV-Analyse mit OpenAI GPT-4o-mini
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import logging
import os
from logging.handlers import RotatingFileHandler
from werkzeug.exceptions import RequestEntityTooLarge
from config import Config
from utils.file_validation import validate_file_upload, get_file_info
from utils.file_cleanup import delete_file, cleanup_old_files
from utils.pdf_extraction import extract_text_from_pdf, PDFExtractionError
from utils.ai_analysis import analyze_cv_with_ai, generate_recommendation, AIAnalysisError, analyze_cv_with_requirements
from utils.job_requirements import load_job_requirements, JobRequirementsError
from utils.big_five_scoring import (
    load_big_five_questions,
    calculate_ocean_scores,
    interpret_score,
    calculate_personality_fit_score,
    get_personality_fit_interpretation,
    calculate_combined_score,
    BigFiveScoringError
)
from utils.big_five_scoring import (
    load_big_five_questions, 
    calculate_ocean_scores, 
    interpret_score,
    get_dimension_name,
    BigFiveScoringError
)

# ====================================
# Professional Logging Setup (Story 1.2)
# ====================================

def setup_logging():
    """
    Configure professional logging with file and console output
    - INFO level for general operations
    - Rotating file handler (max 10MB, 5 backups)
    - Structured format for debugging
    - No sensitive data (sanitized output)
    """
    # Create logs directory if not exists
    os.makedirs('logs', exist_ok=True)
    
    # Define log format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File Handler (Rotating)
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove default handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Initialize logging
logger = setup_logging()
logger.info("="*60)
logger.info("AI Recruiting Demo - Application Starting")
logger.info("="*60)

# ====================================
# Configuration Validation (Story 1.3)
# ====================================

# Validate critical configuration before starting
try:
    Config.validate_critical_config()
    config_summary = Config.get_summary()
    logger.info(f"Configuration Summary: {config_summary}")
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    logger.error("Application cannot start without valid configuration!")
    raise

# Initialize Flask App with validated config
app = Flask(__name__)
app.config.from_object(Config)

logger.info("✓ Flask app configured successfully")


# ====================================
# Error Handlers (Story 2.2)
# ====================================

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error (Flask MAX_CONTENT_LENGTH)"""
    max_mb = app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
    logger.warning(f"File too large (>{ int(max_mb)}MB)")
    return jsonify({
        'success': False,
        'error': f'Datei zu groß (max {int(max_mb)}MB)'
    }), 413


@app.route('/')
def index():
    """
    Landing Page with Upload Form
    Story 2.1: Basic File Upload UI
    Story 10: Pass results to index if available (for single-page tabs)
    Story 11.5: Calculate combined score if CV and Personality results both available
    """
    logger.info("Index page accessed")
    
    # Story 10: Get results from session if available
    cv_results = session.get('cv_results')
    personality_results = session.get('personality_test')
    
    # Story 11.5: Calculate combined score if both CV and Personality results exist
    if cv_results and personality_results and personality_results.get('completed'):
        cv_match_score = cv_results.get('overall_scores', {}).get('weighted_total', 0)
        personality_fit_score = personality_results.get('fit_score', 0)
        
        if cv_match_score > 0 and personality_fit_score > 0:
            try:
                combined = calculate_combined_score(
                    cv_match_score=cv_match_score,
                    personality_fit_score=personality_fit_score,
                    cv_weight=0.70,
                    personality_weight=0.30
                )
                cv_results['combined_score'] = combined
                logger.info(f"Combined score calculated: {combined['combined_score']}/100")
            except Exception as e:
                logger.error(f"Error calculating combined score: {e}")
    
    if cv_results:
        logger.info("Results found in session, passing to index")
        return render_template('index.html', has_results=True, **cv_results)
    
    return render_template('index.html', has_results=False)


@app.route('/results')
def results():
    """
    Results Page - Display CV Analysis
    Story 5.1: Results Display
    Story 11.5: Calculate combined score if both CV and Personality results exist
    """
    logger.info("Results page accessed")
    
    # Get results from session
    results_data = session.get('cv_results')
    
    if not results_data:
        logger.warning("No results in session, redirecting to home")
        return redirect(url_for('index'))
    
    # Story 11.5: Calculate combined score if personality test completed
    personality_results = session.get('personality_test')
    if personality_results and personality_results.get('completed') and not results_data.get('combined_score'):
        cv_match_score = results_data.get('overall_scores', {}).get('weighted_total', 0)
        personality_fit_score = personality_results.get('fit_score', 0)
        
        if cv_match_score > 0 and personality_fit_score > 0:
            try:
                combined = calculate_combined_score(
                    cv_match_score=cv_match_score,
                    personality_fit_score=personality_fit_score,
                    cv_weight=0.70,
                    personality_weight=0.30
                )
                results_data['combined_score'] = combined
                logger.info(f"Combined score calculated for results page: {combined['combined_score']}/100")
            except Exception as e:
                logger.error(f"Error calculating combined score: {e}")
    
    # Story 10: Keep results in session (don't clear) so tabs work
    # session.pop('cv_results', None)  # REMOVED - keep results until page reload
    
    return render_template('results.html', **results_data)


@app.route('/api/results')
def api_results():
    """
    Story 10: API endpoint to check if results are available
    Story 11.5: Include combined score if available
    Returns results as JSON without page navigation
    """
    cv_results = session.get('cv_results')
    
    if not cv_results:
        return jsonify({'success': False, 'hasResults': False}), 200
    
    # Story 11.5: Calculate combined score if personality test completed
    personality_results = session.get('personality_test')
    if personality_results and personality_results.get('completed') and not cv_results.get('combined_score'):
        cv_match_score = cv_results.get('overall_scores', {}).get('weighted_total', 0)
        personality_fit_score = personality_results.get('fit_score', 0)
        
        if cv_match_score > 0 and personality_fit_score > 0:
            try:
                combined = calculate_combined_score(
                    cv_match_score=cv_match_score,
                    personality_fit_score=personality_fit_score,
                    cv_weight=0.70,
                    personality_weight=0.30
                )
                cv_results['combined_score'] = combined
            except Exception as e:
                logger.error(f"Error calculating combined score in API: {e}")
    
    logger.info("Returning results via API")
    return jsonify({'success': True, 'hasResults': True, 'data': cv_results}), 200


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle PDF Upload with Validation & Cleanup
    Story 2.1: Basic File Upload Route
    Story 2.2: File Validation (Type & Size)
    Story 2.4: Temporary File Storage & Cleanup
    """
    logger.info("Upload request received")
    
    # Story 2.4: Cleanup old files (>1 hour) before processing new upload
    cleanup_old_files(app.config['UPLOAD_FOLDER'], max_age_seconds=3600)
    
    filepath = None  # Track filepath for cleanup on error
    
    try:
        # Check if file is in request (this can trigger 413 error)
        if 'cv_file' not in request.files:
            logger.warning("No file in request")
            return jsonify({
                'success': False,
                'error': 'Keine Datei gefunden'
            }), 400
        
        file = request.files['cv_file']
        
        # Story 2.2: Comprehensive File Validation
        is_valid, error_message = validate_file_upload(
            file, 
            max_size=app.config['MAX_CONTENT_LENGTH']
        )
        
        if not is_valid:
            logger.warning(f"File validation failed: {error_message}")
            return jsonify({
                'success': False,
                'error': error_message
            }), 400
        
        # Get file info for logging
        file_info = get_file_info(file)
        logger.info(f"File validation passed: {file_info}")
        
        # Save file temporarily
        import uuid
        from werkzeug.utils import secure_filename
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{unique_id}_{original_filename}"
        
        # Save to upload folder
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logger.info(f"File saved successfully: {filename} ({os.path.getsize(filepath)} bytes)")
        
        # Story 3.1: Extract text from PDF
        try:
            logger.info(f"Starting text extraction: {filename}")
            extraction_result = extract_text_from_pdf(filepath, extract_tables=True)
            
            logger.info(f"Text extraction complete: {extraction_result['word_count']} words, "
                       f"{extraction_result['num_tables']} tables, "
                       f"{extraction_result['num_pages']} pages")
            
            # Story 9.2: AI-Powered CV Analysis with Requirements Matching
            try:
                logger.info("Starting AI-powered CV analysis with requirements matching...")
                
                # Load job requirements
                try:
                    job_requirements = load_job_requirements("power-bi-dev-fttx")
                    logger.info(f"Using job requirements: {job_requirements.position_title}")
                    
                    # Enhanced analysis with requirements matching
                    analysis_result = analyze_cv_with_requirements(
                        extraction_result['text'],
                        job_requirements
                    )
                    
                    cv_analysis = analysis_result.get('standard_cv_analysis', {})
                    requirements_matching = analysis_result.get('requirements_matching', {})
                    overall_scores = analysis_result.get('overall_scores', {})
                    recommendation_text = analysis_result.get('recommendation', 'N/A')
                    match_level = analysis_result.get('match_level', 'unknown')
                    gap_analysis = analysis_result.get('gap_analysis', {})
                    metadata = analysis_result.get('_metadata', {})
                    
                    logger.info(f"Requirements matching complete: {match_level} ({overall_scores.get('weighted_total', 0)}/100)")
                    
                    # Create recommendation object (compatible with old format)
                    recommendation = {
                        'recommendation': recommendation_text,
                        'score': overall_scores.get('weighted_total', 0),
                        'reasoning': gap_analysis.get('strengths', ['N/A'])[0] if gap_analysis.get('strengths') else 'N/A',
                        'strengths': gap_analysis.get('strengths', []),
                        'weaknesses': gap_analysis.get('critical_missing', [])
                    }
                    
                except JobRequirementsError as e:
                    logger.warning(f"Could not load job requirements: {e}. Falling back to standard analysis.")
                    # Fallback to standard analysis
                    cv_analysis = analyze_cv_with_ai(extraction_result['text'])
                    recommendation = generate_recommendation(cv_analysis)
                    requirements_matching = None
                    overall_scores = None
                    gap_analysis = None
                    metadata = None
                    match_level = None
                
                logger.info(f"AI analysis complete: {recommendation['recommendation']} (Score: {recommendation['score']}/100)")
                
                # Story 2.4: Delete file after successful processing
                delete_file(filepath)
                logger.info(f"File deleted after processing: {filename}")
                
                # Story 5.1 + 9.2: Store results in session for display
                session['cv_results'] = {
                    'filename': original_filename,
                    'message': 'CV erfolgreich analysiert',
                    'analysis': cv_analysis,
                    'recommendation': recommendation,
                    'extraction_stats': {
                        'word_count': extraction_result['word_count'],
                        'num_pages': extraction_result['num_pages'],
                        'num_tables': extraction_result['num_tables']
                    },
                    # Story 9.2: Requirements matching data
                    'requirements_matching': requirements_matching,
                    'overall_scores': overall_scores,
                    'gap_analysis': gap_analysis,
                    'match_level': match_level,
                    '_metadata': metadata
                }
                
                # Story 10: Return success - frontend will reload to show results in same page
                return jsonify({
                    'success': True,
                    'message': 'Analyse erfolgreich abgeschlossen'
                }), 200
                
            except AIAnalysisError as e:
                logger.error(f"AI analysis failed: {e}")
                # Delete file on AI error
                delete_file(filepath)
                return jsonify({
                    'success': False,
                    'error': f'KI-Analyse fehlgeschlagen: {str(e)}'
                }), 400
            
        except PDFExtractionError as e:
            logger.error(f"PDF extraction failed: {e}")
            # Delete file on extraction error
            delete_file(filepath)
            return jsonify({
                'success': False,
                'error': f'PDF-Textextraktion fehlgeschlagen: {str(e)}'
            }), 400
        
    except RequestEntityTooLarge:
        # Handle file too large error that occurs during parsing
        max_mb = app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
        logger.warning(f"File too large (>{int(max_mb)}MB)")
        return jsonify({
            'success': False,
            'error': f'Datei zu groß (max {int(max_mb)}MB)'
        }), 413
    
    except Exception as e:
        # Story 2.4: Cleanup on error
        if filepath and os.path.exists(filepath):
            delete_file(filepath)
            logger.info("File deleted after error")
        
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Upload fehlgeschlagen: {str(e)}'
        }), 500


@app.route('/clear-results', methods=['POST'])
def clear_results():
    """
    Story 10: Clear results from session
    Called when user wants to analyze new CV
    """
    session.pop('cv_results', None)
    logger.info("Results cleared from session")
    return jsonify({'success': True}), 200


# ====================================
# Personality Test API Routes (Story 11.3)
# ====================================

@app.route('/api/personality/questions', methods=['GET'])
def api_personality_questions():
    """
    Get Big Five questions for the test
    Story 11.3: Load questions from YAML config
    Returns: 30 randomly selected questions (6 per dimension), shuffled
    """
    import random
    
    try:
        data = load_big_five_questions()
        all_questions = data['questions']
        
        # Group questions by dimension
        questions_by_dimension = {
            'O': [],
            'C': [],
            'E': [],
            'A': [],
            'N': []
        }
        
        for q in all_questions:
            dim = q.get('dimension')
            if dim in questions_by_dimension:
                questions_by_dimension[dim].append(q)
        
        # Randomly select 6 questions per dimension
        selected_questions = []
        questions_per_dimension = 6
        
        for dimension in ['O', 'C', 'E', 'A', 'N']:
            available = questions_by_dimension[dimension]
            
            if len(available) < questions_per_dimension:
                # If not enough questions, use all available
                selected = available
                logger.warning(f"Only {len(available)} questions available for dimension {dimension}, using all")
            else:
                # Randomly select questions_per_dimension questions
                selected = random.sample(available, questions_per_dimension)
            
            selected_questions.extend(selected)
        
        # Shuffle all selected questions randomly
        random.shuffle(selected_questions)
        
        # Return only necessary fields
        questions_data = [
            {
                'id': q['id'],
                'text': q['text'],
                'dimension': q['dimension']
            }
            for q in selected_questions
        ]
        
        logger.info(f"Returning {len(questions_data)} randomly selected personality questions (shuffled)")
        return jsonify({
            'success': True,
            'questions': questions_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error loading personality questions: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler beim Laden der Fragen'
        }), 500


@app.route('/api/personality/start', methods=['POST'])
def api_personality_start():
    """
    Initialize personality test session
    Story 11.3: Start test, initialize session variables
    """
    try:
        session['personality_test'] = {
            'started': True,
            'answers': {},
            'current_question_index': 0,
            'completed': False
        }
        
        logger.info("Personality test session started")
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error starting personality test: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler beim Starten des Tests'
        }), 500


@app.route('/api/personality/status', methods=['GET'])
def api_personality_status():
    """
    Get current personality test status from session
    Story 11.3: Check if test was already started
    """
    test_session = session.get('personality_test')
    
    if not test_session:
        return jsonify({
            'success': True,
            'started': False
        }), 200
    
    return jsonify({
        'success': True,
        'started': test_session.get('started', False),
        'current_question_index': test_session.get('current_question_index', 0),
        'answers': test_session.get('answers', {}),
        'completed': test_session.get('completed', False)
    }), 200


@app.route('/api/personality/progress', methods=['POST'])
def api_personality_progress():
    """
    Save personality test progress
    Story 11.3: Save answers and current question index
    """
    try:
        data = request.get_json()
        
        if 'personality_test' not in session:
            session['personality_test'] = {}
        
        session['personality_test']['answers'] = data.get('answers', {})
        session['personality_test']['current_question_index'] = data.get('current_question_index', 0)
        session.modified = True
        
        logger.debug(f"Progress saved: {len(data.get('answers', {}))} answers")
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error saving progress: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler beim Speichern des Fortschritts'
        }), 500


@app.route('/api/personality/submit', methods=['POST'])
def api_personality_submit():
    """
    Submit personality test and calculate scores
    Story 11.3: Calculate OCEAN scores from answers
    """
    try:
        data = request.get_json()
        answers_raw = data.get('answers', {})
        
        if not answers_raw:
            return jsonify({
                'success': False,
                'error': 'Keine Antworten gefunden'
            }), 400
        
        # Convert answer keys from strings to integers (JSON sends numeric keys as strings)
        answers = {}
        for key, value in answers_raw.items():
            try:
                q_id = int(key)
                if isinstance(value, (int, str)):
                    ans_val = int(value)
                    if 1 <= ans_val <= 5:
                        answers[q_id] = ans_val
                    else:
                        logger.warning(f"Invalid answer value {ans_val} for question {q_id}, skipping")
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid answer key or value: {key}={value}, error: {e}")
        
        if not answers:
            return jsonify({
                'success': False,
                'error': 'Keine gültigen Antworten gefunden'
            }), 400
        
        logger.info(f"Received {len(answers)} valid answers. Answer IDs: {sorted(list(answers.keys()))[:20]}")  # Log first 20 IDs
        
        # Load questions
        questions_data = load_big_five_questions()
        questions = questions_data['questions']
        
        # Debug: Log question IDs that will be used for scoring
        question_ids = [q.get('id') for q in questions]
        logger.debug(f"Available question IDs in pool: {sorted(question_ids)[:20]}... (total: {len(question_ids)})")
        
        # Check which answered question IDs exist in the question pool
        answered_ids = set(answers.keys())
        available_ids = set(question_ids)
        matching_ids = answered_ids & available_ids
        
        if not matching_ids:
            logger.error(f"CRITICAL: No matching question IDs found! Answered IDs: {sorted(answered_ids)}, Available IDs: {sorted(list(available_ids)[:20])}...")
            return jsonify({
                'success': False,
                'error': f'Keine übereinstimmenden Frage-IDs gefunden. Bitte Test neu starten.'
            }), 400
        
        logger.info(f"Found {len(matching_ids)} matching question IDs out of {len(answered_ids)} answered questions")
        
        # Calculate OCEAN scores
        scores = calculate_ocean_scores(answers, questions=questions)
        scores_dict = scores.to_dict()
        
        # Interpret each score
        interpretations = {}
        for dimension in ['O', 'C', 'E', 'A', 'N']:
            score_value = scores_dict[dimension]
            level, description = interpret_score(dimension, score_value)
            interpretations[dimension] = {
                'level': level,
                'description': description,
                'score': score_value
            }
        
        # Calculate Personality Fit Score
        # Try to load job requirements to get personality profile
        job_personality_profile = None
        try:
            from utils.job_requirements import load_job_requirements
            job_requirements = load_job_requirements("power-bi-dev-fttx")
            if job_requirements.personality_profile:
                # Convert PersonalityProfile dataclass to dict for scoring function
                job_personality_profile = {
                    'dimensions': job_requirements.personality_profile.dimensions
                }
                logger.info("Using job-specific personality profile for fit score calculation")
        except Exception as e:
            logger.warning(f"Could not load job personality profile, using fallback: {e}")
        
        fit_score = calculate_personality_fit_score(scores, job_personality_profile=job_personality_profile)
        fit_level, fit_description = get_personality_fit_interpretation(fit_score)
        
        # Save results to session
        if 'personality_test' not in session:
            session['personality_test'] = {}
        
        session['personality_test']['completed'] = True
        session['personality_test']['scores'] = scores_dict
        session['personality_test']['interpretations'] = interpretations
        session['personality_test']['fit_score'] = fit_score
        session['personality_test']['fit_interpretation'] = {
            'level': fit_level,
            'description': fit_description
        }
        session.modified = True
        
        logger.info(f"Personality test submitted. Scores: {scores_dict}, Fit Score: {fit_score}/100")
        
        return jsonify({
            'success': True,
            'scores': scores_dict,
            'interpretations': interpretations,
            'fit_score': fit_score,
            'fit_interpretation': {
                'level': fit_level,
                'description': fit_description
            }
        }), 200
        
    except BigFiveScoringError as e:
        logger.error(f"Big Five scoring error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error submitting personality test: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Fehler beim Berechnen der Ergebnisse'
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'AI Recruiting Demo',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("STARTING SERVER...")
    logger.info(f"Debug Mode: {app.config['DEBUG']}")
    logger.info(f"Upload Folder: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"Max File Size: {app.config['MAX_CONTENT_LENGTH'] / (1024*1024)}MB")
    logger.info("="*60)
    
    # Run with hot-reload enabled (Debug Mode)
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)

