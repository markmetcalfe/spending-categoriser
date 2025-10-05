import sqlite3
from typing import Any, Dict, List
from tabulate import tabulate
import json
import argparse

def print_top_transactions_for_category(cur, cat_desc):
    cur.execute('''
        SELECT *
        FROM transactions
        WHERE description = ?
        ORDER BY ABS(amount) DESC
        LIMIT 4;
    ''', (cat_desc,))
    rows = cur.fetchall()
    if rows:
        print(f"\nTop 4 transactions for category: {cat_desc}")
        print(tabulate(rows, headers=["Date", "Description", "Amount", "Account", "ID"], floatfmt=".2f", tablefmt="psql"))
    else:
        print(f"\nNo transactions found for category: {cat_desc}")

def get_category_summary(conn, category: Dict[str, Any], from_date=None, to_date=None) -> Dict[str, Any]:
    cur = conn.cursor()
    query = '''
        SELECT SUM(amount) AS total_amount
        FROM transactions
        WHERE category = ?
    '''
    params = [category['id']]
    if from_date:
        query += ' AND date >= ?'
        params.append(from_date)
    if to_date:
        query += ' AND date <= ?'
        params.append(to_date)
    cur.execute(query, tuple(params))
    result = cur.fetchone()
    if result and result[0] is not None:
        category['total_amount'] = result[0]
    else:
        category['total_amount'] = 0
    children = []
    for child in category.get('children', []):
        if child.get('hidden', False):
            continue
        child_summary = get_category_summary(conn, child, from_date, to_date)
        if child_summary:
            children.append(child_summary)
            category['total_amount'] += child_summary.get('total_amount', 0)
    category['children'] = children
    return category

def print_category_summary(category: Dict[str, Any], depth: int = 0):
    padding = ""
    if depth > 0:
        padding = " " * ((depth - 1) * 4) + "└── "
    if abs(category['total_amount']) == 0:
        return
    print(f"{padding}{category['description']}: ${abs(category['total_amount']):.2f}")
    for child in category.get('children', []):
        print_category_summary(child, depth + 1)

def print_overall_summary(args, category: Dict[str, Any]):
    from datetime import datetime
    from_date = args.from_date
    to_date = args.to_date
    total_amount = category['total_amount']
    print(f"Total: ${total_amount:.2f}")
    if not from_date or not to_date:
        return
    d1 = datetime.strptime(from_date, "%Y-%m-%d")
    d2 = datetime.strptime(to_date, "%Y-%m-%d")
    days = (d2 - d1).days + 1
    weeks = days / 7
    if weeks < 1:
        return
    per_week = total_amount / weeks
    print(f"Per week: ${per_week:.2f} (from {from_date} to {to_date}, {weeks:.2f} weeks)")
    months = days / 30.44
    if months < 1:
        return
    per_month = total_amount / months
    print(f"Per month: ${per_month:.2f} (from {from_date} to {to_date}, {months:.2f} months)")

def main():
    parser = argparse.ArgumentParser(description='Summarise transactions by category.')
    parser.add_argument('--from-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to-date', type=str, help='End date (YYYY-MM-DD)')
    args = parser.parse_args()

    conn = sqlite3.connect('finances.db')
    with open('categories.json', 'r') as f:
        categories = json.load(f)
    category_summaries = get_category_summary(conn, categories, args.from_date, args.to_date)
    print_category_summary(category_summaries)
    print_overall_summary(args, category_summaries)
    conn.close()

if __name__ == "__main__":
    main()
