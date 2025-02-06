from rag import init

def initialize_rag():
    """
    Initialise le système RAG au démarrage
    """
    print("Initialisation du système RAG...")
    init()
    print("Système RAG initialisé avec succès")

if __name__ == "__main__":
    initialize_rag() 