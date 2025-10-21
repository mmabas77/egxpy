# EGXpy News Fetching Guide

## Overview

EGXpy now includes comprehensive news fetching capabilities with sentiment analysis! This feature helps you stay informed about Egyptian stocks and market news with automatic relevance scoring and sentiment analysis.

## Features

- **Multi-Source News Aggregation**: Fetch news from multiple sources
  - NewsAPI.org (requires free API key)
  - Alpha Vantage News & Sentiment (requires free API key)
  - GDELT Project (completely free, no API key required)

- **Intelligent Sentiment Analysis**:
  - VADER sentiment analyzer (optimized for financial text)
  - TextBlob sentiment analyzer (alternative option)
  - Automatic scoring and classification (positive/negative/neutral)

- **Smart Caching**:
  - Reduces API calls
  - Configurable cache duration
  - Automatic cache cleanup

- **Relevance Scoring**:
  - Filters out irrelevant news
  - Focuses on Egyptian market and financial keywords
  - Configurable relevance threshold

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `requests` - For API calls
- `vaderSentiment` - For sentiment analysis
- `textblob` - Alternative sentiment analyzer

### 2. Configure API Keys (Optional)

Edit `config.json` to add your API keys:

```json
{
    "newsapi": {
        "enabled": true,
        "api_key": "YOUR_NEWSAPI_KEY_HERE"
    },
    "alphavantage": {
        "enabled": true,
        "api_key": "YOUR_ALPHAVANTAGE_KEY_HERE"
    },
    "gdelt": {
        "enabled": true
    }
}
```

**Get Free API Keys:**
- NewsAPI: https://newsapi.org/ (100 requests/day free)
- Alpha Vantage: https://www.alphavantage.co/support/#api-key (25 requests/day free)
- GDELT: No API key needed (completely free)

### 3. Basic Usage

```python
from egxpy.news import NewsFetcher

# Initialize the news fetcher
fetcher = NewsFetcher()

# Fetch news for a specific stock
articles = fetcher.fetch_news_for_ticker(
    ticker='COMI',
    company_name='Commercial International Bank',
    days_back=7
)

# Display articles
for article in articles[:5]:
    print(f"Title: {article['title']}")
    print(f"Sentiment: {article['sentiment']['label']} ({article['sentiment']['score']:.2f})")
    print(f"URL: {article['url']}\n")

# Get sentiment summary
summary = fetcher.get_sentiment_summary(articles)
print(f"Average sentiment: {summary['average_sentiment']:.2f}")
print(f"Positive: {summary['positive_count']}, Negative: {summary['negative_count']}")
```

## Examples

### Example 1: Fetch News for a Specific Stock

```python
from egxpy.news import NewsFetcher

fetcher = NewsFetcher()

# Fetch news for COMI (Commercial International Bank)
articles = fetcher.fetch_news_for_ticker(
    ticker='COMI',
    company_name='Commercial International Bank',
    days_back=7,
    min_relevance=0.3
)

print(f"Found {len(articles)} relevant articles")
```

### Example 2: Fetch General Market News

```python
from egxpy.news import NewsFetcher

fetcher = NewsFetcher()

# Fetch general Egyptian market news
articles = fetcher.fetch_market_news(
    keywords=['Egyptian stock market', 'EGX', 'Egypt economy'],
    days_back=3
)

for article in articles[:3]:
    print(f"- {article['title']}")
```

### Example 3: Compare Sentiment Across Stocks

```python
from egxpy.news import NewsFetcher

fetcher = NewsFetcher()

stocks = {
    'COMI': 'Commercial International Bank',
    'ETEL': 'Egyptian Company for Mobile Services',
    'HRHO': 'Hermes Holding'
}

for ticker, company in stocks.items():
    articles = fetcher.fetch_news_for_ticker(ticker, company, days_back=7)
    summary = fetcher.get_sentiment_summary(articles)
    print(f"{ticker}: {summary['average_sentiment']:.2f} ({len(articles)} articles)")
```

### Example 4: Filter by Sentiment

```python
from egxpy.news import NewsFetcher

fetcher = NewsFetcher()

# Fetch news
articles = fetcher.fetch_news_for_ticker('COMI', days_back=7)

# Filter for positive news only
positive_news = [a for a in articles if a['sentiment']['label'] == 'positive']

print(f"Found {len(positive_news)} positive articles out of {len(articles)} total")
```

## Running the Examples

A comprehensive example script is provided in `examples/news_example.py`:

