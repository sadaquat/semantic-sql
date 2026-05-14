import os
from dotenv import load_dotenv
import psycopg2
from langchain_groq import ChatGroq
from query_engine import SemanticSQLEngine

load_dotenv()


def naive_text_to_sql(question):
    """Baseline: LLM with schema only, no semantic layer."""
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0
    )
    prompt = f"""Generate a PostgreSQL query for the Northwind database.

Tables include: customers, orders, order_details, products.
Key columns in order_details: order_id, product_id, unit_price, quantity, discount.
Key columns in orders: order_id, customer_id, order_date, shipped_date.

Return ONLY the SQL query. No markdown, no explanation.

Question: {question}
SQL:"""
    response = llm.invoke(prompt)
    sql = response.content.strip()
    if sql.startswith("```"):
        sql = sql.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    if sql.lower().startswith("sql\n"):
        sql = sql[4:]
    return sql


def run_query(sql):
    conn = psycopg2.connect(
            os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    try:
        cur.execute(sql)
        result = cur.fetchone()
        return result[0] if result else None
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        cur.close()
        conn.close()


def compare(question):
    print("\n" + "=" * 75)
    print(f"QUESTION: {question}")
    print("=" * 75)

    # Naive
    print("\n--- NAIVE TEXT-TO-SQL (schema only, no business context) ---")
    naive_sql = naive_text_to_sql(question)
    print(f"SQL:\n{naive_sql}")
    naive_result = run_query(naive_sql)
    print(f"\nResult: {naive_result}")

    # Semantic
    print("\n--- SEMANTICSQL (with semantic layer) ---")
    engine = SemanticSQLEngine()
    sem_sql, semantic_used = engine.generate_sql(question)
    print(f"SQL:\n{sem_sql}")
    sem_result = run_query(sem_sql)
    print(f"\nResult: {sem_result}")

    # Difference
    if isinstance(naive_result, (int, float)) and isinstance(sem_result, (int, float)):
        diff = naive_result - sem_result
        pct = (diff / sem_result) * 100 if sem_result else 0
        print(f"\n--- DIFFERENCE ---")
        print(f"Naive overstates revenue by: ${diff:,.2f} ({pct:+.1f}%)")
        print(f"\nWhy? Naive SQL ignored the discount column and likely included")
        print(f"unshipped orders. SemanticSQL enforced the business definition")
        print(f"of revenue (net of discounts, shipped orders only).")


if __name__ == "__main__":
    compare("What is our total revenue?")