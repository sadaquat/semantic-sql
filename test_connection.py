import psycopg2
import yaml

# Test database connection
conn = psycopg2.connect(
    host="localhost",
    database="northwind",
    user="postgres",
    password="postgres"
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM customers;")
print(f"Customer count: {cur.fetchone()[0]}")

# Test semantic layer load
with open("semantic_layer.yaml", "r") as f:
    semantic = yaml.safe_load(f)

print(f"\nLoaded {len(semantic['metrics'])} metrics, {len(semantic['dimensions'])} dimensions")
print(f"Available metrics: {list(semantic['metrics'].keys())}")

# Test a metric by running its SQL
revenue_def = semantic['metrics']['revenue']
test_sql = f"SELECT {revenue_def['sql']} FROM {', '.join(revenue_def['source_tables'])} WHERE {revenue_def['join_logic']} AND {revenue_def['filters']}"
cur.execute(test_sql)
print(f"\nTotal revenue (using semantic layer definition): ${cur.fetchone()[0]:,.2f}")

cur.close()
conn.close()