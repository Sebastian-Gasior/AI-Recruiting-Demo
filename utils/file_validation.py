"""
File Validation Utilities
Story 2.2: File Validation (Type & Size)
"""

import os
import logging

logger = logging.getLogger(__name__)

# Allowed file configuration
ALLOWED_EXTENSIONS = {'pdf'}
ALLOWED_MIME_TYPES = {'application/pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    """
    Check if filename has allowed extension
    
    Args:
        filename (str): Original filename
        
    Returns:
        bool: True if extension is allowed
    """
    if not filename:
        return False
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_upload(file, max_size=MAX_FILE_SIZE):
    """
    Comprehensive file validation
    
    Args:
        file: FileStorage object from Flask request
        max_size: Maximum allowed file size in bytes
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    
    # Check if file exists
    if not file:
        return False, "Bitte wählen Sie eine PDF-Datei"
    
    # Check if filename is empty
    if file.filename == '':
        return False, "Bitte wählen Sie eine PDF-Datei"
    
    # Check file extension
    if not allowed_file(file.filename):
        logger.warning(f"Invalid file extension: {file.filename}")
        return False, "Nur PDF-Dateien erlaubt"
    
    # Read file content to check size and MIME type
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    # Check file size
    if file_size == 0:
        logger.warning(f"Empty file: {file.filename}")
        return False, "Die Datei ist leer"
    
    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        logger.warning(f"File too large: {file.filename} ({size_mb:.1f}MB > {max_mb}MB)")
        return False, f"Datei zu groß (max {int(max_mb)}MB)"
    
    # Check MIME type (more reliable than extension)
    try:
        # Read first 2048 bytes for MIME detection
        file_header = file.read(2048)
        file.seek(0)  # Reset file pointer
        
        # Simple PDF magic number check (more reliable than python-magic on Windows)
        if file_header.startswith(b'%PDF'):
            logger.info(f"File validation passed: {file.filename} ({file_size} bytes)")
            return True, None
        else:
            logger.warning(f"Invalid PDF format: {file.filename}")
            return False, "PDF-Datei konnte nicht gelesen werden"
            
    except Exception as e:
        logger.error(f"Error validating file {file.filename}: {e}")
        return False, "Fehler beim Validieren der Datei"


def get_file_info(file):
    """
    Extract file information
    
    Args:
        file: FileStorage object
        
    Returns:
        dict: File information
    """
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    return {
        'filename': file.filename,
        'size': file_size,
        'size_mb': round(file_size / (1024 * 1024), 2),
        'extension': file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else None
    }

