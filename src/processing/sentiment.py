"""
Sentiment Analysis

Uses transformer models to analyze sentiment of customer feedback
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Sentiment analysis using transformer models"""
    
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initialize sentiment analyzer
        
        Args:
            model_name: Name of the pre-trained model to use
        """
        self.model_name = model_name
        self.pipeline = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the sentiment analysis pipeline"""
        try:
            from transformers import pipeline
            
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                top_k=None
            )
            logger.info(f"Sentiment analyzer initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error initializing sentiment model: {e}")
            logger.warning("Falling back to rule-based sentiment analysis")
            self.pipeline = None
    
    async def analyze(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (sentiment, score) where:
            - sentiment: "positive", "negative", or "neutral"
            - score: float between -1.0 (very negative) and 1.0 (very positive)
        """
        if not text or not text.strip():
            return "neutral", 0.0
        
        try:
            if self.pipeline:
                return await self._analyze_with_model(text)
            else:
                return self._analyze_rule_based(text)
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return "neutral", 0.0
    
    async def analyze_batch(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        Analyze sentiment of multiple texts efficiently
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of (sentiment, score) tuples
        """
        results = []
        
        if self.pipeline:
            try:
                # Use model's batch processing
                predictions = self.pipeline(texts, truncation=True, max_length=512)
                
                for pred in predictions:
                    sentiment, score = self._parse_model_output(pred)
                    results.append((sentiment, score))
            except Exception as e:
                logger.error(f"Error in batch sentiment analysis: {e}")
                # Fallback to rule-based for all
                results = [self._analyze_rule_based(text) for text in texts]
        else:
            results = [self._analyze_rule_based(text) for text in texts]
        
        return results
    
    async def _analyze_with_model(self, text: str) -> Tuple[str, float]:
        """Analyze sentiment using transformer model"""
        try:
            # Truncate text to model's max length
            truncated_text = text[:512]
            
            result = self.pipeline(truncated_text)[0]
            
            return self._parse_model_output(result)
        except Exception as e:
            logger.error(f"Model sentiment analysis failed: {e}")
            return self._analyze_rule_based(text)
    
    def _parse_model_output(self, result: Dict) -> Tuple[str, float]:
        """Parse model output to standard format"""
        if isinstance(result, list):
            # Multiple labels returned
            scores = {item['label'].lower(): item['score'] for item in result}
            
            positive_score = scores.get('positive', 0.0)
            negative_score = scores.get('negative', 0.0)
            
            # Calculate normalized score
            score = positive_score - negative_score
            
            if score > 0.1:
                sentiment = "positive"
            elif score < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return sentiment, score
        else:
            # Single label returned
            label = result['label'].lower()
            confidence = result['score']
            
            if 'positive' in label:
                return "positive", confidence
            elif 'negative' in label:
                return "negative", -confidence
            else:
                return "neutral", 0.0
    
    def _analyze_rule_based(self, text: str) -> Tuple[str, float]:
        """
        Fallback rule-based sentiment analysis
        
        Uses simple keyword matching when model is unavailable
        """
        text_lower = text.lower()
        
        # Positive keywords
        positive_words = [
            'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'perfect', 'best', 'awesome', 'impressive',
            'thank', 'thanks', 'good', 'nice', 'happy', 'helpful'
        ]
        
        # Negative keywords
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'worst',
            'hate', 'disappointed', 'frustrating', 'poor', 'broken',
            'bug', 'issue', 'problem', 'error', 'fail', 'crash',
            'slow', 'confusing', 'difficult', 'useless'
        ]
        
        # Count matches
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate score
        total = positive_count + negative_count
        if total == 0:
            return "neutral", 0.0
        
        score = (positive_count - negative_count) / total
        
        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return sentiment, score
    
    def get_sentiment_trends(
        self,
        sentiments: List[Tuple[str, float]],
        window_size: int = 7
    ) -> Dict[str, any]:
        """
        Calculate sentiment trends over a series of feedback
        
        Args:
            sentiments: List of (sentiment, score) tuples in chronological order
            window_size: Size of moving average window
            
        Returns:
            Dictionary with trend information
        """
        if not sentiments:
            return {
                "trend": "stable",
                "direction": "neutral",
                "confidence": 0.0
            }
        
        # Calculate moving average
        scores = [score for _, score in sentiments]
        
        if len(scores) < window_size:
            window_size = len(scores)
        
        recent_avg = sum(scores[-window_size:]) / window_size
        
        if len(scores) >= window_size * 2:
            earlier_avg = sum(scores[-window_size*2:-window_size]) / window_size
            change = recent_avg - earlier_avg
            
            if change > 0.1:
                trend = "improving"
            elif change < -0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
            change = 0.0
        
        return {
            "trend": trend,
            "recent_average": recent_avg,
            "change": change,
            "direction": "positive" if recent_avg > 0 else "negative" if recent_avg < 0 else "neutral"
        }
