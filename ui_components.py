"""
UI Components for Turbo Air Equipment Viewer
Legacy components for backwards compatibility
Only includes the 4 functions imported by app.py
"""

import streamlit as st
from typing import Callable, Optional

def quantity_selector(current_quantity: int, unique_key: str) -> int:
    """
    Create a quantity selector with + and - buttons
    
    Args:
        current_quantity: Current quantity value
        unique_key: Unique key for the component
        
    Returns:
        Updated quantity value
    """
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("−", key=f"decrease_{unique_key}"):
            return max(1, current_quantity - 1)
    
    with col2:
        st.markdown(f"<h4 style='text-align: center; margin: 0;'>{current_quantity}</h4>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("+", key=f"increase_{unique_key}"):
            return current_quantity + 1
    
    return current_quantity

def empty_state(icon: str, title: str, description: str, 
                button_text: Optional[str] = None, 
                button_action: Optional[Callable] = None):
    """
    Display an empty state with icon, title, description and optional action
    
    Args:
        icon: Emoji or icon to display
        title: Title text
        description: Description text
        button_text: Optional button text
        button_action: Optional button callback
    """
    st.markdown(
        f"""
        <div style='text-align: center; padding: 3rem 1rem;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>{icon}</div>
            <h3 style='margin-bottom: 0.5rem;'>{title}</h3>
            <p style='color: #666; margin-bottom: 2rem;'>{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if button_text and button_action:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(button_text, use_container_width=True):
                button_action()
                st.rerun()

def format_price(price: float, currency_symbol: str = "$") -> str:
    """
    Format a price value with currency symbol and thousand separators
    
    Args:
        price: Price value to format
        currency_symbol: Currency symbol (default: $)
        
    Returns:
        Formatted price string
    """
    return f"{currency_symbol}{price:,.2f}"

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with suffix
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to add when truncated (default: ...)
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix