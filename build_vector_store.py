import os
from dotenv import load_dotenv
import psycopg2
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()

# Connect to Postgres
conn = psycopg2.connect(
    os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL"))
cur = conn.cursor()

# Get all tables and their columns
cur.execute("""
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position
""")

# Group by table
tables = {}
for table_name, column_name, data_type in cur.fetchall():
    tables.setdefault(table_name, []).append(f"{column_name} ({data_type})")

# Build a description for each table
table_descriptions = []
for table_name, columns in tables.items():
    description = f"Table: {table_name}\nColumns: {', '.join(columns)}"

    # Business context — your domain knowledge edge
    business_context = {
        "customers": "Stores customer master data including company name, contact, country, and region.",
        "orders": "Stores order header records — one row per order with customer, dates, shipping info.",
        "order_details": "Line items for each order — product, quantity, unit price, discount.",
        "products": "Product catalog with name, supplier, category, price, stock, and discontinued flag.",
        "categories": "Product category reference data.",
        "suppliers": "Supplier master data.",
        "employees": "Employee records including who handled each order.",
        "shippers": "Shipping company reference data.",
        "region": "Geographic region reference.",
        "territories": "Sales territories linked to employees.",
        "us_states": "US state reference data."
    }

    if table_name in business_context:
        description += f"\nBusiness purpose: {business_context[table_name]}"

    table_descriptions.append({
        "id": table_name,
        "text": description
    })

cur.close()
conn.close()

# Build embeddings and store in Chroma
print("Loading embedding model (first run downloads ~80MB)...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

print("Creating vector store...")
client = chromadb.PersistentClient(path="./.chroma")

# Delete old collection if it exists (lets you re-run safely)
try:
    client.delete_collection("schema")
except Exception:
    pass

collection = client.create_collection("schema")

texts = [t["text"] for t in table_descriptions]
ids = [t["id"] for t in table_descriptions]
embeddings = embedder.encode(texts).tolist()

collection.add(
    ids=ids,
    embeddings=embeddings,
    documents=texts
)

print(f"\nIndexed {len(texts)} tables into vector store.")
print(f"Tables indexed: {ids}")