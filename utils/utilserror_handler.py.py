import streamlit as st
import logging
from datetime import datetime, timezone
import traceback

def safe_render(feature_name):
    """
    A decorator to wrap UI blocks, catch exceptions, log them, 
    and display a clean error message to the user instead of crashing.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error internally
                logging.error(f"Error in {feature_name} at {datetime.now(timezone.utc)}: {traceback.format_exc()}")
                
                # Display clean UI to user
                st.error(f"⚠ Couldn't load {feature_name}.")
                with st.expander("Show Details"):
                    st.caption(f"Error: {str(e)}")
                if st.button(f"Retry {feature_name}"):
                    st.rerun()
        return wrapper
    return decorator