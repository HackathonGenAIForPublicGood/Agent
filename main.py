import streamlit as st
import os
import json
from PdfReader.pdfreader import extract_text_from_pdf
from categorisation import display_results_catégorisation
from forme import analyser_arrete, contexte, AnalyseArrete
from dotenv import load_dotenv

load_dotenv()

def main():
    # Configuration de la clé API depuis la variable d'environnement
    if 'API_KEY' not in st.session_state:
        st.session_state.API_KEY = os.getenv("API_KEY")
    
    if not st.session_state.API_KEY:
        st.error("La variable d'environnement API_KEY n'est pas définie")
        return
    
    st.title("Bienvenue sur l'outil d'aide à la vérification d'arrêté municipal")
    st.write("Veuillez téléverser votre document au format PDF")

    uploaded_file = st.file_uploader("Choisissez un fichier PDF", type="pdf")

    if uploaded_file is not None:
        st.write("Fichier bien envoyé!")
        if st.button("Analyser"):
            with st.spinner("Analyse en cours..."):
                # Extraction du texte
                texte = extract_text_from_pdf(uploaded_file)
                
                try:
                    # Analyse du document et conversion en objet Pydantic
                    resultat_json = analyser_arrete(contexte=contexte, contenu=texte)
                    resultat_dict = json.loads(resultat_json)
                    resultat = AnalyseArrete(**resultat_dict)
                    
                    # Affichage des résultats dans une mise en page structurée
                    st.subheader("📄 Résultats de l'analyse")
                    
                    # Informations générales
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"**Type de document :** {resultat.type_de_document}")
                        st.info(f"**Niveau de confiance :** {resultat.niveau_de_confiance}")
                    
                    with col2:
                        st.info(f"**Collectivité :** {resultat.collectivité}")
                        st.info(f"**Signataire :** {resultat.signataire}")
                    
                    with col3:
                        st.info("**Observations générales :**")
                        st.write(resultat.Observation)
                    
                    # Conformité aux exigences légales
                    st.subheader("📋 Conformité aux exigences légales")
                    
                    # Création d'un dictionnaire pour les icônes
                    icones = {
                        "conforme": "✅",
                        "non conforme": "❌",
                        "implicite": "ℹ️"
                    }
                    
                    # Création de colonnes pour les critères de conformité
                    criteres = list(resultat.conformite_aux_exigences_legales.dict().items())
                    col1, col2 = st.columns(2)
                    
                    # Distribution des critères dans les colonnes
                    for i, (critere, evaluation) in enumerate(criteres):
                        with (col1 if i % 2 == 0 else col2):
                            with st.expander(f"{critere.title()}"):
                                icone = icones.get(evaluation['etat'].lower(), "")
                                st.markdown(f"**État:** {icone} {evaluation['etat']}")
                                st.markdown(f"**Explication:** {evaluation['explication']}")
                
                except Exception as e:
                    st.error(f"Une erreur s'est produite lors de l'analyse : {str(e)}")
                    st.error(f"Résultat JSON : {resultat_json}")  # Pour le débogage

                # Appel de la fonction de catégorisation avec le texte extrait
                st.markdown("---")
                st.subheader("Catégorisation d'Actes Administratifs")
                display_results_catégorisation(texte)

if __name__ == "__main__":
    main()
