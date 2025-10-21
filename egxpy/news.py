"""
EGXpy News Fetching Module

This module provides comprehensive news fetching capabilities for Egyptian stocks
and financial markets. It supports multiple news sources and includes sentiment analysis.

Features:
- Multi-source news aggregation (NewsAPI, Alpha Vantage, GDELT)
- Sentiment analysis using VADER and TextBlob
- Intelligent caching to avoid rate limits
- Relevance scoring for news articles
- Support for Egyptian market-specific keywords

Author: EGXpy Contributors
"""

import os
import json
import pickle
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import hashlib

try:
    import requests
    from retry import retry
except ImportError as e:
    raise ImportError(f"Required dependency missing: {e}. Please install requirements.txt")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NewsCache:
    """Simple file-based caching system for news data"""

    def __init__(self, cache_dir: str = "./cache/news", cache_duration_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_duration = timedelta(hours=cache_duration_hours)
        logger.info(f"News cache initialized at {self.cache_dir}")

    def _get_cache_key(self, query: str, source: str, **params) -> str:
        """Generate cache key from query parameters"""
        cache_str = f"{source}:{query}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(cache_str.encode()).hexdigest()

    def get(self, query: str, source: str, **params) -> Optional[Dict]:
        """Retrieve cached data if available and not expired"""
        cache_key = self._get_cache_key(query, source, **params)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if not cache_file.exists():
            logger.debug(f"Cache miss for {query} from {source}")
            return None

        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)

            # Check if cache is expired
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time > self.cache_duration:
                logger.debug(f"Cache expired for {query} from {source}")
                cache_file.unlink()
                return None

            logger.info(f"Cache hit for {query} from {source}")
            return cached_data['data']
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None

    def set(self, query: str, source: str, data: Dict, **params):
        """Store data in cache"""
        cache_key = self._get_cache_key(query, source, **params)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        cached_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
            logger.debug(f"Cached data for {query} from {source}")
        except Exception as e:
            logger.warning(f"Error writing cache: {e}")

    def clear_expired(self):
        """Remove all expired cache files"""
        count = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                cache_time = datetime.fromisoformat(cached_data['timestamp'])
                if datetime.now() - cache_time > self.cache_duration:
                    cache_file.unlink()
                    count += 1
            except Exception as e:
                logger.warning(f"Error checking cache file {cache_file}: {e}")
        logger.info(f"Cleared {count} expired cache files")


