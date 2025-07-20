import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TextCleaner:
    """
    Text cleaner for normalizing and preprocessing text
    """
    
    def __init__(self):
        # Common patterns to clean
        self.extra_whitespace_pattern = re.compile(r'\s+')
        self.special_chars_pattern = re.compile(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]')
        self.multiple_newlines_pattern = re.compile(r'\n\s*\n\s*\n+')
    
    async def clean_text(self, text: str, aggressive: bool = False) -> str:
        """
        Clean and normalize text
        """
        try:
            if not text:
                return ""
            
            cleaned_text = text.strip()
            
            # Replace multiple whitespaces with single space
            cleaned_text = self.extra_whitespace_pattern.sub(' ', cleaned_text)
            
            # Replace multiple newlines with double newlines
            cleaned_text = self.multiple_newlines_pattern.sub('\n\n', cleaned_text)
            
            if aggressive:
                # More aggressive cleaning
                cleaned_text = self._aggressive_clean(cleaned_text)
            
            logger.info(f"Cleaned text: {len(text)} -> {len(cleaned_text)} characters")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            return text  # Return original text if cleaning fails
    
    def _aggressive_clean(self, text: str) -> str:
        """
        Aggressive text cleaning
        """
        # Remove special characters (keep basic punctuation)
        text = self.special_chars_pattern.sub('', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Normalize dashes
        text = text.replace('–', '-').replace('—', '-')
        
        # Remove extra punctuation
        text = re.sub(r'[\.]{2,}', '.', text)
        text = re.sub(r'[\!]{2,}', '!', text)
        text = re.sub(r'[\?]{2,}', '?', text)
        
        return text
    
    async def normalize_query(self, query: str) -> str:
        """
        Normalize user query for better retrieval
        """
        try:
            if not query:
                return ""
            
            # Basic cleaning
            normalized = query.strip().lower()
            
            # Remove extra whitespace
            normalized = self.extra_whitespace_pattern.sub(' ', normalized)
            
            # Remove leading/trailing punctuation
            normalized = normalized.strip('.,!?;:')
            
            logger.info(f"Normalized query: {query[:50]}... -> {normalized[:50]}...")
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing query: {str(e)}")
            return query
    
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> list:
        """
        Extract potential keywords from text (basic implementation)
        """
        try:
            # Clean text first
            cleaned_text = await self.clean_text(text)
            
            # Split into words
            words = cleaned_text.lower().split()
            
            # Remove common stop words (basic list)
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
                'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
            }
            
            # Filter out stop words and short words
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            
            # Count frequency
            from collections import Counter
            word_counts = Counter(keywords)
            
            # Get top keywords
            top_keywords = [word for word, count in word_counts.most_common(max_keywords)]
            
            logger.info(f"Extracted {len(top_keywords)} keywords from text")
            return top_keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def get_cleaning_stats(self, original_text: str, cleaned_text: str) -> dict:
        """
        Get statistics about text cleaning
        """
        return {
            "original_length": len(original_text),
            "cleaned_length": len(cleaned_text),
            "characters_removed": len(original_text) - len(cleaned_text),
            "compression_ratio": len(cleaned_text) / len(original_text) if original_text else 0
        } 