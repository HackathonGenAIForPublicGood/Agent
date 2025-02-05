from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Dict, Optional
import os
import json
from enum import Enum

class TypeDocument(str, Enum):  # Hériter de str pour la sérialisation JSON
    ARRETE = "arrêté"
    DECISION = "décision"
    DELIBERATION = "délibération"
    CONVENTION = "convention"
    AUTRE = "autre"

class ConformiteDetail(BaseModel):
    etat: str = Field(description="État de conformité (conforme, non conforme ou implicite)")
    explication: str = Field(description="Justification de l'état de conformité")

class ConformiteLegale(BaseModel):
    ecriture: ConformiteDetail
    date: ConformiteDetail
    signature: ConformiteDetail
    visas: ConformiteDetail
    considerants: ConformiteDetail
    dispositif: ConformiteDetail
    publication: ConformiteDetail
    transmission: ConformiteDetail

class AnalyseArrete(BaseModel):
    type_de_document: TypeDocument = Field(description="Type du document administratif (ex : arrêté, décision, ...)")
    conformite_aux_exigences_legales: ConformiteLegale = Field(description="Analyse détaillée de la conformité")
    Observation: str = Field(description="Résumé des observations détaillées")
    niveau_de_confiance: str = Field(description="Note en pourcentage")
    collectivité:str = Field(description="Nom de la collectivité qui a emis le texte")
    signataire:str = Field(description="Nom et prénom du signataire ")

    class Config:
        use_enum_values = True  # Utiliser les valeurs des énumérations lors de la sérialisation

def analyser_arrete(contexte: str, contenu: str) -> str:
    # Récupération de la clé API
    api_key = os.getenv("API_KEY")
    base_url = "https://albert.api.etalab.gouv.fr/v1"
    
    llm = ChatOpenAI(
        base_url=base_url, 
        api_key=api_key, 
        model_name="neuralmagic/Meta-Llama-3.1-70B-Instruct-FP8"
    )
    
    # Utilisation de with_structured_output pour obtenir une sortie structurée
    structured_llm = llm.with_structured_output(
        AnalyseArrete,
        method="function_calling"
    )

    # Création du prompt
    prompt = f"""Tu es un expert en droit administratif français. Analyse le document suivant selon le contexte fourni.
    Fournis une analyse détaillée et précise du document en évaluant sa conformité aux exigences légales.
    
    Le type de document doit être l'une des valeurs suivantes : arrêté, décision, délibération, convention, autre.

    précise les personnes physique et les villes impliqué
    
    Contexte:
    {contexte}
    
    Document à analyser:
    {contenu}
    """

    # Exécution de l'analyse
    try:
        resultat = structured_llm.invoke(prompt)
        # Conversion explicite en JSON
        if isinstance(resultat, str):
            # Si le résultat est déjà une chaîne JSON
            return resultat
        elif hasattr(resultat, 'model_dump'):
            # Si c'est un modèle Pydantic
            return json.dumps(resultat.model_dump(), ensure_ascii=False, indent=2)
        else:
            # Pour tout autre type
            return json.dumps(resultat, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"erreur": str(e)}, ensure_ascii=False, indent=2)