class NewsSource:
    """Base class for news sources"""

    def __init__(self, api_key: Optional[str] = None, cache: Optional[NewsCache] = None):
        self.api_key = api_key
        self.cache = cache
        self.source_name = self.__class__.__name__

    def fetch_news(self, query: str, **kwargs) -> List[Dict]:
        """Fetch news articles - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement fetch_news()")

    def _make_request(self, url: str, params: Dict, use_cache: bool = True) -> Optional[Dict]:
        """Make HTTP request with caching support"""
        # Check cache first
        if use_cache and self.cache:
            cached = self.cache.get(url, self.source_name, **params)
            if cached:
                return cached

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Cache the result
            if use_cache and self.cache:
                self.cache.set(url, self.source_name, data, **params)

            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {self.source_name}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {self.source_name}: {e}")
            return None


class NewsAPISource(NewsSource):
    """NewsAPI.org integration - requires API key"""

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: Optional[str] = None, cache: Optional[NewsCache] = None):
        super().__init__(api_key, cache)
        if not self.api_key:
            logger.warning("NewsAPI key not provided. This source will be disabled.")

    @retry((requests.exceptions.RequestException), tries=3, delay=1, backoff=2)
    def fetch_news(self, query: str, from_date: Optional[str] = None,
                   to_date: Optional[str] = None, language: str = 'en',
                   sort_by: str = 'relevancy', page_size: int = 20) -> List[Dict]:
        """
        Fetch news from NewsAPI

        Args:
            query: Search query (ticker symbol, company name, or keywords)
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
            language: Language code (default: 'en')
            sort_by: Sort by 'relevancy', 'popularity', or 'publishedAt'
            page_size: Number of results (max 100)

        Returns:
            List of news articles
        """
        if not self.api_key:
            logger.warning("NewsAPI key not provided, skipping this source")
            return []

        params = {
            'q': query,
            'apiKey': self.api_key,
            'language': language,
            'sortBy': sort_by,
            'pageSize': min(page_size, 100)
        }

        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date

        data = self._make_request(self.BASE_URL, params)

        if not data or data.get('status') != 'ok':
            logger.error(f"NewsAPI returned error: {data}")
            return []

        articles = []
        for article in data.get('articles', []):
            articles.append({
                'source': 'NewsAPI',
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'content': article.get('content', ''),
                'url': article.get('url', ''),
                'published_at': article.get('publishedAt', ''),
                'author': article.get('author', ''),
                'source_name': article.get('source', {}).get('name', '')
            })

        logger.info(f"Fetched {len(articles)} articles from NewsAPI for query: {query}")
        return articles


class AlphaVantageNewsSource(NewsSource):
    """Alpha Vantage News & Sentiment API integration"""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str] = None, cache: Optional[NewsCache] = None):
        super().__init__(api_key, cache)
        if not self.api_key:
            logger.warning("Alpha Vantage API key not provided. This source will be disabled.")

    @retry((requests.exceptions.RequestException), tries=3, delay=1, backoff=2)
    def fetch_news(self, tickers: Optional[List[str]] = None, topics: Optional[List[str]] = None,
                   time_from: Optional[str] = None, time_to: Optional[str] = None,
                   limit: int = 50) -> List[Dict]:
        """
        Fetch news from Alpha Vantage

        Args:
            tickers: List of ticker symbols
            topics: List of topics (e.g., 'earnings', 'ipo', 'mergers_and_acquisitions')
            time_from: Start time in YYYYMMDDThhmm format
            time_to: End time in YYYYMMDDThhmm format
            limit: Number of results (max 1000)

        Returns:
            List of news articles with sentiment scores
        """
        if not self.api_key:
            logger.warning("Alpha Vantage API key not provided, skipping this source")
            return []

        params = {
            'function': 'NEWS_SENTIMENT',
            'apikey': self.api_key,
            'limit': min(limit, 1000)
        }

        if tickers:
            params['tickers'] = ','.join(tickers)
        if topics:
            params['topics'] = ','.join(topics)
        if time_from:
            params['time_from'] = time_from
        if time_to:
            params['time_to'] = time_to

        data = self._make_request(self.BASE_URL, params)

        if not data or 'feed' not in data:
            logger.error(f"Alpha Vantage returned error: {data}")
            return []

        articles = []
        for item in data.get('feed', []):
            # Extract ticker sentiments if available
            ticker_sentiment = {}
            for ticker_info in item.get('ticker_sentiment', []):
                ticker = ticker_info.get('ticker', '')
                sentiment = ticker_info.get('ticker_sentiment_score', 0)
                ticker_sentiment[ticker] = float(sentiment)

            articles.append({
                'source': 'AlphaVantage',
                'title': item.get('title', ''),
                'summary': item.get('summary', ''),
                'url': item.get('url', ''),
                'published_at': item.get('time_published', ''),
                'authors': item.get('authors', []),
                'source_name': item.get('source', ''),
                'overall_sentiment_score': float(item.get('overall_sentiment_score', 0)),
                'overall_sentiment_label': item.get('overall_sentiment_label', ''),
                'ticker_sentiment': ticker_sentiment
            })

        logger.info(f"Fetched {len(articles)} articles from Alpha Vantage")
        return articles


class GDELTNewsSource(NewsSource):
    """GDELT Project - Free global news database"""

    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    @retry((requests.exceptions.RequestException), tries=3, delay=1, backoff=2)
    def fetch_news(self, query: str, mode: str = 'artlist',
                   max_records: int = 250, timespan: str = '7d',
                   source_country: Optional[str] = None) -> List[Dict]:
        """
        Fetch news from GDELT

        Args:
            query: Search query
            mode: 'artlist' for article list
            max_records: Maximum number of records (max 250)
            timespan: Time span (e.g., '7d', '1m', '3m')
            source_country: Country code (e.g., 'EG' for Egypt)

        Returns:
            List of news articles
        """
        params = {
            'query': query,
            'mode': mode,
            'maxrecords': min(max_records, 250),
            'timespan': timespan,
            'format': 'json'
        }

        if source_country:
            params['sourcecountry'] = source_country

        data = self._make_request(self.BASE_URL, params)

        if not data or 'articles' not in data:
            logger.error(f"GDELT returned error or no articles")
            return []

        articles = []
        for article in data.get('articles', []):
            articles.append({
                'source': 'GDELT',
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'published_at': article.get('seendate', ''),
                'domain': article.get('domain', ''),
                'language': article.get('language', ''),
                'source_country': article.get('sourcecountry', '')
            })

        logger.info(f"Fetched {len(articles)} articles from GDELT for query: {query}")
        return articles


class SentimentAnalyzer:
    """Sentiment analysis for news articles using multiple methods"""

    def __init__(self, method: str = 'vader'):
        """
        Initialize sentiment analyzer

        Args:
            method: 'vader' (default, better for financial text) or 'textblob'
        """
        self.method = method.lower()

        if self.method == 'vader':
            try:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                self.analyzer = SentimentIntensityAnalyzer()
                logger.info("VADER sentiment analyzer initialized")
            except ImportError:
                logger.error("vaderSentiment not installed. Install with: pip install vaderSentiment")
                self.analyzer = None

        elif self.method == 'textblob':
            try:
                from textblob import TextBlob
                self.TextBlob = TextBlob
                logger.info("TextBlob sentiment analyzer initialized")
            except ImportError:
                logger.error("textblob not installed. Install with: pip install textblob")
                self.TextBlob = None
        else:
            logger.warning(f"Unknown sentiment method: {method}. Using vader as fallback.")
            self.method = 'vader'
            try:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                self.analyzer = SentimentIntensityAnalyzer()
            except ImportError:
                self.analyzer = None

    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment scores
        """
        if not text or not text.strip():
            return {'score': 0.0, 'label': 'neutral', 'method': self.method}

        if self.method == 'vader' and self.analyzer:
            scores = self.analyzer.polarity_scores(text)
            compound = scores['compound']

            # Classify sentiment
            if compound >= 0.05:
                label = 'positive'
            elif compound <= -0.05:
                label = 'negative'
            else:
                label = 'neutral'

            return {
                'score': compound,
                'label': label,
                'positive': scores['pos'],
                'negative': scores['neg'],
                'neutral': scores['neu'],
                'method': 'vader'
            }

        elif self.method == 'textblob' and self.TextBlob:
            blob = self.TextBlob(text)
            polarity = blob.sentiment.polarity

            # Classify sentiment
            if polarity > 0.1:
                label = 'positive'
            elif polarity < -0.1:
                label = 'negative'
            else:
                label = 'neutral'

            return {
                'score': polarity,
                'label': label,
                'subjectivity': blob.sentiment.subjectivity,
                'method': 'textblob'
            }

        else:
            logger.warning("No sentiment analyzer available")
            return {'score': 0.0, 'label': 'neutral', 'method': 'none'}

    def analyze_article(self, article: Dict) -> Dict:
        """
        Analyze sentiment of a news article

        Args:
            article: Article dictionary

        Returns:
            Article dictionary with added sentiment information
        """
        # Combine title and description/summary for analysis
        text_parts = []
        if article.get('title'):
            text_parts.append(article['title'])
        if article.get('description'):
            text_parts.append(article['description'])
        elif article.get('summary'):
            text_parts.append(article['summary'])

        text = ' '.join(text_parts)
        sentiment = self.analyze(text)

        article['sentiment'] = sentiment
        return article


