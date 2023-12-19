"""
Helper functions with StreamLit UI utils
"""

import streamlit as st


def reset_session_state(page_name: str) -> None:
    """
    Reset session state variables
    """
    st.session_state.setdefault("last_page", "None")

    st.session_state["current_page"] = page_name
    if st.session_state["current_page"] != st.session_state["last_page"]:
        for key in st.session_state.keys():
            if key not in [
                "authenticated",
                "access_token",
                "df",
                "df_name",
                "prompter_text",
                "button_clicked",
                "df_personalize_jobs",
                "job_name",
                "item_data",
                "prompt",
            ]:
                del st.session_state[key]

    st.session_state["last_page"] = page_name


def button_with_url(
    url: str,
    text: str,
) -> str:
    """
    Create button with URL link
    """
    return f"""
    <a href={url}><button style="
    fontWeight: 400;
    fontSize: 0.85rem;
    padding: 0.25rem 0.75rem;
    borderRadius: 0.25rem;
    margin: 0px;
    lineHeight: 1;
    width: auto;
    userSelect: none;
    backgroundColor: #FFFFFF;
    border: 1px solid rgba(49, 51, 63, 0.2);">{text}</button></a>
    """


def display_cover_with_title(
    title: str,
    description: str,
    image_url: str,
    width: int = 100,
    text_color: str = "#FFFFFF",
) -> None:
    """
    Display cover with title

    Parameters
    ----------
    title : str
        Title to display over the image (upper part)
    description : str
        Description to display over the image (lower part)
    image_url : str
        URL to the cover image
    """

    html_code = f"""
    <div class="container" align="center">
    <img src={image_url} alt="Cover" style="width:{width}%;">
    <div style="position: absolute; top: 8px; left: 32px; font-size: 3rem; font-weight: bold; color: {text_color}" align="center">{title}</div>
    <div style="position: absolute; bottom: 8px; left: 32px; font-size: 1.5rem; color: {text_color}" align="center">{description}</div>
    </div>
    """  # noqa: E501

    st.markdown(
        html_code,
        unsafe_allow_html=True,
    )
