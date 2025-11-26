"""
Big Five Personality Assessment Scoring
Story 11.2: OCEAN Score Calculation from IPIP-30 Answers
Story 11.5: Combined Score Calculation (CV Match + Personality Fit)
"""

import yaml
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class BigFiveScoringError(Exception):
    """Custom exception for Big Five scoring errors"""
    pass


@dataclass
class BigFiveScores:
    """Big Five OCEAN Scores"""
    O: int  # Openness (6-30)
    C: int  # Conscientiousness (6-30)
    E: int  # Extraversion (6-30)
    A: int  # Agreeableness (6-30)
    N: int  # Neuroticism (6-30)
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary"""
        return {
            'O': self.O,
            'C': self.C,
            'E': self.E,
            'A': self.A,
            'N': self.N
        }
    
    def get_all_scores(self) -> Dict[str, int]:
        """Get all scores as dictionary (alias for to_dict)"""
        return self.to_dict()


def load_big_five_questions(
    config_path: str = "config/big_five_questions.yaml"
) -> Dict:
    """
    Load Big Five questions from YAML configuration
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Dictionary with 'dimensions' and 'questions' keys
        
    Raises:
        BigFiveScoringError: If loading or validation fails
    """
    try:
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise BigFiveScoringError(f"Config file not found: {config_path}")
        
        logger.info(f"Loading Big Five questions from {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise BigFiveScoringError("Config file is empty")
        
        if 'questions' not in data:
            raise BigFiveScoringError("'questions' key missing in config")
        
        if 'dimensions' not in data:
            raise BigFiveScoringError("'dimensions' key missing in config")
        
        questions = data['questions']
        
        # Validate minimum number of questions (at least 30, but can be more for random selection)
        if len(questions) < 30:
            raise BigFiveScoringError(
                f"At least 30 questions required, found {len(questions)}. "
                f"For random question selection, 60+ questions (12 per dimension) are recommended."
            )
        
        # Validate questions per dimension (should be at least 6, ideally 12+)
        from collections import Counter
        dimension_counts = Counter(q.get('dimension') for q in questions)
        for dim in ['O', 'C', 'E', 'A', 'N']:
            count = dimension_counts.get(dim, 0)
            if count < 6:
                raise BigFiveScoringError(
                    f"Dimension {dim}: Only {count} questions found (minimum 6 required)"
                )
        
        logger.info(f"✓ Loaded {len(questions)} Big Five questions "
                   f"(O:{dimension_counts.get('O', 0)}, C:{dimension_counts.get('C', 0)}, "
                   f"E:{dimension_counts.get('E', 0)}, A:{dimension_counts.get('A', 0)}, "
                   f"N:{dimension_counts.get('N', 0)})")
        
        return data
        
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error: {e}")
        raise BigFiveScoringError(f"Failed to parse YAML: {e}")
    
    except Exception as e:
        logger.error(f"Error loading Big Five questions: {e}")
        raise BigFiveScoringError(f"Failed to load questions: {e}")


def calculate_ocean_scores(
    answers: Dict[int, int],
    questions: Optional[List[Dict]] = None,
    config_path: str = "config/big_five_questions.yaml"
) -> BigFiveScores:
    """
    Calculate OCEAN scores from IPIP-30 answers
    
    Args:
        answers: Dictionary mapping question_id (1-30) to Likert value (1-5)
                 Example: {1: 4, 2: 5, 3: 2, ...}
        questions: Optional list of question dictionaries. If None, loads from config_path
        config_path: Path to questions YAML file (used if questions is None)
    
    Returns:
        BigFiveScores object with O, C, E, A, N scores (each 6-30)
    
    Raises:
        BigFiveScoringError: If validation fails or calculation error occurs
    
    Scoring Logic:
        - Normal keying (+): 1=1, 2=2, 3=3, 4=4, 5=5
        - Reversed keying (-): 1=5, 2=4, 3=3, 4=2, 5=1
        - Each dimension has 6 questions, so range is 6-30 per dimension
    """
    try:
        # Load questions if not provided
        if questions is None:
            data = load_big_five_questions(config_path)
            questions = data['questions']
        
        # Initialize scores
        scores = {'O': 0, 'C': 0, 'E': 0, 'A': 0, 'N': 0}
        expected_dimensions = {'O', 'C', 'E', 'A', 'N'}
        
        # Validate answers
        if not answers:
            raise BigFiveScoringError("No answers provided")
        
        # Count answered questions per dimension
        answered_per_dimension = {dim: 0 for dim in expected_dimensions}
        
        # Debug: Log received answers
        logger.debug(f"Received answers with keys: {list(answers.keys())[:10]}... (total: {len(answers)})")
        
        # Process each question
        for question in questions:
            q_id = question.get('id')
            dimension = question.get('dimension')
            keying = question.get('keying')
            
            # Validate question structure
            if q_id is None:
                raise BigFiveScoringError("Question missing 'id' field")
            
            # Ensure q_id is an integer for matching
            try:
                q_id = int(q_id)
            except (ValueError, TypeError):
                raise BigFiveScoringError(f"Invalid question ID format: {q_id}")
            
            if dimension not in expected_dimensions:
                raise BigFiveScoringError(f"Invalid dimension '{dimension}' in question {q_id}")
            if keying not in ['+', '-']:
                raise BigFiveScoringError(f"Invalid keying '{keying}' in question {q_id} (expected '+' or '-')")
            
            # Get answer for this question (try both int and string key)
            answer = answers.get(q_id)
            if answer is None:
                # Try string key as fallback
                answer = answers.get(str(q_id))
            
            # Skip unanswered questions
            if answer is None:
                continue  # Don't log warning for every unanswered question (we only have 30 out of 60)
            
            # Validate answer range
            if not isinstance(answer, int) or answer < 1 or answer > 5:
                raise BigFiveScoringError(
                    f"Invalid answer for question {q_id}: {answer} (must be 1-5)"
                )
            
            # Apply reverse scoring if needed
            if keying == "-":
                # Reverse: 1→5, 2→4, 3→3, 4→2, 5→1
                scored_value = 6 - answer
            else:
                # Normal: 1=1, 2=2, 3=3, 4=4, 5=5
                scored_value = answer
            
            # Add to dimension score
            scores[dimension] += scored_value
            answered_per_dimension[dimension] += 1
        
        # Validate that all questions were answered
        total_answered = sum(answered_per_dimension.values())
        if total_answered == 0:
            logger.error(f"No questions were answered! Answers dict: {answers}")
            raise BigFiveScoringError(
                f"No valid answers found. Received {len(answers)} answers but none matched questions."
            )
        
        if total_answered < 30:
            logger.warning(f"Only {total_answered}/30 questions answered")
        
        # Check minimum questions per dimension
        for dim in expected_dimensions:
            count = answered_per_dimension[dim]
            if count < 6:
                logger.warning(f"Dimension {dim}: Only {count}/6 questions answered")
            else:
                logger.debug(f"Dimension {dim}: {count} questions answered, score: {scores[dim]}")
        
        # Create result object
        result = BigFiveScores(
            O=scores['O'],
            C=scores['C'],
            E=scores['E'],
            A=scores['A'],
            N=scores['N']
        )
        
        logger.info(f"✓ OCEAN scores calculated: O={result.O}, C={result.C}, E={result.E}, A={result.A}, N={result.N} "
                   f"(answered: {total_answered} questions)")
        
        return result
        
    except BigFiveScoringError:
        raise
    except Exception as e:
        logger.error(f"Error calculating OCEAN scores: {e}", exc_info=True)
        raise BigFiveScoringError(f"Failed to calculate scores: {e}")


def interpret_score(dimension: str, score: int) -> Tuple[str, str]:
    """
    Interpret a Big Five dimension score
    
    Args:
        dimension: Dimension code ('O', 'C', 'E', 'A', 'N')
        score: Score value (6-30)
    
    Returns:
        Tuple of (level, description)
        level: 'Sehr Niedrig', 'Niedrig', 'Mittel', 'Hoch', 'Sehr Hoch'
        description: Text description of the level
    
    Score Ranges:
        - 6-10: Sehr Niedrig
        - 11-15: Niedrig
        - 16-20: Mittel
        - 21-25: Hoch
        - 26-30: Sehr Hoch
    """
    # Validate dimension
    valid_dimensions = {'O', 'C', 'E', 'A', 'N'}
    if dimension not in valid_dimensions:
        raise ValueError(f"Invalid dimension: {dimension}")
    
    # Validate score range
    if score < 6 or score > 30:
        logger.warning(f"Score {score} outside expected range (6-30) for dimension {dimension}")
    
    # Determine level
    if score <= 10:
        level = "Sehr Niedrig"
    elif score <= 15:
        level = "Niedrig"
    elif score <= 20:
        level = "Mittel"
    elif score <= 25:
        level = "Hoch"
    else:
        level = "Sehr Hoch"
    
    # Generate description based on dimension and level
    descriptions = {
        'O': {
            'Sehr Niedrig': "Sehr konventionell, bevorzugt Bekanntes",
            'Niedrig': "Pragmatisch, fokussiert auf Praktisches",
            'Mittel': "Ausgewogenes Interesse an Neuem und Bekanntem",
            'Hoch': "Kreativ, neugierig, lernbereit",
            'Sehr Hoch': "Sehr kreativ, experimentierfreudig, offen für Neues"
        },
        'C': {
            'Sehr Niedrig': "Unorganisiert, unzuverlässig",
            'Niedrig': "Lässig, spontan",
            'Mittel': "Moderat organisiert",
            'Hoch': "Zuverlässig, organisiert, pflichtbewusst",
            'Sehr Hoch': "Sehr zuverlässig, sehr organisiert, sehr pflichtbewusst"
        },
        'E': {
            'Sehr Niedrig': "Sehr introvertiert, zurückhaltend",
            'Niedrig': "Ruhig, reserviert",
            'Mittel': "Ausgewogen gesellig",
            'Hoch': "Gesellig, gesprächig, energiegeladen",
            'Sehr Hoch': "Sehr extravertiert, sehr gesellig, sehr kommunikativ"
        },
        'A': {
            'Sehr Niedrig': "Konkurrenzorientiert, skeptisch",
            'Niedrig': "Eher skeptisch, distanziert",
            'Mittel': "Ausgewogen kooperativ",
            'Hoch': "Kooperationsfähig, mitfühlend, vertrauensvoll",
            'Sehr Hoch': "Sehr mitfühlend, sehr vertrauensvoll, sehr freundlich"
        },
        'N': {
            'Sehr Niedrig': "Sehr emotional stabil, stressresistent",
            'Niedrig': "Emotional stabil, ruhig",
            'Mittel': "Moderat emotional reagierend",
            'Hoch': "Emotional reagierend, stressempfindlich",
            'Sehr Hoch': "Sehr emotional reagierend, sehr stressempfindlich"
        }
    }
    
    description = descriptions[dimension].get(level, "Keine Beschreibung verfügbar")
    
    return level, description


def get_dimension_name(dimension: str, language: str = "de") -> str:
    """
    Get human-readable name for a Big Five dimension
    
    Args:
        dimension: Dimension code ('O', 'C', 'E', 'A', 'N')
        language: Language code ('de' or 'en')
    
    Returns:
        Dimension name in specified language
    """
    names = {
        'de': {
            'O': "Openness (Offenheit für Erfahrungen)",
            'C': "Conscientiousness (Gewissenhaftigkeit)",
            'E': "Extraversion",
            'A': "Agreeableness (Verträglichkeit)",
            'N': "Neuroticism (Neurotizismus)"
        },
        'en': {
            'O': "Openness to Experience",
            'C': "Conscientiousness",
            'E': "Extraversion",
            'A': "Agreeableness",
            'N': "Neuroticism"
        }
    }
    
    valid_dimensions = {'O', 'C', 'E', 'A', 'N'}
    if dimension not in valid_dimensions:
        raise ValueError(f"Invalid dimension: {dimension}")
    
    lang = language.lower()
    if lang not in names:
        lang = 'de'  # Default to German
    
    return names[lang][dimension]


def calculate_personality_fit_score(
    ocean_scores: BigFiveScores,
    job_personality_profile: Optional[Dict] = None
) -> int:
    """
    Calculate Personality Fit Score based on OCEAN scores
    
    If job_personality_profile is provided, calculates fit based on job-specific requirements.
    Otherwise, uses simplified model focusing on Conscientiousness.
    
    Args:
        ocean_scores: BigFiveScores object with O, C, E, A, N scores
        job_personality_profile: Optional dict with job-specific personality requirements
                                Structure: {'dimensions': {'C': {'ideal_score': 24, 'weight': 0.40, ...}, ...}}
    
    Returns:
        Fit score from 0-100 (higher = better fit)
    
    Scoring Logic (with job profile):
        - Compares candidate scores to ideal scores for each dimension
        - Uses weighted average based on job-specific weights
        - For reversed dimensions (e.g., Neuroticism), lower scores are better
    
    Scoring Logic (without job profile - fallback):
        - Conscientiousness (C) is the strongest predictor of job performance
        - Normalize C score to 0-100 range
    """
    # If job-specific profile is provided, use it
    if job_personality_profile and job_personality_profile.get('dimensions'):
        dimensions_config = job_personality_profile['dimensions']
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for dim in ['O', 'C', 'E', 'A', 'N']:
            if dim not in dimensions_config:
                continue
            
            config = dimensions_config[dim]
            ideal_score = config.get('ideal_score', 18)
            weight = config.get('weight', 0.2)
            is_reversed = config.get('reversed', False)
            
            candidate_score = getattr(ocean_scores, dim)
            
            # Calculate fit for this dimension (0-100)
            if is_reversed:
                # For Neuroticism: lower is better
                # Score = 100 - distance from ideal (normalized)
                distance = abs(candidate_score - ideal_score)
                max_distance = 24  # Max possible distance (6-30 range)
                dimension_fit = max(0, 100 - (distance / max_distance * 100))
            else:
                # For other dimensions: closer to ideal is better
                # Score based on distance from ideal (normalized)
                distance = abs(candidate_score - ideal_score)
                max_distance = 24  # Max possible distance (6-30 range)
                dimension_fit = max(0, 100 - (distance / max_distance * 100))
            
            # Apply weight
            total_weighted_score += dimension_fit * weight
            total_weight += weight
        
        # Normalize by total weight
        if total_weight > 0:
            fit_score = total_weighted_score / total_weight
        else:
            # Fallback to simple Conscientiousness-based score
            c_score = ocean_scores.C
            fit_score = ((c_score - 6) / 24) * 100
        
        fit_score = max(0, min(100, int(fit_score)))
        logger.debug(f"Personality fit score calculated: {fit_score}/100 (job-specific profile)")
        return fit_score
    
    # Fallback: Simplified model using only Conscientiousness
    c_score = ocean_scores.C  # Conscientiousness score (6-30)
    
    # Normalize to 0-100 range
    # Formula: ((score - min) / (max - min)) * 100
    # min = 6, max = 30, range = 24
    fit_score = ((c_score - 6) / 24) * 100
    
    # Ensure score is in valid range
    fit_score = max(0, min(100, int(fit_score)))
    
    logger.debug(f"Personality fit score calculated: {fit_score}/100 (based on C={c_score}, fallback model)")
    
    return fit_score


def get_personality_fit_interpretation(fit_score: int) -> Tuple[str, str]:
    """
    Get interpretation of Personality Fit Score
    
    Args:
        fit_score: Fit score from 0-100
    
    Returns:
        Tuple of (level, description)
    """
    if fit_score >= 80:
        level = "Sehr Hoch"
        description = "Ihr Profil passt sehr gut zur Position. Sehr gute berufliche Eignung."
    elif fit_score >= 65:
        level = "Hoch"
        description = "Ihr Profil passt gut zur Position. Gute berufliche Eignung."
    elif fit_score >= 50:
        level = "Mittel"
        description = "Ihr Profil passt mittelmäßig zur Position. Durchschnittliche Eignung."
    elif fit_score >= 35:
        level = "Niedrig"
        description = "Ihr Profil passt weniger gut zur Position. Geringere Eignung."
    else:
        level = "Sehr Niedrig"
        description = "Ihr Profil passt nicht gut zur Position. Sehr geringe Eignung."
    
    return level, description


def calculate_combined_score(cv_match_score: float, personality_fit_score: int, 
                             cv_weight: float = 0.70, personality_weight: float = 0.30) -> Dict:
    """
    Calculate combined overall score from CV Match and Personality Fit
    
    Story 11.5: 70/30 Gewichtung (CV 70%, Personality 30%)
    
    Args:
        cv_match_score: CV Match Score (0-100)
        personality_fit_score: Personality Fit Score (0-100)
        cv_weight: Weight for CV Match (default 0.70 = 70%)
        personality_weight: Weight for Personality Fit (default 0.30 = 30%)
    
    Returns:
        Dictionary with:
        - combined_score: Overall score (0-100)
        - cv_match_score: Original CV Match Score
        - personality_fit_score: Original Personality Fit Score
        - weights: Applied weights
    """
    # Ensure weights sum to 1.0
    total_weight = cv_weight + personality_weight
    if abs(total_weight - 1.0) > 0.01:
        logger.warning(f"Weights don't sum to 1.0 ({total_weight}), normalizing...")
        cv_weight = cv_weight / total_weight
        personality_weight = personality_weight / total_weight
    
    # Calculate weighted combined score
    combined = (cv_match_score * cv_weight) + (personality_fit_score * personality_weight)
    combined = round(combined, 1)
    
    # Ensure score is in valid range
    combined = max(0.0, min(100.0, combined))
    
    logger.info(f"Combined score calculated: {combined}/100 (CV: {cv_match_score}×{cv_weight}, Personality: {personality_fit_score}×{personality_weight})")
    
    return {
        'combined_score': combined,
        'cv_match_score': round(cv_match_score, 1),
        'personality_fit_score': personality_fit_score,
        'weights': {
            'cv': cv_weight,
            'personality': personality_weight
        }
    }