class NewsFetcher:
    """Main news fetching interface with multi-source aggregation"""

    # Egyptian market keywords for relevance scoring
    EGYPT_KEYWORDS = [
        'egypt', 'egyptian', 'cairo', 'egx', 'egy', 'alexandria',
        'middle east', 'north africa', 'mena', 'arab', 'africa'
    ]

    # Financial keywords for relevance scoring
    FINANCIAL_KEYWORDS = [
        'stock', 'shares', 'market', 'trading', 'exchange', 'investment',
        'dividend', 'earnings', 'revenue', 'profit', 'loss', 'ipo',
        'acquisition', 'merger', 'quarter', 'fiscal', 'finance', 'bank'
    ]

    def __init__(self, config_path: Optional[str] = None, cache_dir: str = "./cache/news"):
        """
        Initialize news fetcher

        Args:
            config_path: Path to configuration file with API keys
            cache_dir: Directory for caching news data
        """
        self.config = self._load_config(config_path)
        self.cache = NewsCache(cache_dir, cache_duration_hours=self.config.get('cache_duration_hours', 24))
        self.sentiment_analyzer = SentimentAnalyzer(method=self.config.get('sentiment_method', 'vader'))

        # Initialize news sources
        self.sources = {}

        # NewsAPI
        if self.config.get('newsapi', {}).get('enabled', False):
            api_key = self.config.get('newsapi', {}).get('api_key')
            if api_key:
                self.sources['newsapi'] = NewsAPISource(api_key, self.cache)
                logger.info("NewsAPI source enabled")

        # Alpha Vantage
        if self.config.get('alphavantage', {}).get('enabled', False):
            api_key = self.config.get('alphavantage', {}).get('api_key')
            if api_key:
                self.sources['alphavantage'] = AlphaVantageNewsSource(api_key, self.cache)
                logger.info("Alpha Vantage source enabled")

        # GDELT (no API key required)
        if self.config.get('gdelt', {}).get('enabled', True):
            self.sources['gdelt'] = GDELTNewsSource(cache=self.cache)
            logger.info("GDELT source enabled")

        if not self.sources:
            logger.warning("No news sources enabled! Please configure API keys in config file.")

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from file or return defaults"""
        default_config = {
            'newsapi': {'enabled': False, 'api_key': None},
            'alphavantage': {'enabled': False, 'api_key': None},
            'gdelt': {'enabled': True},
            'sentiment_method': 'vader',
            'cache_duration_hours': 24,
            'relevance_threshold': 0.3
        }

        if not config_path:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')

        config_file = Path(config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.warning(f"Error loading config file: {e}. Using defaults.")
        else:
            logger.info("No config file found, using default configuration")

        return default_config

    def calculate_relevance_score(self, article: Dict, query: str) -> float:
        """
        Calculate relevance score for an article

        Args:
            article: Article dictionary
            query: Original search query

        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        text = f"{article.get('title', '')} {article.get('description', '')} {article.get('summary', '')}".lower()
        query_lower = query.lower()

        # Query match in title (high weight)
        if query_lower in article.get('title', '').lower():
            score += 0.4

        # Query match in content (medium weight)
        elif query_lower in text:
            score += 0.2

        # Egypt-related keywords
        egypt_matches = sum(1 for kw in self.EGYPT_KEYWORDS if kw in text)
        score += min(egypt_matches * 0.05, 0.2)

        # Financial keywords
        financial_matches = sum(1 for kw in self.FINANCIAL_KEYWORDS if kw in text)
        score += min(financial_matches * 0.03, 0.15)

        # Recency bonus (articles from last 24 hours get bonus)
        try:
            pub_date_str = article.get('published_at', '')
            if pub_date_str:
                # Try multiple date formats
                pub_date = None
                for fmt in ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S', '%Y%m%dT%H%M%S']:
                    try:
                        pub_date = datetime.strptime(pub_date_str[:19], fmt)
                        break
                    except:
                        continue

                if pub_date:
                    hours_old = (datetime.now() - pub_date).total_seconds() / 3600
                    if hours_old < 24:
                        score += 0.1
                    elif hours_old < 72:
                        score += 0.05
        except Exception as e:
            logger.debug(f"Error calculating recency: {e}")

        return min(score, 1.0)

    def fetch_news_for_ticker(self, ticker: str, company_name: Optional[str] = None,
                              days_back: int = 7, min_relevance: Optional[float] = None) -> List[Dict]:
        """
        Fetch news for a specific stock ticker

        Args:
            ticker: Stock ticker symbol (e.g., 'COMI' for Commercial International Bank)
            company_name: Full company name for better search results
            days_back: Number of days to look back
            min_relevance: Minimum relevance score (0.0 to 1.0)

        Returns:
            List of relevant news articles with sentiment analysis
        """
        if min_relevance is None:
            min_relevance = self.config.get('relevance_threshold', 0.3)

        all_articles = []

        # Construct search query
        if company_name:
            query = f"{ticker} OR {company_name}"
        else:
            query = ticker

        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)

        # Fetch from each source
        for source_name, source in self.sources.items():
            try:
                if source_name == 'newsapi':
                    articles = source.fetch_news(
                        query=query,
                        from_date=from_date.strftime('%Y-%m-%d'),
                        to_date=to_date.strftime('%Y-%m-%d')
                    )
                elif source_name == 'alphavantage':
                    articles = source.fetch_news(
                        tickers=[ticker],
                        time_from=from_date.strftime('%Y%m%dT%H%M'),
                        time_to=to_date.strftime('%Y%m%dT%H%M')
                    )
                elif source_name == 'gdelt':
                    articles = source.fetch_news(
                        query=query,
                        timespan=f"{days_back}d",
                        source_country='EG'  # Focus on Egyptian sources
                    )
                else:
                    continue

                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")

        # Add relevance scores
        for article in all_articles:
            article['relevance_score'] = self.calculate_relevance_score(article, query)

        # Filter by relevance
        relevant_articles = [a for a in all_articles if a['relevance_score'] >= min_relevance]

        # Add sentiment analysis
        for article in relevant_articles:
            self.sentiment_analyzer.analyze_article(article)

        # Sort by relevance and recency
        relevant_articles.sort(key=lambda x: (x['relevance_score'], x.get('published_at', '')), reverse=True)

        logger.info(f"Found {len(relevant_articles)} relevant articles for {ticker} (from {len(all_articles)} total)")
        return relevant_articles

    def fetch_market_news(self, keywords: List[str] = None, days_back: int = 7) -> List[Dict]:
        """
        Fetch general Egyptian market news

        Args:
            keywords: List of keywords to search for
            days_back: Number of days to look back

        Returns:
            List of relevant news articles with sentiment analysis
        """
        if keywords is None:
            keywords = ['Egyptian stock market', 'EGX', 'Egypt economy']

        all_articles = []

        for keyword in keywords:
            articles = self.fetch_news_for_ticker(
                ticker=keyword,
                days_back=days_back,
                min_relevance=0.2  # Lower threshold for market news
            )
            all_articles.extend(articles)

        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

        # Sort by relevance and date
        unique_articles.sort(key=lambda x: (x['relevance_score'], x.get('published_at', '')), reverse=True)

        logger.info(f"Found {len(unique_articles)} unique market news articles")
        return unique_articles

    def get_sentiment_summary(self, articles: List[Dict]) -> Dict:
        """
        Get sentiment summary for a list of articles

        Args:
            articles: List of articles with sentiment data

        Returns:
            Dictionary with sentiment statistics
        """
        if not articles:
            return {
                'total_articles': 0,
                'average_sentiment': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0
            }

        sentiments = [a.get('sentiment', {}).get('score', 0) for a in articles]
        labels = [a.get('sentiment', {}).get('label', 'neutral') for a in articles]

        return {
            'total_articles': len(articles),
            'average_sentiment': sum(sentiments) / len(sentiments) if sentiments else 0.0,
            'positive_count': labels.count('positive'),
            'negative_count': labels.count('negative'),
            'neutral_count': labels.count('neutral'),
            'sentiment_distribution': {
                'positive': labels.count('positive') / len(labels) if labels else 0.0,
                'negative': labels.count('negative') / len(labels) if labels else 0.0,
                'neutral': labels.count('neutral') / len(labels) if labels else 0.0
            }
        }


