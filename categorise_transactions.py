import json
import sqlite3
from typing import List, Dict, Any, Optional, Set
import sys
import datetime

def find_most_similar_category(transaction: sqlite3.Row, categories: List[Dict[str, str]], category_override: str, conn, threshold: float = 0.67) -> Optional[str]:
    if "TO M L S METCALFE" in transaction['description']:
        return None
    cur = conn.cursor()
    cur.execute("SELECT id, description, amount, category FROM transactions WHERE category IS NOT NULL AND category != ?", (category_override,))
    if transaction['part'] or transaction['code'] or transaction['ref']:
        part = transaction['part'] or ''
        code = transaction['code'] or ''
        ref = transaction['ref'] or ''
        for other_transaction in cur.fetchall():
            other_part = transaction['part'] or ''
            other_code = transaction['code'] or ''
            other_ref = transaction['ref'] or ''
            if other_part == part and len(part) > 0 and \
               other_code == code and len(code) > 0 and \
               other_ref == ref and len(ref) > 0:
                return get_category_from_id(other_transaction['category'], categories)
    import re
    def tokenize(text: str) -> Set[str]:
        text = re.sub(r'^AP#\d+\s*', '', text)
        text = re.sub(r'^POS W\/D ', '', text)
        text = re.sub(r'[^a-zA-Z0-9 ]', '', text.lower())
        return set(text.split())
    best_score = 0.0
    best_category = None
    for other_transaction in cur.fetchall():
        if not other_transaction['description']:
            continue
        set_a = tokenize(transaction['description'])
        set_b = tokenize(other_transaction['description'])
        if not set_a or not set_b:
            continue
        sim = len(set_a & set_b) / len(set_a | set_b)
        if sim > best_score and sim >= threshold:
            best_score = sim
            best_category = other_transaction['category']
    return get_category_from_id(best_category, categories) if best_category else None

def prompt_category(transaction: sqlite3.Row, categories: List[Dict[str, str]]) -> str:
    try:
        dt = datetime.datetime.strptime(transaction['date'], "%Y-%m-%d")
        date_str = dt.strftime("%A %d %B %Y")
    except Exception:
        date_str = transaction['date']
    category_description = None
    if transaction['category']:
        category_description = get_category_from_id(transaction['category'])['description']
    print(f"""
{transaction['description']} {transaction['part'] or ''} {transaction['code'] or ''} {transaction['ref'] or ''}
Amount: {transaction['amount']} Date: {date_str} Account: {transaction['account']} ID: {transaction['id']}
Category: {category_description or 'None'}
""")
    print("Please choose a category:")
    for i, cat in enumerate(categories):
        print(f"  {i+1}. {cat['description']}")
    choice = input(f"Category number or name: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(categories):
        return categories[int(choice)-1]
    else:
        raise ValueError(f"Invalid category choice: {choice}")

def get_categories(category: Dict[str, Any]) -> List[Dict[str, str]]:
    categories = []
    for child in category.get('children', []):
        categories.extend(get_categories(child))
    categories.append({'id': category['id'], 'description': category['description']})
    return categories

def get_all_categories(category_json_path: str = 'categories.json') -> List[Dict[str, Any]]:
    with open(category_json_path, 'r') as f:
        categories = json.load(f)
    return get_categories(categories)

def get_category_from_id(category_id: str, categories: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    if categories is None:
        categories = get_all_categories()
    for category in categories:
        if category['id'] == category_id:
            return category
    return None

def get_sorted_categories_by_usage(conn) -> List[Dict[str, Any]]:
    categories_flat = get_all_categories()
    cur = conn.cursor()
    cur.execute("SELECT category, COUNT(*) FROM transactions GROUP BY category")
    usage = {row[0]: row[1] for row in cur.fetchall()}
    categories_flat.sort(key=lambda c: (-usage.get(c['id'], 0), c['description']))
    return categories_flat

def main() -> None:
    # Check if a category override was provided as a command line argument
    category_override = sys.argv[1] if len(sys.argv) > 1 else ''
    conn = sqlite3.connect('finances.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    categories = get_sorted_categories_by_usage(conn)
    cur.execute("SELECT * FROM transactions WHERE category IS NULL OR category = ? ORDER BY date", (category_override,))
    all_transactions = cur.fetchall()
    for transaction in all_transactions:
        category = find_most_similar_category(transaction, categories, category_override, conn)
        if not category:
            category = prompt_category(transaction, categories)
        cur.execute("UPDATE transactions SET category = ? WHERE id = ?", (category['id'], transaction['id']))
        conn.commit()
        print(f"Categorized: '{transaction['description']}' as '{category['description']}'\n")
    print("All transactions categorized and saved to the database.")
    conn.close()

if __name__ == "__main__":
    main()
