# \## Why this matters: side-by-side comparison

# 

# Naive text-to-SQL guesses business logic. SemanticSQL uses encoded definitions.

# 

# For "What is our total revenue?":

# \- \*\*Naive LLM\*\*: SUMs unit\_price × quantity — ignores discounts

# \- \*\*SemanticSQL\*\*: SUMs unit\_price × quantity × (1 - discount) — uses the business definition

# 

### Naive LLM said total revenue is $1,354,458

### Your SemanticSQL said $1,239,856

### The naive answer is wrong by $114,602 — a 9.2% overstatement



# Result: \~10% difference. In a $50M revenue company, that's a $5M reporting error.

# 

# This is the gap between a demo and an enterprise-grade tool.



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

