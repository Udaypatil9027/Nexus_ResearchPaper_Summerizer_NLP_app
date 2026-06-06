# summarizer.py
import nltk
import torch
import numpy as np
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
import re

# Download NLTK data once
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

from nltk.tokenize import sent_tokenize


class ResearchPaperSummarizer:
    def __init__(self, model_name="sshleifer/distilbart-cnn-12-6"):
        """Initialize the hybrid summarizer with optimized settings"""
        
        # Use pipeline for faster inference
        self.device = 0 if torch.cuda.is_available() else -1
        self.summarizer = pipeline(
            "summarization",
            model=model_name,
            device=self.device,
            truncation=True
        )
        
        # For extractive scoring
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
    def _ensure_string(self, text):
        """Convert text to string safely"""
        if text is None:
            return ""
        if isinstance(text, (bytes, bytearray)):
            return text.decode('utf-8', errors='ignore')
        return str(text) if not isinstance(text, str) else text
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK with fallback"""
        text = self._ensure_string(text)
        
        if not text.strip():
            return []
        
        try:
            sentences = sent_tokenize(text)
            if sentences:
                return [s.strip() for s in sentences if len(s.strip()) > 20]
        except:
            pass
        
        # Simple fallback
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 30][:50]
    
    def extractive_summarize(self, text: str, num_sentences: int = 8) -> List[str]:
        """Extract key sentences using semantic similarity - Optimized"""
        text = self._ensure_string(text)
        
        if not text.strip():
            return ["No text to summarize"]
        
        sentences = self._split_sentences(text)
        
        if len(sentences) <= num_sentences:
            return sentences
        
        # Get sentence embeddings (faster with batch processing)
        embeddings = self.encoder.encode(sentences, show_progress_bar=False)
        
        # Get document embedding (mean of all sentence embeddings)
        doc_embedding = np.mean(embeddings, axis=0)
        
        # Calculate similarity scores
        similarities = cosine_similarity([doc_embedding], embeddings)[0]
        
        # Get top sentences
        top_indices = np.argsort(similarities)[-num_sentences:]
        top_indices = sorted(top_indices)
        
        return [sentences[i] for i in top_indices]
    
    def abstractive_summarize(self, text: str, max_length: int = 300, 
                              min_length: int = 150) -> str:
        """Generate abstractive summary using DistilBART - Optimized"""
        text = self._ensure_string(text)
        
        if not text.strip():
            return "No text to summarize"
        
        # Optimize text length for faster processing
        if len(text) > 4000:
            text = text[:4000]
        
        try:
            # Adjust length parameters for better quality
            result = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                truncation=True
            )
            return result[0]['summary_text']
        except Exception as e:
            return f"Summary generation error: {str(e)}"
    
    def hybrid_summarize(self, text: str, extractive_ratio: float = 0.25, 
                         max_summary_length: int = 350) -> str:
        """Hybrid approach: extract then abstract - Best quality"""
        text = self._ensure_string(text)
        
        if not text.strip():
            return "No text to summarize"
        
        sentences = self._split_sentences(text)
        
        if not sentences:
            return "Could not extract meaningful sentences"
        
        # Dynamic extractive count based on document length
        if len(sentences) > 40:
            # Extract 20-25% of sentences
            num_extract = max(12, min(25, int(len(sentences) * extractive_ratio)))
            extracted = self.extractive_summarize(text, num_extract)
            processed_text = " ".join(extracted)
        else:
            processed_text = text
        
        # Limit for faster processing
        if len(processed_text) > 3500:
            processed_text = processed_text[:3500]
        
        # Generate final summary with optimal length
        summary = self.abstractive_summarize(
            processed_text, 
            max_length=max_summary_length,
            min_length=int(max_summary_length * 0.6)
        )
        
        return summary