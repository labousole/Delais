# Combien j'attends — délais administratifs français

Site statique qui agrège les délais de traitement réels publiés par les
Caf départementales, remis à jour automatiquement chaque jour via GitHub
Actions, et publié sur GitHub Pages. Coût d'hébergement : 0 €.

**Statut actuel : squelette fonctionnel avec données de démonstration.**
Le site s'affiche et fonctionne tel quel, mais `data/delais.json` contient
des chiffres générés aléatoirement (`"status": "demo_data"`), pas les
vrais délais. Il faut faire tourner le scraper en conditions réelles avant
de communiquer dessus publiquement (voir étape 4).

---

## 1. Publier le site tel quel (5 minutes)

```bash
# depuis ce dossier
git init
git add .
git commit -m "Premier commit"
git branch -M main
git remote add origin https://github.com/<TON_USER>/delais-admin-fr.git
git push -u origin main
```

Puis sur GitHub :
1. **Settings → Pages → Build and deployment → Source : GitHub Actions**
   (pas "Deploy from a branch" — le workflow fourni utilise l'API Pages).
2. Remplace les 3 occurrences de `REPLACE_WITH_YOUR_USERNAME` dans
   `index.html` et `scraper/scrape_caf.py` par ton pseudo GitHub
   (`grep -rn REPLACE_WITH_YOUR_USERNAME .` pour les retrouver).
3. Onglet **Actions → Mise à jour quotidienne des délais → Run workflow**
   pour déclencher un premier build manuellement sans attendre le cron.

Le site sera en ligne sur `https://<TON_USER>.github.io/delais-admin-fr/`.

Pour un nom de domaine perso : ajoute un fichier `CNAME` à la racine avec
ton domaine dedans, et configure un enregistrement DNS `CNAME` pointant
vers `<TON_USER>.github.io`.

---

## 2. Faire tourner le scraper en local (recommandé avant le run auto)

```bash
cd scraper
pip install -r requirements.txt
python scrape_caf.py --limit 5      # test rapide sur 5 départements
```

Regarde `data/scrape_report.json` généré : il liste les départements en
échec (URL introuvable, page changée, aucun délai détecté...). C'est
normal d'en avoir au premier run — voir section 4.

Pour scraper des départements précis :
```bash
python scrape_caf.py --dept 59 75 33
```

Pour tout scraper (~101 requêtes, ~2-3 minutes avec la pause de politesse
intégrée) :
```bash
python scrape_caf.py
```

---

## 3. Comment ça marche

```
delais-admin-fr/
├── index.html              → page unique, lit data/delais.json en JS
├── assets/
│   ├── style.css            → design "ticket de guichet"
│   └── app.js                → fetch + rendu + recherche/filtres
├── data/
│   ├── delais.json           → données consommées par le site (générées)
│   └── scrape_report.json    → rapport d'échecs du dernier run
├── scraper/
│   ├── departments.py         → liste des 101 départements + slug caf.fr
│   ├── scrape_caf.py           → scraper + extraction des délais
│   └── requirements.txt
└── .github/workflows/
    └── update-data.yml         → cron quotidien : scrape → commit → deploy
```

Le workflow GitHub Actions :
1. tourne tous les jours à 05:30 UTC (`cron`), ou manuellement via
   "Run workflow" ;
2. exécute `scrape_caf.py`, qui écrase `data/delais.json` ;
3. committe le fichier s'il a changé ;
4. republie le site sur GitHub Pages.

Comme tout est statique + Actions, il n'y a **aucun serveur à gérer** et
le tier gratuit GitHub (2 000 min/mois sur un repo public) suffit très
largement pour un run quotidien de quelques minutes.

---

## 4. ⚠️ Ce qui reste à fiabiliser avant mise en prod publique

Ce projet a été généré sans accès réseau à `caf.fr` (bac à sable isolé),
donc certains points sont des **best-effort à vérifier**, pas des
certitudes :

- **Les slugs d'URL** (`caf-du-nord`, `caf-de-la-gironde`, etc.) dans
  `departments.py` sont générés à partir des règles de genre grammatical
  français. Seuls `59`, `75` et `83` ont été confirmés en dur dans
  `OVERRIDES`. Après le premier run, corrige les slugs listés en échec
  dans `data/scrape_report.json` directement dans le dict `OVERRIDES`.
- **Le parseur de délais** (`parse_delais_page`) cherche des formulations
  du type *« délai moyen de X jours »* / *« traité sous X jours »* autour
  des mots "APL", "RSA", "AAH", "Prime d'activité". Chaque Caf rédige sa
  page à sa façon — attends-toi à devoir enrichir `PRESTATIONS` et
  `DELAY_PATTERN` au fil des vrais runs.
- **Couverture actuelle : uniquement la Caf.** Le schéma JSON
  (`departments[].delais`) est prévu pour accueillir d'autres sources
  (préfectures, France Travail, impôts) : ajoute simplement de nouvelles
  clés de prestation et, si besoin, un nouveau scraper qui écrit dans la
  même structure `data/delais.json`.
- **Respect du site source :** le scraper fait une pause de 1,5 s entre
  chaque requête et s'identifie via un `User-Agent` dédié. Vérifie le
  `robots.txt` de caf.fr et adapte la fréquence si besoin avant de monter
  en charge.

## 5. Prochaines étapes suggérées

- Ajouter un scraper pour les délais préfecture (titres de séjour) à
  partir des données déjà partiellement publiques (ANEF, sites
  préfectoraux).
- Brancher une régie publicitaire (Ezoic/Mediavine) une fois un trafic
  réel établi — juste un tag à ajouter dans `index.html`, aucun impact
  sur l'archi statique.
- Ajouter un flux RSS/Atom des plus fortes hausses de délai (réutilisable
  pour un post automatique Bluesky/Mastodon, comme sur La Boussole).