def create_default_config(output_path: str = "./config.json"):
    """
    Create a default configuration file with placeholders for API keys

    Args:
        output_path: Path where to save the config file
    """
    default_config = {
        "newsapi": {
            "enabled": False,
            "api_key": "YOUR_NEWSAPI_KEY_HERE",
            "note": "Get free API key from https://newsapi.org/"
        },
        "alphavantage": {
            "enabled": False,
            "api_key": "YOUR_ALPHAVANTAGE_KEY_HERE",
            "note": "Get free API key from https://www.alphavantage.co/support/#api-key"
        },
        "gdelt": {
            "enabled": True,
            "note": "GDELT is free and requires no API key"
        },
        "sentiment_method": "vader",
        "cache_duration_hours": 24,
        "relevance_threshold": 0.3
    }

    config_path = Path(output_path)
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=4)

    logger.info(f"Created default configuration file at {output_path}")
    print(f"Configuration file created at {output_path}")
    print("Please edit this file and add your API keys to enable news sources.")


if __name__ == "__main__":
    # Example usage
    print("EGXpy News Fetching Module")
    print("=" * 50)

    # Create default config if it doesn't exist
    config_path = Path("./config.json")
    if not config_path.exists():
        create_default_config()

    # Initialize news fetcher
    fetcher = NewsFetcher()

    # Example: Fetch news for a ticker
    print("\nFetching news for ticker 'COMI' (Commercial International Bank)...")
    articles = fetcher.fetch_news_for_ticker(
        ticker='COMI',
        company_name='Commercial International Bank',
        days_back=7
    )

    print(f"\nFound {len(articles)} relevant articles")

    if articles:
        print("\nTop 3 articles:")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. {article.get('title', 'No title')}")
            print(f"   Source: {article.get('source', 'Unknown')}")
            print(f"   Relevance: {article.get('relevance_score', 0):.2f}")
            sentiment = article.get('sentiment', {})
            print(f"   Sentiment: {sentiment.get('label', 'N/A')} ({sentiment.get('score', 0):.2f})")
            print(f"   URL: {article.get('url', 'N/A')}")

        # Get sentiment summary
        summary = fetcher.get_sentiment_summary(articles)
        print("\n" + "=" * 50)
        print("Sentiment Summary:")
        print(f"Total articles: {summary['total_articles']}")
        print(f"Average sentiment: {summary['average_sentiment']:.3f}")
        print(f"Positive: {summary['positive_count']} ({summary['sentiment_distribution']['positive']:.1%})")
        print(f"Negative: {summary['negative_count']} ({summary['sentiment_distribution']['negative']:.1%})")
        print(f"Neutral: {summary['neutral_count']} ({summary['sentiment_distribution']['neutral']:.1%})")