contexte = """
Prendre un arrêté
Le maire prend des arrêtés dans le cadre de ses pouvoirs de police et dans le cadre des compétences qui lui ont été déléguées en début de mandat par le Conseil Municipal.
Articles L. 2212-1 et suivants du CGCT
Article L. 2122-22 du CGCT
On peut classer les arrêtés municipaux en deux catégories :
* 		les arrêtés réglementaires que l'on peut qualifier de décisions générales et impersonnelles (ex : un arrêté instituant un sens unique dans une rue) ;
* 		les arrêtés non réglementaires, que l'on peut qualifier de décisions individuelles ou collectives concernant une ou plusieurs personnes nommément désignées (par exemple, un arrêté de mise en demeure de démolir un bâtiment menaçant ruine et constituant un danger).
Les arrêtés municipaux ne sont applicables que sur le territoire de la commune. Ils concernent à la fois les habitants de la commune et toutes les personnes y résidant momentanément, même les étrangers de passage.
Ils ne doivent respecter aucune forme déterminée. Il faut qu'ils soient écrits, datés et signés.
Cependant, il vaut mieux adopter une formulation générale claire et rédiger l'arrêté avec le maximum de précisions regroupées sous trois catégories de mentions les "visas", les "considérants", le "dispositif " :
* 		les "visas" indiquent les textes en application desquels le maire prendra son arrêté (articles du code concerné, lois, décrets et arrêtés applicables). Notons que l'absence de visa n'est pas de nature à entraîner l'annulation de l'acte ;
* 		les "considérants" exposent les motifs justifiant l'arrêté ;
* 		le "dispositif" exprime le contenu de l'arrêté: le premier article doit mentionner son objet, les autres indiquent les dispositions complémentaires et, à titre indicatif, l'autorité chargée de son exécution.
La motivation des actes
Le maire doit motiver toutes ses décisions administratives prises dans le cadre de ses prérogatives de puissance publique, toute décision individuelle défavorable (exemples : un refus de permis de construire, la résiliation du contrat d'un agent contractuel) et toutes celles dérogeant aux règles générales fixées par la loi ou le règlement.
La motivation comporte les considérations de droit et de fait qui permettent de comprendre la décision prise. Elle doit répondre aux critères suivants :
* 		être écrite ;
* 		être précise ;
* 		être contemporaine de l'acte (ni anticipée, ni ultérieure) ;
* 		être adaptée aux circonstances propres à chaque affaire.
Loi n° 79-587 du 11 juillet 1979 relative à la motivation des actes administratifs et à l'amélioration des relations entre l'administration et le public.
La transmission des actes
Tous les actes pris par les autorités communales (maire ou conseil municipal) ne sont pas soumis à l'obligation de transmission au représentant de l'État.
Article L. 2131-1 du CGCT
Lorsqu'ils relèvent de cette obligation, les actes des autorités communales entrent en vigueur, c'est-à-dire qu'ils sont exécutoires de plein droit :
* 		dès qu'ils ont été régulièrement publiés, ou affichés, ou notifiés aux intéressés ;
* 		et dès qu'ils ont été transmis au préfet ou à son délégué dans l'arrondissement.
Le maire certifie, sous sa responsabilité, le caractère exécutoire des actes pris par les autorités communales.
La preuve de la réception des actes par le préfet ou son délégué dans l'arrondissement peut être apportée par tout moyen. L'accusé de réception, qui est immédiatement délivré, peut être utilisé à cet effet, mais n'est pas une condition du caractère exécutoire des actes.
Aucun délai de transmission n'est fixé sauf pour certains actes. Ainsi, le maire doit transmettre :
* 		dans un délai de 15 jours :
    * 		le budget primitif et le compte administratif après le délai limite fixé pour leur adoption ;
    * 		les conventions de délégation de service public, les marchés publics, les contrats de partenariat à compter de leur signature ;
    * 		les décisions individuelles à compter de leur signature.
* 		dans un délai de 8 jours maximum à compter de leur adoption :
    * 		les délibérations relatives à un référendum local.
* 		dans un délai de 2 mois au moins avant la date du scrutin :
    * 		les délibérations relatives à une consultation.
Article L. 2131-1 du CGCT
La publicité des actes
Les actes réglementaires ne peuvent pas être exécutés avant leur publication en texte intégral dans le recueil des actes administratifs, ou dans tout autre support municipal, ou leur affichage. Il est possible de coupler cette publication sur support papier avec une publication complémentaire sur support numérique. Cette dernière ne remplace en aucune façon la publication sur support papier.
Les actes individuels ne peuvent pas être exécutés avant leur notification à l'administré concerné. Sauf disposition spécifique, la loi n'impose pas de forme pour la notification.
Articles L. 2131-1 et L 2131-3 du CGCT
Le registre des actes
Les arrêtés du maire ainsi que les actes de publication et de notification sont inscrits par ordre chronologique, soit sur le registre de la mairie, soit sur un registre propre aux actes du maire.
Les décisions prises par le maire, sur délégation du conseil municipal, sont inscrites dans le registre des délibérations.
Le registre propre aux actes du maire doit être coté et paraphé par le maire et tenu selon les mêmes règles que celles applicables au registre des délibérations. Les feuillets sur lesquels sont transcrits les actes du maire doivent comporter les mentions du nom de la commune ainsi que la nature de chacun de ces actes.
Le maire peut déléguer sa signature à des fonctionnaires territoriaux en ce qui concerne l'apposition du paraphe sur les feuillets du registre. En cas de litige, l'inscription au registre des arrêtés constitue un moyen de preuve de l'existence de la l'arrêté et de sa publication ou de sa notification.
S'agissant des communes de 3 500 habitants et plus, les arrêtés réglementaires doivent être publiés au moins tous les trois mois dans un recueil des actes administratifs. Ce recueil doit être mis à la disposition du public à la mairie et, éventuellement, dans les mairies annexes et les mairies d'arrondissement. Les administrés sont prévenus dans les vingt-quatre heures par affichage aux endroits où s'opère l'affichage officiel. Le recueil peut également être diffusé soit gratuitement, soit vendu au numéro ou par abonnement. Il peut s'intituler bulletin officiel, bulletin municipal, bulletin des actes administratifs ...
Articles L 2122-29, R.2122-7 et R.2122-8 du CGCT
La communication au public
Toute personne physique ou morale peut se faire communiquer les arrêtés municipaux, dans les conditions prévues par la loi n°78-753 du 17 juillet 1978 modifiée, et les publier sous sa responsabilité.
Cette communication peut s'opérer :
* 		par consultation gratuite sur place, à condition que la préservation du document le permette ;
* 		par la délivrance d'une copie aux frais du requérant ;
* 		par courrier électronique.
Article L.2121-26 du CGCT
Loi n°78-753 du 17 juillet 1978 portant diverses mesures d'amélioration des relations entre l'administration et le public et diverses dispositions d'ordre administratif, social et fiscal
Le retrait et l'abrogation des arrêtés
Les arrêtés municipaux sont applicables tant qu'ils n'ont pas fait l'objet d'un retrait ou d'une abrogation par le maire.
Le retrait signifie que l'acte est réputé n'avoir jamais existé et n'avoir produit aucun effet juridique. Il est donc retiré à compter de sa date d'adoption.
L'abrogation signifie que l'acte ne produit plus d'effets juridiques pour l'avenir, à compter de la date prescrite dans la disposition prononçant cette abrogation. En revanche, l'acte a existé et a produit des effets juridiques de la date de son adoption jusqu'à la veille de la date de son abrogation.
La rétroactivité
Une décision administrative ne peut en principe entrer en vigueur qu'à compter de sa date de publication (s'il s'agit d'un règlement) ou de sa date de signature (s'il s'agit d'une décision individuelle favorable) ou de sa date de notification (s'il s'agit d'une décision individuelle défavorable). Toute décision qui prévoit une date d'application antérieure est illégale en tant qu'elle est rétroactive.
Cela se justifie par le fait qu'il serait illogique d'appliquer une règle juridique à une époque où elle ne pouvait pas être encore connue.
Dès 1948, le Conseil d'État (arrêt CE - 25 juin 1948 - Société du journal de l'Aurore) a érigé le principe de non-rétroactivité des actes administratifs en principe général du droit. La rétroactivité consiste en l'application d'une mesure nouvelle dans le passé. Elle est réalisée lorsque l'acte prévoit lui-même son application antérieurement à son adoption ou à la publicité dont il doit faire l'objet.
La rétroactivité est cependant admise :
* 		lorsqu'elle est prévue par une disposition législative ;
* 		lorsqu'elle résulte d'une annulation contentieuse prononcée par le juge de l'excès de pouvoir ;
* 		lorsqu'elle est exigée par la situation que l'acte administratif a pour objet de régir (en cas de vide juridique) ;
* 		lorsque l'administration procède au retrait d'un acte illégal dans le délai prévu.
Sauf ces cas particuliers, un acte administratif rétroactif est irrégulier et peut donc être annulé.
Toutefois, le Conseil d'État a encadré l'application rétroactive :
* 		de l'annulation d'un acte administratif, l'intérêt général pouvant exceptionnellement justifier que le juge administratif module dans le temps les effets des annulations découlant des illégalités constatées (CE, 11 mai 2004, AC, n°255886) ;
* 		d'un revirement de jurisprudence, lorsque ce dernier concerne l'existence et les modalités d'exercice d'un recours juridictionnel.
"""

