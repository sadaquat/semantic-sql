import os
import yaml
import pandas as pd
import streamlit as st
import plotly.express as px
from config import get_secret

from query_engine import SemanticSQLEngine

#load_dotenv()

# ---------- Page setup ----------
st.set_page_config(
    page_title="SemanticSQL — Enterprise AI Analytics",
    page_icon="🧠",
    layout="wide"
)

# ---------- Cache the engine so it's only initialized once ----------
@st.cache_resource
def get_engine():
    return SemanticSQLEngine()


# ---------- Sidebar ----------
with st.sidebar:
    st.title("🧠 SemanticSQL")
    st.markdown(
        "Natural-language analytics with a **semantic layer** — "
        "the missing piece in most GenAI BI tools."
    )

    st.divider()
    st.subheader("Why this is different")
    st.markdown(
        "- LLMs don't understand business definitions out of the box\n"
        "- 'Revenue' isn't a column — it's a rule (net of discounts, shipped only)\n"
        "- This system encodes those rules in a YAML semantic layer the LLM consults"
    )

    st.divider()
    st.subheader("Try these")
    sample_questions = [
        "What is our total revenue?",
        "Who are the top 5 customers by revenue?",
        "Show me revenue by country",
        "How many orders were placed in 1997?",
        "Show monthly revenue trend",
    ]
    for q in sample_questions:
        if st.button(q, key=f"sample_{q}"):
            st.session_state["question"] = q

    st.divider()
    st.caption("Built by Sadaquat Khan · [GitHub](https://github.com/sadaquat/semantic-sql) · [LinkedIn](https://www.linkedin.com/in/sadaquat-khan)")


# ---------- Header ----------
st.title("Ask your data in plain English")
st.markdown(
    "Type a business question. The system retrieves relevant tables, "
    "consults the semantic layer for business definitions, generates SQL, "
    "validates it, and runs it on the Northwind sample database."
)

# ---------- Input ----------
question = st.text_input(
    "Your question:",
    value=st.session_state.get("question", ""),
    placeholder="e.g., Who are our top 5 customers by revenue?"
)

run_button = st.button("Ask", type="primary")


# ---------- Run query ----------
if run_button and question:
    engine = get_engine()

    with st.spinner("Generating SQL and querying database..."):
        try:
            sql, semantic_used = engine.generate_sql(question)
            valid, msg = engine.validate_sql(sql)

            if not valid:
                st.error(f"Query blocked by guardrails: {msg}")
                st.code(sql, language="sql")
            else:
                columns, rows = engine.execute(sql)
                df = pd.DataFrame(rows, columns=columns)

                # Two columns: SQL on left, results on right
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.subheader("Generated SQL")
                    st.code(sql, language="sql")

                    # Show which semantic terms were used
                    used_terms = []
                    for cat, items in semantic_used.items():
                        used_terms.extend(items.keys())
                    if used_terms:
                        st.success(f"✓ Semantic layer terms used: {', '.join(used_terms)}")
                    else:
                        st.info("No specific semantic terms matched — direct schema query.")

                with col2:
                    st.subheader(f"Results ({len(df)} rows)")
                    st.dataframe(df, use_container_width=True)

                # ---------- Auto-visualize ----------
                st.divider()
                st.subheader("Visualization")

                if len(df) == 1 and len(df.columns) == 1:
                    # Single number → KPI card
                    value = df.iloc[0, 0]
                    if isinstance(value, (int, float)):
                        st.metric(label=df.columns[0], value=f"{value:,.2f}")
                    else:
                        st.write(value)

                elif len(df.columns) == 2 and len(df) > 1:
                    # Two columns → likely a category + value
                    x_col, y_col = df.columns[0], df.columns[1]
                    # Heuristic: if x looks like a date, use line chart
                    if "date" in x_col.lower() or "month" in x_col.lower() or "year" in x_col.lower():
                        fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
                    else:
                        # Sort and limit for readability
                        df_sorted = df.sort_values(by=y_col, ascending=False).head(15)
                        fig = px.bar(df_sorted, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.info("No chart auto-generated for this result shape.")

        except Exception as e:
            st.error(f"Error: {e}")


# ---------- Footer / comparison demo ----------
st.divider()
with st.expander("🔬 See the killer demo: Naive vs SemanticSQL comparison"):
    st.markdown(
        "For the question **'What is our total revenue?'**, here's what naive "
        "text-to-SQL gets versus this system:"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Naive text-to-SQL**")
        st.code("SELECT SUM(unit_price * quantity)\nFROM order_details;", language="sql")
        st.metric("Result", "$1,354,458", delta="+9.2% overstated", delta_color="inverse")
        st.caption("Ignores discounts and unshipped orders.")

    with col2:
        st.markdown("**SemanticSQL (with semantic layer)**")
        st.code(
            "SELECT SUM(od.unit_price * od.quantity * (1 - od.discount))\n"
            "FROM order_details od\n"
            "JOIN orders o ON od.order_id = o.order_id\n"
            "WHERE o.shipped_date IS NOT NULL;",
            language="sql"
        )
        st.metric("Result", "$1,239,856", delta="Accurate", delta_color="normal")
        st.caption("Uses business definition of revenue from semantic layer.")

    st.markdown(
        "In a $50M company, that 9.2% gap is a **$4.6M reporting error**. "
        "This is why every enterprise GenAI BI tool needs a semantic layer."
    )