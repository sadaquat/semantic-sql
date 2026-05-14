import os
from dotenv import load_dotenv

load_dotenv()

def get_secret(key, default=None):
    """
    Get a secret from Streamlit secrets if running on Streamlit Cloud,
    otherwise fall back to environment variables (.env file locally).
    """
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)