contenu = """
Date de mise en ligne : le 21 juillet 2023
Mairie du secteur Paris-Centre. – Délégation de signature de la Maire de paris donné au
directeur général des services, aux directeurs généraux adjoints des services et à la
directrice générale adjointe des services de la Mairie.
La Maire de Paris,
Vu les articles L 2122-27, L 2122-30, L 2511-27 et R 2122-8 du Code général des collectivités
territoriales ;
Vu la délibération 2020 DDCT 17 du 3 juillet 2020, par laquelle le Conseil de Paris a donné à
la Maire de Paris délégation de pouvoir en ce qui concerne les actes énumérés à l’article L.
2122-22 du Code général des collectivités territoriales et l’a autorisée à déléguer sa signature
en ces matières aux responsables des services de la Ville de Paris ;
Vu l’arrêté du 10 juillet 2020 affectant Monsieur David-Dominique FLEURIER à la Mairie du
secteur Paris-Centre, pour exercer les fonctions de directeur général adjoint des services de la
Mairie du secteur Paris-Centre ;
Vu l’arrêté du 1er juin 2021 détachant Monsieur Alban GIRAUD, dans l’emploi de directeur
général adjoint des services de la Mairie du secteur Paris-Centre ;
Vu l’arrêté du 28 septembre 2021 détachant Madame Isabelle VERDOU, dans l’emploi de
directrice générale adjointe des services de la Mairie du secteur Paris-Centre ;
Vu l’arrêté du 26 juin 2023 détachant Monsieur Elie BEAUROY, dans l’emploi de directeur
général des services de la Mairie du secteur Paris-Centre ;
Sur proposition de Madame la Secrétaire Générale de la Ville de Paris,
ARRÊTE :
Article premier : La signature de la Maire de Paris est déléguée à Monsieur Elie BEAUROY,
directeur général des services de la Mairie du secteur Paris-Centre. En cas d’absence ou
d’empêchement de Monsieur Elie BEAUROY, la signature de la Maire de Paris est déléguée à
Monsieur David-Dominique FLEURIER, directeur général adjoint des services de la Mairie du
secteur Paris-Centre, à Madame Isabelle VERDOU, directrice générale adjointe des services de
la Mairie du secteur Paris-Centre et à Monsieur Alban GIRAUD, directeur général adjoint des
services de la Mairie du secteur Paris-Centre, pour les actes énumérés ci-dessous :
- procéder à la légalisation ou à la certification matérielle de signature des administrés ;
- procéder aux certifications conformes à l’original des copies de documents ;
- procéder à la délivrance des différents certificats prévus par les dispositions législatives ou
réglementaires en vigueur ;
2
- recevoir les notifications, délivrer les récépissés et assurer l’information des présidents des
bureaux de vote dans les conditions définies par les articles R 46 et R 47, dernier alinéa, du Code
électoral ;
- préparer, organiser et exécuter, au titre des attributions légales fixées à l’article L 2122-27 du
Code général des collectivités territoriales et dans les conditions prévues à cet effet par le Code
électoral, les opérations, actes et décisions, individuels et collectifs, ainsi que les arrêts
comptables relatifs à la tenue des listes électorales et au déroulement des opérations électorales,
à l’exclusion des désignations prévues à l’article R 43 du Code électoral ;
- coter et parapher, et le cas échéant, viser annuellement conformément aux dispositions légales
et réglementaires les registres, livres et répertoires concernés ;
- coter et parapher les feuillets du registre des délibérations du conseil d’arrondissement ;
- signer les autorisations de fermeture de cercueil et les autorisations de crémation en application
des articles R 2213-17 et R 2213-34 du Code général des collectivités territoriales;
- signer les autorisations pour le dépôt provisoire du cercueil sur le territoire parisien et hors
cimetière parisien ;
- signer toutes copies et extraits d’actes d’état-civil ;
- signer les affirmations des procès-verbaux par des gardes particuliers assermentés ;
- valider les attestations d’accueil conformément aux articles L 211-3 à L 211-10 et R 211-11 à
R 211-26 du Code de l’entrée et du séjour des étrangers et du droit d’asile ;
- émettre les avis demandés par l’Office Français de l’immigration et de l’intégration sur les
demandes de regroupement familial des étrangers soumis à cette procédure, conformément aux
articles R 421-9 à R 421-19 du Code de l’entrée et du séjour des étrangers et du droit d’asile ;
- attester le service fait figurant sur les états liquidatifs d’heures supplémentaires effectuées par
les agents placés sous leur autorité ;
- signer les décisions de recrutement, de prolongation et de fin d’engagement d’agents vacataires
en qualité de suppléants de gardien de mairie d’arrondissement, de renfort pour les élections,
le recensement général de la population et le budget participatif ;
- signer les décisions d’engagement et leurs avenants, les cartes officielles, les décisions de
licenciement et l’arrêté collectif de nomination des agents recenseurs ;
- signer les décisions individuelles d’engagement des agents de bureaux de vote ou l’arrêté
collectif de nomination des agents de bureau de vote ;
- attester le service fait par les agents recenseurs et les agents de bureaux de vote ;
- signer les décisions de recrutement d’agents saisonniers durant la période estivale ;
- notifier les décisions portant non-renouvellement des contrats des agents non titulaires placés
sous leur autorité, à l’exclusion des collaborateurs du Maire d’arrondissement ;
- signer les arrêtés de temps partiel, de congé maternité, de congé paternité, de congé parental,
de congé d’adoption, d’attribution de prime d’installation concernant les personnels de
catégories B et C placés sous leur autorité, à l’exception des directrices et directeurs généraux
adjoints des services et des collaborateurs du Maire d’arrondissement ;
3
- signer les arrêtés de congé initial à plein traitement de un à trente jours au titre d’un accident
de service, de trajet ou de travail non contesté ;
- signer les arrêtés de sanctions du premier groupe pour les agents de catégories B et C ;
- signer les fiches d’évaluation des personnels placés sous leur autorité ;
- signer les conventions de stage (stagiaires extérieurs) d’une durée inférieure à deux mois
(280 heures) ;
- attester du service fait figurant sur les factures du marché annuel de fourniture de plateaux repas
à l’occasion des scrutins électoraux ;
- signer tous les contrats ou conventions permettant la rémunération de tiers intervenant lors de
manifestations ou d’activités d’animation et toutes pièces comptables et attestations de service
fait correspondantes ;
- signer les conventions d’occupation de locaux et les conventions de prêt de matériel.
- signer tous les actes administratifs et tous les titres, états de recouvrement de créances de la
Ville de Paris et factures, pris ou émis dans le cadre de l’exécution du budget municipal en
recettes.
Article 2 : L’arrêté du 27 janvier 2022, déléguant la signature de la Maire de Paris à Madame
Catherine ARRIAL, directrice générale des services de la Mairie du secteur Paris-Centre, à
Monsieur David-Dominique FLEURIER, directeur général adjoint des services de la Mairie du
secteur Paris-Centre, à Madame Isabelle VERDOU, directrice générale adjointe des services de
la Mairie du secteur Paris-Centre et à Monsieur Alban GIRAUD, directeur général adjoint des
services en charge de l’espace public de la Mairie du secteur Paris-Centre est abrogé.
Article 3 : Le présent arrêté sera publié sur le portail des publications administratives de la Ville
de Paris.
Article 4 : Ampliation du présent arrêté sera adressée :
- à M. le Préfet de la région d’Ile-de-France, Préfet de Paris,
- à Mme le Directrice régionale des Finances Publiques, d’Ile-de-France et
de Paris,
- à Mme la Secrétaire Générale de la Ville de Paris,
- à Mme la Directrice de la Démocratie, des Citoyen·ne·s et des
Territoires,
- à M. le Maire de Paris-Centre,
- aux intéressé·e.s.
Fait à Paris, le 19 juillet 2023
La Maire de Paris
Anne HIDALGO
"""

# Exemple d'utilisation
if __name__ == "__main__":
    resultat = analyser_arrete(
        contexte=contexte,
        contenu=contenu
    )
    print(resultat)
