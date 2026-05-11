# \# SemanticSQL

# 

# Natural-language analytics for enterprise BI — translating business questions into SQL via a semantic layer.

# 

# \## Why semantic layer matters

# 

# Most text-to-SQL systems fail in real enterprises because LLMs guess at business definitions. "Revenue" isn't a column — it's a rule (e.g., net of discounts, excluding cancelled orders). This project encodes those rules in a semantic layer the LLM consults before generating SQL.

# 

# \## Stack

# \- PostgreSQL 16 (Dockerized)

# \- Northwind sample dataset

# \- Python 3.12, LangChain, ChromaDB

# \- Streamlit UI (coming Weekend 3)

# 

# \## Status

# \- \[x] Day 1: Postgres + semantic layer foundation

# \- \[ ] Day 2: LLM integration + RAG over schema

# \- \[ ] Day 3: Streamlit UI + auto-visualization

# 

# \## Run locally

# \\```

# docker-compose up -d

# python -m venv venv

# .\\venv\\Scripts\\Activate.ps1

# pip install -r requirements.txt

# python test\_connection.py

# \\```

