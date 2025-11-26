"""
AI-Powered CV Analysis with OpenAI
Story 4.1: OpenAI API Integration & Token Management
Story 4.2: Prompt Engineering
Story 4.3: JSON Output Parsing
Story 4.4: Recommendation Engine
Story 9.2: Enhanced AI Prompt für Requirement-Matching
"""

import json
import logging
import tiktoken
from openai import OpenAI, OpenAIError, RateLimitError, APIConnectionError, AuthenticationError
from typing import Dict, Optional, List
from config import Config

logger = logging.getLogger(__name__)

# Initialize OpenAI Client
client = None

def get_openai_client():
    """Get or initialize OpenAI client"""
    global client
    if client is None:
        try:
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise AIAnalysisError(f"OpenAI client initialization failed: {e}")
    return client


class AIAnalysisError(Exception):
    """Custom exception for AI analysis errors"""
    pass


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Count tokens in text for a given model
    
    Args:
        text (str): Text to count tokens for
        model (str): Model name (default: gpt-4o-mini)
        
    Returns:
        int: Number of tokens
    """
    try:
        # Get encoding for model
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        logger.warning(f"Token counting failed: {e}, using estimate")
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4


def analyze_cv_with_ai(cv_text: str, model: str = "gpt-4o-mini", temperature: float = 0.3) -> Dict:
    """
    Analyze CV text using OpenAI GPT
    
    Args:
        cv_text (str): Extracted CV text
        model (str): OpenAI model to use
        temperature (float): Model temperature (0.0-1.0, lower = more consistent)
        
    Returns:
        dict: Structured CV analysis
        
    Raises:
        AIAnalysisError: If analysis fails
    """
    
    # Get OpenAI client
    client = get_openai_client()
    
    if not cv_text or len(cv_text.strip()) < 10:
        raise AIAnalysisError("CV text too short for analysis (minimum 10 characters)")
    
    # Count tokens
    input_tokens = count_tokens(cv_text, model)
    logger.info(f"CV text contains ~{input_tokens} tokens")
    
    if input_tokens > 10000:
        logger.warning(f"CV is very long ({input_tokens} tokens), may be expensive")
    
    # Story 4.2: Prompt Engineering
    system_prompt = """Du bist ein professioneller HR-Experte und CV-Analyst.
Deine Aufgabe ist es, Lebensläufe präzise zu analysieren und strukturierte Informationen zu extrahieren.

Analysiere den folgenden Lebenslauf und extrahiere alle relevanten Informationen.
Gib die Informationen als JSON zurück mit folgender Struktur:

{
  "personal": {
    "name": "Vollständiger Name",
    "email": "Email-Adresse",
    "phone": "Telefonnummer",
    "location": "Stadt/Region"
  },
  "experience": [
    {
      "position": "Jobtitel",
      "company": "Firmenname",
      "period": "Zeitraum (z.B. 2020-2023)",
      "technologies": ["Tech1", "Tech2"],
      "description": "Kurze Beschreibung"
    }
  ],
  "education": [
    {
      "degree": "Abschluss",
      "institution": "Universität/Schule",
      "year": "Jahr oder Zeitraum",
      "field": "Studienrichtung"
    }
  ],
  "skills": {
    "technical": ["Skill1", "Skill2"],
    "soft": ["Skill1", "Skill2"],
    "languages": [{"language": "Deutsch", "level": "Muttersprache"}]
  },
  "career_level": "Junior/Mid/Senior/Lead",
  "main_expertise": "Hauptkompetenzbereich"
}

