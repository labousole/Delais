#!/usr/bin/env python3
"""
Scraper des délais de traitement Caf, département par département.

Chaque Caf publie une page "Délais de traitement" en langage assez libre
("Les déclarations trimestrielles de Prime d'activité sont actuellement
traitées dans un délai moyen de 23 jours"). Ce script :

  1. Télécharge la page de chaque département (voir departments.py).
  2. Cherche des motifs "délai moyen de X jour(s)" / "traité(es) sous X jours"
     associés à une prestation connue (APL, RSA, Prime d'activité, AAH...).
  3. Écrit le résultat consolidé dans data/delais.json.

⚠️ Fragilité connue : chaque Caf rédige sa page à sa sauce (structure HTML,
formulations, prestations couvertes). Le parseur ci-dessous couvre les
formulations les plus courantes vues lors de la conception du projet, mais
il faudra l'ajuster au fil de l'eau — voir la fonction `parse_delais_page`
et le rapport `data/scrape_report.json` généré à chaque run (liste des
départements en échec).

Usage :
    python scrape_caf.py                  # scrape tous les départements
    python scrape_caf.py --limit 5         # test rapide sur 5 départements
    python scrape_caf.py --dept 59 75      # scrape seulement ces départements
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from departments import get_departments

BASE_URL = "https://www.caf.fr/allocataires/{slug}/offre-de-service/thematique-libre/delais-de-traitement"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; DelaisAdminFR/1.0; "
        "+https://github.com/REPLACE_WITH_YOUR_USERNAME/delais-admin-fr)"
    )
}
TIMEOUT = 15
SLEEP_BETWEEN_REQUESTS = 1.5  # politesse envers le serveur caf.fr

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "delais.json"
REPORT_FILE = DATA_DIR / "scrape_report.json"

# Prestations recherchées dans le texte de la page, avec leurs synonymes.
PRESTATIONS = {
    "prime_activite": ["prime d'activité", "prime d activité"],
    "apl": ["apl", "aide au logement", "aides au logement"],
    "rsa": ["rsa", "revenu de solidarité active"],
    "aah": ["aah", "allocation adulte handicapé"],
}

# Motif générique : "délai moyen de 23 jours", "traités sous 15 jours",
# "traitées dans un délai de 3 semaines", etc.
DELAY_PATTERN = re.compile(
    r"(?:délai(?:s)?\s*(?:moyen\s*)?(?:de\s*traitement\s*)?(?:est\s*)?(?:de|d')?\s*|"
    r"trait[ée]e?s?\s*(?:dans un délai de|sous|en)\s*)"
    r"(\d{1,3})\s*(jour|jours|semaine|semaines|mois)",
    re.IGNORECASE,
)


def to_days(value: int, unit: str) -> int:
    unit = unit.lower()
    if unit.startswith("jour"):
        return value
    if unit.startswith("semaine"):
        return value * 7
    if unit.startswith("mois"):
        return value * 30
    return value


def parse_delais_page(html: str) -> dict:
    """Extrait un dict {prestation: délai_en_jours} depuis le HTML brut.

    On raisonne phrase par phrase (plutôt qu'avec une fenêtre de caractères
    fixe) pour éviter d'associer le délai d'une prestation au délai
    mentionné juste avant/après pour une AUTRE prestation dans le texte.
    """
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    # découpage grossier en phrases
    sentences = re.split(r"(?<=[.!?])\s+", text)

    results = {}
    for key, synonyms in PRESTATIONS.items():
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(syn in sentence_lower for syn in synonyms):
                match = DELAY_PATTERN.search(sentence_lower)
                if match:
                    results[key] = to_days(int(match.group(1)), match.group(2))
                    break
    return results


def scrape_department(dept: dict, session: requests.Session) -> dict:
    url = BASE_URL.format(slug=dept["slug"])
    entry = {
        "code": dept["code"],
        "name": dept["name"],
        "slug": dept["slug"],
        "source_url": url,
        "delais": {},
        "status": "ok",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        resp = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 404:
            entry["status"] = "url_introuvable"
            return entry
        resp.raise_for_status()
        delais = parse_delais_page(resp.text)
        if not delais:
            entry["status"] = "page_ok_mais_aucun_delai_detecte"
        entry["delais"] = delais
    except requests.RequestException as exc:
        entry["status"] = f"erreur_reseau: {exc}"
    return entry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Ne traiter que N départements (test rapide)")
    parser.add_argument("--dept", nargs="*", default=None, help="Ne traiter que ces codes département")
    args = parser.parse_args()

    departments = get_departments()
    if args.dept:
        wanted = set(args.dept)
        departments = [d for d in departments if d["code"] in wanted]
    if args.limit:
        departments = departments[: args.limit]

    session = requests.Session()
    results = []
    failures = []

    for i, dept in enumerate(departments, 1):
        print(f"[{i}/{len(departments)}] {dept['name']} ({dept['code']}) -> {dept['slug']}", file=sys.stderr)
        entry = scrape_department(dept, session)
        results.append(entry)
        if entry["status"] != "ok" or not entry["delais"]:
            failures.append({"code": entry["code"], "name": entry["name"], "status": entry["status"]})
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    DATA_DIR.mkdir(exist_ok=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "caf.fr (pages 'Délais de traitement' par département)",
        "unit": "jours",
        "departments": results,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    REPORT_FILE.write_text(
        json.dumps({"total": len(departments), "failures": failures}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n✅ {len(results)} départements traités, {len(failures)} en échec ou sans donnée.", file=sys.stderr)
    print(f"   -> {OUTPUT_FILE}", file=sys.stderr)
    print(f"   -> {REPORT_FILE} (détail des échecs à corriger dans departments.py)", file=sys.stderr)


if __name__ == "__main__":
    main()
