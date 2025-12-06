import streamlit as st
from services.utils import clean_text

# ------------------------------------------------------
# JOB CARD COMPONENT (FINAL REST-STABLE VERSION)
# ------------------------------------------------------
def job_card(job_data, key_prefix="", show_actions=False):
    """
    Renders a single job card with stable button keys.

    Args:
        job_data (dict): Job information returned from API.
        key_prefix (str): Unique ID used for button keys.
        show_actions (bool): Whether to show action buttons.
    """

    # -----------------------------------------
    # JOB TITLE
    # -----------------------------------------
    job_title = job_data.get("job_title", "Unknown Job Title")
    st.subheader(job_title)

    # -----------------------------------------
    # BASIC JOB INFORMATION
    # -----------------------------------------
    company = job_data.get("employer_name", "Unknown Company")
    country = job_data.get("job_country", "Not Specified")
    city = job_data.get("job_city", "")
    remote_flag = job_data.get("job_is_remote", False)
    description = clean_text(job_data.get("job_description", ""))[:350]

    st.markdown(f"**Company:** {company}")
    st.markdown(f"**Country:** {country}")

    if city:
        st.markdown(f"**City:** {city}")

    if remote_flag:
        st.markdown("**Remote:** Yes")
    else:
        st.markdown("**Remote:** No")

    st.write("---")

    # -----------------------------------------
    # JOB SUMMARY
    # -----------------------------------------
    st.markdown("### Job Summary")
    st.write(description + "...")

    st.write("---")

    # -----------------------------------------
    # APPLY LINK
    # -----------------------------------------
    apply_link = (
        job_data.get("job_apply_link")
        or job_data.get("job_apply_url")
        or job_data.get("apply_link")
    )

    if apply_link:
        st.markdown(
            f"<a href='{apply_link}' target='_blank'><strong>Apply Here</strong></a>",
            unsafe_allow_html=True,
        )
    else:
        st.warning("No application link provided for this job.")

    st.write("---")

    # -----------------------------------------
    # BUTTON ACTIONS (Save / Match / Cover)
    # -----------------------------------------
    if show_actions:
        col1, col2, col3 = st.columns(3)

        # SAVE JOB BUTTON (rest controlled)
        with col1:
            st.button(
                "Save Job",
                key=f"{key_prefix}_save_btn",
                help="Save this job to your dashboard"
            )

        # MATCH SCORE BUTTON
        with col2:
            st.button(
                "AI Match Score",
                key=f"{key_prefix}_match_btn",
                help="Check how well your resume matches this job"
            )

        # COVER LETTER BUTTON
        with col3:
            st.button(
                "Generate Cover Letter",
                key=f"{key_prefix}_cover_btn",
                help="Generate an ATS-friendly cover letter"
            )

    st.write("----")
