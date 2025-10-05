import os
import pandas as pd
import sqlite3
from typing import List, Optional
import datetime
import hashlib

def get_statement_files(directory: str = "statements") -> List[str]:
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return []
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith('.csv')]

def load_transactions_from_csv(csv_path: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return None
    df = pd.read_csv(csv_path)
    if df.shape[1] < 4:
        print(f"CSV {csv_path} must have at least 4 columns (date, description, ..., amount, balance).")
        return None
    # Extract columns by position
    date_col = df.columns[1]
    desc_col = df.columns[2]
    ref_col = df.columns[4]
    part_col = df.columns[5]
    code_col = df.columns[6]
    amount_col = df.columns[-2]
    balance_col = df.columns[-1]
    df['Date'] = df[date_col].apply(lambda x: datetime.datetime.strptime(x, "%d-%m-%Y").date().isoformat())
    df['Description'] = df[desc_col]
    df['Reference'] = df[ref_col]
    df['Particulars'] = df[part_col]
    df['Code'] = df[code_col]
    df['Amount'] = df[amount_col]
    df['Balance'] = df[balance_col]
    df['SourceFile'] = os.path.basename(csv_path)
    return df[['Description', 'Particulars', 'Code', 'Reference', 'Amount', 'Date', 'Balance', 'SourceFile']]

def get_existing_accounts(conn) -> List[str]:
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT account FROM transactions")
    accounts = [row[0] for row in cur.fetchall() if row[0]]
    return sorted(accounts)

def main() -> None:
    statement_dir = "statements"
    file_paths = get_statement_files(statement_dir)
    if not file_paths:
        print(f"No CSV files found in '{statement_dir}' directory.")
        return
    conn = sqlite3.connect('finances.db')
    cur = conn.cursor()
    # Ensure tables exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            description TEXT,
            part TEXT,
            code TEXT,
            ref TEXT,
            amount REAL,
            date TEXT,
            balance REAL,
            account TEXT,
            category TEXT
        )
    """)
    all_transactions = []
    for path in file_paths:
        existing_accounts = get_existing_accounts(conn)
        print(f"\nProcessing file: {os.path.basename(path)}")
        if existing_accounts:
            print("Existing accounts:")
            for i, acc in enumerate(existing_accounts):
                print(f"  {i+1}. {acc}")
            print(f"  {len(existing_accounts)+1}. Enter a new account name")
            choice = input("Select an account by number or enter a new name: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(existing_accounts):
                account = existing_accounts[int(choice)-1]
            elif choice == str(len(existing_accounts)+1):
                account = input("Enter new account name: ").strip()
            else:
                account = choice if choice else input("Enter account name: ").strip()
        else:
            account = input(f"Enter the account name for '{os.path.basename(path)}': ").strip()
        df = load_transactions_from_csv(path)
        if df is not None:
            df['Account'] = account
            all_transactions.append(df)
    if not all_transactions:
        print("No valid transactions loaded.")
        return
    full_df = pd.concat(all_transactions, ignore_index=True)
    inserted = 0
    skipped = 0
    total = 0
    for _, row in full_df.iterrows():
        total += 1
        unique_str = f"{row['Description']}|{row['Amount']}|{row['Date']}|{row['Balance']}|{row['Account']}"
        transaction_id = hashlib.md5(unique_str.encode('utf-8')).hexdigest()
        cur.execute("""
            SELECT 1
            FROM transactions
            WHERE id = ?
        """, (transaction_id,))
        if cur.fetchone():
            cur.execute("""
                UPDATE transactions
                SET part = ?, code = ?, ref = ?
                WHERE id = ?
            """, (row['Particulars'], row['Code'], row['Reference'], transaction_id))
            skipped += 1
            continue
        cur.execute(
            "INSERT OR REPLACE INTO transactions (id, description, part, code, ref, amount, date, balance, account) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (transaction_id, row['Description'], row['Particulars'], row['Code'], row['Reference'], row['Amount'], row['Date'], row['Balance'], row['Account'])
        )
        inserted += 1
    conn.commit()
    print(f"Processed {total} transactions: {inserted} inserted or updated, {skipped} skipped (duplicates).")
    conn.close()

if __name__ == "__main__":
    main()
