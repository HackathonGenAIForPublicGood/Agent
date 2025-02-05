import streamlit as st
from catégorie import categorize_llm

def display_results(results):
    st.subheader("📄 Résultats de la catégorisation")

    # Informations générales
    for idx, result in enumerate(results):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**Catégorie principale :** {result.main_category.name} ({result.main_category.value})")
            st.info(f"**Sous-catégorie :** {result.sub_category.name} ({result.sub_category.value})")
        
        with col2:
            st.info(f"**Niveau de confiance :** {result.confidence:.1%}")

        # Expander pour l'explication
        with st.expander("Voir l'explication"):
            st.markdown(f"**Explication :** {result.explanation}")

def display_results_catégorisation(text_input):
    st.title("📑 Catégorisation d'Actes Administratifs")
    st.markdown("""
    Cet outil analyse et catégorise automatiquement les actes administratifs selon la nomenclature ACTES.
    Entrez votre texte ci-dessous pour obtenir les catégories correspondantes.
    """)

    with st.expander("⚙️ Paramètres avancés"):
        show_details = st.checkbox("Afficher les détails de l'analyse", value=True)
        min_confidence = st.slider("Seuil de confiance minimum", 0.0, 1.0, 0.5, 0.1)

    # Analyse automatique si le texte est fourni
    with st.spinner("Analyse en cours..."):
        try:
            results = categorize_llm(text_input, DEBUG=False)
            
            # Filtrer les résultats selon le seuil de confiance
            results = [r for r in results if r.confidence >= min_confidence]
            
            # Afficher un résumé
            st.success(f"✅ Analyse terminée - {len(results)} catégories identifiées")
            
            # Afficher les résultats détaillés si demandé
            if show_details:
                display_results(results)
            else:
                # Afficher un résumé simplifié
                for result in results:
                    st.markdown(f"- **{result.sub_category.value}** ({result.confidence:.2%})")
            
        except Exception as e:
            st.error(f"Une erreur s'est produite : {str(e)}")

