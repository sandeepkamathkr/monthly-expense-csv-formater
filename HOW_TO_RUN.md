# How to Run Your Monthly CSV Processing

## Simple Command

```bash
python3 simple_processor.py
```

Run this from the project directory after placing your CSV exports in the same folder.

---

## Monthly Workflow

1. Export CSV files from CommBank and HSBC
2. Drop them into the `/monthly-expense-csv-formater/` folder
3. Run `python3 simple_processor.py`
4. Upload the `_Monthly_Processed.csv` files to your expense app

---

## Before Running

- Place your CSV files in the same directory as `simple_processor.py`
- Supported filenames: `CSVData*.csv` (CommBank) and `TransHist*.csv` (HSBC)
- Already processed files (`_Monthly_Processed.csv`) are automatically skipped

---

## What Gets Filtered Out

The script automatically excludes the following transaction types so you don't have to clean them up manually:

| Type | Examples |
|---|---|
| Credit card repayments | HSBC CARDS BPAY, BPAY PAYMENT |
| Internal bank transfers | Transfer from/to xx(account), Transfer to xx0475 |
| Investment transfers | Transfer To Pearler |
| Incoming family transfers | Fast Transfer From Kalathil R Kamath |
| Named family transfers | Transfer To K R Kamath, Transfer To Kaushik Patel |
| Salary & income | Salary TRANSPORTSERVICE, PARENTALLEAVEPAY |
| Credits & refunds | Direct Credit, Return APPLE.COM |
| One-off exclusions | DR RABIA SHAIKH |

### Adding a New Exclusion

Open `simple_processor.py` and add a keyword to the `EXCLUDE_FILTERS` list at the top:

```python
EXCLUDE_FILTERS = [
    'HSBC CARDS',
    'BPAY PAYMENT',
    'YOUR NEW KEYWORD HERE',   # Add your keyword and a comment
    ...
]
```

The match is case-insensitive, so `'SALARY'` will also catch `Salary` and `salary`.

---

## Output Files

Each input file gets a corresponding processed file:

| Input | Output |
|---|---|
| `CSVData (14).csv` | `CSVData (14)_Monthly_Processed.csv` |
| `CSVData (15).csv` | `CSVData (15)_Monthly_Processed.csv` |
| `TransHist (7).csv` | `TransHist (7)_Monthly_Processed.csv` |

---

## Categories Applied

| Category | Examples |
|---|---|
| Eating out | DoorDash, Guzman Y Gomez, restaurants, cafes |
| Groceries | Coles, Woolworths, Aldi, Sunrise Fresh |
| Bills | Electricity, council rates, subscriptions |
| Transport | Opal, parking, Toyota service |
| Entertainment | Netflix, Disney+, Apple, Audible |
| Fitness | Box fitness, gym memberships |
| Medicine | Chemist Warehouse, Specsavers |
| Insurance | Medibank, Toyota Insurance |
| Shopping | Kmart, Big W, Officeworks |
| Utilities | Optus, Vodafone, Aussie Broadband |
| Rent | Starr Partners Trust Account |
| Personal Care | Haircuts, grooming |
| Other | Anything not matched above |

---

## Requirements

- Python 3
- pandas (`pip install pandas`)
