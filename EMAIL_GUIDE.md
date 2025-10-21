# EGXpy Email Notification System Guide

## Overview

EGXpy now includes a comprehensive email notification system that sends beautiful HTML emails for:
- **Sentiment Alerts**: Get notified when stocks show strong positive or negative sentiment
- **Daily Digests**: Receive daily summaries of all tracked stocks
- **Breaking News**: Instant alerts for important news articles
- **Custom Alerts**: Configure your own threshold-based triggers

## Features

### Email Providers Supported

1. **SMTP** (Gmail, Outlook, Custom Servers)
   - ✅ Free to use
   - ✅ No API keys required (just email credentials)
   - ✅ Works with any SMTP server
   - ⚠️  Recommended: Use App Passwords for Gmail

2. **SendGrid** (Optional)
   - ✅ Free tier: 100 emails/day
   - ✅ Reliable delivery
   - ✅ Better for high volume
   - ⚠️  Requires API key

### Email Templates

All emails use beautiful, responsive HTML templates:

- **Sentiment Alert**: Shows sentiment summary with top articles
- **Daily Digest**: Market overview table with all tracked stocks
- **Breaking News**: Single article with full details and sentiment
- All templates are mobile-friendly and professional

## Quick Start

### Step 1: Configure Email Settings

Edit `config.json` and update the email section:

```json
{
    "email": {
        "enabled": true,  // Change from false to true
        "provider": "smtp",
        "smtp_config": {
            "host": "smtp.gmail.com",
            "port": 587,
            "use_tls": true,
            "username": "your_email@gmail.com",
            "password": "your_app_password",  // For Gmail: create App Password
            "sender": "EGXpy Alerts <your_email@gmail.com>"
        },
        "alert_recipients": [
            "your_email@example.com"
        ]
    }
}
```

### Step 2: For Gmail Users - Create App Password

**IMPORTANT**: Gmail requires App Passwords (not your regular password)

1. Go to https://myaccount.google.com/apppasswords
2. Sign in to your Google Account
3. Click "Select app" → Choose "Mail"
4. Click "Select device" → Choose "Other" → Enter "EGXpy"
5. Click "Generate"
6. Copy the 16-character password
7. Paste it in config.json as the "password" value

### Step 3: Test Your Configuration

```bash
python examples/email_notifications_example.py
```

This will:
- Check your configuration
- Send a test email
- Verify everything is working

## Usage Examples

### Example 1: Send Sentiment Alert

```python
from egxpy.news import NewsFetcher
from egxpy.notifications import NotificationManager

# Initialize
fetcher = NewsFetcher()
notifier = NotificationManager()

# Fetch news
articles = fetcher.fetch_news_for_ticker('COMI')
summary = fetcher.get_sentiment_summary(articles)

# Send alert
notifier.send_sentiment_alert(
    ticker='COMI',
    company_name='Commercial International Bank',
    articles=articles,
    sentiment_summary=summary,
    alert_type='positive'  # or 'negative'
)
```

### Example 2: Send Daily Digest

```python
from egxpy.news import NewsFetcher
from egxpy.notifications import NotificationManager

fetcher = NewsFetcher()
notifier = NotificationManager()

# Monitor multiple stocks
stocks = ['COMI', 'ETEL', 'HRHO', 'ORWE']
stocks_data = []

for ticker in stocks:
    articles = fetcher.fetch_news_for_ticker(ticker, days_back=1)
    summary = fetcher.get_sentiment_summary(articles)

    stocks_data.append({
        'ticker': ticker,
        'company_name': fetcher.company_lookup.get_company_name(ticker),
        'articles_count': len(articles),
        'avg_sentiment': summary['average_sentiment']
    })

# Send digest
market_summary = {
    'total_articles': sum(s['articles_count'] for s in stocks_data),
    'positive_count': 0,  # Calculate from your data
    'negative_count': 0
}

notifier.send_daily_digest(stocks_data, market_summary)
```

### Example 3: Send Breaking News Alert

```python
from egxpy.news import NewsFetcher
from egxpy.notifications import NotificationManager

fetcher = NewsFetcher()
notifier = NotificationManager()

# Get latest article
articles = fetcher.fetch_news_for_ticker('COMI', days_back=1)
latest_article = articles[0]

# Send alert
notifier.send_breaking_news_alert(
    ticker='COMI',
    company_name='Commercial International Bank',
    article=latest_article
)
```

