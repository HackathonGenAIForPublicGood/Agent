from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import os
from langchain_community.embeddings import HuggingFaceEmbeddings

# Charger les variables d'environnement
load_dotenv()
from llm import get_llm

class RAGAgent:
    def __init__(self, model_name: str = "neuralmagic/Meta-Llama-3.1-70B-Instruct-FP8"):
        self.llm = get_llm(model_name=model_name)

        embedding = self.get_embedding_model()
        self.vector_store = Chroma(
                embedding_function=embedding,
                collection_name="rag_collection",
                persist_directory="./chroma_langchain_db"
            )

    def get_embedding_model(self):
        # Get DB
        model_name = "dangvantuan/sentence-camembert-base"
        model_kwargs = {
            "device": "mps",
            "tokenizer_kwargs": {'legacy': True}
        }
        encode_kwargs = {"normalize_embeddings": True}
        embedding_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        return embedding_model


    def load_documents(self, file_path):
        """
        Charge et découpe les documents en morceaux
        Supporte les fichiers PDF
        """
        if file_path.lower().endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, separators=["Article"])
        texts = text_splitter.split_documents(documents)
        return texts
        
    def create_vector_store(self, texts):
        """
        Crée une base de données vectorielle à partir des textes en évitant les doublons
        """
        embedding = self.get_embedding_model()
        
        # Vérifie si la base existe déjà
        self.vector_store = Chroma(
            embedding_function=embedding,
            collection_name="rag_collection",
            persist_directory="./chroma_langchain_db"
        )
        
        # Traitement par lots de 1000 documents
        batch_size = 1000
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Vérifie les doublons pour chaque texte du lot
            for text in batch:
                # Recherche de documents similaires
                similar_docs = self.vector_store.similarity_search_with_score(
                    text.page_content,
                    k=1
                )
                
                # Si aucun document similaire n'est trouvé ou si la similarité est faible
                if not similar_docs or similar_docs[0][1] > 0.1:
                    self.vector_store.add_documents([text])
            
            print(f"Traitement du lot {i//batch_size + 1} terminé ({i+len(batch)}/{len(texts)} documents)")
        
    def inspect_collection(self):
        """
        Affiche le contenu de la base de données vectorielle
        """
        if not self.vector_store:
            raise ValueError("La base de données vectorielle n'est pas initialisée")
            
        collection = self.vector_store.get()
        print(f"Nombre de documents : {len(collection['ids'])}")


    def extract_keywords_with_llm(self, text, num_keywords=3):
        """
        Extrait les mots-clés d'un texte en utilisant le LLM
        Args:
            text (str): Le texte à analyser
            num_keywords (int): Nombre de mots-clés souhaité
        Returns:
            list: Liste des mots-clés extraits
        """
        prompt = f"""En tant qu'expert en droit administratif et constitutionnel, identifie les {num_keywords} concepts juridiques principaux dans ce texte.

        Concentre-toi sur :
        - La nature générale de la mesure administrative
        - Le type d'acte juridique
        - Les personnes ou entités concernées
        - La portée territoriale de la mesure (ville, département, région, etc.)
        - L'objectif principal de la mesure (maire, préfet, etc.)

        Réponds uniquement avec une liste de {num_keywords} concepts généraux séparés par des virgules, sans phrases explicatives.
        Par exemple, pour le texte suivant :
        "ARTICLE 1 : Tout mineur agé de moins de 13 ans ne pourra, sans étre accompagné d'une personne majeure, \ncirculer de 23h a 6h sur la voie publique, dans les périmétres Quartiers Prioritaires de la ville figurants sur le \nplan annexé. \nARTICLE 2 : Cette interdiction s'applique toutes les nuits du lundi au dimanche inclus pour la période du 22 \navril au 30 septembre. \nARTICLE 3 : En cas d'urgence ou de danger immédiat pour lui ou pour autrui et sans préjudice des sanctions \npénales prévues a I'article R610-5 du code pénal, tout mineur de 13 ans en infraction avec les dispositions \nsusvisées pourra étre reconduit & son domicile ou au commissariat par les agents de la police nationale ou de \nla police municipale. \nEn application de I'article 40 du code de procédure pénale et de I'article 375 du code civil, les autorités \nsusmentionnées informeront sans délai le Procureur de la République de tous les faits susceptibles de donner \nlieu a 'engagement de poursuites ou a la saisine du Juge des Enfants. \nARTICLE 4 : En cas de manquements aux obligations édictées par le présent arrété, les parents des enfants \nconcernés pourront faire I'objet de poursuites pénales sur le fondement de 'article R610-5 et de 'article L227- \n17 du Code Pénal. \nARTICLE 5 : Madame la Directrice Générale des Services de la Mairie de Béziers, Monsieur le Commissaire \nCentral de Police et Monsieur le Directeur de la Direction de la Police Municipale de la Mairie sont chargés, \nchacun en ce qui le concerne, de I'exécution du présent arrété. \nFait en I'Hétel de Ville de Béziers, 22 AVR 2024"
        Le retour contiendrait au minimum : "couvre-feu pour les mineurs dans une ville de france métropolitaine"

        Texte à analyser :  {text}"""

        response = self.llm.invoke(prompt)
        keywords = [kw.strip() for kw in response.content.split(',')]
        return keywords

    def analyze_document_keywords(self, file_path):
        """
        Analyse un document et extrait ses mots-clés en utilisant le LLM
        Args:
            file_path (str): Chemin vers le document
        Returns:
            list: Liste des mots-clés du document
        """
        texts = self.load_documents(file_path)
        # Combine les premiers chunks pour obtenir un aperçu représentatif
        sample_text = " ".join([doc.page_content for doc in texts])  
        return self.extract_keywords_with_llm(sample_text)

    def analyze_fraud_risk(self, file_path):
        """
        Analyse le risque de fraude d'un document en se basant sur les mots-clés
        et le contenu similaire dans la base de connaissances
        Args:
            file_path (str): Chemin vers le document à analyser
        Returns:
            dict: Résultats de l'analyse avec indice de confiance et justification
        """
        # Extraction des mots-clés du document
        keywords = self.analyze_document_keywords(file_path)
        print("keywords : ", keywords)
        # Recherche des passages pertinents pour chaque mot-clé
        relevant_passages = []
        for keyword in keywords:
            results = self.vector_store.similarity_search_with_score(
                keyword,
                k=2
            )
            relevant_passages.extend([doc[0].page_content for doc in results])

        #print("relevant_passages : ", relevant_passages)
        # Préparation du prompt pour l'analyse
        analysis_prompt = f"""En tant qu'expert en droit administratif et constitutionnel, analyse la validité juridique de ce document selon les critères suivants :

        Document à analyser : {self.load_documents(file_path)}

        Éléments juridiques identifiés : {', '.join(keywords)}
        
        Références juridiques similaires dans la base de données :
        {' '.join(relevant_passages[:30])}

        Sur la base de ces éléments :
        1. Évalue l'indice de confiance de ce document (0-100%, où 100% indique une confiance totale dans l'authenticité du document)
        2. Justifie ton évaluation par une analyse approfondie des éléments juridiques identifiés et des références similaires dans la base de données.

        Réponds au format suivant :
        Indice de confiance: [pourcentage]
        Justification: [liste des points]
        """
        
        response = self.llm.invoke(analysis_prompt)
        return response.content

    def analyze_fraud_risk_from_text(self, text):
        """
        Analyse le risque de fraude d'un texte en se basant sur les mots-clés
        et le contenu similaire dans la base de connaissances
        Args:
            text (str): Texte à analyser
        Returns:
            dict: Résultats de l'analyse avec indice de confiance et justification
        """
        # Extraction des mots-clés du texte
        keywords = self.extract_keywords_with_llm(text)
        print("keywords : ", keywords)
        
        # Recherche des passages pertinents pour chaque mot-clé
        relevant_passages = []
        for keyword in keywords:
            results = self.vector_store.similarity_search_with_score(
                keyword,
                k=6
            )
            relevant_passages.extend([doc[0].page_content for doc in results])

        # Préparation du prompt pour l'analyse
        analysis_prompt = f"""En tant qu'expert en droit administratif et constitutionnel, ta mission est d'analyser la validité juridique d'un document administratif en te basant UNIQUEMENT sur les références juridiques de notre base de données.

        Document à analyser : {text}

        Références juridiques officielles disponibles :
        {' '.join(relevant_passages[:20])}

        Concepts juridiques identifiés : {', '.join(keywords)}

        RÈGLES D'ANALYSE :
        - Ignorer toute référence juridique mentionnée dans le document à analyser
        - Se baser UNIQUEMENT sur les références juridiques fournies par la base de données
        - Ne pas tenir compte des aspects formels ou de la structure du document
        - Analyser uniquement la légalité et la cohérence du contenu

        Procède à l'analyse selon les étapes suivantes :

        1. ANALYSE DU CONTENU
        - Compare les mesures prises avec celles présentes dans les références
        - Vérifie si l'intensité des mesures est cohérente avec les précédents
        - Examine si les pouvoirs exercés correspondent à ceux documentés dans les références

        2. VÉRIFICATION DE LA COMPÉTENCE
        - Compare avec les domaines d'intervention autorisés selon les références
        - Vérifie si les mesures correspondent aux prérogatives documentées

        3. ANALYSE DE LA PROPORTIONNALITÉ
        - Évalue si l'intensité des mesures est comparable aux cas similaires
        - Compare avec les solutions retenues dans des situations analogues

        4. definie ton indice de confiance
        - en fonction de l'analyse du contenu, des éléments cohérents et divergents des références et des citations pertinentes
        - en fonction de la pertinence des références par rapport au document

        Format de réponse attendu à RESPECTER :
        Indice de confiance : [pourcentage]

        **Analyse du contenu** :
        - [observations basées uniquement sur la comparaison avec les références]

        **Concepts juridiques identifiés** :
        - [liste des concepts juridiques identifiés]

        **Éléments cohérents avec les références** :
        - [liste des points conformes aux précédents lié au contenu du document]

        **Éléments divergents des références** :
        - [liste des incohérences par rapport aux précédents lié au contenu du document]

        **Citations pertinentes des références** :
        - [extraits précis de la base de données justifiant l'analyse]

        Conclusion finale : [synthèse de l'analyse]
        """
        
        response = self.llm.invoke(analysis_prompt)
        return response.content


def init():
    rag = RAGAgent()
    document = rag.load_documents("docs/code_civil.pdf")
    document1 = rag.load_documents("docs/code_penal.pdf")
    document2 = rag.load_documents("docs/code_territorial.pdf")
    document3 = rag.load_documents("docs/code_de_securite_intérieure.pdf")
    rag.create_vector_store(document)
    rag.create_vector_store(document1)
    rag.create_vector_store(document2)
    rag.create_vector_store(document3)


def get_result(text):
    rag = RAGAgent()
    return rag.analyze_fraud_risk_from_text(text)

if __name__ == "__main__":
    init()
    
    # Exemple de texte à analyser
    texte_exemple = """ARTICLE 1 : Tout mineur âgé de moins de 13 ans ne pourra, sans être accompagné d'une personne majeure,
    circuler de 23h à 6h sur la voie publique, dans les périmètres Quartiers Prioritaires de la ville."""
    
    result = get_result(texte_exemple)
    print(result)
