#!/usr/bin/env python3
"""
Fixed Local Monthly CSV Processor
Handles files without headers correctly
"""

import pandas as pd
import os

# Transactions to always exclude (internal transfers, credit card repayments, income/credits)
EXCLUDE_FILTERS = [
    'HSBC CARDS',           # Credit card repayments from CommBank to HSBC
    'BPAY PAYMENT',         # Credit card payments showing on HSBC side
    'TRANSFER FROM XX',     # Internal transfers from own bank accounts (by account number)
    'TRANSFER TO XX',       # Internal transfers to own bank accounts (by account number)
    'TRANSFER TO PEARLER',  # Investment transfers to Pearler
    'FAST TRANSFER FROM',   # Incoming family/personal credits
    'TRANSFER TO K R KAMATH',   # Family transfers to K R Kamath
    'TRANSFER TO KAUSHIK PATEL',  # Personal transfers to Kaushik Patel
    'DIRECT CREDIT',        # Income, cashback and other credits coming in
    'PARENTALLEAVEPAY',     # Parental leave government income
    'SALARY',               # Salary/wage income coming in
    'DR RABIA SHAIKH',      # One-off doctor payment
    'RETURN ',              # Refunds/returns credited back
]

def is_excluded(description):
    """Return True if the transaction should be excluded from output."""
    description_upper = str(description).upper().strip()
    return any(keyword.upper() in description_upper for keyword in EXCLUDE_FILTERS)


