import streamlit as st

st.set_page_config(page_title="Chumcred Job Engine", layout="wide")

# -----------------------------------------------------------
# HERO SECTION
# -----------------------------------------------------------
st.markdown("""
<div style='text-align:center; padding: 30px;'>
    <h1 style='color:#1a73e8;'>🚀 Chumcred Job Engine</h1>
    <h3>Your AI-powered global job search companion</h3>
    <p style='font-size:18px;'>Discover jobs, analyze roles, generate cover letters, and get match scores — all using advanced AI.</p>
</div>
""", unsafe_allow_html=True)

st.write("---")

# -----------------------------------------------------------
# FEATURES
# -----------------------------------------------------------
st.header("✨ Why Choose Chumcred Job Engine?")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🌍 Global Job Search")
    st.write("Search remote, hybrid, or on-site jobs worldwide.")

with col2:
    st.subheader("🤖 AI Job Match Score")
    st.write("See how well your resume matches job descriptions.")

with col3:
    st.subheader("✉️ Auto Cover Letter")
    st.write("Generate professional cover letters instantly.")

col4, col5, col6 = st.columns(3)

with col4:
    st.subheader("🧠 Skills Extraction")
    st.write("AI extracts key skills from job descriptions.")

with col5:
    st.subheader("🌎 Country Eligibility")
    st.write("AI smart-checks global eligibility requirements.")

with col6:
    st.subheader("💾 Save Jobs")
    st.write("Save roles and review them anytime.")

st.write("---")

# -----------------------------------------------------------
# ABOUT THIS APP  (Merged from old About page)
# -----------------------------------------------------------
st.header("📘 About This App")
st.write("### Your AI-Powered Job Search, Application, and Career Growth Companion")

st.markdown("""
Chumcred Job Engine is an intelligent, AI-driven platform designed to simplify and accelerate your job search.
Whether you're a fresh graduate, a mid-career professional, or an executive job seeker, the app helps you
discover real opportunities, understand job requirements, and improve your chances of getting hired.

---

## 🌟 What This App Helps You Do

### 🔎 **1. Smart Job Search (AI-Powered)**
- Search jobs globally by role or skill  
- Filter and save jobs  
- Revisit saved jobs anytime  

---

### 🤖 **2. AI Tools for Job Seekers**
- AI Eligibility Checker  
- AI Match Score  
- AI Cover Letter Writer  
- AI Interview Q&A  

---

### 💾 **3. Saved Jobs Dashboard**
Revisit saved roles anytime.

---

### 📊 **4. Personal Analytics**
The app tracks:
- Jobs searched  
- Jobs saved  
- AI tools used  
- Job categories explored  

---

### 🧑‍💼 **5. Admin Functions**
Admins can:
- Add users  
- Monitor job search behavior  
- Understand job trends  

---

## 🎯 Who Should Use This App?
- Job seekers  
- Professionals switching careers  
- Students  
- Recruiters or mentors  

---

## 🔐 Privacy & Security
Your data is safe. Only essential job information is stored.

---

## 🚀 Why We Built This
To give job seekers **clarity, direction, and confidence**.

---
""")

st.write("---")

# -----------------------------------------------------------
# SUBSCRIPTION INFO
# -----------------------------------------------------------
st.header("💳 Simple & Affordable Subscription Plans")

st.markdown("""
| Plan | Price | Credits |
|------|--------|----------|
| **1 Month** | ₦3,000 | 100 Credits |
| **3 Months** | ₦7,500 | 300 Credits |
| **1 Year** | ₦25,000 | 1,500 Credits |

**Payment Account**  
**Account Name: Chumcred Limited**                                                                                                                
**Bank: Sterling Bank Plc**  
**Account No: 0087611334**
""")

st.write("---")

# -----------------------------------------------------------
# CALL TO ACTION
# -----------------------------------------------------------
st.header("🚀 Get Started")

colA, colB = st.columns(2)

with colA:
    if st.button("🔐 Login Now"):
        st.switch_page("app.py")

with colB:
    if st.button("📝 Register Account"):
        st.switch_page("pages/1_registration.py")

st.write("---")

# -----------------------------------------------------------
# FAQ SECTION
# -----------------------------------------------------------
st.header("❓ Frequently Asked Questions")

with st.expander("How does AI Job Match Score work?"):
    st.write("The AI compares your resume with job descriptions and returns a similarity evaluation.")

with st.expander("How do I activate my account?"):
    st.write("Make payment, submit your reference on the Subscription page, and Admin will manually activate you.")

with st.expander("How are credits deducted?"):
    st.write("Each AI action reduces credits. Job Match (5), Cover Letter (5), Skills (4), Eligibility (4).")

with st.expander("Can I save jobs?"):
    st.write("Yes — saved jobs are available in your account dashboard.")

st.write("---")

# -----------------------------------------------------------
# FOOTER
# -----------------------------------------------------------
st.markdown("""
<div style='text-align:center; padding:20px; color:gray;'>
    © 2025 Chumcred Limited. All rights reserved.  
    For support call <b>08025420200</b>
</div>
""", unsafe_allow_html=True)
