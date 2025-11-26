"""
AI Recruiting Demo - Configuration Module
Sichere Environment Variable Verwaltung mit Validation
Environment Configuration & API Key Setup
"""

import os
import secrets
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()


class Config:
    """
    Application Configuration mit Environment Variable Validation
    """
    
    # ====================================
    # OpenAI Configuration (CRITICAL)
    # ====================================
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # ====================================
    # Flask Configuration
    # ====================================
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 10485760))  # 10MB default
    
    # ====================================
    # Email Configuration (OPTIONAL - Epic 8)
    # ====================================
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')
    
    @classmethod
    def validate_critical_config(cls):
        """
        Validate critical configuration variables
        Raises ValueError if critical variables are missing or invalid
        
        Returns:
            bool: True if validation successful
        """
        errors = []
        warnings = []
        
        # Critical: OpenAI API Key
        if not cls.OPENAI_API_KEY or cls.OPENAI_API_KEY == 'sk-proj-your-api-key-here':
            errors.append("❌ OPENAI_API_KEY ist nicht konfiguriert oder ungültig")
            errors.append("   → Füge deinen API Key in .env hinzu: OPENAI_API_KEY=sk-proj-...")
        elif cls.OPENAI_API_KEY.startswith('sk-'):
            logger.info("✓ OpenAI API Key gefunden (starts with 'sk-')")
        else:
            warnings.append("⚠️  OpenAI API Key hat ungewöhnliches Format (erwartet: sk-...)")
        
        # Check SECRET_KEY
        if cls.SECRET_KEY and len(cls.SECRET_KEY) >= 32:
            logger.info("✓ SECRET_KEY konfiguriert")
        else:
            warnings.append("⚠️  SECRET_KEY ist nicht gesetzt (verwende auto-generated)")
        
        # Check Upload Folder
        if cls.UPLOAD_FOLDER:
            logger.info(f"✓ Upload Folder: {cls.UPLOAD_FOLDER}")
            # Create folder if not exists
            os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        else:
            errors.append("❌ UPLOAD_FOLDER ist nicht konfiguriert")
        
        # Check Max Content Length
        if cls.MAX_CONTENT_LENGTH > 0:
            logger.info(f"✓ Max Content Length: {cls.MAX_CONTENT_LENGTH / (1024*1024):.1f}MB")
        else:
            errors.append("❌ MAX_CONTENT_LENGTH muss > 0 sein")
        
        # Optional: Email Configuration (nur Warnung, kein Error)
        if not cls.MAIL_USERNAME or not cls.MAIL_PASSWORD:
            warnings.append("⚠️  Email-Konfiguration unvollständig (Epic 8 optional)")
        
        # Print warnings
        if warnings:
            logger.warning("=" * 60)
            logger.warning("CONFIGURATION WARNINGS:")
            for warning in warnings:
                logger.warning(warning)
            logger.warning("=" * 60)
        
        # Handle errors
        if errors:
            logger.error("=" * 60)
            logger.error("❌ CRITICAL CONFIGURATION ERRORS:")
            for error in errors:
                logger.error(error)
            logger.error("=" * 60)
            raise ValueError("Critical configuration errors - see logs above")
        
        # Success
        logger.info("=" * 60)
        logger.info("✓ CONFIG LOADED SUCCESSFULLY")
        logger.info("=" * 60)
        return True
    
    @classmethod
    def get_summary(cls):
        """
        Get configuration summary for debugging
        (with sanitized sensitive data)
        """
        return {
            'openai_configured': bool(cls.OPENAI_API_KEY and cls.OPENAI_API_KEY.startswith('sk-')),
            'debug_mode': cls.DEBUG,
            'upload_folder': cls.UPLOAD_FOLDER,
            'max_upload_size_mb': cls.MAX_CONTENT_LENGTH / (1024*1024),
            'email_configured': bool(cls.MAIL_USERNAME and cls.MAIL_PASSWORD),
        }

