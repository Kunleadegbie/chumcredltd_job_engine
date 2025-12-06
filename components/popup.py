import streamlit as st

def show_popup(title: str, message: str):
    """
    Displays a floating popup notification using raw HTML/CSS/JS.
    Works in all Streamlit pages.
    """

    popup_html = f"""
    <style>
        /* POPUP BASE STYLES */
        .popup-container {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999999;
            animation: fadeInSlide 0.6s ease-out;
        }}

        .popup-box {{
            background: #ffffff;
            padding: 16px 22px;
            border-radius: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.25);
            border-left: 6px solid #4CAF50;
            min-width: 260px;
        }}

        .popup-title {{
            font-size: 17px;
            font-weight: bold;
            margin-bottom: 8px;
            color: #333;
        }}

        .popup-message {{
            font-size: 14px;
            color: #444;
        }}

        /* ANIMATION */
        @keyframes fadeInSlide {{
            0% {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            100% {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
    </style>

    <div class="popup-container">
        <div class="popup-box">
            <div class="popup-title">{title}</div>
            <div class="popup-message">{message}</div>
        </div>
    </div>

    <script>
        setTimeout(function() {{
            var popup = document.querySelector('.popup-container');
            if (popup) {{
                popup.style.transition = "all 0.5s ease";
                popup.style.opacity = "0";
                popup.style.transform = "translateY(-10px)";
                setTimeout(() => popup.remove(), 500);
            }}
        }}, 3500);
    </script>
    """

    st.markdown(popup_html, unsafe_allow_html=True)