WICHTIG:
- Falls eine Information nicht im CV steht, nutze "N/A"
- Sei präzise und objektiv
- Extrahiere alle Technologien und Tools
- Gib NUR valides JSON zurück, keine zusätzlichen Kommentare"""

    user_prompt = f"Analysiere diesen Lebenslauf:\n\n{cv_text}"
    
    try:
        logger.info(f"Sending CV to OpenAI API (model: {model}, temp: {temperature})")
        
        # Story 4.1: API Call with error handling
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=2000,
            timeout=30.0
        )
        
        # Extract response
        content = response.choices[0].message.content
        
        # Token usage
        usage = response.usage
        logger.info(f"API call successful - Tokens: input={usage.prompt_tokens}, "
                   f"output={usage.completion_tokens}, total={usage.total_tokens}")
        
        # Estimate cost (GPT-4o-mini pricing: ~$0.15/1M input tokens, ~$0.60/1M output tokens)
        cost_estimate = (usage.prompt_tokens * 0.15 / 1_000_000) + \
                       (usage.completion_tokens * 0.60 / 1_000_000)
        logger.info(f"Estimated cost: ${cost_estimate:.4f}")
        
        # Story 4.3: Parse JSON
        try:
            # Clean response (sometimes GPT adds markdown)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            cv_data = json.loads(content)
            logger.info("CV analysis parsed successfully")
            
            # Add metadata
            cv_data['_metadata'] = {
                'model': model,
                'tokens_input': usage.prompt_tokens,
                'tokens_output': usage.completion_tokens,
                'tokens_total': usage.total_tokens,
                'cost_estimate_usd': round(cost_estimate, 4)
            }
            
            return cv_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {content}")
            raise AIAnalysisError(f"GPT response is not valid JSON: {e}")
    
    except RateLimitError as e:
        logger.error(f"OpenAI rate limit reached: {e}")
        raise AIAnalysisError("API-Rate-Limit erreicht. Bitte versuchen Sie es später erneut.")
    
    except APIConnectionError as e:
        logger.error(f"OpenAI connection error: {e}")
        raise AIAnalysisError("Verbindung zur OpenAI API fehlgeschlagen. Bitte prüfen Sie Ihre Internetverbindung.")
    
    except AuthenticationError as e:
        logger.error(f"OpenAI authentication error: {e}")
        raise AIAnalysisError("Ungültiger API-Key. Bitte prüfen Sie die Konfiguration.")
    
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise AIAnalysisError(f"OpenAI API Fehler: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error during AI analysis: {e}", exc_info=True)
        raise AIAnalysisError(f"Unerwarteter Fehler bei der KI-Analyse: {str(e)}")


def generate_recommendation(cv_data: Dict) -> Dict:
    """
    Generate hiring recommendation based on CV analysis
    Story 4.4: Recommendation Engine
    
    Args:
        cv_data (dict): Analyzed CV data
        
    Returns:
        dict: Recommendation with reasoning
    """
    
    try:
        # Extract key factors
        career_level = cv_data.get('career_level', 'N/A')
        experience = cv_data.get('experience', [])
        technical_skills = cv_data.get('skills', {}).get('technical', [])
        education = cv_data.get('education', [])
        
        # Simple scoring logic
        score = 0
        strengths = []
        weaknesses = []
        
        # Career level scoring
        if career_level == 'Senior' or career_level == 'Lead':
            score += 30
            strengths.append("Hohe Seniorität und Erfahrung")
        elif career_level == 'Mid':
            score += 20
            strengths.append("Solide Mid-Level Erfahrung")
        elif career_level == 'Junior':
            score += 10
        
        # Experience scoring
        if len(experience) >= 3:
            score += 25
            strengths.append(f"Umfangreiche Berufserfahrung ({len(experience)} Positionen)")
        elif len(experience) >= 1:
            score += 15
        else:
            weaknesses.append("Wenig oder keine Berufserfahrung")
        
        # Technical skills scoring
        if len(technical_skills) >= 10:
            score += 25
            strengths.append(f"Breites technisches Skillset ({len(technical_skills)} Skills)")
        elif len(technical_skills) >= 5:
            score += 15
            strengths.append("Gutes technisches Skillset")
        else:
            weaknesses.append("Begrenztes technisches Skillset")
        
        # Education scoring
        if len(education) >= 1:
            score += 20
            if any('master' in str(e.get('degree', '')).lower() or 
                   'msc' in str(e.get('degree', '')).lower() for e in education):
                strengths.append("Akademischer Hintergrund (Master/höher)")
            else:
                strengths.append("Akademischer Hintergrund")
        
        # Generate recommendation
        if score >= 70:
            recommendation = "Geeignet"
            reasoning = "Kandidat erfüllt die meisten Anforderungen und zeigt starke Qualifikationen."
        elif score >= 50:
            recommendation = "Bedingt geeignet"
            reasoning = "Kandidat zeigt Potenzial, aber es gibt einige Lücken in der Qualifikation."
        else:
            recommendation = "Nicht geeignet"
            reasoning = "Kandidat erfüllt zu wenige der Anforderungen für diese Position."
        
        return {
            'recommendation': recommendation,
            'score': score,
            'reasoning': reasoning,
            'strengths': strengths[:3],  # Top 3
            'weaknesses': weaknesses[:3] if weaknesses else ["Keine signifikanten Schwächen identifiziert"],
            'summary': f"{recommendation} - Score: {score}/100"
        }
        
    except Exception as e:
        logger.error(f"Error generating recommendation: {e}")
        return {
            'recommendation': 'Fehler',
            'score': 0,
            'reasoning': 'Konnte keine Empfehlung generieren',
            'strengths': [],
            'weaknesses': [],
            'summary': 'Fehler bei der Empfehlungsgenerierung'
        }


# ============================================================================
# STORY 9.2: REQUIREMENT-MATCHING ANALYSIS
# ============================================================================

def analyze_cv_with_requirements(
    cv_text: str,
    job_requirements: 'JobRequirements',
    model: str = "gpt-4o-mini",
    temperature: float = 0.2
) -> Dict:
    """
    Analyze CV against structured job requirements
    Story 9.2: Enhanced AI Prompt für Requirement-Matching
    
    Args:
        cv_text: Extracted CV text
        job_requirements: JobRequirements object with must/should/nice-to-have
        model: OpenAI model to use
        temperature: Lower than standard for more consistent matching
        
    Returns:
        dict: Enhanced analysis with requirements matching
    """
    from utils.job_requirements import format_requirements_for_prompt
    
    client = get_openai_client()
    
    if not cv_text or len(cv_text.strip()) < 10:
        raise AIAnalysisError("CV text too short for analysis")
    
    # Count tokens
    requirements_text = format_requirements_for_prompt(job_requirements)
    combined_text = f"{cv_text}\n\n{requirements_text}"
    input_tokens = count_tokens(combined_text, model)
    logger.info(f"CV + Requirements contains ~{input_tokens} tokens")
    
    # Enhanced System Prompt for Requirements Matching
    system_prompt = f"""Du bist ein professioneller HR-Experte spezialisiert auf IT-Recruiting.

