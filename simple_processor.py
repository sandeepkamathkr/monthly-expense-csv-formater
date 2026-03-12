#!/usr/bin/env python3
"""
Monthly CSV Processor
Processes bank CSV exports with configurable categories and exclusions.
Edit categories.json to add/remove keywords or exclusion rules.
"""

import pandas as pd
import os
import json
import re

CATEGORIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'categories.json')

# Payment processor prefixes that hide the real vendor name
_PREFIX_RE = re.compile(
    r'^(SQ \*|LS \*|ZLR\*|SMP\*|ShopBack\s+|PB\s+|SP \*)',
    flags=re.IGNORECASE
)


class SimpleTransactionCategorizer:
    """Categorizes transactions using rules from categories.json."""

    def __init__(self):
        with open(CATEGORIES_FILE, 'r') as f:
            config = json.load(f)

        # Pull out the exclusion rules, leaving only category rules
        self.exclude_rules = config.pop('_exclude', {})

        # Store keywords in uppercase so matching is case-insensitive
        self.category_rules = {
            cat: [kw.upper() for kw in keywords]
            for cat, keywords in config.items()
        }

    def strip_prefix(self, description):
        """Remove payment processor prefixes (SQ *, LS *, ZLR*, etc.)."""
        return _PREFIX_RE.sub('', str(description)).strip()

    def should_exclude(self, description):
        """Return True if this row should be dropped (income or personal transfer)."""
        desc_upper = str(description).upper()
        for group in self.exclude_rules.values():
            for pattern in group:
                if pattern.upper() in desc_upper:
                    return True
        return False

    def categorize(self, description):
        """Categorize a transaction based on its description."""
        cleaned = self.strip_prefix(description)
        desc_upper = cleaned.upper()

        for category, keywords in self.category_rules.items():
            if any(kw in desc_upper for kw in keywords):
                return category

        return 'Other'


def clean_amount(amount_str):
    """Clean and convert amount string to float."""
    if pd.isna(amount_str):
        return 0.0
    cleaned = str(amount_str).replace('"', '').replace(',', '').strip()
    try:
        return abs(float(cleaned))
    except Exception:
        return 0.0


def clean_date(date_str):
    """Clean and standardize date to DD/MM/YYYY."""
    if pd.isna(date_str):
        return ""
    cleaned = str(date_str).replace('\ufeff', '').strip()
    try:
        if '/' in cleaned:
            return cleaned
        date_obj = pd.to_datetime(cleaned, format='%d %b %Y')
        return date_obj.strftime('%d/%m/%Y')
    except Exception:
        return cleaned


def detect_file_format(df):
    """Detect whether the file has a header row or starts directly with data."""
    first_row = df.iloc[0]
    try:
        pd.to_datetime(str(first_row.iloc[0]), format='%d/%m/%Y')
        return 'no_headers'
    except Exception:
        try:
            pd.to_datetime(str(first_row.iloc[0]))
            return 'no_headers'
        except Exception:
            pass
    if any(word in str(first_row.iloc[0]).lower() for word in ['date', 'transaction']):
        return 'has_headers'
    return 'no_headers'


def process_file(filename):
    """
    Process a single CSV file.

    CommBank format (no headers): Date | Amount | Description | Running Balance
    TransHist format (has headers): Transaction Date | Posting Date | Description | Amount
    Both produce the same output: Date, Description, Amount, Category
    """
    print(f"📁 Processing: {filename}")

    if not os.path.exists(filename):
        print(f"  ❌ File not found: {filename}")
        return None

    try:
        df_peek = pd.read_csv(filename)
        file_format = detect_file_format(df_peek)

        if file_format == 'no_headers':
            df = pd.read_csv(filename, header=None)
            print(f"  📊 Found {len(df)} rows (CommBank format)")
        else:
            df = df_peek
            print(f"  📊 Found {len(df)} rows (TransHist format)")

        categorizer = SimpleTransactionCategorizer()

        # Column positions differ between formats:
        #   CommBank:   col0=Date, col1=Amount, col2=Description
        #   TransHist:  col0=TxnDate, col1=PostingDate(skip), col2=Description, col3=Amount
        is_transhist = 'transhist' in filename.lower() or file_format == 'has_headers'

        result_df = pd.DataFrame()
        result_df['Date'] = df.iloc[:, 0].apply(clean_date)
        result_df['Description'] = df.iloc[:, 2].astype(str).str.strip()

        if is_transhist:
            result_df['Amount'] = df.iloc[:, 3].apply(clean_amount)
        else:
            result_df['Amount'] = df.iloc[:, 1].apply(clean_amount)

        # Drop income and personal transfer rows
        result_df = result_df[
            ~result_df['Description'].apply(categorizer.should_exclude)
        ].copy()

        # Drop rows with zero/invalid amounts and missing data
        result_df = result_df[result_df['Amount'] > 0].copy()
        result_df = result_df.dropna(subset=['Date', 'Description']).copy()
        result_df = result_df[result_df['Description'] != 'nan'].copy()

        # Categorize
        result_df['Category'] = result_df['Description'].apply(categorizer.categorize)

        # Enforce consistent column order
        result_df = result_df[['Date', 'Description', 'Amount', 'Category']]

        print(f"  ✅ Kept: {len(result_df)} transactions")
        print(f"  💰 Total: ${result_df['Amount'].sum():.2f}")

        if len(result_df) > 0:
            top_categories = result_df['Category'].value_counts().head(3)
            print(f"  🏷️  Top categories: {dict(top_categories)}")

        return result_df

    except Exception as e:
        print(f"  ❌ Error processing {filename}: {e}")
        import traceback
        traceback.print_exc()
        return None


def find_csv_files():
    """Find all raw CSV files in the current directory, skipping processed outputs."""
    import glob
    input_files = []
    for f in sorted(glob.glob("*.csv")):
        if ('_Processed.csv' in f or '_Monthly_Processed.csv' in f or
                f.endswith('_processed.csv') or f.endswith('_monthly_processed.csv')):
            continue
        input_files.append(f)
    return input_files


def main():
    """Main processing function."""
    print("🔄 MONTHLY EXPENSE PROCESSOR")
    print("=" * 45)
    print(f"📁 Working in: {os.getcwd()}")
    print()

    csv_files = find_csv_files()

    if not csv_files:
        print("❌ No CSV files found.")
        print("   Add your bank export CSV files to this directory and run again.")
        return

    print(f"📄 Found {len(csv_files)} CSV file(s):")
    for f in csv_files:
        print(f"   • {f}")
    print()

    successful = 0
    total_transactions = 0
    total_amount = 0.0
    processed_files = []

    for filename in csv_files:
        base_name = filename.replace('.csv', '')
        output_filename = f"{base_name}_Monthly_Processed.csv"

        result_df = process_file(filename)

        if result_df is not None and len(result_df) > 0:
            result_df.to_csv(output_filename, index=False)
            print(f"  💾 Saved: {output_filename}")
            successful += 1
            total_transactions += len(result_df)
            total_amount += result_df['Amount'].sum()
            processed_files.append(output_filename)
        elif result_df is not None:
            print(f"  ⚠️  No valid transactions found in {filename}")

        print()

    print("=" * 45)
    print(f"📊 SUMMARY: {successful}/{len(csv_files)} files processed")

    if successful > 0:
        print(f"📈 Total transactions: {total_transactions}")
        print(f"💰 Total amount: ${total_amount:.2f}")
        print()
        print("✅ Output files:")
        for pf in processed_files:
            print(f"   • {pf}")
        print()
        print("Next month: replace CSV files and run python3 simple_processor.py")


if __name__ == "__main__":
    main()
