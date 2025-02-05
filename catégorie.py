from typing import List, Dict
from langchain.prompts import ChatPromptTemplate
import os

from entities.catégorie import SubCategory, MainCategory, CategoryResult
from llm import get_llm



class ActesCategorizer:
    def __init__(self, model_name: str = "AgentPublic/llama3-instruct-8b"):
        self.llm = get_llm(model_name=model_name)
        self.categories = self._generate_category_hierarchy()
        self.structured_llm = self.llm.with_structured_output(CategoryResult)

    def _generate_category_hierarchy(self) -> Dict[MainCategory, List[SubCategory]]:
        hierarchy = {}
        for main_cat in MainCategory:
            hierarchy[main_cat] = [sub_cat for sub_cat in SubCategory if sub_cat.value.startswith(main_cat.value)]
        return hierarchy

    def categorize(self, text: str) -> CategoryResult:
        categories_str = self._format_categories()
        prompt = ChatPromptTemplate.from_template(
            """
            Vous êtes un expert en catégorisation des actes administratifs selon la NOMENCLATURE ACTES SIMPLIFIEE.
            Analysez le texte fourni et identifiez toutes les sous-catégories pertinentes en vous basant sur leurs descriptions.
            
            Pour chaque sous-catégorie identifiée, vous devez fournir :
            1. La sous-catégorie concernée
            2. Sa catégorie principale (grand famille)
            3. Un score de confiance entre 0 et 1
            4. Une explication détaillée justifiant la pertinence

            {categories}

            Texte à catégoriser : {text}

            Retournez une liste structurée de toutes les sous-catégories pertinentes, 
            chacune avec sa catégorie principale, son score de confiance et son explication.
            """
        )

        messages = prompt.format_messages(
            categories=categories_str,
            text=text
        )

        return self.structured_llm.invoke(messages)

    def _format_categories(self) -> str:
        categories_str = ""
        for main_cat in MainCategory:
            categories_str += f"{main_cat.value}. {main_cat.name}\n"
            for sub_cat in self.categories[main_cat]:
                categories_str += f"  {sub_cat.value} {sub_cat.name}: {self._get_subcategory_description(sub_cat)}\n"
        return categories_str

    def _get_subcategory_description(self, sub_cat: SubCategory) -> str:
        descriptions = {
            # 1. COMMANDE PUBLIQUE
            SubCategory.MARCHES_PUBLICS: """Actes relatifs aux marchés publics incluant :
                - Délibérations de constitution de la commission d'appel d'offres
                - Délibérations relatives au règlement intérieur
                - Délibérations d'autorisation de signature
                - Délibérations/décisions relatives aux MAPA
                - Délibérations relatives aux avenants et marchés complémentaires""",
            
            SubCategory.DELEGATIONS_SERVICE_PUBLIC: """Actes relatifs aux délégations de service public incluant :
                - Contrats et avenants
                - Commission d'ouverture des plis
                - Désignation commission DSP
                - Autorisation à signer""",
            
            SubCategory.CONVENTIONS_MANDAT: """Documents relatifs aux conventions de mandat :
                - Délibérations
                - Conventions
                - Avenants
                - Compte-rendus""",
            
            SubCategory.AUTRES_CONTRATS: """Documents relatifs aux :
                - Partenariats public-privé
                - Conventions publiques d'aménagement""",
            
            SubCategory.TRANSACTIONS: "Documents relatifs aux protocoles transactionnels et accords amiables",
            
            SubCategory.ACTES_MAITRISE_OEUVRE: "Documents relatifs aux marchés de maîtrise d'œuvre selon le type de procédure retenue",
            
            SubCategory.ACTES_SPECIAUX_DIVERS: "Procédures de commande publique ne pouvant être classées dans les autres rubriques",
            
            # 2. URBANISME
            SubCategory.DOCUMENTS_URBANISME: """Documents d'urbanisme incluant :
                - SCOT : arrêtés d'enquête publique, délibérations de périmètre, approbations
                - PLU : arrêtés d'enquête publique, délibérations d'élaboration, modifications
                - Cartes communales : délibérations d'élaboration et d'approbation
                - ZAC : concertation, dossiers de création/réalisation""",
            
            SubCategory.ACTES_OCCUPATION_SOLS: """Actes relatifs au droit d'occupation des sols :
                - Certificats d'urbanisme
                - Permis de construire/démolir/lotir
                - Déclarations de travaux
                - Arrêtés d'alignement
                - DUP de voirie""",
            
            SubCategory.DROIT_PREEMPTION_URBAIN: """Actes relatifs au droit de préemption :
                - Délibérations d'institution du DPU
                - Décisions de préemption""",
            
            # 3. DOMAINE ET PATRIMOINE
            SubCategory.ACQUISITIONS: "Délibérations concernant les acquisitions gratuites ou onéreuses",
            
            SubCategory.ALIENATIONS: "Délibérations et arrêtés concernant les cessions gratuites ou onéreuses",
            
            SubCategory.LOCATIONS: """Actes relatifs aux locations :
                - Baux à prendre
                - Baux emphytéotiques""",
            
            SubCategory.LIMITES_TERRITORIALES: """Actes relatifs aux limites territoriales :
                - Modifications des limites
                - Dossiers d'enquête
                - Délibérations de périmètres""",
            
            SubCategory.ACTES_GESTION_DOMAINE_PUBLIC: """Actes de gestion du domaine public :
                - Classement/déclassement des voiries
                - Affectation/désaffectation de biens
                - Tarifs des services publics locaux
                - Concessions de cimetière""",
            
            SubCategory.ACTES_GESTION_DOMAINE_PRIVE: "Délibérations et arrêtés concernant les baux à donner",
            
            # 4. FONCTION PUBLIQUE
            SubCategory.PERSONNEL_TITULAIRE_FPT: "Personnel titulaire de la fonction publique territoriale",
            
            SubCategory.PERSONNEL_CONTRACTUEL: "Personnel contractuel de la fonction publique territoriale",
            
            SubCategory.FONCTION_PUBLIQUE_HOSPITALIERE: "Fonction publique hospitalière",
            
            SubCategory.AUTRES_CATEGORIES_PERSONNEL: "Autres catégories de personnel",
            
            SubCategory.REGIME_INDEMNITAIRE: "Régime indemnitaire",
            
            # 5. INSTITUTIONS ET VIE POLITIQUE
            SubCategory.ELECTION_EXECUTIF: "Élection exécutive",
            
            SubCategory.FONCTIONNEMENT_ASSEMBLEES: "Fonctionnement des assemblées",
            
            SubCategory.DESIGNATION_REPRESENTANTS: "Désignation de représentants",
            
            SubCategory.DELEGATION_FONCTIONS: "Délégation de fonctions",
            
            SubCategory.DELEGATION_SIGNATURE: "Délégation de signature",
            
            SubCategory.EXERCICE_MANDATS_LOCAUX: "Exercice des mandats locaux",
            
            SubCategory.INTERCOMMUNALITE: "Intercommunalité",
            
            SubCategory.DECISION_ESTER_JUSTICE: "Décision est-elle de justice ?",
            
            # 6. LIBERTES PUBLIQUES ET POUVOIRS DE POLICE
            SubCategory.POLICE_MUNICIPALE: "Police municipale",
            
            SubCategory.POUVOIRS_PRESIDENT_CONSEIL_GENERAL: "Pouvoirs du président du conseil général",
            
            SubCategory.AUTRES_ACTES_REGLEMENTAIRES: "Autres actes réglementaires",
            
            SubCategory.ACTES_PRIS_NOM_ETAT: "Actes pris en nom d'état",
            
            # 7. FINANCES LOCALES
            SubCategory.DECISIONS_BUDGETAIRES: "Décisions budgétaires",
            
            SubCategory.FISCALITE: "Fiscalité",
            
            SubCategory.EMPRUNTS: "Emprunts",
            
            SubCategory.INTERVENTIONS_ECONOMIQUES: "Interventions économiques",
            
            SubCategory.SUBVENTIONS: "Subventions",
            
            SubCategory.CONTRIBUTIONS_BUDGETAIRES: "Contributions budgétaires",
            
            SubCategory.AVANCES: "Avances",
            
            SubCategory.FONDS_CONCOURS: "Fonds de concours",
            
            SubCategory.PRISE_PARTICIPATION: "Prise de participation",
            
            SubCategory.DIVERS_FINANCES: "Divers financés",
            
            # 8. DOMAINES DE COMPETENCES PAR THEMES
            SubCategory.ENSEIGNEMENT: "Enseignement",
            
            SubCategory.AIDE_SOCIALE: "Aide sociale",
            
            SubCategory.POLITIQUE_VILLE_HABITAT_LOGEMENT: "Politique de la ville, de l'habitat et du logement",
            
            SubCategory.ENVIRONNEMENT: "Environnement",
            
            # 9. AUTRES DOMAINES DE COMPETENCES
            SubCategory.AUTRES_DOMAINES_COMMUNES: "Autres domaines communaux",
            
            SubCategory.AUTRES_DOMAINES_DEPARTEMENTS: "Autres domaines départementaux",
            
            SubCategory.VOEUX_ET_MOTIONS: "Voeux et motions",
        }
        return descriptions.get(sub_cat, "Description non disponible")

    def get_categories(self) -> Dict[str, List[str]]:
        return {main.name: [f"{sub.value}: {sub.name}" for sub in subs]
                for main, subs in self.categories.items()}


