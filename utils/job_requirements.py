"""
Job Requirements Management
Story 9.1: Loading and validation of structured job requirements
"""

import yaml
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RequirementCategory:
    """Single category of requirements (e.g., 'Power BI & Datenvisualisierung')"""
    category: str
    weight: float  # Weight within requirement level (e.g., 0.25 = 25% of must_have)
    skills: List[str]


@dataclass
class PersonalityProfile:
    """Big Five personality profile requirements for a position"""
    dimensions: Dict[str, Dict[str, any]] = field(default_factory=dict)
    # Structure: {
    #   'C': {'ideal_score': 24, 'weight': 0.40, 'min_score': 18},
    #   'O': {'ideal_score': 22, 'weight': 0.20},
    #   ...
    # }


@dataclass
class JobRequirements:
    """Complete job requirements for a position"""
    position_id: str
    position_title: str
    department: str = "IT"
    
    must_have: List[RequirementCategory] = field(default_factory=list)
    should_have: List[RequirementCategory] = field(default_factory=list)
    nice_to_have: List[RequirementCategory] = field(default_factory=list)
    
    # Personality profile (optional)
    personality_profile: Optional[PersonalityProfile] = None
    
    # Scoring configuration
    scoring_weights: Dict[str, float] = field(default_factory=dict)
    scoring_thresholds: Dict[str, int] = field(default_factory=dict)
    scoring_recommendations: Dict[str, str] = field(default_factory=dict)
    
    def get_total_skills_count(self) -> Dict[str, int]:
        """Count total skills per requirement level"""
        return {
            'must_have': sum(len(cat.skills) for cat in self.must_have),
            'should_have': sum(len(cat.skills) for cat in self.should_have),
            'nice_to_have': sum(len(cat.skills) for cat in self.nice_to_have),
            'total': sum(len(cat.skills) for cat in self.must_have + self.should_have + self.nice_to_have)
        }
    
    def get_categories_summary(self) -> str:
        """Get summary of requirement categories"""
        counts = self.get_total_skills_count()
        return (
            f"{self.position_title}\n"
            f"Must-Have: {len(self.must_have)} categories, {counts['must_have']} skills\n"
            f"Should-Have: {len(self.should_have)} categories, {counts['should_have']} skills\n"
            f"Nice-to-Have: {len(self.nice_to_have)} categories, {counts['nice_to_have']} skills\n"
            f"Total: {counts['total']} skills"
        )


class JobRequirementsError(Exception):
    """Custom exception for job requirements errors"""
    pass


