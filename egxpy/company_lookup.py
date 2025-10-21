"""
Company Name Lookup Module

Automatically retrieves company names for stock tickers using:
1. Built-in dictionary for Egyptian Exchange (EGX) stocks
2. yfinance library as fallback for other tickers
3. Caching to avoid repeated lookups

This module is completely free and requires no API keys.

Author: EGXpy Contributors
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


# Comprehensive Egyptian Exchange (EGX) company mapping
# Source: Egyptian Exchange official listings
EGX_COMPANIES = {
    # Banks
    'COMI': 'Commercial International Bank',
    'CIEB': 'Credit Agricole Egypt',
    'SAIB': 'Société Arabe Internationale de Banque',
    'ADIB': 'Abu Dhabi Islamic Bank Egypt',
    'EXPA': 'Export Development Bank of Egypt',
    'QNBA': 'Qatar National Bank Alahli',
    'ADCB': 'Abu Dhabi Commercial Bank Egypt',
    'HDBK': 'Housing and Development Bank',
    'BCAI': 'Banque du Caire',
    'BCOE': 'Banque Misr',
    'NSGB': 'National Societe Generale Bank',
    'UNBE': 'Union National Bank Egypt',
    'FAIB': 'Faisal Islamic Bank of Egypt',

    # Telecommunications
    'ETEL': 'Egyptian Company for Mobile Services',  # Etisalat Misr
    'ORTE': 'Orascom Telecom Media and Technology',
    'GTHE': 'Global Telecom Holding',

    # Real Estate
    'PHDC': 'Palm Hills Developments',
    'OCDI': 'Orascom Development Egypt',
    'MNHD': 'Madinet Nasr for Housing and Development',
    'THDC': 'Talaat Moustafa Group Holding',
    'SODIC': 'Sixth of October Development and Investment Company',
    'HELI': 'Heliopolis Company for Housing and Development',
    'RMGD': 'Raya Holding for Technology and Communications',
    'ORAS': 'Orascom Construction',

    # Industrial
    'SWDY': 'El Sewedy Electric Company',
    'IRON': 'Egyptian Iron and Steel Company',
    'ALCN': 'Alexandria National Iron and Steel',
    'ESRS': 'Egyptian Starch and Glucose Manufacturing',
    'SKPC': 'Sidi Kerir Petrochemicals Company',
    'AIND': 'Arabian International Company for Spinning and Weaving',
    'NCCD': 'The National Company for Maize Products',
    'ECAP': 'Egyptian Chemical Industries (Kima)',
    'SULI': 'Suez Cement Company',
    'TORA': 'Tora Cement Company',
    'EKHO': 'El Ezz Dekheila Steel Company',
    'EAST': 'Eastern Company',
    'GTHE': 'Global Telecom Holding',

    # Consumer Goods
    'JUFO': 'Juhayna Food Industries',
    'DFRE': 'Domty',
    'EDBR': 'Edita Food Industries',
    'ARPI': 'Arabian Pipelines Company',
    'ODOM': 'Orascom Development Egypt',
    'EMFD': 'Egyptian Media Production City',

    # Investment & Holding Companies
    'HRHO': 'Hermes Holding Company',
    'PIOH': 'Pioneers Holding for Financial Investments',
    'CCAP': 'Cairo Capital Holding',
    'EFIH': 'Egyptian Financial Group Hermes Holding',
    'CIPH': 'Chemical Industries Holding Company',
    'MTPH': 'Metal and Engineering Industries Holding',

    # Tourism & Entertainment
    'OTMT': 'Orascom Hotels and Development',
    'TPRI': 'Travco Group for Tourism',
    'RMDI': 'Remida for Hotels and Real Estate Investments',
    'EGTS': 'Egyptian Tourism Resorts Company',
    'SHMS': 'Sharm Dreams Company for Tourism',

    # Healthcare & Pharmaceuticals
    'ALXA': 'Alexandria Pharmaceuticals',
    'PHAR': 'Alexandria Pharmaceuticals and Chemical Industries',
    'ACPH': 'Alexandria Company for Pharmaceuticals',
    'MBID': 'Medical Union Pharmaceuticals (Mibiopharm)',
    'ALUM': 'Alexandria Medical Equipment',
    'EBPC': 'Egyptian International Pharmaceuticals Industries Company',

    # Textiles
    'ORWE': 'Oriental Weavers',
    'KABO': 'El Kahera for Spinning and Weaving',
    'UNIL': 'United Arab Spinning and Weaving',
    'NRTX': 'Nile Cotton Ginning Company',

    # Food & Beverage
    'ISMA': 'Ismailia Misr Poultry Company',
    'UNFO': 'United Arab Company for Food Industries',
    'SUGR': 'Upper Egypt for Flour Mills',
    'AJWA': 'Ajwa for Food Industries',

    # Construction & Materials
    'SCEM': 'Suez Cement Company',
    'ACEM': 'Arabian Cement Company',
    'TCEM': 'Tora Portland Cement Company',
    'NCEM': 'National Cement Company',
    'BCEM': 'Beni Suef Cement Company',

    # Energy & Utilities
    'ASEC': 'Asec Cement Company',
    'GASCO': 'Gas and Petrochemical Services Company',
    'KAPCO': 'Kafr El Zayat for Pesticides and Chemicals',

    # Logistics & Transportation
    'AUTO': 'GB Auto',
    'UEGC': 'Universal Company for Paper and Industrial Supplies',
    'ELSA': 'Egyptian Transport and Commercial Services',

    # Financial Services (Non-Banking)
    'HELI': 'Heliopolis Company for Housing and Development',
    'GMID': 'GMI Leasing Company',
    'ELFT': 'Egyptian Financial and Industrial Company',

    # Technology
    'RITE': 'Raya Information Technology',
    'MFPC': 'Misr Fertilizers Production Company',

    # Agriculture
    'MFPC': 'Misr Fertilizers Production Company',
    'NFPC': 'Nile Fertilizers Production Company',
    'ESGL': 'Egyptian Company for Starch Glucose and Derivatives',

    # Other
    'EKPC': 'Egyptian Kuwait Holding',
    'EMOB': 'Egyptian Media Production City',
    'TMGH': 'Talaat Moustafa Group Holding',
}


class CompanyLookup:
    """Company name lookup with multiple fallback methods"""

    def __init__(self, cache_file: str = None):
        """
        Initialize company lookup

        Args:
            cache_file: Path to cache file for storing lookups
        """
        self.cache_file = cache_file or str(Path.home() / '.egxpy_company_cache.json')
        self.cache = self._load_cache()
        self.yfinance_available = self._check_yfinance()

    def _check_yfinance(self) -> bool:
        """Check if yfinance is available"""
        try:
            import yfinance
            logger.info("yfinance library available for company lookups")
            return True
        except ImportError:
            logger.info("yfinance not installed - only built-in EGX companies available")
            return False

    def _load_cache(self) -> Dict[str, str]:
        """Load cached company names"""
        cache_path = Path(self.cache_file)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cache = json.load(f)
                logger.debug(f"Loaded {len(cache)} cached company names")
                return cache
            except Exception as e:
                logger.warning(f"Error loading cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        """Save cache to file"""
        try:
            cache_path = Path(self.cache_file)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.debug(f"Saved {len(self.cache)} company names to cache")
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")

    def _lookup_yfinance(self, ticker: str) -> Optional[str]:
        """
        Lookup company name using yfinance

        Args:
            ticker: Stock ticker symbol

        Returns:
            Company name or None if not found
        """
        if not self.yfinance_available:
            return None

        try:
            import yfinance as yf

            # Try the ticker as-is first
            stock = yf.Ticker(ticker)
            info = stock.info

            # Try to get long name or short name
            company_name = info.get('longName') or info.get('shortName')

            if company_name and company_name != ticker:
                logger.info(f"Found company name via yfinance: {ticker} -> {company_name}")
                return company_name

            # For EGX stocks, try with .CA suffix (Cairo Exchange)
            if ticker not in ['COMI', 'ETEL', 'HRHO']:  # Avoid double lookup for known EGX
                stock_ca = yf.Ticker(f"{ticker}.CA")
                info_ca = stock_ca.info
                company_name = info_ca.get('longName') or info_ca.get('shortName')

                if company_name and company_name != f"{ticker}.CA":
                    logger.info(f"Found company name via yfinance with .CA: {ticker} -> {company_name}")
                    return company_name

        except Exception as e:
            logger.debug(f"yfinance lookup failed for {ticker}: {e}")

        return None

    def get_company_name(self, ticker: str, use_cache: bool = True,
                        fallback_to_yfinance: bool = True) -> Optional[str]:
        """
        Get company name for a ticker

        Args:
            ticker: Stock ticker symbol
            use_cache: Whether to use cached results
            fallback_to_yfinance: Whether to try yfinance if not in built-in list

        Returns:
            Company name or None if not found
        """
        ticker = ticker.upper().strip()

        # Check cache first
        if use_cache and ticker in self.cache:
            logger.debug(f"Company name from cache: {ticker} -> {self.cache[ticker]}")
            return self.cache[ticker]

        # Check built-in EGX companies
        if ticker in EGX_COMPANIES:
            company_name = EGX_COMPANIES[ticker]
            logger.debug(f"Company name from built-in: {ticker} -> {company_name}")

            # Cache it
            self.cache[ticker] = company_name
            self._save_cache()

            return company_name

        # Fallback to yfinance
        if fallback_to_yfinance:
            company_name = self._lookup_yfinance(ticker)
            if company_name:
                # Cache it
                self.cache[ticker] = company_name
                self._save_cache()
                return company_name

        logger.warning(f"No company name found for ticker: {ticker}")
        return None

    def get_all_egx_tickers(self) -> Dict[str, str]:
        """
        Get all known EGX tickers and company names

        Returns:
            Dictionary of ticker -> company name
        """
        return EGX_COMPANIES.copy()

    def search_by_company_name(self, company_name: str) -> Optional[str]:
        """
        Reverse lookup: find ticker by company name

        Args:
            company_name: Full or partial company name

        Returns:
            Ticker symbol or None if not found
        """
        company_name_lower = company_name.lower()

        # Search in built-in EGX companies
        for ticker, name in EGX_COMPANIES.items():
            if company_name_lower in name.lower():
                return ticker

        # Search in cache
        for ticker, name in self.cache.items():
            if company_name_lower in name.lower():
                return ticker

        return None

    def add_custom_mapping(self, ticker: str, company_name: str):
        """
        Add a custom ticker -> company name mapping

        Args:
            ticker: Stock ticker symbol
            company_name: Company name
        """
        ticker = ticker.upper().strip()
        self.cache[ticker] = company_name
        self._save_cache()
        logger.info(f"Added custom mapping: {ticker} -> {company_name}")


# Global instance for easy access
_global_lookup = None

def get_company_name(ticker: str) -> Optional[str]:
    """
    Convenience function to get company name for a ticker

    Args:
        ticker: Stock ticker symbol

    Returns:
        Company name or None if not found
    """
    global _global_lookup
    if _global_lookup is None:
        _global_lookup = CompanyLookup()
    return _global_lookup.get_company_name(ticker)


if __name__ == "__main__":
    # Example usage
    print("EGXpy Company Lookup Module")
    print("=" * 60)

    lookup = CompanyLookup()

    # Test some Egyptian stocks
    test_tickers = ['COMI', 'ETEL', 'HRHO', 'ORWE', 'SWDY', 'PHDC']

    print("\nEgyptian Stock Lookups:")
    print("-" * 60)
    for ticker in test_tickers:
        company = lookup.get_company_name(ticker)
        if company:
            print(f"{ticker:10} -> {company}")
        else:
            print(f"{ticker:10} -> Not found")

    print("\n" + "=" * 60)
    print(f"Total EGX companies in database: {len(EGX_COMPANIES)}")

    # Test reverse lookup
    print("\nReverse Lookup Test:")
    print("-" * 60)
    search_term = "Commercial"
    ticker = lookup.search_by_company_name(search_term)
    print(f"Search for '{search_term}': {ticker}")