def categorize_llm(text_to_categorize: str):
    categorizer = ActesCategorizer()
    result = categorizer.categorize(text_to_categorize)

    # Tri des résultats par confiance décroissante
    sorted_results = sorted(result.subcategories, key=lambda x: x.confidence, reverse=True)
    
    for sub_result in sorted_results:
        print(f"\nSous-catégorie : {sub_result.sub_category.value} - {sub_result.sub_category.name}")
        print(f"Catégorie principale : {sub_result.main_category.value} - {sub_result.main_category.name}")
        print(f"Confiance : {sub_result.confidence}")
        print(f"Explication : {sub_result.explanation}")


if __name__ == "__main__":
    TEXT = """
La Maire de Paris,
Vu le code général des collectivités territoriales, et notamment ses articles L.2213-1, L.2213-6,
L.2512-14, L.2511-30 ;
Vu le code de la voirie routière, et notamment son article L.113-2 ;
Vu le code général de la propriété des personnes publiques, et notamment ses articles L.2122-1 à
L.2125-1 ;
Vu l’arrêté municipal en date du 11 juin 2021, modifié, relatif au Règlement de l’installation des
étalages et terrasses sur la voie publique ; ainsi que des contre étalages et contre terrasses, des
commerces accessoires, aux terrasses et des dépôts de matériels ou objets divers devant les
commerces et des terrasses estivales, notamment son article A6 ;
Vu la concertation menée par la Maire du 5
e arrondissement en application de l’article A6 du présent
règlement ;
Vu l’arrêté 2023P19040 en date du 25 octobre 2023 instituant une aire piétonne dans le quartier
Mouffetard à Paris 5e
;
Considérant la nécessité de favoriser les circulations douces et piétonnes et le potentiel de
végétalisation de la rue Mouffetard ;
Considérant que la circulation de véhicules motorisés dans les aires piétonnes est théoriquement
réservée aux riverains, commerçants et véhicules d’urgence, véhicules municipaux pour nécessité de
service et taxis ;
Considérant le gabarit de la chaussée et l’étroitesse des trottoirs qui induisent régulièrement des
conflits d’usage ;
Considérant le projet d’aménagements et de piétonisation de la rue Mouffetard et ses abords, en vue
de prendre en compte à la fois, la qualité du paysage urbain, l’activité commerciale importante,
l’animation et le confort des piétons, dans le périmètre suivant :
La rue Mouffetard, dans sa partie comprise entre la place de la Contrescarpe, et
la rue de l’Epée de Bois ;
Considérant qu’il apparaît en conséquence nécessaire de limiter dans ce secteur l’implantation des
emprises de terrasses accordées aux commerçants sur le domaine public ;
Considérant qu’au regard de ce contexte spécifique, il convient d’élaborer un règlement particulier ;
Sur proposition de la Maire du 5
e arrondissement et de la Direction de l’Urbanisme ;
Date de mise en ligne : le 19 juin 2024
ARRÊTE :
Article premier : L’arrêté municipal en date du 11 juin 2021, modifié, est modifié comme suit :
Au Titre III – « Dispositions localisées particulières »,
Un nouvel article DP.14 est rédigé comme suit :
DP. 14 Charte locale portant règlement particulier de la rue Mouffetard – 5
e arrondissement
- les terrasses sur les trottoirs sont interdites ;
- les terrasses sur la chaussée sont interdites
- les terrasses positionnées sur le trottoir d’en face sont interdites ;
- les terrasses latérales au-devant du commerce voisin sont interdites ;
Le secteur concerné comprend les établissements localisés rue Mouffetard des deux côtés, rives paire
et impaire, dans sa partie comprise entre la place de la Contrescarpe, et la rue de l’Epée de Bois.
Article 2 : Le présent arrêté sera publié sur le portail des publications administratives de la Ville de
Paris.
Fait à Paris, le 17 juin 2024
Pour la Maire de Paris et par délégation,
Le Secrétaire Général Adjoint
Olivier FRAISSEIX
"""
    categorize_llm(TEXT)