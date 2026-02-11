import streamlit as st

def inject_google_analytics(ga_tag_id: str):
    """
    Injeta o código do Google Analytics no frontend do Streamlit.
    """
    ga_code = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={ga_tag_id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{ga_tag_id}');
    </script>
    """
    # Injetar no head (via markdown inseguro, mas é o método comum para GA no Streamlit)
    st.markdown(ga_code, unsafe_allow_html=True)
