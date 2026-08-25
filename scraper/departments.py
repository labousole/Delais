"""
Référentiel des départements français utilisé pour construire les URLs
des pages "Délais de traitement" de chaque Caf départementale.

⚠️ IMPORTANT — À LIRE AVANT DE FAIRE TOURNER LE SCRAPER EN PRODUCTION :
Le pattern d'URL caf.fr observé (voir README) est de la forme :

    https://www.caf.fr/allocataires/<slug>/offre-de-service/thematique-libre/delais-de-traitement

où <slug> ressemble à "caf-du-nord", "caf-de-paris", "caf-du-var", etc.
Ce module GÉNÈRE ces slugs à partir du nom du département et de son article
("du", "de la", "des", "de l'", "de"). Cette génération est une estimation
raisonnable basée sur la connaissance générale des noms de départements
français — elle n'a PAS été vérifiée en direct contre caf.fr (le bac à
sable de génération n'a pas accès au domaine caf.fr). Il faut donc :

  1. Faire tourner `python scrape_caf.py --check-urls` (voir plus bas) après
     publication, pour repérer les slugs qui renvoient une 404.
  2. Corriger les entrées fautives directement dans OVERRIDES ci-dessous.

C'est un point de friction connu du projet, pas un oubli.
"""

import unicodedata

# (code, nom, article) — article ∈ {"du", "de la", "des", "de l'", "de"}
DEPARTMENTS = [
    ("01", "Ain", "de l'"),
    ("02", "Aisne", "de l'"),
    ("03", "Allier", "de l'"),
    ("04", "Alpes-de-Haute-Provence", "des"),
    ("05", "Hautes-Alpes", "des"),
    ("06", "Alpes-Maritimes", "des"),
    ("07", "Ardèche", "de l'"),
    ("08", "Ardennes", "des"),
    ("09", "Ariège", "de l'"),
    ("10", "Aube", "de l'"),
    ("11", "Aude", "de l'"),
    ("12", "Aveyron", "de l'"),
    ("13", "Bouches-du-Rhône", "des"),
    ("14", "Calvados", "du"),
    ("15", "Cantal", "du"),
    ("16", "Charente", "de la"),
    ("17", "Charente-Maritime", "de la"),
    ("18", "Cher", "du"),
    ("19", "Corrèze", "de la"),
    ("2A", "Corse-du-Sud", "de la"),
    ("2B", "Haute-Corse", "de la"),
    ("21", "Côte-d'Or", "de la"),
    ("22", "Côtes-d'Armor", "des"),
    ("23", "Creuse", "de la"),
    ("24", "Dordogne", "de la"),
    ("25", "Doubs", "du"),
    ("26", "Drôme", "de la"),
    ("27", "Eure", "de l'"),
    ("28", "Eure-et-Loir", "de l'"),
    ("29", "Finistère", "du"),
    ("30", "Gard", "du"),
    ("31", "Haute-Garonne", "de la"),
    ("32", "Gers", "du"),
    ("33", "Gironde", "de la"),
    ("34", "Hérault", "de l'"),
    ("35", "Ille-et-Vilaine", "de l'"),
    ("36", "Indre", "de l'"),
    ("37", "Indre-et-Loire", "de l'"),
    ("38", "Isère", "de l'"),
    ("39", "Jura", "du"),
    ("40", "Landes", "des"),
    ("41", "Loir-et-Cher", "de"),
    ("42", "Loire", "de la"),
    ("43", "Haute-Loire", "de la"),
    ("44", "Loire-Atlantique", "de la"),
    ("45", "Loiret", "du"),
    ("46", "Lot", "du"),
    ("47", "Lot-et-Garonne", "du"),
    ("48", "Lozère", "de la"),
    ("49", "Maine-et-Loire", "du"),
    ("50", "Manche", "de la"),
    ("51", "Marne", "de la"),
    ("52", "Haute-Marne", "de la"),
    ("53", "Mayenne", "de la"),
    ("54", "Meurthe-et-Moselle", "de"),
    ("55", "Meuse", "de la"),
    ("56", "Morbihan", "du"),
    ("57", "Moselle", "de la"),
    ("58", "Nièvre", "de la"),
    ("59", "Nord", "du"),
    ("60", "Oise", "de l'"),
    ("61", "Orne", "de l'"),
    ("62", "Pas-de-Calais", "du"),
    ("63", "Puy-de-Dôme", "du"),
    ("64", "Pyrénées-Atlantiques", "des"),
    ("65", "Hautes-Pyrénées", "des"),
    ("66", "Pyrénées-Orientales", "des"),
    ("67", "Bas-Rhin", "du"),
    ("68", "Haut-Rhin", "du"),
    ("69", "Rhône", "du"),
    ("70", "Haute-Saône", "de la"),
    ("71", "Saône-et-Loire", "de"),
    ("72", "Sarthe", "de la"),
    ("73", "Savoie", "de la"),
    ("74", "Haute-Savoie", "de la"),
    ("75", "Paris", "de"),
    ("76", "Seine-Maritime", "de la"),
    ("77", "Seine-et-Marne", "de"),
    ("78", "Yvelines", "des"),
    ("79", "Deux-Sèvres", "des"),
    ("80", "Somme", "de la"),
    ("81", "Tarn", "du"),
    ("82", "Tarn-et-Garonne", "du"),
    ("83", "Var", "du"),
    ("84", "Vaucluse", "du"),
    ("85", "Vendée", "de la"),
    ("86", "Vienne", "de la"),
    ("87", "Haute-Vienne", "de la"),
    ("88", "Vosges", "des"),
    ("89", "Yonne", "de l'"),
    ("90", "Territoire de Belfort", "du"),
    ("91", "Essonne", "de l'"),
    ("92", "Hauts-de-Seine", "des"),
    ("93", "Seine-Saint-Denis", "de la"),
    ("94", "Val-de-Marne", "du"),
    ("95", "Val-d'Oise", "du"),
    ("971", "Guadeloupe", "de la"),
    ("972", "Martinique", "de la"),
    ("973", "Guyane", "de la"),
    ("974", "La Réunion", "de la"),
    ("976", "Mayotte", "de"),
]

# Corrections manuelles connues (à compléter au fil des vérifications réelles).
# Clé = code département, valeur = slug complet exact "caf-...".
OVERRIDES = {
    "59": "caf-du-nord",
    "83": "caf-du-var",
    "75": "caf-de-paris",
}


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def build_slug(name: str, article: str) -> str:
    """Construit un slug best-effort du type 'caf-du-nord' / 'caf-de-la-gironde'."""
    art = article.replace("'", "-").replace(" ", "-").lower()
    raw = f"caf-{art}-{name}"
    raw = _strip_accents(raw).lower()
    raw = raw.replace("'", "-").replace(" ", "-")
    # nettoyage des doubles tirets éventuels
    while "--" in raw:
        raw = raw.replace("--", "-")
    return raw.strip("-")


def get_departments():
    """Retourne la liste des départements avec leur slug CAF (best-effort)."""
    result = []
    for code, name, article in DEPARTMENTS:
        slug = OVERRIDES.get(code) or build_slug(name, article)
        result.append({"code": code, "name": name, "slug": slug, "verified": code in OVERRIDES})
    return result


if __name__ == "__main__":
    for dept in get_departments():
        flag = "✓" if dept["verified"] else " "
        print(f"[{flag}] {dept['code']:>3}  {dept['name']:<28} -> {dept['slug']}")
