"""
Example script demonstrating the news fetching capabilities of EGXpy

This script shows how to:
1. Fetch news for specific stocks
2. Get general market news
3. Analyze sentiment
4. Display results in a useful format

Author: EGXpy Contributors
"""

import sys
from pathlib import Path

# Add parent directory to path to import egxpy
sys.path.insert(0, str(Path(__file__).parent.parent))

from egxpy.news import NewsFetcher, create_default_config
import json


def print_article(article, index=None):
    """Pretty print a news article"""
    if index:
        print(f"\n{'='*80}")
        print(f"Article {index}")
        print(f"{'='*80}")
    else:
        print(f"\n{'-'*80}")

    print(f"Title: {article.get('title', 'N/A')}")
    print(f"Source: {article.get('source', 'N/A')} - {article.get('source_name', 'N/A')}")
    print(f"Published: {article.get('published_at', 'N/A')}")
    print(f"URL: {article.get('url', 'N/A')}")

    # Description/Summary
    desc = article.get('description') or article.get('summary', '')
    if desc:
        print(f"\nDescription: {desc[:200]}..." if len(desc) > 200 else f"\nDescription: {desc}")

    # Relevance score
    if 'relevance_score' in article:
        print(f"\nRelevance Score: {article['relevance_score']:.2f}")

    # Sentiment
    if 'sentiment' in article:
        sentiment = article['sentiment']
        print(f"Sentiment: {sentiment.get('label', 'N/A').upper()} (score: {sentiment.get('score', 0):.3f})")

        # Additional sentiment details
        if 'positive' in sentiment:
            print(f"  - Positive: {sentiment['positive']:.2f}")
            print(f"  - Negative: {sentiment['negative']:.2f}")
            print(f"  - Neutral: {sentiment['neutral']:.2f}")


def print_sentiment_summary(summary):
    """Pretty print sentiment summary"""
    print(f"\n{'='*80}")
    print("SENTIMENT SUMMARY")
    print(f"{'='*80}")
    print(f"Total Articles: {summary['total_articles']}")
    print(f"Average Sentiment: {summary['average_sentiment']:.3f}")
    print(f"\nDistribution:")
    print(f"  - Positive: {summary['positive_count']} ({summary['sentiment_distribution']['positive']:.1%})")
    print(f"  - Negative: {summary['negative_count']} ({summary['sentiment_distribution']['negative']:.1%})")
    print(f"  - Neutral: {summary['neutral_count']} ({summary['sentiment_distribution']['neutral']:.1%})")


def example_1_fetch_ticker_news():
    """Example 1: Fetch news for a specific ticker"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Fetching News for COMI (Commercial International Bank)")
    print("="*80)

    # Initialize news fetcher
    fetcher = NewsFetcher()

    # Fetch news for COMI
    articles = fetcher.fetch_news_for_ticker(
        ticker='COMI',
        company_name='Commercial International Bank',
        days_back=7,
        min_relevance=0.2
    )

    print(f"\nFound {len(articles)} relevant articles\n")

    # Display top 5 articles
    for i, article in enumerate(articles[:5], 1):
        print_article(article, i)

    # Sentiment summary
    if articles:
        summary = fetcher.get_sentiment_summary(articles)
        print_sentiment_summary(summary)


def example_2_fetch_market_news():
    """Example 2: Fetch general Egyptian market news"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Fetching General Egyptian Market News")
    print("="*80)

    # Initialize news fetcher
    fetcher = NewsFetcher()

    # Fetch market news
    articles = fetcher.fetch_market_news(
        keywords=['Egyptian stock market', 'EGX', 'Egypt economy'],
        days_back=3
    )

    print(f"\nFound {len(articles)} relevant market news articles\n")

    # Display top 3 articles
    for i, article in enumerate(articles[:3], 1):
        print_article(article, i)

    # Sentiment summary
    if articles:
        summary = fetcher.get_sentiment_summary(articles)
        print_sentiment_summary(summary)


def example_3_compare_multiple_stocks():
    """Example 3: Compare sentiment across multiple stocks"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Comparing Sentiment Across Multiple Egyptian Stocks")
    print("="*80)

    # Initialize news fetcher
    fetcher = NewsFetcher()

    # Egyptian blue chip stocks
    stocks = {
        'COMI': 'Commercial International Bank',
        'ETEL': 'Egyptian Company for Mobile Services',
        'HRHO': 'Hermes Holding',
        'ORWE': 'Oriental Weavers'
    }

    results = {}

    for ticker, company_name in stocks.items():
        print(f"\nFetching news for {ticker} ({company_name})...")
        articles = fetcher.fetch_news_for_ticker(
            ticker=ticker,
            company_name=company_name,
            days_back=7,
            min_relevance=0.2
        )

        summary = fetcher.get_sentiment_summary(articles)
        results[ticker] = {
            'company': company_name,
            'articles': len(articles),
            'sentiment': summary['average_sentiment'],
            'positive': summary['positive_count'],
            'negative': summary['negative_count'],
            'neutral': summary['neutral_count']
        }

    # Display comparison table
    print("\n" + "="*80)
    print("SENTIMENT COMPARISON")
    print("="*80)
    print(f"\n{'Ticker':<8} {'Company':<35} {'Articles':<10} {'Avg Sentiment':<15} {'Pos/Neg/Neu'}")
    print("-"*95)

    for ticker, data in results.items():
        print(f"{ticker:<8} {data['company'][:34]:<35} {data['articles']:<10} "
              f"{data['sentiment']:>7.3f}{'':8} "
              f"{data['positive']}/{data['negative']}/{data['neutral']}")


def example_4_export_to_json():
    """Example 4: Export news data to JSON"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Exporting News Data to JSON")
    print("="*80)

    # Initialize news fetcher
    fetcher = NewsFetcher()

    # Fetch news
    articles = fetcher.fetch_news_for_ticker(
        ticker='COMI',
        company_name='Commercial International Bank',
        days_back=7
    )

    # Export to JSON
    output_file = 'comi_news.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)

    print(f"\nExported {len(articles)} articles to {output_file}")
    print(f"File size: {Path(output_file).stat().st_size / 1024:.2f} KB")

    # Also export sentiment summary
    summary = fetcher.get_sentiment_summary(articles)
    summary_file = 'comi_sentiment_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4)

    print(f"Exported sentiment summary to {summary_file}")


def main():
    """Main function to run all examples"""
    print("\n" + "="*80)
    print("EGXpy News Fetching Examples")
    print("="*80)

    # Check if config exists, create if not
    config_path = Path(__file__).parent.parent / 'config.json'
    if not config_path.exists():
        print("\nNo configuration file found. Creating default config...")
        create_default_config(str(config_path))
        print("\nIMPORTANT: To enable more news sources, edit config.json and add your API keys.")
        print("For now, we'll use the free GDELT news source.\n")
        input("Press Enter to continue...")

    # Run examples
    try:
        example_1_fetch_ticker_news()
        input("\n\nPress Enter to continue to Example 2...")

        example_2_fetch_market_news()
        input("\n\nPress Enter to continue to Example 3...")

        example_3_compare_multiple_stocks()
        input("\n\nPress Enter to continue to Example 4...")

        example_4_export_to_json()

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("Examples completed!")
    print("="*80)


if __name__ == "__main__":
    main()