### Example 4: Automatic Threshold Monitoring

```python
from egxpy.news import NewsFetcher
from egxpy.notifications import NotificationManager

fetcher = NewsFetcher()
notifier = NotificationManager()

# Fetch news
articles = fetcher.fetch_news_for_ticker('COMI')
summary = fetcher.get_sentiment_summary(articles)

# Automatically check thresholds and send alert if exceeded
alert_sent = notifier.check_sentiment_thresholds(
    ticker='COMI',
    company_name='Commercial International Bank',
    articles=articles,
    sentiment_summary=summary
)

if alert_sent:
    print("Alert sent!")
```

## Configuration Reference

### Email Settings

```json
{
    "email": {
        "enabled": false,              // Enable/disable all email notifications
        "provider": "smtp",            // "smtp" or "sendgrid"

        // SMTP Configuration (Gmail, Outlook, etc.)
        "smtp_config": {
            "host": "smtp.gmail.com",  // SMTP server hostname
            "port": 587,               // SMTP port (587 for TLS, 465 for SSL)
            "use_tls": true,           // Use TLS encryption
            "username": "...",         // Your email address
            "password": "...",         // Your password (App Password for Gmail)
            "sender": "..."            // Sender name and email
        },

        // SendGrid Configuration (Alternative)
        "sendgrid_config": {
            "api_key": "...",          // SendGrid API key
            "sender": "..."            // Sender email address
        },

        // Recipients
        "alert_recipients": [          // Who receives sentiment alerts
            "user1@example.com",
            "user2@example.com"
        ],
        "digest_recipients": [         // Who receives daily digests
            "user1@example.com"
        ],

        // Alert Rules
        "alert_thresholds": {
            "positive_sentiment_threshold": 0.7,     // Alert when sentiment >= 0.7
            "negative_sentiment_threshold": -0.6,    // Alert when sentiment <= -0.6
            "min_articles_for_alert": 3,             // Minimum articles to trigger alert
            "send_breaking_news": true,              // Enable breaking news alerts
            "send_daily_digest": false,              // Enable daily digest (WIP)
            "digest_time": "08:00"                   // When to send digest (WIP)
        }
    }
}
```

### Threshold Settings Explained

- **positive_sentiment_threshold** (0.0 to 1.0)
  - Send alert when average sentiment is **greater than or equal** to this value
  - Example: 0.7 means "very positive" news
  - Higher value = fewer alerts, only very positive news

- **negative_sentiment_threshold** (-1.0 to 0.0)
  - Send alert when average sentiment is **less than or equal** to this value
  - Example: -0.6 means "very negative" news
  - Lower value (more negative) = fewer alerts, only very negative news

- **min_articles_for_alert** (integer)
  - Minimum number of articles required before sending alert
  - Prevents alerts from single articles
  - Recommended: 3-5 articles

## SMTP Provider Setup Guides

### Gmail

1. **Enable 2-Factor Authentication** (required for App Passwords)
   - Go to https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. **Create App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Create new app password for "Mail"
   - Copy the 16-character password

3. **Configure in config.json**:
   ```json
   "smtp_config": {
       "host": "smtp.gmail.com",
       "port": 587,
       "use_tls": true,
       "username": "your_email@gmail.com",
       "password": "your_16_char_app_password",
       "sender": "EGXpy Alerts <your_email@gmail.com>"
   }
   ```

### Outlook/Hotmail

```json
"smtp_config": {
    "host": "smtp-mail.outlook.com",
    "port": 587,
    "use_tls": true,
    "username": "your_email@outlook.com",
    "password": "your_password",
    "sender": "EGXpy Alerts <your_email@outlook.com>"
}
```

### Yahoo Mail

```json
"smtp_config": {
    "host": "smtp.mail.yahoo.com",
    "port": 587,
    "use_tls": true,
    "username": "your_email@yahoo.com",
    "password": "your_app_password",  // Generate at Yahoo Account Security
    "sender": "EGXpy Alerts <your_email@yahoo.com>"
}
```

### Custom SMTP Server

```json
"smtp_config": {
    "host": "mail.your-domain.com",
    "port": 587,
    "use_tls": true,
    "username": "alerts@your-domain.com",
    "password": "your_password",
    "sender": "Market Alerts <alerts@your-domain.com>"
}
```