AUFGABE:
1. Analysiere den CV wie gewohnt (Personal, Experience, Education, Skills)
2. Prüfe **ALLE** Anforderungen der Stellenausschreibung gegen den CV:
   - MUST-HAVE Anforderungen (60% Gewichtung)
   - SHOULD-HAVE Anforderungen (30% Gewichtung) - **WICHTIG: Diese MÜSSEN analysiert werden!**
   - NICE-TO-HAVE Anforderungen (10% Gewichtung) - **WICHTIG: Diese MÜSSEN analysiert werden!**
3. Bewerte ob jede Anforderung erfüllt ist (true/false)
4. Gib KONKRETE BEWEISE aus dem CV an (wörtliche Zitate)

**KRITISCH**: Du MUSST alle drei Kategorien analysieren:
- must_have: Muss komplett ausgefüllt werden
- should_have: Muss komplett ausgefüllt werden (nicht leer lassen!)
- nice_to_have: Muss komplett ausgefüllt werden (nicht leer lassen!)

STELLENANFORDERUNGEN:
{requirements_text}

BEWERTUNGSKRITERIEN:
- "found": true → Skill ist nachweisbar (explizit ODER implizit durch verwandte Erfahrung)
- "found": false → Skill wird nicht erwähnt UND ist auch nicht implizit erkennbar
- "evidence" → Wörtliches Zitat oder konkrete Stelle aus dem CV als Beweis

WICHTIG - SEMANTISCHES MATCHING:
1. **ODER-Verknüpfungen**: Mindestens EINE Option = true
2. **Verwandte Skills zählen**: "SQL-Datenquellen" = SQL, "Power Query" = ETL, "Datenbereinigung" = Datenoptimierung
3. **Skill-Level**: "Grundkenntnisse" / "Mitwirkung" / "Unterstützung bei" = found:true
4. **Technologie-Familien**: "SQL" = alle SQL-DBs, "ETL" = Power Query/SSIS/Data Factory
5. **WICHTIG - Sprachkenntnisse**: IMMER extrahieren wenn vorhanden! Format: [{{"language": "Deutsch", "level": "Muttersprache"}}, ...]

