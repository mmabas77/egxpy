"""
Example script demonstrating the email notification system

This script shows how to:
1. Configure email notifications
2. Send sentiment alerts
3. Send daily digest emails
4. Send breaking news alerts
5. Automatic threshold monitoring

Author: EGXpy Contributors
"""

import sys
from pathlib import Path

# Add parent directory to path to import egxpy
sys.path.insert(0, str(Path(__file__).parent.parent))

from egxpy.news import NewsFetcher
from egxpy.notifications import NotificationManager
from egxpy.company_lookup import CompanyLookup


def example_1_sentiment_alert():
    """Example 1: Send sentiment alert for a stock"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Sentiment Alert Email")
    print("="*80)

    # Initialize
    fetcher = NewsFetcher()
    notifier = NotificationManager()

    if not notifier.enabled:
        print("\n⚠️  Email notifications are DISABLED in config.json")
        print("To enable:")
        print('1. Edit config.json and set "email": {"enabled": true}')
        print("2. Configure your SMTP or SendGrid settings")
        print("3. Add recipient email addresses")
        return

    # Fetch news for a stock
    print("\nFetching news for COMI (Commercial International Bank)...")
    articles = fetcher.fetch_news_for_ticker('COMI', days_back=7)

    if not articles:
        print("No articles found!")
        return

    # Get sentiment summary
    summary = fetcher.get_sentiment_summary(articles)
    print(f"\nSentiment Summary:")
    print(f"  Articles: {summary['total_articles']}")
    print(f"  Average Sentiment: {summary['average_sentiment']:.3f}")
    print(f"  Positive: {summary['positive_count']}")
    print(f"  Negative: {summary['negative_count']}")

    # Send alert
    alert_type = 'positive' if summary['average_sentiment'] > 0 else 'negative'
    print(f"\n📧 Sending {alert_type} sentiment alert email...")

    success = notifier.send_sentiment_alert(
        ticker='COMI',
        company_name='Commercial International Bank',
        articles=articles,
        sentiment_summary=summary,
        alert_type=alert_type
    )

    if success:
        print("✓ Sentiment alert email sent successfully!")
    else:
        print("✗ Failed to send sentiment alert email")


def example_2_daily_digest():
    """Example 2: Send daily digest email with multiple stocks"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Daily Digest Email")
    print("="*80)

    # Initialize
    fetcher = NewsFetcher()
    notifier = NotificationManager()

    if not notifier.enabled:
        print("\n⚠️  Email notifications are DISABLED")
        return

    # Monitor multiple stocks
    stocks = ['COMI', 'ETEL', 'HRHO', 'ORWE', 'SWDY']
    stocks_data = []
    total_articles = 0
    total_positive = 0
    total_negative = 0

    print("\nFetching news for multiple stocks...")

    for ticker in stocks:
        print(f"  - Fetching {ticker}...")
        articles = fetcher.fetch_news_for_ticker(ticker, days_back=1)

        if articles:
            summary = fetcher.get_sentiment_summary(articles)
            stocks_data.append({
                'ticker': ticker,
                'company_name': fetcher.company_lookup.get_company_name(ticker) if fetcher.company_lookup else ticker,
                'articles_count': len(articles),
                'avg_sentiment': summary['average_sentiment']
            })

            total_articles += len(articles)
            total_positive += summary['positive_count']
            total_negative += summary['negative_count']

    if not stocks_data:
        print("No data available for digest!")
        return

    # Market summary
    market_summary = {
        'total_articles': total_articles,
        'positive_count': total_positive,
        'negative_count': total_negative
    }

    print(f"\n📧 Sending daily digest email...")
    print(f"  Stocks tracked: {len(stocks_data)}")
    print(f"  Total articles: {total_articles}")

    success = notifier.send_daily_digest(stocks_data, market_summary)

    if success:
        print("✓ Daily digest email sent successfully!")
    else:
        print("✗ Failed to send daily digest email")


