# ==========================================================
# components/analytics.py — Google Analytics (GA4) Injector
# ==========================================================

import os
import streamlit as st
import streamlit.components.v1 as components


def render_analytics():
    """
    Inject GA4 tracking script safely.
    Set GA_MEASUREMENT_ID in environment variables (e.g. G-XXXXXXXXXX).
    If not set, does nothing.
    """
    ga_id = os.getenv("GA_MEASUREMENT_ID", "").strip()
    if not ga_id:
        return

    # Prevent duplicate injection on the same page render
    if st.session_state.get("_ga_injected"):
        return

    st.session_state["_ga_injected"] = True

    components.html(
        f"""
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());
          gtag('config', '{ga_id}');
        </script>
        """,
        height=0,
    )
