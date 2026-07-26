import streamlit as st
import logging
from datetime import datetime, timezone
import traceback

def safe_render(feature_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error in {feature_name} at {datetime.now(timezone.utc)}: {traceback.format_exc()}")
                st.error(f"⚠ Couldn't load {feature_name}.")
                with st.expander("Show Details"):
                    st.caption(f"Error: {str(e)}")
                if st.button(f"Retry {feature_name}", key=f"retry_{feature_name}"):
                    st.rerun()
        return wrapper
    return decorator