def example_3_breaking_news_alert():
    """Example 3: Send breaking news alert for the latest article"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Breaking News Alert")
    print("="*80)

    # Initialize
    fetcher = NewsFetcher()
    notifier = NotificationManager()

    if not notifier.enabled:
        print("\n⚠️  Email notifications are DISABLED")
        return

    # Fetch latest news
    print("\nFetching latest news for COMI...")
    articles = fetcher.fetch_news_for_ticker('COMI', days_back=1)

    if not articles:
        print("No recent articles found!")
        return

    # Get the most recent article
    latest_article = articles[0]

    print(f"\nLatest article:")
    print(f"  Title: {latest_article.get('title', 'N/A')[:60]}...")
    print(f"  Sentiment: {latest_article.get('sentiment', {}).get('label', 'N/A')}")

    print(f"\n📧 Sending breaking news alert...")

    success = notifier.send_breaking_news_alert(
        ticker='COMI',
        company_name='Commercial International Bank',
        article=latest_article
    )

    if success:
        print("✓ Breaking news alert sent successfully!")
    else:
        print("✗ Failed to send breaking news alert")


def example_4_automatic_threshold_monitoring():
    """Example 4: Automatic sentiment threshold monitoring"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Automatic Threshold Monitoring")
    print("="*80)

    # Initialize
    fetcher = NewsFetcher()
    notifier = NotificationManager()

    if not notifier.enabled:
        print("\n⚠️  Email notifications are DISABLED")
        return

    # Get threshold settings
    thresholds = notifier.config.get('email', {}).get('alert_thresholds', {})
    positive_threshold = thresholds.get('positive_sentiment_threshold', 0.7)
    negative_threshold = thresholds.get('negative_sentiment_threshold', -0.6)

    print(f"\nThreshold Settings:")
    print(f"  Positive alert threshold: >= {positive_threshold}")
    print(f"  Negative alert threshold: <= {negative_threshold}")

    # Monitor a stock
    ticker = 'COMI'
    print(f"\nMonitoring {ticker}...")

    articles = fetcher.fetch_news_for_ticker(ticker, days_back=7)

    if not articles:
        print("No articles found!")
        return

    summary = fetcher.get_sentiment_summary(articles)
    avg_sentiment = summary['average_sentiment']

    print(f"\nCurrent sentiment: {avg_sentiment:.3f}")

    # Check thresholds
    alert_sent = notifier.check_sentiment_thresholds(
        ticker=ticker,
        company_name='Commercial International Bank',
        articles=articles,
        sentiment_summary=summary
    )

    if alert_sent:
        print("✓ Threshold exceeded! Alert email sent.")
    else:
        print("ℹ️  Sentiment within normal range. No alert sent.")


def example_5_test_email_configuration():
    """Example 5: Test email configuration"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Test Email Configuration")
    print("="*80)

    notifier = NotificationManager()

    print(f"\nEmail Configuration Status:")
    print(f"  Enabled: {notifier.enabled}")

    if notifier.enabled:
        email_config = notifier.config.get('email', {})
        print(f"  Provider: {email_config.get('provider', 'N/A').upper()}")
        print(f"  Alert Recipients: {email_config.get('alert_recipients', [])}")
        print(f"  Digest Recipients: {email_config.get('digest_recipients', [])}")

        # Test with a simple alert
        print(f"\n📧 Sending test email...")

        # Create dummy data
        test_article = {
            'title': 'Test Article - EGXpy Email System',
            'description': 'This is a test email to verify your email configuration is working correctly.',
            'url': 'https://github.com/yourusername/egxpy',
            'published_at': '2024-01-01',
            'source_name': 'EGXpy Test',
            'sentiment': {
                'label': 'positive',
                'score': 0.5
            }
        }

        success = notifier.send_breaking_news_alert(
            ticker='TEST',
            company_name='Test Company',
            article=test_article
        )

        if success:
            print("✓ Test email sent successfully!")
            print("  Check your inbox to verify delivery.")
        else:
            print("✗ Failed to send test email")
            print("  Please check your configuration:")
            print("  1. Verify SMTP credentials (username/password)")
            print("  2. Check recipient email addresses")
            print("  3. For Gmail: use App Password, not regular password")
    else:
        print("\nEmail notifications are disabled!")
        print("\nTo enable email notifications:")
        print("1. Edit config.json")
        print('2. Set "email": {"enabled": true}')
        print("3. Configure SMTP or SendGrid settings:")
        print("   - For Gmail: Use App Password (https://myaccount.google.com/apppasswords)")
        print("   - Host: smtp.gmail.com, Port: 587")
        print("4. Add recipient email addresses")


def main():
    """Main function to run all examples"""
    print("\n" + "="*80)
    print("EGXpy Email Notification Examples")
    print("="*80)

    print("\nThese examples demonstrate the email notification system.")
    print("Before running, please configure email settings in config.json")

    # Check configuration
    config_path = Path(__file__).parent.parent / 'config.json'
    if not config_path.exists():
        print("\n⚠️  ERROR: config.json not found!")
        return

    try:
        # Run test first
        example_5_test_email_configuration()
        input("\n\nPress Enter to continue to Example 1, or Ctrl+C to exit...")

        example_1_sentiment_alert()
        input("\n\nPress Enter to continue to Example 2, or Ctrl+C to exit...")

        example_2_daily_digest()
        input("\n\nPress Enter to continue to Example 3, or Ctrl+C to exit...")

        example_3_breaking_news_alert()
        input("\n\nPress Enter to continue to Example 4, or Ctrl+C to exit...")

        example_4_automatic_threshold_monitoring()

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
