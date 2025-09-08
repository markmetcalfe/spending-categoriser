# Spending Categoriser

This project is a spending categoriser that helps you analyse your bank statements and break down your spending into meaningful categories. It is designed to make it easy to track where your money goes, identify spending patterns, and gain insights into your financial habits.

## Features

- **Import Bank Statements:** Load CSV files of your bank statements into the system.
- **Automatic & Manual Categorisation:** Transactions are automatically categorised based on past data and similarity, with the option for manual review and override.
- **Custom Categories:** Define your own categories and subcategories in `categories.json`.
- **Database Storage:** All transactions are stored in a local SQLite database for fast access and analysis.
- **Spending Summaries:** Generate summaries of your spending by category, including totals and breakdowns.

## How It Works

1. **Prepare Your Statements:**
   - Place your bank statement CSV files in the `statements/` directory.
2. **Load Transactions:**
   - Run `load_transactions.py` to import transactions into the database.
3. **Categorise Transactions:**
   - Run `categorise_transactions.py` to automatically and/or manually assign categories to each transaction.
4. **Summarise Spending:**
   - Run `summary_by_category.py` to see a breakdown of your spending by category.

## Getting Started

1. Install dependencies:
   ```sh
   rm -rf .venv && \
   python -m venv .venv && \
   source .venv/bin/activate && \
   pip install -r requirements.txt
   ```
2. Place your CSV files in the `statements/` folder.
3. Copy `categories.example.json` to `categories.json` and add/modify/remove categories to your liking.
3. Run the scripts in order:
   ```sh
   python load_transactions.py
   python categorise_transactions.py
   python summary_by_category.py
   ```

## Example

After running the scripts, you'll get a summary like:

```
Essential: $1200.00
    └── Rent: $1000.00
    └── Utilities: $200.00
Non-Essential: $500.00
    └── Dining Out: $150.00
    └── Groceries: $350.00
```

## License

MIT License
