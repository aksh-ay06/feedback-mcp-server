"""
Theme Extraction

Extracts and clusters themes from customer feedback using NLP techniques
"""

import logging
from collections import Counter
from typing import Dict, List

logger = logging.getLogger(__name__)


class ThemeExtractor:
    """Extract themes from feedback using clustering and NLP"""
    
    def __init__(self):
        """Initialize theme extractor"""
        self.vectorizer = None
        self.clustering_model = None
        self.nlp = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models and vectorizers"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.cluster import KMeans
            import spacy
            
            # Initialize TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 3),
                min_df=2
            )
            
            # Try to load spaCy model
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found, using basic extraction")
                self.nlp = None
            
            logger.info("Theme extractor initialized")
        except Exception as e:
            logger.error(f"Error initializing theme extractor: {e}")
            self.vectorizer = None
    
    async def extract_themes(
        self,
        texts: List[str],
        num_themes: int = 10,
        min_frequency: int = 3
    ) -> List[Dict]:
        """
        Extract themes from a collection of feedback texts
        
        Args:
            texts: List of feedback text strings
            num_themes: Number of themes to extract
            min_frequency: Minimum frequency for a theme to be included
            
        Returns:
            List of theme dictionaries with name, keywords, frequency
        """
        if not texts:
            return []
        
        try:
            if self.vectorizer and len(texts) >= num_themes:
                return await self._extract_with_clustering(texts, num_themes, min_frequency)
            else:
                return await self._extract_with_keywords(texts, num_themes, min_frequency)
        except Exception as e:
            logger.error(f"Error extracting themes: {e}")
            return await self._extract_with_keywords(texts, num_themes, min_frequency)
    
    async def _extract_with_clustering(
        self,
        texts: List[str],
        num_themes: int,
        min_frequency: int
    ) -> List[Dict]:
        """Extract themes using TF-IDF and K-means clustering"""
        from sklearn.cluster import KMeans
        
        try:
            # Vectorize texts
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Cluster
            kmeans = KMeans(n_clusters=num_themes, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # Get feature names
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Extract top terms for each cluster
            themes = []
            for cluster_id in range(num_themes):
                # Get cluster center
                center = kmeans.cluster_centers_[cluster_id]
                
                # Get top features for this cluster
                top_indices = center.argsort()[-10:][::-1]
                top_terms = [feature_names[i] for i in top_indices]
                
                # Count documents in this cluster
                cluster_size = sum(1 for label in cluster_labels if label == cluster_id)
                
                if cluster_size >= min_frequency:
                    # Generate theme name from top terms
                    theme_name = self._generate_theme_name(top_terms[:3])
                    
                    themes.append({
                        "name": theme_name,
                        "keywords": top_terms[:5],
                        "frequency": cluster_size,
                        "confidence": float(cluster_size / len(texts))
                    })
            
            # Sort by frequency
            themes.sort(key=lambda x: x['frequency'], reverse=True)
            
            return themes
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return await self._extract_with_keywords(texts, num_themes, min_frequency)
    
    async def _extract_with_keywords(
        self,
        texts: List[str],
        num_themes: int,
        min_frequency: int
    ) -> List[Dict]:
        """Extract themes using simple keyword frequency"""
        # Extract key phrases
        all_phrases = []
        
        if self.nlp:
            # Use spaCy for better phrase extraction
            for text in texts:
                doc = self.nlp(text[:1000])  # Limit text length
                
                # Extract noun phrases
                noun_phrases = [chunk.text.lower() for chunk in doc.noun_chunks]
                all_phrases.extend(noun_phrases)
                
                # Extract named entities
                entities = [ent.text.lower() for ent in doc.ents]
                all_phrases.extend(entities)
        else:
            # Fallback to simple word extraction
            import re
            for text in texts:
                # Extract words (simple tokenization)
                words = re.findall(r'\b[a-z]{4,}\b', text.lower())
                all_phrases.extend(words)
        
        # Count frequency
        phrase_counts = Counter(all_phrases)
        
        # Filter common stop phrases
        stop_phrases = {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'their'}
        filtered_counts = {
            phrase: count 
            for phrase, count in phrase_counts.items() 
            if phrase not in stop_phrases and count >= min_frequency
        }
        
        # Get top themes
        top_phrases = sorted(filtered_counts.items(), key=lambda x: x[1], reverse=True)[:num_themes]
        
        themes = [
            {
                "name": phrase.title(),
                "keywords": [phrase],
                "frequency": count,
                "confidence": float(count / len(texts))
            }
            for phrase, count in top_phrases
        ]
        
        return themes
    
    def _generate_theme_name(self, top_terms: List[str]) -> str:
        """Generate a readable theme name from top terms"""
        # Clean and capitalize
        cleaned = [term.replace('_', ' ').title() for term in top_terms]
        
        # Combine first 2-3 terms
        if len(cleaned) >= 2:
            return f"{cleaned[0]} & {cleaned[1]}"
        elif len(cleaned) == 1:
            return cleaned[0]
        else:
            return "General Feedback"
    
    async def track_theme_evolution(
        self,
        historical_themes: List[Dict],
        current_themes: List[Dict]
    ) -> Dict:
        """
        Track how themes evolve over time
        
        Args:
            historical_themes: Themes from previous period
            current_themes: Themes from current period
            
        Returns:
            Dictionary with evolution analysis
        """
        if not historical_themes or not current_themes:
            return {
                "emerging": current_themes[:5] if current_themes else [],
                "declining": [],
                "stable": []
            }
        
        # Build name to theme mapping
        historical_map = {t['name']: t for t in historical_themes}
        current_map = {t['name']: t for t in current_themes}
        
        emerging = []
        declining = []
        stable = []
        
        # Find emerging themes (new or growing significantly)
        for name, theme in current_map.items():
            if name not in historical_map:
                emerging.append(theme)
            else:
                old_freq = historical_map[name]['frequency']
                new_freq = theme['frequency']
                
                growth_rate = (new_freq - old_freq) / old_freq if old_freq > 0 else 1.0
                
                if growth_rate > 0.5:
                    emerging.append({**theme, "growth_rate": growth_rate})
                elif growth_rate < -0.3:
                    declining.append({**theme, "growth_rate": growth_rate})
                else:
                    stable.append(theme)
        
        # Find declining themes (disappeared or shrinking)
        for name, theme in historical_map.items():
            if name not in current_map:
                declining.append({**theme, "status": "disappeared"})
        
        return {
            "emerging": sorted(emerging, key=lambda x: x.get('growth_rate', x['frequency']), reverse=True),
            "declining": sorted(declining, key=lambda x: x.get('growth_rate', -x['frequency'])),
            "stable": sorted(stable, key=lambda x: x['frequency'], reverse=True)
        }
    
    def cluster_similar_feedback(
        self,
        texts: List[str],
        similarity_threshold: float = 0.7
    ) -> List[List[int]]:
        """
        Group similar feedback items together
        
        Args:
            texts: List of feedback texts
            similarity_threshold: Minimum similarity to group together
            
        Returns:
            List of lists, where each inner list contains indices of similar items
        """
        if not self.vectorizer or len(texts) < 2:
            return [[i] for i in range(len(texts))]
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Vectorize
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Calculate similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Group similar items
            clusters = []
            used = set()
            
            for i in range(len(texts)):
                if i in used:
                    continue
                
                cluster = [i]
                used.add(i)
                
                # Find similar items
                for j in range(i + 1, len(texts)):
                    if j not in used and similarity_matrix[i][j] >= similarity_threshold:
                        cluster.append(j)
                        used.add(j)
                
                clusters.append(cluster)
            
            return clusters
        except Exception as e:
            logger.error(f"Error clustering feedback: {e}")
            return [[i] for i in range(len(texts))]