NUR found:false wenn Skill KOMPLETT fehlt (weder explizit noch implizit)

JSON STRUKTUR:
{{
  "standard_cv_analysis": {{
    "personal": {{"name": "...", "email": "...", "phone": "...", "location": "..."}},
    "experience": [...],
    "education": [...],
    "skills": {{
      "technical": ["Skill1", "Skill2"],
      "soft": ["Skill1", "Skill2"],
      "languages": [
        {{"language": "Deutsch", "level": "Muttersprache"}},
        {{"language": "Englisch", "level": "Fließend"}},
        {{"language": "Spanisch", "level": "Grundkenntnisse"}}
      ]
    }},
    "career_level": "...",
    "main_expertise": "..."
  }},
    "requirements_matching": {{
      "must_have": [
        {{
          "category": "Power BI & Datenvisualisierung",
          "skills": [
            {{"skill": "Power BI Reports", "found": true, "evidence": "5 Jahre Power BI Entwicklung"}},
            {{"skill": "DAX", "found": true, "evidence": "Sehr gute DAX-Kenntnisse"}},
            {{"skill": "Power Query", "found": false, "evidence": null}}
          ],
          "category_match_percentage": 67
        }}
      ],
      "should_have": [
        {{
          "category": "Data Lakehouse & Reporting Umgebung",
          "skills": [
            {{"skill": "Data Lakehouse Architektur", "found": true/false, "evidence": "..."}},
            ...
          ],
          "category_match_percentage": ...
        }}
      ],
      "nice_to_have": [
        {{
          "category": "Azure Kenntnisse",
          "skills": [
            {{"skill": "Azure Data Factory", "found": true/false, "evidence": "..."}},
            ...
          ],
          "category_match_percentage": ...
        }}
      ]
    }},
  "gap_analysis": {{
    "critical_missing": ["Liste der fehlenden Must-Have Skills"],
    "nice_missing": ["Liste der fehlenden Should/Nice Skills"],
    "strengths": ["Besondere Stärken für diese Position"]
  }}
}}

