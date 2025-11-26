"""
PDF Text Extraction Utilities
Story 3.1: pdfplumber Integration & Basic Text Extraction
Story 3.2: Table Extraction for Skills-Matrices
"""

import pdfplumber
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Custom exception for PDF extraction errors"""
    pass


def extract_text_from_pdf(pdf_path: str, extract_tables: bool = True, use_fallback: bool = True) -> Dict[str, any]:
    """
    Extract text and metadata from PDF using pdfplumber
    Story 3.1: Basic text extraction
    Story 3.2: Table extraction
    Story 3.3: Error handling with fallback
    
    Args:
        pdf_path (str): Path to PDF file
        extract_tables (bool): Whether to extract tables (default: True)
        use_fallback (bool): Use simple extraction as fallback on error (default: True)
        
    Returns:
        dict: Extracted data with text, tables, and metadata
        
    Raises:
        PDFExtractionError: If extraction fails (and fallback disabled/fails)
    """
    try:
        logger.info(f"Starting PDF extraction: {pdf_path}")
        
        with pdfplumber.open(pdf_path) as pdf:
            # Extract metadata
            metadata = pdf.metadata or {}
            num_pages = len(pdf.pages)
            
            logger.info(f"PDF has {num_pages} pages")
            
            # Extract text from all pages
            full_text = ""
            all_tables = []
            
            for page_num, page in enumerate(pdf.pages, start=1):
                logger.debug(f"Processing page {page_num}/{num_pages}")
                
                # Extract text
                page_text = page.extract_text()
                
                if page_text:
                    full_text += f"\n\n=== Seite {page_num} ===\n\n"
                    full_text += page_text
                else:
                    logger.warning(f"No text found on page {page_num}")
                
                # Extract tables if requested
                if extract_tables:
                    tables = page.extract_tables()
                    if tables:
                        logger.info(f"Found {len(tables)} table(s) on page {page_num}")
                        for table_idx, table in enumerate(tables, start=1):
                            all_tables.append({
                                'page': page_num,
                                'table_index': table_idx,
                                'data': table
                            })
                            
                            # Add formatted table to text
                            full_text += f"\n\n[TABELLE {table_idx} - Seite {page_num}]\n"
                            full_text += format_table(table)
                            full_text += "\n"
            
            # Clean up text
            full_text = full_text.strip()
            
            # Prepare result
            result = {
                'text': full_text,
                'num_pages': num_pages,
                'num_tables': len(all_tables),
                'tables': all_tables,
                'metadata': {
                    'title': metadata.get('Title', ''),
                    'author': metadata.get('Author', ''),
                    'subject': metadata.get('Subject', ''),
                    'creator': metadata.get('Creator', ''),
                },
                'char_count': len(full_text),
                'word_count': len(full_text.split())
            }
            
            logger.info(f"Extraction complete: {result['word_count']} words, {result['num_tables']} tables")
            
            return result
            
    except FileNotFoundError:
        error_msg = f"PDF file not found: {pdf_path}"
        logger.error(error_msg)
        raise PDFExtractionError(error_msg)
    
    except Exception as e:
        error_msg = f"Error extracting PDF {pdf_path}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Story 3.3: Try fallback method
        if use_fallback:
            logger.warning("Attempting fallback extraction (simple mode)...")
            try:
                text = extract_text_simple(pdf_path)
                logger.info("Fallback extraction successful")
                return {
                    'text': text,
                    'num_pages': 1,  # Unknown in fallback mode
                    'num_tables': 0,
                    'tables': [],
                    'metadata': {},
                    'char_count': len(text),
                    'word_count': len(text.split()),
                    'fallback_used': True
                }
            except Exception as fallback_error:
                logger.error(f"Fallback extraction also failed: {fallback_error}")
        
        raise PDFExtractionError(error_msg)


def format_table(table: List[List[str]]) -> str:
    """
    Format table data as pipe-separated text
    
    Args:
        table: List of rows (each row is a list of cells)
        
    Returns:
        str: Formatted table string
    """
    if not table:
        return ""
    
    formatted_lines = []
    
    for row in table:
        # Clean and join cells
        cells = [str(cell).strip() if cell else "" for cell in row]
        formatted_lines.append(" | ".join(cells))
    
    return "\n".join(formatted_lines)


def get_pdf_info(pdf_path: str) -> Dict[str, any]:
    """
    Get basic PDF information without extracting full text
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        dict: PDF information
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return {
                'num_pages': len(pdf.pages),
                'metadata': pdf.metadata or {},
                'page_sizes': [
                    {'width': page.width, 'height': page.height}
                    for page in pdf.pages
                ]
            }
    except Exception as e:
        logger.error(f"Error getting PDF info: {e}")
        return {'error': str(e)}


def extract_text_simple(pdf_path: str) -> str:
    """
    Simple text extraction without tables or metadata
    Fallback method for when full extraction fails
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        str: Extracted text
        
    Raises:
        PDFExtractionError: If even simple extraction fails
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                except Exception as page_error:
                    logger.warning(f"Failed to extract page: {page_error}")
                    continue  # Skip problematic pages
            
            if not text.strip():
                raise PDFExtractionError("No text could be extracted from PDF")
            
            return text.strip()
    except PDFExtractionError:
        raise
    except Exception as e:
        logger.error(f"Simple extraction failed: {e}")
        raise PDFExtractionError(f"Text extraction failed: {e}")

