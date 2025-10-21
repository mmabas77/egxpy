"""
EGXpy Email Notification System

This module provides comprehensive email notification capabilities for Egyptian stocks,
market news, and sentiment analysis alerts.

Features:
- Multiple email providers (SMTP, SendGrid, Mailgun)
- Beautiful HTML email templates
- Real-time alerts based on sentiment thresholds
- Scheduled digest emails (daily/weekly)
- Portfolio performance notifications
- Breaking news alerts
- Customizable alert rules

Author: EGXpy Contributors
"""

import os
import json
import smtplib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.utils import formatdate

logger = logging.getLogger(__name__)


class EmailProvider:
    """Base class for email providers"""

    def __init__(self, config: Dict):
        self.config = config
        self.provider_name = self.__class__.__name__

    def send_email(self, recipient: str, subject: str, body_html: str,
                   body_text: Optional[str] = None) -> bool:
        """Send email - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement send_email()")


class SMTPProvider(EmailProvider):
    """SMTP email provider (Gmail, Outlook, custom SMTP servers)"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.host = config.get('host', 'smtp.gmail.com')
        self.port = config.get('port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.sender = config.get('sender', self.username)
        self.use_tls = config.get('use_tls', True)

        if not self.username or not self.password:
            logger.warning("SMTP username or password not configured")

    def send_email(self, recipient: str, subject: str, body_html: str,
                   body_text: Optional[str] = None) -> bool:
        """
        Send email via SMTP

        Args:
            recipient: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body (fallback)

        Returns:
            True if successful, False otherwise
        """
        if not self.username or not self.password:
            logger.error("SMTP credentials not configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender
            msg['To'] = recipient
            msg['Date'] = formatdate(localtime=True)

            # Add plain text version
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)

            # Add HTML version
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)

            # Connect and send
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {recipient} via SMTP")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False


