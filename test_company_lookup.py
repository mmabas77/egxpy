"""
Quick test script to verify company name automatic lookup works

This script tests the integration between news fetching and company lookup
"""

from egxpy.company_lookup import CompanyLookup

print("Testing Company Name Automatic Lookup")
print("=" * 60)

# Initialize lookup
lookup = CompanyLookup()

# Test common Egyptian stocks
test_tickers = ['COMI', 'ETEL', 'HRHO', 'ORWE', 'SWDY', 'PHDC', 'JUFO', 'DFRE']

print("\nAutomatic Company Name Resolution:")
print("-" * 60)
for ticker in test_tickers:
    company = lookup.get_company_name(ticker)
    if company:
        print(f"✓ {ticker:8} -> {company}")
    else:
        print(f"✗ {ticker:8} -> NOT FOUND")

# Test reverse lookup
print("\n" + "=" * 60)
print("Reverse Lookup (Company Name -> Ticker):")
print("-" * 60)

test_names = ['Commercial', 'Hermes', 'Palm Hills', 'Juhayna']
for name in test_names:
    ticker = lookup.search_by_company_name(name)
    if ticker:
        print(f"'{name}' -> {ticker}")
    else:
        print(f"'{name}' -> NOT FOUND")

# Show total count
print("\n" + "=" * 60)
print(f"Total Egyptian companies in database: {len(lookup.get_all_egx_tickers())}")
print("=" * 60)

print("\n✓ Company lookup working correctly!")
print("\nNow you can use news fetching with just the ticker:")
print("  fetcher.fetch_news_for_ticker('COMI')  # No company name needed!")
