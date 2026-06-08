import sqlite3
import os
import argparse
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'whereami_core.db')

def show_results(date_filter=None):
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"=== RESULTS {'FOR ' + date_filter if date_filter else 'ALL TIME'} ===")

        print("\n=== AXES DICTIONARY (Водоразделы) ===")
        # Note: axes_dictionary currently doesn't have created_at, showing all
        cursor.execute("SELECT id, pole_minus_1, pole_plus_1, status FROM axes_dictionary")
        for row in cursor.fetchall():
            print(f"- ID: {row['id']}\n  Pole (-1): {row['pole_minus_1']}\n  Pole (+1): {row['pole_plus_1']}\n  Status: {row['status']}\n")

        print("=== PARTIES REGISTRY (Партии / Субъекты) ===")
        cursor.execute("SELECT id, name, created_at FROM parties_registry")
        for row in cursor.fetchall():
            print(f"- {row['name']} (ID: {row['id']}, Created: {row['created_at']})")

        print("\n=== RECENT PARTY DOCUMENTS (Заявления) ===")
        
        query = '''
            SELECT p.name, d.document_text, d.created_at
            FROM party_documents d
            JOIN parties_registry p ON p.id = d.party_id
        '''
        params = []
        if date_filter:
            query += " WHERE date(d.created_at) = ?"
            params.append(date_filter)
            
        query += " ORDER BY d.created_at DESC LIMIT 20"
        
        cursor.execute(query, params)
        docs = cursor.fetchall()
        if not docs:
            print("No documents found for this criteria.")
        for row in docs:
            print(f"[{row['created_at']}] [{row['name']}]: {row['document_text'][:150]}...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View Antigravity 2.0 Database Results")
    parser.add_argument("--date", type=str, help="Filter documents by date (YYYY-MM-DD)", default=None)
    parser.add_argument("--today", action="store_true", help="Filter documents for today")
    args = parser.parse_args()
    
    date_filter = args.date
    if args.today:
        date_filter = datetime.now().strftime("%Y-%m-%d")
        
    show_results(date_filter)
