"""
File Cleanup Utilities
Story 2.4: Temporary File Storage & Cleanup
"""

import os
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def delete_file(filepath):
    """
    Safely delete a file
    
    Args:
        filepath (str): Path to file
        
    Returns:
        bool: True if deleted successfully
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"File deleted: {filepath}")
            return True
        else:
            logger.warning(f"File not found for deletion: {filepath}")
            return False
    except Exception as e:
        logger.error(f"Error deleting file {filepath}: {e}")
        return False


def cleanup_old_files(upload_folder, max_age_seconds=3600):
    """
    Clean up files older than max_age_seconds
    
    Args:
        upload_folder (str): Upload directory path
        max_age_seconds (int): Maximum file age in seconds (default: 1 hour)
        
    Returns:
        int: Number of files deleted
    """
    if not os.path.exists(upload_folder):
        logger.warning(f"Upload folder not found: {upload_folder}")
        return 0
    
    deleted_count = 0
    current_time = time.time()
    
    try:
        for filename in os.listdir(upload_folder):
            filepath = os.path.join(upload_folder, filename)
            
            # Skip if not a file
            if not os.path.isfile(filepath):
                continue
            
            # Check file age
            file_age = current_time - os.path.getmtime(filepath)
            
            if file_age > max_age_seconds:
                if delete_file(filepath):
                    deleted_count += 1
                    logger.info(f"Deleted old file: {filename} (age: {file_age:.0f}s)")
        
        if deleted_count > 0:
            logger.info(f"Cleanup complete: {deleted_count} old files deleted")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return deleted_count


def get_upload_folder_size(upload_folder):
    """
    Calculate total size of upload folder
    
    Args:
        upload_folder (str): Upload directory path
        
    Returns:
        dict: Folder statistics
    """
    if not os.path.exists(upload_folder):
        return {'total_files': 0, 'total_size_mb': 0}
    
    total_size = 0
    file_count = 0
    
    for filename in os.listdir(upload_folder):
        filepath = os.path.join(upload_folder, filename)
        if os.path.isfile(filepath):
            total_size += os.path.getsize(filepath)
            file_count += 1
    
    return {
        'total_files': file_count,
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2)
    }

