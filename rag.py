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
    def __init__(self, model_name: str = "AgentPublic/llama3-instruct-8b"):
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
            "device": "cpu",
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
        if os.path.exists("./chroma_langchain_db"):
            self.vector_store = Chroma(
                embedding_function=embedding,
                collection_name="rag_collection",
                persist_directory="./chroma_langchain_db"
            )
            
            # Vérifie les doublons pour chaque nouveau texte
            for text in texts:
                # Recherche de documents similaires
                results = self.vector_store.similarity_search_with_relevance_scores(
                    text.page_content,
                    k=1
                )
                
                # Si aucun document similaire n'est trouvé ou si la similarité est faible (< 0.95)
                if not results or results[0][1] < 0.95:
                    self.vector_store.add_documents([text])
        else:
            # Création initiale de la base
            self.vector_store = Chroma.from_documents(
                documents=texts,
                embedding=embedding,
                collection_name="rag_collection",
                persist_directory="./chroma_langchain_db"
            )
        
        # Persiste les changements
        self.vector_store.persist()
        
    def inspect_collection(self):
        """
        Affiche le contenu de la base de données vectorielle
        """
        if not self.vector_store:
            raise ValueError("La base de données vectorielle n'est pas initialisée")
            
        collection = self.vector_store.get()
        print(f"Nombre de documents : {len(collection['ids'])}")


    def extract_keywords_with_llm(self, text, num_keywords=5):
        """
        Extrait les mots-clés d'un texte en utilisant le LLM
        Args:
            text (str): Le texte à analyser
            num_keywords (int): Nombre de mots-clés souhaité
        Returns:
            list: Liste des mots-clés extraits
        """
        prompt = f"""En tant qu'expert en droit administratif et constitutionnel, identifie les {num_keywords} éléments juridiques les plus significatifs dans ce texte.

        Concentre-toi spécifiquement sur :
        - Les références au Code Général des Collectivités Territoriales (CGCT)
        - Les visas et considérants juridiques
        - Les références aux lois et décrets applicables
        - Les mentions obligatoires (date, signature, tampon)
        - Les autorités compétentes et leur pouvoir juridique
        - La hiérarchie des normes juridiques
        
        Réponds uniquement avec une liste de termes séparés par des virgules, sans phrases explicatives.
        
        Texte à analyser : {text}"""

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
        
        # Recherche des passages pertinents pour chaque mot-clé
        relevant_passages = []
        for keyword in keywords:
            results = self.vector_store.similarity_search_with_score(
                keyword,
                k=2
            )
            relevant_passages.extend([doc[0].page_content for doc in results])
        # Préparation du prompt pour l'analyse
        analysis_prompt = f"""En tant qu'expert en droit administratif et constitutionnel, analyse la validité juridique de ce document selon les critères suivants :

        Document à analyser : {self.load_documents(file_path)}

        Éléments juridiques identifiés : {', '.join(keywords)}
        
        Références juridiques similaires dans la base de données :
        {' '.join(relevant_passages[:10])}

        Sur la base de ces éléments :
        1. Évalue l'indice de confiance de ce document (0-100%, où 100% indique une confiance totale dans l'authenticité du document)
        2. Justifie ton évaluation en quelques points clés

        Réponds au format suivant :
        Indice de confiance: [pourcentage]
        Justification: [liste des points]
        """
        
        response = self.llm.invoke(analysis_prompt)
        return response.content

if __name__ == "__main__":
    # Créer une instance de RAGAgent
    rag = RAGAgent()
    
    # Charger et préparer les documents
    documents = rag.load_documents("legitext.pdf")
    

    # Analyser le risque de fraude
    fraud_analysis = rag.analyze_fraud_risk("arrete_beziers_test.pdf")
    print("\nAnalyse de l'indice de confiance:")
    print(fraud_analysis)
    
