import os
import yaml
from dotenv import load_dotenv
import psycopg2
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_groq import ChatGroq

load_dotenv()


class SemanticSQLEngine:
    def __init__(self):
        # Load semantic layer
        with open("semantic_layer.yaml", "r") as f:
            self.semantic = yaml.safe_load(f)

        # Load vector store
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.chroma = chromadb.PersistentClient(path="./.chroma")
        self.collection = self.chroma.get_collection("schema")

        # Load LLM (Groq + Llama 3.3)
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0
        )

        # DB connection
        self.conn = psycopg2.connect(
                    os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
        )

    def retrieve_relevant_tables(self, question, top_k=4):
        """Find the most relevant tables for the question."""
        query_emb = self.embedder.encode([question]).tolist()
        results = self.collection.query(query_embeddings=query_emb, n_results=top_k)
        return results["documents"][0]

    def find_relevant_semantic_terms(self, question):
        """Identify which semantic terms might apply, with smarter matching."""
        question_lower = question.lower()
        relevant = {"metrics": {}, "dimensions": {}, "business_rules": {}}

        # Synonyms map — extend this as needed
        synonyms = {
            "revenue": ["revenue", "sales", "earnings", "income"],
            "order_count": ["order count", "number of orders", "how many orders", "total orders"],
            "average_order_value": ["average order", "avg order", "aov", "mean order"],
            "top_customer": ["top customer", "biggest customer", "best customer", "largest customer"],
            "active_product": ["active product", "current product", "available product"],
            "recent_period": ["recent", "lately", "last 90 days", "latest"],
            "customer": ["customer", "client", "buyer"],
            "product": ["product", "item", "sku"],
            "region": ["region", "country", "location", "geography"],
            "time_period": ["month", "year", "quarter", "monthly", "yearly", "by time"],
        }

        for category in ["metrics", "dimensions", "business_rules"]:
            for key, definition in self.semantic.get(category, {}).items():
                # Use synonym list if defined, else fall back to the key itself
                triggers = synonyms.get(key, [key.replace("_", " ")])
                if any(trigger in question_lower for trigger in triggers):
                    relevant[category][key] = definition

        return relevant

    def generate_sql(self, question):
        """Generate SQL using retrieved schema + semantic layer context."""
        relevant_tables = self.retrieve_relevant_tables(question)
        relevant_semantic = self.find_relevant_semantic_terms(question)

        prompt = f"""You are an expert SQL analyst working with a PostgreSQL database (Northwind sample).

Generate a valid PostgreSQL query to answer the user's question.

=== RELEVANT TABLES ===
{chr(10).join(relevant_tables)}

=== SEMANTIC LAYER (business definitions — USE THESE EXACTLY) ===
{yaml.dump(relevant_semantic, default_flow_style=False) if any(relevant_semantic.values()) else "No specific semantic terms matched. Use direct column references."}

=== RULES ===
1. If a semantic metric is defined above, use its exact SQL expression — do NOT invent your own.
2. If a business rule is defined (e.g., 'top_customer', 'active_product'), apply its logic.
3. Only use SELECT statements. Never DROP, DELETE, UPDATE, INSERT, or ALTER.
4. Use table aliases for readability.
5. Return ONLY the SQL query. No markdown fences, no explanation, no preamble.

=== USER QUESTION ===
{question}

SQL:"""

        response = self.llm.invoke(prompt)
        sql = response.content.strip()

        # Strip markdown if the model adds it anyway
        if sql.startswith("```"):
            sql = sql.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if sql.lower().startswith("sql\n"):
            sql = sql[4:]

        return sql, relevant_semantic

    def validate_sql(self, sql):
        """Guardrails: block dangerous operations."""
        forbidden = ["drop", "delete", "update", "insert", "alter", "truncate", "create"]
        sql_lower = sql.lower()
        for word in forbidden:
            if f" {word} " in f" {sql_lower} " or sql_lower.startswith(word):
                return False, f"Blocked: query contains forbidden operation '{word}'"
        return True, "OK"

    def execute(self, sql):
        """Run the SQL and return results."""
        cur = self.conn.cursor()
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        cur.close()
        return columns, rows

    def ask(self, question):
        """End-to-end: question → SQL → results."""
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}")

        sql, semantic_used = self.generate_sql(question)
        print(f"\nGenerated SQL:\n{sql}")

        if semantic_used and any(semantic_used.values()):
            used_terms = []
            for cat, items in semantic_used.items():
                used_terms.extend(items.keys())
            print(f"\nSemantic layer terms used: {used_terms}")

        valid, msg = self.validate_sql(sql)
        if not valid:
            print(f"\nValidation failed: {msg}")
            return

        try:
            columns, rows = self.execute(sql)
            print(f"\nResults ({len(rows)} rows):")
            print(" | ".join(columns))
            print("-" * 60)
            for row in rows[:10]:
                print(" | ".join(str(v) for v in row))
            if len(rows) > 10:
                print(f"... and {len(rows) - 10} more rows")
        except Exception as e:
            print(f"\nExecution error: {e}")


if __name__ == "__main__":
    engine = SemanticSQLEngine()

    test_questions = [
        "What is our total revenue?",
        "Who are the top 5 customers by revenue?",
        "Show me revenue by country",
        "How many orders were placed in 1997?",
        "What is the average order value?",
    ]

    for q in test_questions:
        engine.ask(q)