class SimpleTransactionCategorizer:
    """Simple categorization system."""

    def __init__(self):
        self.category_rules = {
            'Eating out': [
                'DOORDASH', 'MENULOG', 'UBER EATS', 'RESTAURANT', 'GUZMAN Y GOMEZ',
                'MCDONALD', 'KFC', 'SUBWAY', 'PIZZA', 'CAFE', 'BAKERY', 'DUMPLINGS',
                'CURRY LOVERS', 'LITTLE GREECE', 'INCAFE', 'CHAT THAI', 'SUSHI',
                'NOODLE BAR', 'CENTRAL FRUIT JUICE', 'MANOUSHI',
                'BREADTOP', 'CHATIME', 'LEAF CAFE', 'CHARGRILL', 'URBAN CHOWK',
                'PMC GOLDEN TOWER', 'CHINESE', 'JAPANESE', 'THAI',
                'BISTRO', 'GRILL', 'KITCHEN', 'EATERY', 'TAKEAWAY', 'DELIVERY',
                'DASHPASS',
                # Confirmed eating out vendors
                'FRIED BROTHERS', 'INDOCHAINESE', 'MRS WANG', 'AMRITSARI DHABA',
                'CHERRY BEAN', 'SAVIA MANRAM', 'SAIVA MANRAM', 'MAD MEX',
                'LITTLE INDIA', 'MAX BRENNER', 'S PATEL & K SHAH', 'THREEFOLD PASTRY',
                'MESSINA', 'THREE BEANS', 'JAIPUR SWEETS', 'NARAYAN',
                'SHOPBACK SARAVANAA', 'A2B SYDNEY', 'DAVID S KITCHEN',
                '7 ELEVEN', '7-ELEVEN', 'WESTMEAD PRIVATE', 'LS PHTY',
                'TAM PH PTY', 'GECAL ENTERPRISES', 'BWS LIQUOR', 'CHATKAZZ',
                'SHARVIL FOODS', 'RIMPLE KANE',
            ],
            'Groceries': [
                'COLES', 'WOOLWORTHS', 'ALDI', 'IGA', 'SUNRISE FRUIT', 'SUNRISE FRESH',
                'GREEN FARM MEAT', 'BUTCHER', 'GROCERY', 'SUPERMARKET', 'FRESH',
            ],
            'Medicine': [
                'CHEMIST WAREHOUSE', 'SHOPBACK CHEMIST', 'PHARMACY', 'QSCAN', 'LAVERTY PATHOLOGY',
                'DARCY ROAD PHARMACY', 'DENTIST', 'HOSPITAL', 'CLINIC', 'MEDICARE',
            ],
            'Transport': [
                'TRANSPORTFORNSW', 'OPAL', 'TRAIN', 'BUS', 'FERRY',
                'UBER', 'TAXI', 'RIDESHARE', 'PARKING', 'WILSON PARKING', 'EASYPARK',
                'PCC EAT STREET',
            ],
            'Sandeep Fitness': [
                'BOXFITNESS', 'GYM', 'FITNESS', 'YOGA', 'PILATES', 'SPORT', 'GOCARDLESS',
            ],
            'Entertainment': [
                'NETFLIX', 'SPOTIFY', 'APPLE.COM/BILL', 'APPLE MUSIC', 'DISNEY',
                'PAYPAL *NETFLIX', 'PAYPAL *DISNEY',
                'AMAZON PRIME', 'ENTERTAINMENT', 'MOVIE', 'CINEMA',
                'OPENAI', 'CHATGPT', 'CLAUDE.AI',
                'AUDIBLE', 'KINDLE',
            ],
            'Shopping': [
                'AMAZON', 'EBAY', 'OFFICEWORKS', 'COSTCO', 'TARGET', 'KMART', 'BUNNINGS',
                'BIG W', 'THE REJECT SHOP',
                # Confirmed shopping vendors
                'DISCOUNT PARTY WAREHOUSE', 'HOME AND HUTCH', 'MICHE BOUTIQUE',
                'CAKE DECORATING', 'SMART DOLLAR', 'SPECSAVERS', 'CHEESECAKE SHOP',
            ],
            'Internet': [
                'AUSSIE BROADBAND', 'TELSTRA', 'INTERNET', 'NBN', 'BROADBAND',
                'VODAFONEAUS',
            ],
            'Mobile bill': [
                'OPTUS', 'VODAFONE', 'PAYPAL *VODAFONE', 'PREPAID', 'BOOST MOBILE',
            ],
            'Medical insurance': [
                'MEDIBANK PHI', 'BUPA', 'HCF', 'NIB', 'HEALTH FUND', 'HEALTH INSURANCE',
            ],
            'Life insurance': [
                'MEDIBANK LIFE', 'AIA', 'TAL LIFE', 'LIFE INSURANCE',
            ],
            'Car insurance': [
                'TOYOTA INSURANCE', 'AIOI NISSAY', 'NRMA', 'AAMI', 'RACV', 'CAR INSURANCE',
            ],
            'Car Service': [
                'PARRAMATTA TOYOTA', 'CAR SERVICE', 'AUTO SERVICE', 'MECHANIC',
            ],
            'Day care': [
                'ADVANCED EL',
            ],
            'Isha Swimming': [
                'CUMBERLAND COUNC',
            ],
            'Personal Care': [
                'HAIRCUT', 'BARBER', 'SALON', 'BEAUTY', 'SMP*BROWN BOYS', 'BROWN BOYS',
            ],
            'Rent': [
                'STARR PARTNERS', 'RENT', 'REAL ESTATE',
            ],
            'Personal Transfer': [
                'TRANSFER TO', 'PAYID', 'OSKO', 'TRANSFER FROM', 'KALATHIL', 'KAMATH',
            ],
            'Bills': [
                'BPAY', 'DIRECT DEBIT', 'SUBSCRIPTION',
            ],
            'Fees': [
                'INTERNATIONAL TRANSACTION FEE', 'OVERSEAS TRANSACTION FEE', 'FEE', 'CHARGE',
            ],
        }
    
    def categorize(self, description):
        """Categorize a transaction based on its description."""
        description_upper = str(description).upper().strip()
        
        for category, keywords in self.category_rules.items():
            if any(keyword in description_upper for keyword in keywords):
                return category
        
        return 'Other'

def clean_amount(amount_str):
    """Clean and convert amount string to float."""
    if pd.isna(amount_str):
        return 0.0
    
    cleaned = str(amount_str).replace('"', '').replace(',', '').strip()
    try:
        if cleaned.startswith(('+', '-')):
            return abs(float(cleaned))
        return abs(float(cleaned))
    except:
        return 0.0