def load_job_requirements(
    position_id: str = "power-bi-dev-fttx",
    config_path: str = "config/job_requirements.yaml"
) -> JobRequirements:
    """
    Load job requirements from YAML configuration
    
    Args:
        position_id: ID of the position to load
        config_path: Path to YAML config file
        
    Returns:
        JobRequirements object with all requirements
        
    Raises:
        JobRequirementsError: If loading or validation fails
    """
    try:
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise JobRequirementsError(f"Config file not found: {config_path}")
        
        logger.info(f"Loading job requirements from {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data or 'positions' not in data:
            raise JobRequirementsError("Invalid config structure: 'positions' key missing")
        
        # Find position
        position_data = None
        for pos in data['positions']:
            if pos.get('position_id') == position_id:
                position_data = pos
                break
        
        if not position_data:
            available = [p.get('position_id') for p in data['positions']]
            raise JobRequirementsError(
                f"Position '{position_id}' not found. Available: {available}"
            )
        
        # Parse requirement categories
        must_have = _parse_categories(position_data.get('must_have', []))
        should_have = _parse_categories(position_data.get('should_have', []))
        nice_to_have = _parse_categories(position_data.get('nice_to_have', []))
        
        # Load scoring configuration
        scoring = data.get('scoring', {})
        
        # Load personality profile if available
        personality_data = position_data.get('personality_profile')
        personality_profile = None
        if personality_data:
            personality_profile = PersonalityProfile(
                dimensions=personality_data.get('dimensions', {})
            )
        
        requirements = JobRequirements(
            position_id=position_data['position_id'],
            position_title=position_data['position_title'],
            department=position_data.get('department', 'IT'),
            must_have=must_have,
            should_have=should_have,
            nice_to_have=nice_to_have,
            personality_profile=personality_profile,
            scoring_weights=scoring.get('weights', {}),
            scoring_thresholds=scoring.get('thresholds', {}),
            scoring_recommendations=scoring.get('recommendations', {})
        )
        
        logger.info(f"✓ Job requirements loaded successfully")
        logger.info(f"  {requirements.get_categories_summary()}")
        
        return requirements
        
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error: {e}")
        raise JobRequirementsError(f"Failed to parse YAML: {e}")
    
    except Exception as e:
        logger.error(f"Error loading job requirements: {e}")
        raise JobRequirementsError(f"Failed to load requirements: {e}")


def _parse_categories(categories_data: List[Dict]) -> List[RequirementCategory]:
    """Parse requirement categories from YAML data"""
    categories = []
    
    for cat_data in categories_data:
        if not isinstance(cat_data, dict):
            logger.warning(f"Invalid category data (not a dict): {cat_data}")
            continue
        
        category = cat_data.get('category', 'Unknown')
        weight = cat_data.get('weight', 1.0)
        skills = cat_data.get('skills', [])
        
        if not skills:
            logger.warning(f"Category '{category}' has no skills")
            continue
        
        categories.append(RequirementCategory(
            category=category,
            weight=weight,
            skills=skills
        ))
    
    return categories


def get_all_positions() -> List[Dict[str, str]]:
    """
    Get list of all available positions
    
    Returns:
        List of dicts with position_id and position_title
    """
    try:
        config_path = Path("config/job_requirements.yaml")
        
        if not config_path.exists():
            return []
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        positions = []
        for pos in data.get('positions', []):
            positions.append({
                'position_id': pos.get('position_id'),
                'position_title': pos.get('position_title'),
                'department': pos.get('department', 'IT')
            })
        
        return positions
        
    except Exception as e:
        logger.error(f"Error loading positions list: {e}")
        return []


def format_requirements_for_prompt(requirements: JobRequirements) -> str:
    """
    Format job requirements for AI prompt
    
    Args:
        requirements: JobRequirements object
        
    Returns:
        Formatted string for AI prompt
    """
    lines = [
        f"POSITION: {requirements.position_title}",
        f"",
        "="*60,
        "MUST-HAVE ANFORDERUNGEN (60% Gewichtung):",
        "="*60,
    ]
    
    for category in requirements.must_have:
        lines.append(f"\n{category.category} (Gewicht: {category.weight*100:.0f}%):")
        for skill in category.skills:
            lines.append(f"  - {skill}")
    
    lines.extend([
        "",
        "="*60,
        "SHOULD-HAVE ANFORDERUNGEN (30% Gewichtung):",
        "="*60,
    ])
    
    for category in requirements.should_have:
        lines.append(f"\n{category.category} (Gewicht: {category.weight*100:.0f}%):")
        for skill in category.skills:
            lines.append(f"  - {skill}")
    
    lines.extend([
        "",
        "="*60,
        "NICE-TO-HAVE ANFORDERUNGEN (10% Gewichtung):",
        "="*60,
    ])
    
    for category in requirements.nice_to_have:
        lines.append(f"\n{category.category} (Gewicht: {category.weight*100:.0f}%):")
        for skill in category.skills:
            lines.append(f"  - {skill}")
    
    return "\n".join(lines)


# Example usage for testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("Loading job requirements...")
    try:
        reqs = load_job_requirements("power-bi-dev-fttx")
        print("\n" + reqs.get_categories_summary())
        print("\n" + "="*60)
        print("FORMATTED FOR PROMPT:")
        print("="*60)
        print(format_requirements_for_prompt(reqs))
    except JobRequirementsError as e:
        print(f"Error: {e}")