WICHTIG:
- Sei sehr präzise beim Matching
- Nur "found": true wenn wirklich nachweisbar
- **MÜSSEN ANALYSIERT WERDEN**: must_have, should_have UND nice_to_have - ALLE drei Kategorien!
- Prüfe JEDE einzelne Anforderung aus ALLEN drei Kategorien gegen den CV
- Gib NUR valides JSON zurück, keine Kommentare
"""
    
    user_prompt = f"Analysiere diesen CV für die Position '{job_requirements.position_title}':\n\n{cv_text}"
    
    try:
        logger.info(f"Sending CV + Requirements to OpenAI (model: {model})")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=3000,  # More tokens for detailed matching
            timeout=90.0  # Longer timeout for complex analysis (increased from 45s)
        )
        
        content = response.choices[0].message.content
        usage = response.usage
        
        logger.info(f"API call successful - Tokens: input={usage.prompt_tokens}, "
                   f"output={usage.completion_tokens}, total={usage.total_tokens}")
        
        # Parse JSON
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        
        analysis_data = json.loads(content)
        
        # Validate requirements_matching structure
        req_matching = analysis_data.get('requirements_matching', {})
        
        # Log what we received for debugging
        logger.info(f"Requirements matching received:")
        logger.info(f"  must_have: {len(req_matching.get('must_have', []))} categories")
        logger.info(f"  should_have: {len(req_matching.get('should_have', []))} categories")
        logger.info(f"  nice_to_have: {len(req_matching.get('nice_to_have', []))} categories")
        
        # Ensure all three categories exist (even if empty)
        if 'must_have' not in req_matching:
            logger.warning("must_have missing from requirements_matching, adding empty array")
            req_matching['must_have'] = []
        if 'should_have' not in req_matching:
            logger.warning("should_have missing from requirements_matching, adding empty array")
            req_matching['should_have'] = []
        if 'nice_to_have' not in req_matching:
            logger.warning("nice_to_have missing from requirements_matching, adding empty array")
            req_matching['nice_to_have'] = []
        
        # Calculate scores
        scores = calculate_requirement_scores(
            req_matching,
            job_requirements
        )
        
        # Log calculated scores
        logger.info(f"Calculated scores: must={scores['must_have']}, should={scores['should_have']}, nice={scores['nice_to_have']}, total={scores['weighted_total']}")
        
        analysis_data['overall_scores'] = scores
        
        # Determine recommendation
        weighted_total = scores['weighted_total']
        thresholds = job_requirements.scoring_thresholds
        recommendations = job_requirements.scoring_recommendations
        
        if weighted_total >= thresholds.get('excellent_match', 80):
            recommendation = recommendations.get('excellent_match', 'Excellent Match')
            match_level = 'excellent_match'
        elif weighted_total >= thresholds.get('good_match', 60):
            recommendation = recommendations.get('good_match', 'Good Match')
            match_level = 'good_match'
        elif weighted_total >= thresholds.get('partial_match', 40):
            recommendation = recommendations.get('partial_match', 'Partial Match')
            match_level = 'partial_match'
        else:
            recommendation = recommendations.get('poor_match', 'Poor Match')
            match_level = 'poor_match'
        
        analysis_data['recommendation'] = recommendation
        analysis_data['match_level'] = match_level
        
        # Add metadata
        cost_estimate = (usage.prompt_tokens * 0.15 / 1_000_000) + \
                       (usage.completion_tokens * 0.60 / 1_000_000)
        
        analysis_data['_metadata'] = {
            'model': model,
            'tokens_input': usage.prompt_tokens,
            'tokens_output': usage.completion_tokens,
            'tokens_total': usage.total_tokens,
            'cost_estimate_usd': round(cost_estimate, 6),
            'position_id': job_requirements.position_id,
            'position_title': job_requirements.position_title
        }
        
        logger.info(f"Requirements matching complete: {match_level} ({weighted_total}/100)")
        
        return analysis_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        raise AIAnalysisError(f"Invalid JSON response from AI: {e}")
    
    except (RateLimitError, APIConnectionError, AuthenticationError, OpenAIError) as e:
        logger.error(f"OpenAI API error: {e}")
        raise AIAnalysisError(f"AI analysis failed: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error in requirements matching: {e}", exc_info=True)
        raise AIAnalysisError(f"Requirements matching failed: {e}")


def calculate_requirement_scores(
    requirements_matching: Dict,
    job_requirements: 'JobRequirements'
) -> Dict:
    """
    Calculate weighted scores for requirements matching
    
    Args:
        requirements_matching: Dict with must_have/should_have/nice_to_have matching results
        job_requirements: JobRequirements object with weights
        
    Returns:
        dict: Calculated scores per level and weighted total
    """
    def calc_level_score(categories: List[Dict]) -> float:
        """Calculate average match percentage across all categories"""
        if not categories:
            return 0.0
        
        total_skills = 0
        matched_skills = 0
        
        for category in categories:
            skills = category.get('skills', [])
            for skill_data in skills:
                total_skills += 1
                if skill_data.get('found', False):
                    matched_skills += 1
        
        if total_skills == 0:
            return 0.0
        
        return (matched_skills / total_skills) * 100
    
    must_score = calc_level_score(requirements_matching.get('must_have', []))
    should_score = calc_level_score(requirements_matching.get('should_have', []))
    nice_score = calc_level_score(requirements_matching.get('nice_to_have', []))
    
    # Get weights from job requirements
    weights = job_requirements.scoring_weights
    must_weight = weights.get('must_have', 0.6)
    should_weight = weights.get('should_have', 0.3)
    nice_weight = weights.get('nice_to_have', 0.1)
    
    weighted_total = (
        must_score * must_weight +
        should_score * should_weight +
        nice_score * nice_weight
    )
    
    return {
        'must_have': round(must_score, 1),
        'should_have': round(should_score, 1),
        'nice_to_have': round(nice_score, 1),
        'weighted_total': round(weighted_total, 1)
    }

