import streamlit as st
from PdfReader.pdfreader import extract_text_from_pdf, extract_text_from_docx, extract_text_from_upload

def main():
    st.title("Bienvenue sur l'outil d'aide à la vérification d'arrêté' municipal")
    st.write("Veuillez téléverser votre document au format PDF")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        st.write("Fichier bien envoyé!")
        if st.button("Validate"):
            st.write("Validation in progress...")
            # Add your validation logic here
            st.write("Validation complete!")

if __name__ == "__main__":
    main()