import streamlit as st
import textwrap

st.markdown(
    textwrap.dedent("""
<div class="ti-hero">
  <div class="ti-badges">
    <span class="ti-badge">⚡ CV Intelligence</span>
    <span class="ti-badge">🎯 SmartMatch</span>
    <span class="ti-badge">🧠 InterviewIQ</span>
  </div>

  <h1 class="ti-title">Turn Potential Into Opportunity — Faster</h1>

  <div class="ti-subtitle ti-muted">
    TalentIQ helps people move from <b>“I’m searching”</b> to <b>“I’m job-ready and getting interviews”</b>
    with clear scoring, guided improvements, and role-fit matching.
  </div>

  <div class="ti-divider"></div>

  <div class="ti-kpi">
    <div class="ti-card">
      <b>✅ Know your employability score</b><br/>
      <span class="ti-muted ti-small">Upload a CV → see strengths, gaps, ATS readiness, and what to fix.</span>
    </div>

    <div class="ti-card">
      <b>🎯 Get matched to relevant roles</b><br/>
      <span class="ti-muted ti-small">SmartMatch ranks fit and shows why you match (and how to improve).</span>
    </div>

    <div class="ti-card">
      <b>🧠 Practice interviews confidently</b><br/>
      <span class="ti-muted ti-small">InterviewIQ generates questions and gives structured feedback.</span>
    </div>
  </div>
</div>
"""),
    unsafe_allow_html=True
)