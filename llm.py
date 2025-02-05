from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = "https://albert.api.etalab.gouv.fr/v1"
API_KEY = os.getenv("API_KEY")


def get_llm(base_url: str = BASE_URL, api_key: str = API_KEY, model_name: str = "neuralmagic/Meta-Llama-3.1-70B-Instruct-FP8") -> ChatOpenAI:
    """
    Crée et retourne une instance de ChatOpenAI configurée.

    Args:
        base_url (str): URL de base de l'API ALbert
        api_key (str): Clé API pour l'authentification pour l'API Albert
        model_name (str): Nom du modèle à utiliser

    Returns:
        ChatOpenAI: Modèle depuis l'API Albert
    """
    return ChatOpenAI(base_url=base_url, api_key=api_key, model_name=model_name)
