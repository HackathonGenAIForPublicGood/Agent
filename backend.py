from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from forme import analyser_arrete, contexte
from rag import get_result, init
from catégorie import categorize_llm
import json
from PdfReader.pdfreader import extract_text_from_upload
import io
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API Analyse d'Actes Administratifs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # URL du frontend Vue
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#init()

# Ajouter ces classes pour la validation des données
class TexteRequest(BaseModel):
    texte: str
    contexte: dict = {
        "type_document": "arrete",
        "emetteur": "mairie",
        "date": "2023",
        "lieu": "Paris"
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint pour uploader et lire un fichier (PDF, DOCX, etc.)
    Retourne le texte extrait
    """
    try:
        contents = await file.read()
        file_obj = io.BytesIO(contents)
        file_obj.type = file.content_type
        
        texte = extract_text_from_upload(file_obj)
        return {"texte": texte}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la lecture du fichier: {str(e)}"
        )

@app.post("/categoriser")
async def categoriser_texte(request: TexteRequest):
    """
    Endpoint pour catégoriser un texte
    """
    try:
        print(f"Données reçues dans /categoriser: {request}")  # Log de debug
        resultats = categorize_llm(request.texte, DEBUG=False)
        return [
            {
                "sub_category": {
                    "value": res.sub_category.value,
                    "name": res.sub_category.name
                },
                "main_category": {
                    "value": res.main_category.value,
                    "name": res.main_category.name
                },
                "confidence": res.confidence,
                "explanation": res.explanation
            }
            for res in resultats
        ]
    except Exception as e:
        print(f"Erreur dans /categoriser: {str(e)}")  # Log de debug
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyser")
async def analyser_texte(request: TexteRequest):
    """
    Endpoint pour analyser la forme d'un texte
    """
    try:
        print(f"Données reçues dans /analyser: {request}")  # Log de debug
        # On crée un contexte par défaut si nécessaire
        resultat = analyser_arrete(contenu=request.texte)
        if isinstance(resultat, str):
            return json.loads(resultat)
        return resultat
    except Exception as e:
        print(f"Erreur dans /analyser: {str(e)}")  # Log de debug
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyser-validite")
async def analyser_validite(request: TexteRequest):
    """
    Endpoint pour analyser la validité juridique d'un texte
    """
    try:
        print(f"Données reçues dans /analyser-validite: {request}")  # Log de debug
        resultat = get_result(request.texte)
        return {"analyse": resultat}
    except Exception as e:
        print(f"Erreur dans /analyser-validite: {str(e)}")  # Log de debug
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """
    Page d'accueil de l'API
    """
    return {
        "message": "API d'analyse d'actes administratifs",
        "endpoints": [
            "/categoriser - POST - Catégorisation d'un texte administratif",
            "/analyser - POST - Analyse de la forme d'un texte administratif",
            "/analyser-validite - POST - Analyse de la validité juridique d'un texte",
            "/upload - POST - Upload et lecture d'un fichier (PDF, DOCX, etc.)"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 