def clean_date(date_str):
    """Clean and standardize date format."""
    if pd.isna(date_str):
        return ""
    
    cleaned = str(date_str).replace('﻿', '').strip()
    
    try:
        if '/' in cleaned:
            return cleaned
        else:
            date_obj = pd.to_datetime(cleaned, format='%d %b %Y')
            return date_obj.strftime('%d/%m/%Y')
    except:
        return cleaned

def detect_file_format(df):
    """Detect if the file has headers or starts directly with data."""
    first_row = df.iloc[0]
    
    # Check if first column looks like a date
    try:
        pd.to_datetime(str(first_row.iloc[0]), format='%d/%m/%Y')
        return 'no_headers'  # Data starts immediately
    except:
        try:
            pd.to_datetime(str(first_row.iloc[0]))
            return 'no_headers'  # Data starts immediately  
        except:
            pass
    
    # Check if it looks like headers
    if any(word in str(first_row.iloc[0]).lower() for word in ['date', 'transaction']):
        return 'has_headers'
    
    return 'no_headers'  # Default assumption

def process_file(filename, output_format):
    """Process a single CSV file."""
    print(f"📁 Processing: {filename}")
    
    if not os.path.exists(filename):
        print(f"  ❌ File not found: {filename}")
        return None
    
    try:
        # First, peek at the file to detect format
        df_peek = pd.read_csv(filename)
        file_format = detect_file_format(df_peek)
        
        if file_format == 'no_headers':
            # Read without treating first row as headers
            df = pd.read_csv(filename, header=None)
            print(f"  📊 Found {len(df)} rows (raw data format)")
        else:
            df = df_peek
            print(f"  📊 Found {len(df)} rows (with headers)")
        
        print(f"  📋 First row: {list(df.iloc[0])}")
        
        categorizer = SimpleTransactionCategorizer()
        result_df = pd.DataFrame()
        
        if output_format == "Date_Amount_Description_Category":
            # For CSVData.csv and CSVData2.csv (raw format expected)
            result_df['Date'] = df.iloc[:, 0].apply(clean_date)
            result_df['Amount'] = df.iloc[:, 1].apply(clean_amount) 
            result_df['Description'] = df.iloc[:, 2].astype(str).str.strip()
            result_df['Category'] = result_df['Description'].apply(categorizer.categorize)
            
        elif output_format == "Date_Description_Amount_Category":
            # For TransHist.csv
            if file_format == 'has_headers' and 'Category' in df.columns:
                # Already has proper headers and categories
                result_df['Date'] = df['Date'].apply(clean_date) if 'Date' in df.columns else df.iloc[:, 0].apply(clean_date)
                result_df['Description'] = df['Description'].astype(str).str.strip() if 'Description' in df.columns else df.iloc[:, 2].astype(str).str.strip()
                result_df['Amount'] = df['Amount'].apply(clean_amount) if 'Amount' in df.columns else df.iloc[:, 3].apply(clean_amount)
                result_df['Category'] = df['Category'].astype(str).str.strip() if 'Category' in df.columns else result_df['Description'].apply(categorizer.categorize)
            else:
                # Raw format - no proper headers
                result_df['Date'] = df.iloc[:, 0].apply(clean_date)
                result_df['Description'] = df.iloc[:, 2].astype(str).str.strip()
                result_df['Amount'] = df.iloc[:, 3].apply(clean_amount)
                result_df['Category'] = result_df['Description'].apply(categorizer.categorize)
        
        # Filter positive amounts and clean data
        result_df = result_df[result_df['Amount'] > 0].copy()
        result_df = result_df.dropna(subset=['Date', 'Description']).copy()

        # Exclude internal transfers, credit card repayments and income/credits
        excluded = result_df[result_df['Description'].apply(is_excluded)]
        if len(excluded) > 0:
            print(f"  🚫 Excluded {len(excluded)} transaction(s):")
            for _, row in excluded.iterrows():
                print(f"     - {row['Date']} | {row['Description'][:60]} | ${row['Amount']:.2f}")
        result_df = result_df[~result_df['Description'].apply(is_excluded)].copy()
        
        print(f"  ✅ Processed: {len(result_df)} transactions")
        print(f"  💰 Total: ${result_df['Amount'].sum():.2f}")
        print(f"  📈 Categories: {len(result_df['Category'].unique())} types")
        
        # Show top categories
        if len(result_df) > 0:
            top_categories = result_df['Category'].value_counts().head(3)
            print(f"  🏷️  Top categories: {dict(top_categories)}")
        
        return result_df
        
    except Exception as e:
        print(f"  ❌ Error processing {filename}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def determine_output_format(filename):
    """Determine the best output format based on filename or content."""
    filename_lower = filename.lower()
    
    # TransHist files get the Date_Description_Amount_Category format
    if 'transhist' in filename_lower or 'trans_hist' in filename_lower:
        return 'Date_Description_Amount_Category'
    
    # Everything else gets Date_Amount_Description_Category format
    return 'Date_Amount_Description_Category'

def find_csv_files():
    """Find all CSV files in the current directory, excluding processed ones."""
    import glob
    
    all_csv_files = glob.glob("*.csv")
    
    # Exclude already processed files but include original input files
    input_files = []
    for file in all_csv_files:
        # Skip files that are clearly processed outputs
        if ('_Processed.csv' in file or 
            '_Monthly_Processed.csv' in file or 
            file.endswith('_processed.csv') or 
            file.endswith('_monthly_processed.csv')):
            continue
        # Include all other CSV files
        input_files.append(file)
    
    return sorted(input_files)  # Sort for consistent ordering

def main():
    """Main processing function."""
    print("🔄 AUTOMATIC CSV PROCESSOR")
    print("=" * 45)
    print(f"📁 Working in: {os.getcwd()}")
    print()
    
    # Find all CSV files automatically
    csv_files = find_csv_files()
    
    if not csv_files:
        print("❌ No CSV files found to process!")
        print("   Make sure you have CSV files in the current directory.")
        return
    
    print(f"📄 Found {len(csv_files)} CSV file(s) to process:")
    for file in csv_files:
        print(f"   • {file}")
    print()
    
    successful = 0
    total_transactions = 0
    total_amount = 0
    processed_files = []
    
    for filename in csv_files:
        # Determine output format based on filename
        output_format = determine_output_format(filename)
        
        # Generate output filename
        base_name = filename.replace('.csv', '')
        output_filename = f"{base_name}_Monthly_Processed.csv"
        
        print(f"🎯 Target format: {output_format.replace('_', ', ')}")
        
        result_df = process_file(filename, output_format)
        
        if result_df is not None and len(result_df) > 0:
            # Save the processed file
            result_df.to_csv(output_filename, index=False)
            print(f"  💾 Saved: {output_filename}")
            
            successful += 1
            total_transactions += len(result_df)
            total_amount += result_df['Amount'].sum()
            processed_files.append(output_filename)
        elif result_df is not None:
            print(f"  ⚠️  No valid transactions found in {filename}")
        
        print()
    
    # Summary
    print("=" * 45)
    print(f"📊 SUMMARY: {successful}/{len(csv_files)} files processed")
    
    if successful > 0:
        print(f"📈 Total transactions: {total_transactions}")
        print(f"💰 Total amount: ${total_amount:.2f}")
        print()
        print("✅ Your processed files:")
        for processed_file in processed_files:
            print(f"   • {processed_file}")
        print()
        print("🔄 Next month:")
        print("   1. Replace CSV files with new exports")
        print("   2. Run: python3 simple_processor.py")
        print("   3. Get fresh processed files automatically!")
    else:
        print("❌ No files were successfully processed.")
        print("   Check that your CSV files contain valid transaction data.")

if __name__ == "__main__":
    main()