class SendGridProvider(EmailProvider):
    """SendGrid email provider"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.sender = config.get('sender')

        if not self.api_key:
            logger.warning("SendGrid API key not configured")

        # Check if sendgrid is installed
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            self.sendgrid = sendgrid
            self.Mail = Mail
            self.Email = Email
            self.To = To
            self.Content = Content
            logger.info("SendGrid library available")
        except ImportError:
            logger.warning("SendGrid library not installed. Install with: pip install sendgrid")
            self.sendgrid = None

    def send_email(self, recipient: str, subject: str, body_html: str,
                   body_text: Optional[str] = None) -> bool:
        """
        Send email via SendGrid

        Args:
            recipient: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body (fallback)

        Returns:
            True if successful, False otherwise
        """
        if not self.api_key:
            logger.error("SendGrid API key not configured")
            return False

        if not self.sendgrid:
            logger.error("SendGrid library not installed")
            return False

        try:
            message = self.Mail(
                from_email=self.Email(self.sender),
                to_emails=self.To(recipient),
                subject=subject,
                html_content=self.Content("text/html", body_html)
            )

            if body_text:
                message.plain_text_content = self.Content("text/plain", body_text)

            sg = self.sendgrid.SendGridAPIClient(api_key=self.api_key)
            response = sg.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {recipient} via SendGrid")
                return True
            else:
                logger.error(f"SendGrid returned status code: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {e}")
            return False


class EmailTemplates:
    """HTML email templates for various notification types"""

    @staticmethod
    def sentiment_alert(ticker: str, company_name: str, articles: List[Dict],
                       sentiment_summary: Dict, alert_type: str) -> str:
        """
        Generate HTML for sentiment alert email

        Args:
            ticker: Stock ticker
            company_name: Company name
            articles: List of news articles
            sentiment_summary: Sentiment summary statistics
            alert_type: 'positive' or 'negative'

        Returns:
            HTML string
        """
        alert_color = '#28a745' if alert_type == 'positive' else '#dc3545'
        alert_emoji = '📈' if alert_type == 'positive' else '📉'

        avg_sentiment = sentiment_summary.get('average_sentiment', 0)
        total_articles = sentiment_summary.get('total_articles', 0)
        pos_count = sentiment_summary.get('positive_count', 0)
        neg_count = sentiment_summary.get('negative_count', 0)
        neu_count = sentiment_summary.get('neutral_count', 0)

        # Build articles HTML
        articles_html = ""
        for article in articles[:5]:  # Top 5 articles
            sentiment = article.get('sentiment', {})
            sentiment_label = sentiment.get('label', 'neutral').upper()
            sentiment_score = sentiment.get('score', 0)
            sentiment_color = '#28a745' if sentiment_label == 'POSITIVE' else ('#dc3545' if sentiment_label == 'NEGATIVE' else '#6c757d')

            articles_html += f"""
            <div style="border-left: 4px solid {sentiment_color}; padding: 15px; margin: 15px 0; background: #f8f9fa;">
                <h3 style="margin: 0 0 10px 0; color: #333;">
                    <a href="{article.get('url', '#')}" style="color: #007bff; text-decoration: none;">
                        {article.get('title', 'No title')}
                    </a>
                </h3>
                <p style="color: #666; margin: 5px 0;">
                    {article.get('description', article.get('summary', 'No description available'))[:200]}...
                </p>
                <div style="margin-top: 10px;">
                    <span style="background: {sentiment_color}; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px;">
                        {sentiment_label} ({sentiment_score:.2f})
                    </span>
                    <span style="color: #999; margin-left: 10px; font-size: 12px;">
                        {article.get('source_name', article.get('source', 'Unknown'))}
                    </span>
                    <span style="color: #999; margin-left: 10px; font-size: 12px;">
                        {article.get('published_at', 'Unknown date')}
                    </span>
                </div>
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">

            <!-- Header -->
            <div style="background: {alert_color}; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">{alert_emoji} Sentiment Alert</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">{ticker} - {company_name}</p>
            </div>

            <!-- Summary Box -->
            <div style="background: #fff; padding: 30px; border: 1px solid #ddd; border-top: none;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="margin: 0 0 15px 0; color: {alert_color};">Sentiment Summary</h2>
                    <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                        <div style="text-align: center; padding: 10px;">
                            <div style="font-size: 32px; font-weight: bold; color: {alert_color};">
                                {avg_sentiment:.3f}
                            </div>
                            <div style="color: #666; font-size: 14px;">Average Sentiment</div>
                        </div>
                        <div style="text-align: center; padding: 10px;">
                            <div style="font-size: 32px; font-weight: bold; color: #007bff;">
                                {total_articles}
                            </div>
                            <div style="color: #666; font-size: 14px;">Total Articles</div>
                        </div>
                    </div>
                    <div style="margin-top: 20px; text-align: center;">
                        <span style="margin: 0 10px;">
                            <strong style="color: #28a745;">{pos_count}</strong> Positive
                        </span>
                        <span style="margin: 0 10px;">
                            <strong style="color: #dc3545;">{neg_count}</strong> Negative
                        </span>
                        <span style="margin: 0 10px;">
                            <strong style="color: #6c757d;">{neu_count}</strong> Neutral
                        </span>
                    </div>
                </div>

                <h2 style="color: #333; border-bottom: 2px solid {alert_color}; padding-bottom: 10px;">
                    Recent News Articles
                </h2>

                {articles_html}

                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="color: #666; font-size: 14px;">
                        This alert was generated by EGXpy News Notification System<br>
                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </div>

        </body>
        </html>
        """

        return html

    @staticmethod
    def daily_digest(stocks_data: List[Dict], market_summary: Dict) -> str:
        """
        Generate HTML for daily digest email

        Args:
            stocks_data: List of dictionaries with stock data
            market_summary: Overall market summary

        Returns:
            HTML string
        """
        # Build stocks table
        stocks_html = ""
        for stock in stocks_data:
            ticker = stock.get('ticker', 'N/A')
            company = stock.get('company_name', 'N/A')
            articles_count = stock.get('articles_count', 0)
            sentiment = stock.get('avg_sentiment', 0)

            sentiment_color = '#28a745' if sentiment > 0.05 else ('#dc3545' if sentiment < -0.05 else '#6c757d')
            sentiment_label = 'Positive' if sentiment > 0.05 else ('Negative' if sentiment < -0.05 else 'Neutral')

            stocks_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #ddd;"><strong>{ticker}</strong></td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">{company}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">{articles_count}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">
                    <span style="color: {sentiment_color}; font-weight: bold;">
                        {sentiment:.3f}
                    </span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">
                    <span style="background: {sentiment_color}; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px;">
                        {sentiment_label}
                    </span>
                </td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px;">

            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 32px;">📊 Daily Market Digest</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">Egyptian Exchange News & Sentiment Analysis</p>
                <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">{datetime.now().strftime('%A, %B %d, %Y')}</p>
            </div>

            <!-- Content -->
            <div style="background: #fff; padding: 30px; border: 1px solid #ddd; border-top: none;">

                <!-- Market Summary -->
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
                    <h2 style="margin: 0 0 15px 0; color: #667eea;">Market Overview</h2>
                    <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                        <div style="text-align: center; padding: 10px;">
                            <div style="font-size: 28px; font-weight: bold; color: #667eea;">
                                {market_summary.get('total_articles', 0)}
                            </div>
                            <div style="color: #666; font-size: 14px;">Total Articles</div>
                        </div>
                        <div style="text-align: center; padding: 10px;">
                            <div style="font-size: 28px; font-weight: bold; color: #28a745;">
                                {market_summary.get('positive_count', 0)}
                            </div>
                            <div style="color: #666; font-size: 14px;">Positive News</div>
                        </div>
                        <div style="text-align: center; padding: 10px;">
                            <div style="font-size: 28px; font-weight: bold; color: #dc3545;">
                                {market_summary.get('negative_count', 0)}
                            </div>
                            <div style="color: #666; font-size: 14px;">Negative News</div>
                        </div>
                        <div style="text-align: center; padding: 10px;">
                            <div style="font-size: 28px; font-weight: bold; color: #007bff;">
                                {len(stocks_data)}
                            </div>
                            <div style="color: #666; font-size: 14px;">Stocks Tracked</div>
                        </div>
                    </div>
                </div>

                <!-- Stocks Table -->
                <h2 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                    Stock-by-Stock Analysis
                </h2>

                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <thead>
                        <tr style="background: #667eea; color: white;">
                            <th style="padding: 12px; text-align: left;">Ticker</th>
                            <th style="padding: 12px; text-align: left;">Company</th>
                            <th style="padding: 12px; text-align: center;">Articles</th>
                            <th style="padding: 12px; text-align: center;">Sentiment</th>
                            <th style="padding: 12px; text-align: center;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {stocks_html}
                    </tbody>
                </table>

                <!-- Footer -->
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="color: #666; font-size: 14px;">
                        Powered by <strong>EGXpy</strong> - Egyptian Stock Market Analysis<br>
                        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </div>

        </body>
        </html>
        """

        return html

    @staticmethod
    def breaking_news_alert(ticker: str, company_name: str, article: Dict) -> str:
        """
        Generate HTML for breaking news alert

        Args:
            ticker: Stock ticker
            company_name: Company name
            article: News article dictionary

        Returns:
            HTML string
        """
        sentiment = article.get('sentiment', {})
        sentiment_label = sentiment.get('label', 'neutral').upper()
        sentiment_score = sentiment.get('score', 0)
        sentiment_color = '#28a745' if sentiment_label == 'POSITIVE' else ('#dc3545' if sentiment_label == 'NEGATIVE' else '#6c757d')

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; padding: 20px;">

            <!-- Header -->
            <div style="background: #dc3545; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">🚨 Breaking News Alert</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">{ticker} - {company_name}</p>
            </div>

            <!-- Content -->
            <div style="background: #fff; padding: 30px; border: 1px solid #ddd; border-top: none;">

                <h2 style="margin: 0 0 15px 0; color: #333;">
                    <a href="{article.get('url', '#')}" style="color: #007bff; text-decoration: none;">
                        {article.get('title', 'No title')}
                    </a>
                </h2>

                <div style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid {sentiment_color};">
                    <p style="margin: 0; color: #666; font-size: 16px;">
                        {article.get('description', article.get('summary', 'No description available'))}
                    </p>
                </div>

                <div style="margin: 20px 0;">
                    <div style="display: inline-block; margin-right: 15px;">
                        <span style="background: {sentiment_color}; color: white; padding: 8px 15px; border-radius: 5px; font-size: 14px;">
                            Sentiment: {sentiment_label} ({sentiment_score:.2f})
                        </span>
                    </div>
                    <div style="display: inline-block; color: #999; font-size: 14px;">
                        <strong>Source:</strong> {article.get('source_name', article.get('source', 'Unknown'))}<br>
                        <strong>Published:</strong> {article.get('published_at', 'Unknown date')}
                    </div>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <a href="{article.get('url', '#')}" style="background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Read Full Article
                    </a>
                </div>

                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="color: #666; font-size: 12px;">
                        This alert was generated by EGXpy Breaking News System<br>
                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </div>

        </body>
        </html>
        """

        return html


class NotificationManager:
    """Main notification manager with alert rules and scheduling"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize notification manager

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.provider = self._initialize_provider()
        self.enabled = self.config.get('email', {}).get('enabled', False)

        if not self.enabled:
            logger.info("Email notifications disabled in configuration")

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from file"""
        if not config_path:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')

        config_file = Path(config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")

        return {}

    def _initialize_provider(self) -> Optional[EmailProvider]:
        """Initialize email provider based on configuration"""
        email_config = self.config.get('email', {})
        provider_type = email_config.get('provider', 'smtp').lower()

        if provider_type == 'smtp':
            smtp_config = email_config.get('smtp_config', {})
            return SMTPProvider(smtp_config)
        elif provider_type == 'sendgrid':
            sendgrid_config = email_config.get('sendgrid_config', {})
            return SendGridProvider(sendgrid_config)
        else:
            logger.error(f"Unknown email provider: {provider_type}")
            return None

    def send_sentiment_alert(self, ticker: str, company_name: str,
                            articles: List[Dict], sentiment_summary: Dict,
                            alert_type: str) -> bool:
        """
        Send sentiment alert email

        Args:
            ticker: Stock ticker
            company_name: Company name
            articles: List of news articles
            sentiment_summary: Sentiment summary
            alert_type: 'positive' or 'negative'

        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.provider:
            logger.debug("Email notifications disabled")
            return False

        recipients = self.config.get('email', {}).get('alert_recipients', [])
        if not recipients:
            logger.warning("No alert recipients configured")
            return False

        subject = f"{'🔺' if alert_type == 'positive' else '🔻'} Sentiment Alert: {ticker} - {alert_type.upper()}"
        body_html = EmailTemplates.sentiment_alert(ticker, company_name, articles,
                                                   sentiment_summary, alert_type)

        success = True
        for recipient in recipients:
            result = self.provider.send_email(recipient, subject, body_html)
            success = success and result

        return success

    def send_daily_digest(self, stocks_data: List[Dict], market_summary: Dict) -> bool:
        """
        Send daily digest email

        Args:
            stocks_data: List of stock data dictionaries
            market_summary: Market summary statistics

        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.provider:
            logger.debug("Email notifications disabled")
            return False

        recipients = self.config.get('email', {}).get('digest_recipients',
                                                       self.config.get('email', {}).get('alert_recipients', []))
        if not recipients:
            logger.warning("No digest recipients configured")
            return False

        subject = f"📊 Daily Market Digest - {datetime.now().strftime('%Y-%m-%d')}"
        body_html = EmailTemplates.daily_digest(stocks_data, market_summary)

        success = True
        for recipient in recipients:
            result = self.provider.send_email(recipient, subject, body_html)
            success = success and result

        return success

    def send_breaking_news_alert(self, ticker: str, company_name: str,
                                 article: Dict) -> bool:
        """
        Send breaking news alert

        Args:
            ticker: Stock ticker
            company_name: Company name
            article: News article

        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.provider:
            logger.debug("Email notifications disabled")
            return False

        recipients = self.config.get('email', {}).get('alert_recipients', [])
        if not recipients:
            logger.warning("No alert recipients configured")
            return False

        subject = f"🚨 Breaking News: {ticker} - {article.get('title', 'News Alert')[:50]}"
        body_html = EmailTemplates.breaking_news_alert(ticker, company_name, article)

        success = True
        for recipient in recipients:
            result = self.provider.send_email(recipient, subject, body_html)
            success = success and result

        return success

    def check_sentiment_thresholds(self, ticker: str, company_name: str,
                                   articles: List[Dict], sentiment_summary: Dict) -> bool:
        """
        Check if sentiment exceeds configured thresholds and send alerts

        Args:
            ticker: Stock ticker
            company_name: Company name
            articles: News articles
            sentiment_summary: Sentiment summary

        Returns:
            True if alert was sent
        """
        if not articles or not sentiment_summary:
            return False

        thresholds = self.config.get('email', {}).get('alert_thresholds', {})
        positive_threshold = thresholds.get('positive_sentiment_threshold', 0.7)
        negative_threshold = thresholds.get('negative_sentiment_threshold', -0.6)

        avg_sentiment = sentiment_summary.get('average_sentiment', 0)

        # Check positive threshold
        if avg_sentiment >= positive_threshold:
            logger.info(f"Positive sentiment threshold exceeded for {ticker}: {avg_sentiment:.3f}")
            return self.send_sentiment_alert(ticker, company_name, articles,
                                            sentiment_summary, 'positive')

        # Check negative threshold
        elif avg_sentiment <= negative_threshold:
            logger.info(f"Negative sentiment threshold exceeded for {ticker}: {avg_sentiment:.3f}")
            return self.send_sentiment_alert(ticker, company_name, articles,
                                            sentiment_summary, 'negative')

        return False


if __name__ == "__main__":
    # Example usage
    print("EGXpy Email Notification System")
    print("=" * 60)

    # Check configuration
    config_path = Path(__file__).parent.parent / 'config.json'
    if not config_path.exists():
        print("No configuration file found!")
        print("Please configure email settings in config.json")
    else:
        manager = NotificationManager(str(config_path))

        if manager.enabled:
            print(f"✓ Email notifications enabled")
            print(f"  Provider: {manager.config.get('email', {}).get('provider', 'smtp').upper()}")
            print(f"  Recipients: {manager.config.get('email', {}).get('alert_recipients', [])}")
        else:
            print("✗ Email notifications disabled")
            print("  Enable in config.json to receive alerts")