```bash
cd examples
python news_example.py
```

This will run through 4 different examples demonstrating:
1. Fetching news for a specific ticker
2. Fetching general market news
3. Comparing sentiment across multiple stocks
4. Exporting data to JSON

## Configuration Options

Edit `config.json` to customize behavior:

```json
{
    "sentiment_method": "vader",           // or "textblob"
    "cache_duration_hours": 24,            // How long to cache results
    "relevance_threshold": 0.3             // Minimum relevance score (0.0-1.0)
}
```

### Configuration Parameters

- **sentiment_method**: Choose between `vader` (better for financial text) or `textblob`
- **cache_duration_hours**: How long to cache news data (default: 24 hours)
- **relevance_threshold**: Minimum relevance score for articles (0.0 to 1.0, default: 0.3)

## Understanding Sentiment Scores

### VADER Sentiment (Default)

- **Score range**: -1.0 (most negative) to +1.0 (most positive)
- **Classification**:
  - Positive: score >= 0.05
  - Negative: score <= -0.05
  - Neutral: -0.05 < score < 0.05

### TextBlob Sentiment (Alternative)

- **Score range**: -1.0 (most negative) to +1.0 (most positive)
- **Classification**:
  - Positive: score > 0.1
  - Negative: score < -0.1
  - Neutral: -0.1 <= score <= 0.1

## Understanding Relevance Scores

Relevance scores (0.0 to 1.0) are calculated based on:

1. **Query match in title** (high weight: +0.4)
2. **Query match in content** (medium weight: +0.2)
3. **Egyptian market keywords** (up to +0.2):
   - egypt, egyptian, cairo, egx, mena, etc.
4. **Financial keywords** (up to +0.15):
   - stock, market, trading, earnings, dividend, etc.
5. **Recency bonus** (up to +0.1):
   - Articles from last 24 hours get bonus
   - Articles from last 72 hours get smaller bonus

## API Rate Limits

### Free Tier Limits

- **NewsAPI**: 100 requests/day
- **Alpha Vantage**: 25 requests/day (5 per minute)
- **GDELT**: Unlimited (250 articles per request max)

### Best Practices

1. **Enable caching** to reduce API calls
2. **Start with GDELT** (free, unlimited) to test
3. **Add API keys later** for more comprehensive coverage
4. **Use reasonable date ranges** (7 days is usually sufficient)

## Troubleshooting

### No Articles Found

1. **Check API keys**: Make sure API keys are correctly configured
2. **Try broader queries**: Use company name in addition to ticker
3. **Lower relevance threshold**: Set `min_relevance=0.2` or lower
4. **Check cache**: Clear cache directory if results seem stale

### API Errors

1. **Rate limit exceeded**: Wait or use caching
2. **Invalid API key**: Double-check your keys in config.json
3. **Network errors**: Check internet connection

### Import Errors

```bash
# If you get import errors, install dependencies:
pip install requests vaderSentiment textblob
```

## Cache Management

Cache files are stored in `./cache/news/` by default.

```python
from egxpy.news import NewsFetcher

fetcher = NewsFetcher(cache_dir="./my_custom_cache")

# Clear expired cache files
fetcher.cache.clear_expired()
```

## Integration with Existing EGXpy

The news module integrates seamlessly with existing EGXpy data fetching:

```python
from egxpy.download import get_EGXdata
from egxpy.news import NewsFetcher
from datetime import date

# Fetch price data
stocks = ['COMI', 'ETEL', 'HRHO']
prices = get_EGXdata(stocks, 'Daily', date(2024,1,1), date(2024,12,31))

# Fetch news for the same stocks
fetcher = NewsFetcher()
for stock in stocks:
    articles = fetcher.fetch_news_for_ticker(stock, days_back=7)
    sentiment = fetcher.get_sentiment_summary(articles)
    print(f"{stock}: {sentiment['average_sentiment']:.2f}")
```

## Contributing

Found a bug or want to add a new news source? Contributions are welcome!

## Egyptian Stock Tickers Reference

Common Egyptian Exchange (EGX) tickers you might want to track:

- **COMI**: Commercial International Bank
- **ETEL**: Egyptian Company for Mobile Services (Etisalat)
- **HRHO**: Hermes Holding
- **ORWE**: Oriental Weavers
- **SWDY**: El Sewedy Electric
- **PHDC**: Palm Hills Developments
- **OCDI**: Orascom Construction

## License

This module is part of the EGXpy project.

---

**Happy news fetching! 📰📈**