## SendGrid Setup (Alternative)

SendGrid is recommended if you need to send many emails or want better delivery rates.

### Step 1: Create SendGrid Account

1. Go to https://sendgrid.com/
2. Sign up for free account (100 emails/day free)
3. Verify your email address

### Step 2: Create API Key

1. Go to Settings → API Keys
2. Click "Create API Key"
3. Give it a name (e.g., "EGXpy")
4. Choose "Full Access"
5. Copy the API key

### Step 3: Configure

```json
{
    "email": {
        "enabled": true,
        "provider": "sendgrid",  // Change from "smtp"
        "sendgrid_config": {
            "api_key": "SG.your_api_key_here",
            "sender": "alerts@yourdomain.com"
        }
    }
}
```

### Step 4: Install SendGrid Library

```bash
pip install sendgrid
```

## Troubleshooting

### Gmail: "Username and Password not accepted"

**Problem**: Authentication failed

**Solutions**:
1. Make sure you're using an **App Password**, not your regular password
2. Enable 2-Factor Authentication first
3. Generate new App Password at https://myaccount.google.com/apppasswords
4. Check username is your full email address

### Emails Not Arriving

**Check**:
1. Spam/Junk folder
2. Verify recipient email address in config.json
3. Check email provider logs for errors
4. Run test example to see error messages

### SMTP Connection Timeout

**Solutions**:
1. Check internet connection
2. Verify SMTP host and port are correct
3. Some networks block port 587 - try port 465 with SSL
4. Check firewall settings

### SendGrid Errors

**Solutions**:
1. Verify API key is correct
2. Check sender email is verified in SendGrid
3. Ensure you haven't exceeded free tier (100 emails/day)
4. Check SendGrid dashboard for error details

## Best Practices

### 1. Start with Test Emails

Always test with a single recipient first:

```json
"alert_recipients": ["your_personal_email@gmail.com"]
```

### 2. Use Appropriate Thresholds

- **Conservative** (fewer alerts): positive >= 0.8, negative <= -0.7
- **Moderate** (balanced): positive >= 0.7, negative <= -0.6
- **Aggressive** (more alerts): positive >= 0.5, negative <= -0.4

### 3. Monitor Multiple Stocks

Track 5-10 stocks for daily digests, not hundreds:

```python
watchlist = ['COMI', 'ETEL', 'HRHO', 'ORWE', 'SWDY']
```

### 4. Respect Rate Limits

- **Gmail**: ~500 emails/day limit
- **SendGrid Free**: 100 emails/day
- Use digests to consolidate information

### 5. Security

- Never commit config.json with real passwords to git
- Use environment variables for production
- For Gmail: Always use App Passwords, never regular password

## Advanced: Schedule Daily Digest

Use cron (Linux/Mac) or Task Scheduler (Windows) to run daily:

### Linux/Mac Cron

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 8 AM
0 8 * * * cd /path/to/egxpy && python examples/email_notifications_example.py > /dev/null 2>&1
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 8:00 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `examples/email_notifications_example.py`
7. Start in: `C:\path\to\egxpy`

## Integration with Existing Code

### Add Notifications to Your Script

```python
from egxpy.news import NewsFetcher
from egxpy.notifications import NotificationManager

# Your existing code
fetcher = NewsFetcher()
articles = fetcher.fetch_news_for_ticker('COMI')

# Add notification
notifier = NotificationManager()
if notifier.enabled:
    summary = fetcher.get_sentiment_summary(articles)
    notifier.check_sentiment_thresholds('COMI', 'Commercial International Bank',
                                        articles, summary)
```

## Email Template Customization

Email templates are defined in `egxpy/notifications.py` in the `EmailTemplates` class.

To customize:

1. Edit `EmailTemplates.sentiment_alert()`, `EmailTemplates.daily_digest()`, or `EmailTemplates.breaking_news_alert()`
2. Modify HTML/CSS in the template strings
3. Add your branding, colors, logos

## Support

If you encounter issues:

1. Check this guide's Troubleshooting section
2. Run the test example: `python examples/email_notifications_example.py`
3. Check the logs for error messages
4. Verify your config.json syntax is valid JSON

## License

This module is part of the EGXpy project.

---

**Happy email alerting! 📧📊**
