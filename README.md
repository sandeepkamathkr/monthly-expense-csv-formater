# Monthly Expense CSV Formatter

A Python tool that processes raw bank CSV exports from CommBank and HSBC into clean, categorised transaction files ready to import into your monthly expense tracking app.

## What It Does

- Automatically detects and processes all CSV files in the directory
- Supports two bank export formats: **CommBank (CSVData)** and **HSBC Credit Card (TransHist)**
- Categorises transactions into spending groups (Groceries, Eating out, Bills, etc.)
- Automatically excludes unwanted transactions (internal transfers, salary, credit card repayments, income)
- Outputs clean `_Monthly_Processed.csv` files ready for import

## Supported File Types

| File Pattern | Bank | Format |
|---|---|---|
| `CSVData*.csv` | CommBank | Date, Description, Amount, Category |
| `TransHist*.csv` | HSBC Credit Card | Date, Description, Amount, Category |

## Quick Start

```bash
python3 simple_processor.py
```

Place your exported CSV files in the same folder and run the command. Processed files are saved automatically.

## Automatic Exclusions

The following transaction types are automatically removed from output:

| Filter | Reason |
|---|---|
| `HSBC CARDS` / `BPAY PAYMENT` | Credit card repayments (double counting) |
| `TRANSFER FROM XX` / `TRANSFER TO XX` | Internal transfers between own accounts |
| `FAST TRANSFER FROM` | Incoming family/personal credits |
| `TRANSFER TO PEARLER` | Investment transfers |
| `TRANSFER TO K R KAMATH` / `TRANSFER TO KAUSHIK PATEL` | Family transfers |
| `SALARY` | Wage/salary income |
| `DIRECT CREDIT` / `PARENTALLEAVEPAY` | Government payments and income |
| `DR RABIA SHAIKH` | One-off medical payment |
| `RETURN ` | Refunds credited back |

To add a new exclusion, add a keyword to `EXCLUDE_FILTERS` in `simple_processor.py`.

## Output

Each input file produces a processed file:
- `CSVData (14).csv` → `CSVData (14)_Monthly_Processed.csv`
- `TransHist (7).csv` → `TransHist (7)_Monthly_Processed.csv`

## Requirements

- Python 3
- pandas (`pip install pandas`)
