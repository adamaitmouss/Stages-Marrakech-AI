# Guide du code source pour la soutenance

Les numéros de ligne ci-dessous correspondent exactement à la copie `PROJET_FINAL` au 9 novembre 2026. Les extraits sont lus automatiquement depuis les fichiers cités; ils ne sont pas reconstitués. Après toute modification de code, régénérez `INDEX_FONCTIONNALITES_CODE.csv` et revérifiez les extraits.

## Parcours rapide dans VS Code

Ouvrez `PROJET_FINAL` comme dossier. Dans VS Code, `Ctrl+P` ouvre un fichier par nom; `Ctrl+G` va à une ligne. Les lignes courtes ci-dessous constituent le parcours principal; les classes et fonctions d’assistance apparaissent dans l’index CSV.

## Limite de sécurité à dire avant les modules personnels

L’authentification locale actuelle ouvre une session unique pour l’application. Elle ne crée pas un périmètre privé distinct pour chaque compte autour de `cvs` et `candidatures`. La passerelle a un profil privé administrateur unique et interdit l’inscription, tandis que le profil de démonstration utilise des données synthétiques partagées. Présentez cette limite avant toute démonstration de CV ou de suivi.

## 1. Lancement Flask

**Objectif.** Démarrer le serveur local et assembler les modules.

**Technologies.** Python, Flask, configuration par variables d’environnement.

**Données / tables.** tables SQLite du profil actif.

**Fichiers, symboles et extraits source.**

- `backend/app.py:8-10` — `bloc de configuration vérifié`. Entrée de lancement et écoute locale.

```python
if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=False)
```

**Lecture des instructions principales :**
- `backend/app.py:8` ne démarre le serveur que lorsque le fichier est exécuté directement.
- `backend/app.py:9` appelle la fabrique Flask.
- `backend/app.py:10` lie Flask à 127.0.0.1:5000 avec le mode debug désactivé.
- `backend/web.py:20-31` exige une attestation et un marqueur synthétique pour la base publique.
- `backend/web.py:35-42` applique les migrations et traite une collecte restée en état running après arrêt.

- `backend/web.py:15-42` — `create_app`. Construction, contrôles de profil, migrations et coffre.

```python
def create_app(overrides=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(settings(overrides))
    if app.config.get('TRUST_PROXY'):
        app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
    if app.config.get('PUBLIC_DEMO_MODE'):
        if not app.config.get('PUBLIC_DEMO_DATA_CONFIRMED'):
            raise RuntimeError('Le mode public exige l’attestation d’un jeu synthétique.')
        db_uri=Path(app.config['DATABASE']).resolve().as_uri()+'?mode=ro'
        try:
            check=sqlite3.connect(db_uri,uri=True)
            marker=check.execute("SELECT value FROM deployment_metadata WHERE key='dataset_type'").fetchone()
            check.close()
        except sqlite3.Error as exc:
            raise RuntimeError('La base publique doit porter le marqueur de données synthétiques.') from exc
        if not marker or marker[0]!='synthetic_public_demo':
            raise RuntimeError('Base refusée en mode public : les données doivent être synthétiques.')
    vault = Vault(app.config['PRIVATE_DIR'])
    app.secret_key = vault.session_key
    app.extensions['vault'] = vault
    migrate(app.config['DATABASE'], app.config['BACKUP_DIR'])
    migrate_phase5(app.config['DATABASE'], app.config['BACKUP_DIR'])
    migrate_phase7(app.config['DATABASE'], app.config['BACKUP_DIR'])
    migrate_phase9(app.config['DATABASE'], app.config['BACKUP_DIR'])
    app.extensions['gemini_search_jobs']={}
    with connect(app.config['DATABASE']) as db:
        if not app.config.get('PUBLIC_DEMO_MODE'):
            db.execute("UPDATE collector_runs SET status='failed',finished_at=?,error_summary='Collecte interrompue à l’arrêt précédent.' WHERE status='running'",(now(),))
```

**Lecture des instructions principales :**
- `backend/app.py:8` ne démarre le serveur que lorsque le fichier est exécuté directement.
- `backend/app.py:9` appelle la fabrique Flask.
- `backend/app.py:10` lie Flask à 127.0.0.1:5000 avec le mode debug désactivé.
- `backend/web.py:20-31` exige une attestation et un marqueur synthétique pour la base publique.
- `backend/web.py:35-42` applique les migrations et traite une collecte restée en état running après arrêt.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: démarrer le serveur local et assembler les modules.

**Tests associés.** tests/test_installation.py; tests/test_application.py::test_pages_connected. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Lancer `LANCER_SOUTENANCE_LOCALE.bat`, lire la vérification et ouvrir l’application locale.

**Phrase possible.** « Le point d’entrée appelle une fabrique Flask qui rassemble les routes, la sécurité et Dash. »

## 2. Authentification

**Objectif.** Distinguer le mot de passe local historique de la passerelle Login/Register/Logout.

**Technologies.** Flask session, Werkzeug, scrypt, cookies, CSRF.

**Données / tables.** auth.json local / base de comptes auth_gateway séparée.

**Fichiers, symboles et extraits source.**

- `backend/security.py:49-60` — `setup, login`. Configuration et validation du mot de passe local.

```python
    def setup(self, password):
        if not isinstance(password, str) or len(password) < 12 or len(password) > 256:
            raise ValueError('Choisissez un mot de passe de 12 à 256 caractères.')
        with _setup_lock:
            with (self.path / 'auth.json').open('x', encoding='utf-8') as f:
                json.dump({'password_hash': generate_password_hash(password)}, f)

    def login(self, password):
        if not self.configured or not isinstance(password, str):
            return False
        auth = json.loads((self.path / 'auth.json').read_text())
        return check_password_hash(auth['password_hash'], password)
```

**Lecture des instructions principales :**
- `backend/security.py:49-54` impose une taille de mot de passe puis stocke un hash Werkzeug dans un fichier créé sans écrasement.
- `backend/security.py:56-60` vérifie le mot de passe sans comparer du texte en clair.
- `auth_gateway/security.py:13-18` prépare le stockage de hachages scrypt et un sel.
- `auth_gateway/app.py:228-262` vérifie si l’inscription est permise, normalise les données et crée un compte dans la base de la passerelle.

- `auth_gateway/security.py:13-31` — `hash_password, verify_password`. Hachage du mot de passe de compte.

```python
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32)
    return '$'.join(('scrypt', str(SCRYPT_N), str(SCRYPT_R), str(SCRYPT_P),
                     base64.urlsafe_b64encode(salt).decode('ascii'),
                     base64.urlsafe_b64encode(digest).decode('ascii')))


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_text, digest_text = encoded.split('$', 5)
        if scheme != 'scrypt':
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode('ascii'))
        expected = base64.urlsafe_b64decode(digest_text.encode('ascii'))
        actual = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False
```

**Lecture des instructions principales :**
- `backend/security.py:49-54` impose une taille de mot de passe puis stocke un hash Werkzeug dans un fichier créé sans écrasement.
- `backend/security.py:56-60` vérifie le mot de passe sans comparer du texte en clair.
- `auth_gateway/security.py:13-18` prépare le stockage de hachages scrypt et un sel.
- `auth_gateway/app.py:228-262` vérifie si l’inscription est permise, normalise les données et crée un compte dans la base de la passerelle.

- `auth_gateway/app.py:228-262` — `gateway_register`. Inscription de la passerelle et contrôles de profil.

```python
    def gateway_register():
        current = g.auth_session
        if not cfg['AUTH_ALLOW_REGISTRATION']:
            return auth_page('register', 'La création de compte est désactivée pour cette base privée.', csrf=current['csrf']), 403
        tunnel.initialize()
        if not tunnel.public_demo:
            return auth_page('register', 'L’inscription est disponible uniquement avec le jeu synthétique.', csrf=current['csrf']), 403
        if request.method == 'GET':
            return auth_page('register', csrf=current['csrf'])
        if not csrf_ok(current):
            return auth_page('register', 'Votre formulaire a expiré. Rechargez la page.', csrf=current['csrf']), 403
        first = request.form.get('first_name', '').strip()
        last = request.form.get('last_name', '').strip()
        email = normalize_email(request.form.get('email', ''))
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        errors = []
        if not valid_name(first) or not valid_name(last):
            errors.append('Saisissez un prénom et un nom valides.')
        if len(email) > 254 or not EMAIL_RE.fullmatch(email):
            errors.append('Saisissez une adresse email valide.')
        if not valid_password(password):
            errors.append('Le mot de passe doit contenir au moins 12 caractères, une lettre et un chiffre.')
        if password != confirm:
            errors.append('La confirmation du mot de passe ne correspond pas.')
        if errors:
            return auth_page('register', ' '.join(errors), csrf=current['csrf'], first_name=first, last_name=last, email=email), 400
        ip_key = _attempt_key('register-ip', request.remote_addr or 'unknown')
        if not store.consume_attempt(ip_key, 10, 3600):
            return auth_page('register', 'Trop de créations depuis cette adresse. Réessayez plus tard.', csrf=current['csrf']), 429
        if not store.create_user(first, last, email, hash_password(password), role='demo'):
            return auth_page('register', 'Un compte existe déjà avec cette adresse email.', csrf=current['csrf'], first_name=first, last_name=last, email=email), 409
        created = store.get_user_by_email(email)
        rotate_for(created['id'])
        return redirect('/account')
```

**Lecture des instructions principales :**
- `backend/security.py:49-54` impose une taille de mot de passe puis stocke un hash Werkzeug dans un fichier créé sans écrasement.
- `backend/security.py:56-60` vérifie le mot de passe sans comparer du texte en clair.
- `auth_gateway/security.py:13-18` prépare le stockage de hachages scrypt et un sel.
- `auth_gateway/app.py:228-262` vérifie si l’inscription est permise, normalise les données et crée un compte dans la base de la passerelle.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: distinguer le mot de passe local historique de la passerelle login/register/logout.

**Tests associés.** tests/test_application.py::test_auth_and_csrf_required; auth_gateway/tests/test_gateway.py. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Tester sur la démo synthétique; ne pas créer un compte public sur l’historique privé.

**Phrase possible.** « L’authentification protège une session, mais le cœur existant n’isole pas les candidatures et les CV par utilisateur. »

## 3. Entreprises

**Objectif.** Lire le répertoire et afficher les fiches via l’API locale.

**Technologies.** SQL paramétré, Flask, JavaScript.

**Données / tables.** entreprises.

**Fichiers, symboles et extraits source.**

- `backend/api.py:94-96` — `companies`. Lecture des entreprises avec identifiant local rowid.

```python
def companies():
    return rows(config()['DATABASE'], 'SELECT rowid AS id,* FROM entreprises')

```

**Lecture des instructions principales :**
- `backend/api.py:94-95` exécute la lecture locale et expose `rowid` comme identifiant API.
- `dashboard/js/ui.js:85-96` construit les lignes et les contrôles de recherche dans le navigateur.

- `dashboard/js/ui.js:85-96` — `repère fonctionnel vérifié dans le fichier`. Construction de la page entreprise.

```javascript
async function companiesPage(){
 const data=await api('/entreprises');title('Les entreprises de votre écosystème','Explorez les entreprises et préparez une prise de contact ciblée.',navlink('Voir la carte','carte.html',false,'map'));
 const search=h('input',{placeholder:'Nom de l’entreprise…','aria-label':'Rechercher une entreprise'}),sector=select([...new Set(data.map(d=>d.Secteur).filter(Boolean))].sort(),'Tous les secteurs'),count=h('p',{class:'section-info'}),table=h('tbody');
 function render(){const q=search.value.toLocaleLowerCase();const filtered=data.filter(c=>(c.Nom||'').toLocaleLowerCase().includes(q)&&(!sector.value||c.Secteur===sector.value));count.textContent=filtered.length+' entreprise(s) trouvée(s)';table.replaceChildren(...filtered.map(c=>h('tr',{},h('td',{},h('strong',{},c.Nom),h('div',{class:'meta'},c.Adresse)),h('td',{},badge(c.Secteur||'Autre')),h('td',{},c['Téléphone']||'—',h('div',{class:'meta'},c.Emails||'Email non renseigné')),h('td',{},h('div',{class:'actions'},link('Site ↗',c['Site Web']),link('Maps ↗',c['Google Maps']))),h('td',{},c.Emails?button('Préparer un CV',()=>companyDialog(c),false,'send'):badge('Sans email','gray')))));}
 search.oninput=sector.onchange=render;
 main.append(h('div',{class:'toolbar'},search,sector),count,panel(null,h('div',{class:'table-wrap'},h('table',{},h('thead',{},h('tr',{},['Entreprise','Secteur','Coordonnées','Liens','Action'].map(t=>h('th',{},t)))),table))));render();
}
function offerCard(o,match=null){
 const company=o.entreprise_nom||'Entreprise non renseignée';const level=match?(match.score>=70?'Correspondance forte':match.score>=40?'Correspondance partielle':'Correspondance faible'):'';const availability=o.availability==='active'?badge('Active','green'):o.availability==='expired'?badge('Expirée','amber'):badge('Validité inconnue','gray');const card=h('article',{class:'panel offer'},h('div',{class:'score-row'},badge(o.source||'Stagiaires.ma','gray'),match?h('div',{},h('div',{class:'score'},match.score,h('small',{},' / 100')),badge(level,match.score>=70?'green':'amber')):badge(o['Type contrat']||'Offre','green')),h('h3',{},o.Titre||'Offre sans titre'),h('div',{class:'meta'},company+' · '+(o.ville||'Localisation non renseignée')),h('div',{class:'chips'},availability,badge(o['Type stage']||'Stage non précisé'),badge(formatDate(o['Date publication']),'gray'),o.collected_at?badge('Importée le '+formatDate(o.collected_at),'gray'):null));
 if(match){card.append(h('p',{class:'subtle'},match.explanation),h('div',{class:'chips'},match.matched.map(s=>badge(s,'green')),match.missing.slice(0,8).map(s=>badge('À développer : '+s,'amber'))),h('p',{class:'meta'},match.recommendation));const det=h('details',{},h('summary',{},'Comprendre le score'),h('div',{class:'match-components'},Object.entries(match.contributions).map(([k,v])=>h('div',{},({skills:'Compétences',education:'Formation / domaine',experience:'Expérience / projets',location:'Localisation',opportunity:'Type d’opportunité'})[k],h('span',{},v+' / '+match.weights[k])))));if(match.uncertain)det.append(h('p',{class:'meta'},'Estimation incertaine : description, compétences ou localisation insuffisantes. '+match.limitations));card.append(det);}else card.append(h('p',{class:'desc'},cleanDescription(o.Description)));
 card.append(h('div',{class:'actions'},link('Voir l’offre ↗',o.application_url||o['Lien public']||o['Lien annonce'],'btn'),button('Postuler',()=>applicationDialog(o.ID),true,'send')));return card;
}
```

**Lecture des instructions principales :**
- `backend/api.py:94-95` exécute la lecture locale et expose `rowid` comme identifiant API.
- `dashboard/js/ui.js:85-96` construit les lignes et les contrôles de recherche dans le navigateur.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: lire le répertoire et afficher les fiches via l’api locale.

**Tests associés.** tests/test_application.py::test_pages_connected. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Rechercher une entreprise et expliquer les champs manquants indiqués dans le rapport de données.

**Phrase possible.** « La page consomme une API locale, tandis que les données restent dans SQLite. »

## 4. Offres

**Objectif.** Lister et trier les offres, contrôler l’URL et calculer un état depuis l’expiration.

**Technologies.** Flask, SQLite, validation URL.

**Données / tables.** offres, entreprises.

**Fichiers, symboles et extraits source.**

- `backend/api.py:98-110` — `offers`. Tri, URL de candidature, disponibilité et type.

```python
def offers():
    values = rows(config()['DATABASE'], 'SELECT * FROM offres ORDER BY "Date publication" DESC')
    for o in values:
        o['application_url'] = safe_url(o.get('Lien public')) or safe_url(o.get('Lien annonce'))
        expiry = str(o.get('Date expiration') or '')[:10]
        try:
            o['availability'] = 'active' if date.fromisoformat(expiry) >= date.today() else 'expired'
        except ValueError:
            o['availability'] = 'unknown'
        o['statut_offre']=o['availability']
        o.update(classify_offer(o))
    priority = {'active': 0, 'unknown': 1, 'expired': 2}
    return sorted(values, key=lambda o: priority[o['availability']])
```

**Lecture des instructions principales :**
- `backend/api.py:98-101` lit les offres triées par date puis choisit une URL publique sûre.
- `backend/api.py:102-107` calcule le statut à partir de la date d’expiration; une date invalide devient `unknown`.
- `backend/api.py:108-110` classe les types et donne priorité à une offre active.

- `dashboard/js/ui.js:97-104` — `repère fonctionnel vérifié dans le fichier`. Rendu de la page d’offres.

```javascript
async function offersPage(){
 const data=await api('/offres');title('Trouvez votre prochaine opportunité','Des stages et premiers emplois, avec un parcours de candidature transparent.',navlink('Matching IA','matching.html',true,'spark'));
 const search=h('input',{placeholder:'Titre ou mot-clé…','aria-label':'Rechercher une offre',value:new URLSearchParams(location.search).get('q')||''}),stage=select([...new Set(data.map(o=>o['Type stage']).filter(Boolean))].sort(),'Tous les types fournis'),contract=select([...new Set(data.map(o=>o['Type contrat']).filter(Boolean))].sort(),'Tous les contrats'),locationFilter=select([['','Toutes les villes'],['Marrakech','Marrakech'],['Maroc','Autres villes du Maroc']],'Tous les lieux'),kind=select([['','Stage ou emploi'],['stage','Stage'],['stage_pfe','Stage PFE'],['stage_initiation','Stage d’initiation'],['stage_technique','Stage technique'],['premier_emploi','Premier emploi'],['inconnu','Type inconnu']],'Tous les types'),domain=select([['','Tous les secteurs'],['informatique','Informatique'],['data_science','Data Science / IA'],['developpement','Développement'],['marketing','Marketing']],'Tous les secteurs'),paid=select([['','Rémunération non filtrée'],['true','Rémunération indiquée']],'Toutes rémunérations'),count=h('p',{class:'section-info'}),cards=h('div',{class:'cards-grid'});
 function render(){const q=search.value.toLocaleLowerCase();const found=data.filter(o=>(o.Titre||'').toLocaleLowerCase().includes(q)&&(!stage.value||stage.value===o['Type stage'])&&(!contract.value||contract.value===o['Type contrat'])&&(!locationFilter.value||(locationFilter.value==='Maroc'?o.is_morocco:o.location_group===locationFilter.value))&&(!kind.value||o.opportunity_type===kind.value||o.internship_subtype===kind.value)&&(!domain.value||o.domain_group===domain.value)&&(!paid.value||o.paid===true));count.textContent=found.length+' offre(s) · Classification expliquée; les informations inconnues ne sont pas supposées';cards.replaceChildren(...found.map(o=>offerCard(o)));if(!found.length)cards.append(empty('Aucune offre pour ces filtres','Essayez un autre mot-clé ou élargissez les filtres.'));}
 search.oninput=stage.onchange=contract.onchange=locationFilter.onchange=kind.onchange=domain.onchange=paid.onchange=render;main.append(h('div',{class:'toolbar'},search,stage,contract,locationFilter,kind,domain,paid),count,cards);render();
}

async function applicationDialog(id){
```

**Lecture des instructions principales :**
- `backend/api.py:98-101` lit les offres triées par date puis choisit une URL publique sûre.
- `backend/api.py:102-107` calcule le statut à partir de la date d’expiration; une date invalide devient `unknown`.
- `backend/api.py:108-110` classe les types et donne priorité à une offre active.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: lister et trier les offres, contrôler l’url et calculer un état depuis l’expiration.

**Tests associés.** tests/test_application.py::test_offers_prioritize_active_and_label_expired_or_unknown. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Montrer un lien et préciser que les annonces historiques ne sont pas vérifiées en temps réel.

**Phrase possible.** « Le statut visible est dérivé des dates enregistrées et ne garantit pas que l’annonce existe encore. »

## 5. Connecteurs API/RSS

**Objectif.** Extraire des réponses d’API et de flux configurés, en bornant les requêtes.

**Technologies.** requests, JSON/RSS, HTTPS, connecteurs mockables.

**Données / tables.** collector_runs, collector_source_runs, collector_staging.

**Fichiers, symboles et extraits source.**

- `backend/collectors/platforms.py:23-56` — `_request, parse_greenhouse`. Requête partagée et parseur Greenhouse.

```python
def _request(session, url, params=None):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in {
        'boards-api.greenhouse.io', 'api.lever.co', 'api.eu.lever.co',
        'api.ashbyhq.com', 'api.smartrecruiters.com'
    } or parsed.username or parsed.password:
        raise ValueError('URL du connecteur externe refusée.')
    response = session.get(url, params=params, timeout=TIMEOUT, allow_redirects=False,
                           headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    if 300 <= response.status_code < 400:
        raise ValueError('Redirection du connecteur refusée.')
    response.raise_for_status()
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError('Réponse du connecteur trop volumineuse.')
    return response


def parse_greenhouse(data, company, source):
    jobs = data.get('jobs') if isinstance(data, dict) else None
    if not isinstance(jobs, list):
        raise ValueError('Réponse Greenhouse invalide.')
    result = []
    for raw in jobs[:PAGE_SIZE * MAX_PAGES]:
        if not isinstance(raw, dict):
            continue
        location = raw.get('location') or {}
        item = normalize_offer({'source_id': raw.get('id'), 'title': raw.get('title'),
            'company': company, 'city': location.get('name') if isinstance(location, dict) else location,
            'description': raw.get('content'), 'published_at': raw.get('updated_at'),
            'job_url': raw.get('absolute_url') or raw.get('url'),
            'apply_url': raw.get('applyUrl') or raw.get('absolute_url') or raw.get('url')}, source)
        if item:
            result.append(item)
    return result
```

**Lecture des instructions principales :**
- `platforms.py:23-37` construit une URL HTTPS sur un hôte fixe, applique timeout et limite de réponse.
- `platforms.py:40-56` parse Greenhouse vers les champs canoniques.
- `collectors/service.py:48-98` valide séparément fréquence, permissions, URL, identifiant et source activée.
- `collectors/service.py:139-205` journalise les réponses et erreurs par source.

- `backend/collectors/jawb.py:17-64` — `_safe_jawb_url, _request, _local, parse_rss, fetch_rss`. Validation de l’URL et parsing RSS.

```python
def _safe_jawb_url(value):
    url = urljoin(BASE + '/', value)
    p = urlparse(url)
    return p.scheme == 'https' and p.hostname == 'jawb.ma' and p.username is None and p.password is None


def _request(session, url, params=None):
    if not _safe_jawb_url(url):
        raise ValueError('Redirection hors du domaine Jawb refusée.')
    response = session.get(url, params=params, timeout=TIMEOUT, allow_redirects=False,
                           headers={'User-Agent': USER_AGENT, 'Accept': 'application/json, application/rss+xml, application/xml'})
    if 300 <= response.status_code < 400:
        raise ValueError('Redirection inattendue du flux Jawb.')
    response.raise_for_status()
    if len(response.content) > 4_000_000:
        raise ValueError('Réponse Jawb trop volumineuse.')
    return response


def _local(element):
    return element.tag.rsplit('}', 1)[-1].lower()


def parse_rss(xml_text):
    root = ET.fromstring(xml_text)
    items = [node for node in root.iter() if _local(node) in ('item', 'entry')]
    result = []
    for node in items[:50]:
        values = {}
        for child in node:
            key = _local(child)
            if key == 'link':
                values[key] = child.attrib.get('href') or (child.text or '').strip()
            elif key in ('title','description','summary','content','pubdate','published','updated','guid','id'):
                values[key] = child.text or ''
        result.append({'title': values.get('title'), 'description': values.get('description') or values.get('summary') or values.get('content'),
                       'url': values.get('link') or values.get('guid') or values.get('id'), 'source_id': values.get('guid') or values.get('id') or values.get('link'),
                       'published_at': values.get('pubdate') or values.get('published') or values.get('updated')})
    return result


def fetch_rss(session=None, city='Marrakech', profession=''):
    session = session or requests.Session()
    params = {'ville': city}
    if profession:
        params['metier'] = profession
    response = _request(session, BASE + '/rss.xml', params=params)
    return [o for raw in parse_rss(response.text) if (o := normalize_offer(raw, 'Jawb RSS'))]
```

**Lecture des instructions principales :**
- `platforms.py:23-37` construit une URL HTTPS sur un hôte fixe, applique timeout et limite de réponse.
- `platforms.py:40-56` parse Greenhouse vers les champs canoniques.
- `collectors/service.py:48-98` valide séparément fréquence, permissions, URL, identifiant et source activée.
- `collectors/service.py:139-205` journalise les réponses et erreurs par source.

- `backend/collectors/service.py:48-98` — `set_sources_config`. Permissions et activation de source.

```python
def set_sources_config(path, values):
    allowed = {'external_enabled','auto_enabled','frequency','jawb_rss_enabled','jawb_import_approved','jawb_consult_allowed','jawb_storage_allowed','jawb_display_allowed','jawb_permission_ref','career_import_approved','jawb_company_ids','career_feeds','career_boards'}
    with connect(path) as db:
        for key, value in values.items():
            if key not in allowed:
                continue
            if key in ('external_enabled','auto_enabled','jawb_rss_enabled','jawb_import_approved','jawb_consult_allowed','jawb_storage_allowed','jawb_display_allowed','career_import_approved') and type(value) is not bool:
                raise ValueError(f'Paramètre invalide : {key}.')
            if key == 'frequency' and value not in ('daily','weekly'):
                raise ValueError('Fréquence de collecte invalide.')
            if key == 'jawb_company_ids':
                if not isinstance(value,list) or len(value)>50 or any(not isinstance(v,str) or len(v)>120 for v in value):
                    raise ValueError('Identifiants Jawb invalides.')
            if key == 'career_feeds':
                if not isinstance(value,list) or len(value)>20 or any(not isinstance(v,dict) or len(str(v.get('name','')))>100 or len(str(v.get('url','')))>500 or len(str(v.get('permission_ref','')))>500 for v in value):
                    raise ValueError('Liste de flux carrière invalide.')
                for feed in value:
                    parsed=urlsplit(str(feed.get('url') or ''))
                    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:
                        raise ValueError('Chaque flux carrière doit utiliser une URL HTTPS publique sans identifiants intégrés.')
                    if any(type(feed.get(k,False)) is not bool for k in ('consultation_allowed','storage_allowed','display_allowed')):
                        raise ValueError('Les trois périmètres d’autorisation du flux carrière doivent être des cases distinctes.')
            if key == 'career_boards':
                if not isinstance(value, list) or len(value) > 100:
                    raise ValueError('Registre de sites carrières invalide (100 sources maximum).')
                required = ('name','official_url','career_url','platform','board_id','city','sector','permission_ref')
                for board in value:
                    if not isinstance(board, dict) or any(not isinstance(board.get(field, ''), str) or len(board.get(field, '')) > 500 for field in required):
                        raise ValueError('Champs du registre carrière invalides.')
                    if board.get('platform') not in ('greenhouse','lever','ashby','smartrecruiters','rss'):
                        raise ValueError('Plateforme ATS inconnue.')
                    if board.get('platform')!='rss' and not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', board.get('board_id','')):
                        raise ValueError('Identifiant de job board invalide.')
                    for url_key in ('official_url','career_url'):
                        parsed = urlsplit(board.get(url_key, ''))
                        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                            raise ValueError('Les URL officielles et carrières doivent être HTTPS, sans identifiants.')
                    for flag in ('consultation_allowed','storage_allowed','display_allowed','enabled'):
                        if type(board.get(flag, False)) is not bool:
                            raise ValueError('Les droits et l’activation de chaque entreprise doivent être explicites.')
                    if board.get('enabled') and (not board.get('permission_ref').strip() or not all(board.get(k) for k in ('consultation_allowed','storage_allowed','display_allowed'))):
                        raise ValueError('Une source ne peut être activée sans référence et trois droits attestés.')
                    if board.get('platform')=='lever' and board.get('region','global') not in ('global','eu'):
                        raise ValueError('Région Lever invalide.')
                    if board.get('last_verified_at'):
                        try:datetime.fromisoformat(board['last_verified_at'])
                        except ValueError:raise ValueError('Date de vérification de la source invalide.')
            if key=='jawb_permission_ref' and (not isinstance(value,str) or len(value)>500):
                raise ValueError('Référence de l’autorisation Jawb invalide.')
            set_setting(db,key,value)
    return sources_config(path)
```

**Lecture des instructions principales :**
- `platforms.py:23-37` construit une URL HTTPS sur un hôte fixe, applique timeout et limite de réponse.
- `platforms.py:40-56` parse Greenhouse vers les champs canoniques.
- `collectors/service.py:48-98` valide séparément fréquence, permissions, URL, identifiant et source activée.
- `collectors/service.py:139-205` journalise les réponses et erreurs par source.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: extraire des réponses d’api et de flux configurés, en bornant les requêtes.

**Tests associés.** tests/test_phase5.py; tests/test_phase8.py. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Parcourir une fixture de test; ne pas lancer de récupération externe sans autorisation.

**Phrase possible.** « Le connecteur existe, mais seules une permission et une exécution enregistrée prouvent l’usage réel. »

## 6. Import CSV/XLSX

**Objectif.** Lire un export remis, appliquer un mapping et produire un aperçu à valider.

**Technologies.** Pandas/openpyxl, API multipart, staging.

**Données / tables.** collector_staging puis offres.

**Fichiers, symboles et extraits source.**

- `backend/api.py:491-503` — `collect_provided_offers_preview`. Réception du fichier et du mapping.

```python
@api.post('/collect/offers/file/preview')
def collect_provided_offers_preview():
    upload=request.files.get('file')
    if upload is None or not upload.filename:raise ValueError('Sélectionnez un fichier CSV ou Excel.')
    try:mapping=json.loads(request.form.get('mapping') or '{}')
    except (TypeError,ValueError):raise ValueError('Mapping de colonnes JSON invalide.')
    if not isinstance(mapping,dict):raise ValueError('Le mapping doit être un objet colonne → champ.')
    value=stage_provided_file(config()['DATABASE'],upload.filename,upload.read(),
        request.form.get('source_name'),request.form.get('permission_ref'),
        request.form.get('consultation_allowed')=='true',request.form.get('storage_allowed')=='true',
        request.form.get('display_allowed')=='true',mapping)
    value['run']=run_details(config()['DATABASE'],value['id'])
    return jsonify(value),201
```

**Lecture des instructions principales :**
- `api.py:491-503` reçoit le fichier et le mapping, puis place le contenu en aperçu.
- `provided_offers.py:67-90` lit les lignes et convertit les colonnes choisies.
- `provided_offers.py:120-169` enregistre l’aperçu comme staging et ne crée pas directement une offre validée.

- `backend/collectors/provided_offers.py:67-90` — `parse_provided_offers`. Lecture et normalisation du tableau fourni.

```python
def parse_provided_offers(filename, content, source_name, mapping=None, include_report=False):
    source = str(source_name or '').strip()
    if len(source) < 3 or len(source) > 60:
        raise ValueError('Indiquez le nom du producteur ou de l’organisme (3 à 60 caractères).')
    raw = _rows(filename, content)
    if len(raw) > 10000:
        raise ValueError('Le fichier dépasse la limite de 10 000 lignes.')
    if not raw:
        raise ValueError('Le fichier ne contient aucune annonce.')
    custom={}
    for header,target in (mapping or {}).items():
        target=str(target or '').strip()
        if target not in TARGET_FIELDS:
            raise ValueError(f'Champ de destination invalide dans le mapping : {target}.')
        custom[_header(header)]=TARGET_FIELDS[target]
    offers, errors = [], []
    headers=list(raw[0].keys()) if raw else []
    recognized={str(header):custom.get(_header(header)) or ALIASES.get(_header(header)) for header in headers}
    for line, row in enumerate(raw, 2):
        fields = {}
        for key, value in row.items():
            normalized_key = _header(key)
            field = custom.get(normalized_key) or ALIASES.get(normalized_key)
            if field:
```

**Lecture des instructions principales :**
- `api.py:491-503` reçoit le fichier et le mapping, puis place le contenu en aperçu.
- `provided_offers.py:67-90` lit les lignes et convertit les colonnes choisies.
- `provided_offers.py:120-169` enregistre l’aperçu comme staging et ne crée pas directement une offre validée.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: lire un export remis, appliquer un mapping et produire un aperçu à valider.

**Tests associés.** tests/test_phase7.py provided-file tests; tests/test_phase8.py CSV/XLSX tests. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Utiliser un fichier de démonstration fictif sur base temporaire.

**Phrase possible.** « L’aperçu contrôle les colonnes; une décision humaine précède l’écriture en base. »

## 7. Nettoyage et normalisation

**Objectif.** Nettoyer texte, URL, date et schéma canonique sans inventer les valeurs manquantes.

**Technologies.** Python, regex, datetime, Pandas pour les anciens fichiers Excel.

**Données / tables.** payload de staging puis offres.

**Fichiers, symboles et extraits source.**

- `backend/collectors/schema.py:18-47` — `canonical_url, parse_date`. Nettoyage du texte, URL canonique et parsing de dates.

```python
    return re.sub(r'\s+', ' ', value).strip()[:limit]


def canonical_url(value):
    if not value:
        return ''
    try:
        parts = urlsplit(str(value).strip())
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
            return ''
        host = parts.hostname.lower().removeprefix('www.')
        path = re.sub('/+$', '', parts.path or '/')
        return urlunsplit(('https', host, path, '', ''))
    except ValueError:
        return ''


def parse_date(value):
    if not value:
        return None
    if isinstance(value,(int,float)) and value>0:
        try:
            from datetime import timedelta
            seconds=float(value)/1000 if value>10**11 else float(value)
            return (datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(seconds=seconds)).isoformat(timespec='seconds')
        except (OverflowError,ValueError):return None
    value = str(value).strip()
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
```

**Lecture des instructions principales :**
- `schema.py:18-22` retire les balises, décode le texte et borne sa longueur.
- `schema.py:25-36` accepte uniquement les URL HTTPS sans identifiants et enlève les paramètres pour l’identité canonique.
- `schema.py:39-55` parse les dates connues et renvoie `None` si elles ne sont pas interprétables.
- `validation.py:21-27` refuse les schémas URL qui ne sont pas publics et sûrs.

- `backend/validation.py:21-27` — `safe_url`. Validation des liens sûrs.

```python
def safe_url(value):
    if not isinstance(value, str):
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme in ('https', 'http') and parsed.hostname and not parsed.username and not parsed.password:
        return value.strip()
    return None
```

**Lecture des instructions principales :**
- `schema.py:18-22` retire les balises, décode le texte et borne sa longueur.
- `schema.py:25-36` accepte uniquement les URL HTTPS sans identifiants et enlève les paramètres pour l’identité canonique.
- `schema.py:39-55` parse les dates connues et renvoie `None` si elles ne sont pas interprétables.
- `validation.py:21-27` refuse les schémas URL qui ne sont pas publics et sûrs.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: nettoyer texte, url, date et schéma canonique sans inventer les valeurs manquantes.

**Tests associés.** tests/test_phase5.py invalid RSS; tests/test_phase8.py mapping/date/URL tests. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Montrer le rejet d’une URL HTTP ou d’une date mal formée dans les fixtures.

**Phrase possible.** « Une valeur inconnue reste inconnue; le nettoyage ne fabrique ni date ni coordonnées. »

## 8. SQLite et migrations

**Objectif.** Ouvrir la base, gérer les transactions, créer une sauvegarde et faire évoluer le schéma.

**Technologies.** sqlite3, PRAGMA, transactions.

**Données / tables.** 19 tables de la base privée, dont entreprises, offres et candidatures.

**Fichiers, symboles et extraits source.**

- `backend/db.py:13-34` — `backup_database, connect`. Sauvegarde cohérente et connexion SQLite.

```python
def backup_database(path, backup_dir, label='avant_import'):
    target_dir=Path(backup_dir);target_dir.mkdir(parents=True,exist_ok=True)
    target=target_dir/f'{label}_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.db'
    source=sqlite3.connect(path,timeout=15);destination=sqlite3.connect(target)
    try:source.backup(destination)
    finally:destination.close();source.close()
    return target


@contextmanager
def connect(path):
    con = sqlite3.connect(path, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
```

**Lecture des instructions principales :**
- `db.py:13-19` utilise le mécanisme de sauvegarde SQLite plutôt qu’une copie brute pendant un accès concurrent.
- `db.py:23-34` ouvre une connexion et configure les options du fichier.
- `db.py:37-92` déduit les migrations appliquées, sauvegarde avant une évolution et met à jour le schéma.

- `backend/db.py:37-92` — `migrate`. Migrations et index de base.

```python
def migrate(path, backup_dir):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        version = db.execute('PRAGMA user_version').fetchone()[0]
        if version >= 1:
            return
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        target = Path(backup_dir) / ('avant_migration_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.db')
        backup = sqlite3.connect(target)
        db.backup(backup)
        backup.close()
        db.execute('BEGIN IMMEDIATE')
        if db.execute('PRAGMA user_version').fetchone()[0] >= 1:
            return
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='entreprises'").fetchone():
            raise RuntimeError('Base initiale entreprises/offres absente. Restaurer la base livrée avant de démarrer.')
        db.execute('''CREATE TABLE IF NOT EXISTS candidatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nom_entreprise TEXT, secteur TEXT,
            email TEXT, telephone TEXT, date_candidature TEXT, statut TEXT, commentaire TEXT)''')
        additions = {
            'entreprises': {'place_id': 'TEXT', 'latitude': 'REAL', 'longitude': 'REAL', 'geo_verified_at': 'TEXT',
                            'geo_source': 'TEXT', 'quartier': 'TEXT', 'ville': 'TEXT'},
            'offres': {'source': "TEXT DEFAULT 'Stagiaires.ma'", 'entreprise_nom': 'TEXT', 'entreprise_ref': 'INTEGER',
                       'relation_verified': 'INTEGER DEFAULT 0', 'ville': 'TEXT', 'recruitment_email': 'TEXT',
                       'email_verified': 'INTEGER DEFAULT 0'},
            'candidatures': {'offre_id': 'INTEGER', 'offre_titre': 'TEXT', 'cv_id': 'INTEGER', 'source': 'TEXT',
                             'canal': 'TEXT', 'updated_at': 'TEXT', 'created_at': 'TEXT', 'email_validated': 'INTEGER DEFAULT 0'},
        }
        for table, columns in additions.items():
            existing = {r['name'] for r in db.execute(f'PRAGMA table_info({table})')}
            for name, typ in columns.items():
                if name not in existing:
                    db.execute(f'ALTER TABLE {table} ADD COLUMN {name} {typ}')
        schema = '''
        CREATE TABLE IF NOT EXISTS cvs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, template TEXT NOT NULL,
            payload BLOB NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS candidature_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, candidature_id INTEGER NOT NULL,
            old_status TEXT, new_status TEXT NOT NULL, changed_at TEXT NOT NULL,
            FOREIGN KEY(candidature_id) REFERENCES candidatures(id));
        CREATE TABLE IF NOT EXISTS send_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, idempotency_key TEXT UNIQUE NOT NULL,
            payload_hash TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
            candidature_id INTEGER, error_code TEXT);
        CREATE INDEX IF NOT EXISTS idx_candidatures_offre ON candidatures(offre_id);
        CREATE INDEX IF NOT EXISTS idx_history_candidature ON candidature_history(candidature_id);
        '''
        for statement in schema.split(';'):
            if statement.strip():
                db.execute(statement)
        timestamp = now()
        db.execute('UPDATE candidatures SET updated_at=COALESCE(updated_at,?),created_at=COALESCE(created_at,?)', (timestamp, timestamp))
        db.execute('''INSERT INTO candidature_history(candidature_id,old_status,new_status,changed_at)
                      SELECT id,NULL,COALESCE(statut,'Non envoyée'),? FROM candidatures''', (timestamp,))
        db.execute('PRAGMA user_version=1')
```

**Lecture des instructions principales :**
- `db.py:13-19` utilise le mécanisme de sauvegarde SQLite plutôt qu’une copie brute pendant un accès concurrent.
- `db.py:23-34` ouvre une connexion et configure les options du fichier.
- `db.py:37-92` déduit les migrations appliquées, sauvegarde avant une évolution et met à jour le schéma.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: ouvrir la base, gérer les transactions, créer une sauvegarde et faire évoluer le schéma.

**Tests associés.** tests/test_application.py::test_migration_preserves_five_and_is_idempotent. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Ouvrir la base en lecture seule et montrer `integrity_check`.

**Phrase possible.** « SQLite confirme l’intégrité de ce fichier, tandis que les relations non déclarées doivent être vérifiées côté application. »

## 9. Dashboard Dash

**Objectif.** Calculer des indicateurs depuis SQLite et les actualiser selon les filtres.

**Technologies.** Dash, Plotly, Pandas.

**Données / tables.** entreprises, offres, candidatures.

**Fichiers, symboles et extraits source.**

- `backend/analytics.py:15-38` — `load_data`. Chargement des données depuis le chemin configuré.

```python
def load_data(path, tab, sector=None, stage=None, contract=None, start=None, end=None, company=None):
    table = {'companies': 'entreprises', 'offers': 'offres', 'applications': 'candidatures'}[tab]
    if tab=='offers':
        data=rows(path, '''SELECT offres.*,
            CASE WHEN COALESCE(offres.relation_verified,0)=1 THEN entreprises."Secteur" ELSE NULL END AS secteur
            FROM offres LEFT JOIN entreprises ON offres.entreprise_ref=entreprises.rowid AND COALESCE(offres.relation_verified,0)=1''')
    else:
        data=rows(path, f'SELECT * FROM {table}')
    df = pd.DataFrame(data)
    if df.empty:
        return df
    for column, value in [('Secteur' if tab == 'companies' else 'secteur', sector), ('Type stage', stage), ('Type contrat', contract),
                          ('Nom' if tab == 'companies' else 'nom_entreprise' if tab == 'applications' else 'entreprise_nom', company)]:
        if column in df.columns and value:
            df = df[df[column] == value]
    date_col = 'Date publication' if tab == 'offers' else 'date_candidature' if tab == 'applications' else None
    if date_col:
        dates = pd.to_datetime(df[date_col], errors='coerce', utc=True)
        if start:
            df = df[dates >= pd.Timestamp(start, tz='UTC')]
            dates = dates.loc[df.index]
        if end:
            df = df[dates < pd.Timestamp(end, tz='UTC')+pd.Timedelta(days=1)]
    return df
```

**Lecture des instructions principales :**
- `analytics.py:15-38` lit les tables avec le chemin configuré et sélectionne les filtres.
- `analytics.py:114-140` monte Dash sur Flask à `/analytics/` et construit le layout.
- `analytics.py:158-180` recalcule les indicateurs et la figure selon les filtres.
- `analytics.py:182-190` exporte les données filtrées et réinitialise les filtres.

- `backend/analytics.py:114-180` — `mount_dash, options, update`. Montage Dash et callbacks de filtre/KPI.

```python
def mount_dash(server):
    app = Dash(__name__, server=server, routes_pathname_prefix='/analytics/',
               requests_pathname_prefix='/analytics/', title='Analyses • Stages Marrakech',
               external_stylesheets=['/css/analytics.css'], serve_locally=True)
    path = server.config['DATABASE']
    origin_notice = dataset_notice(path, server.config.get('PUBLIC_DEMO_MODE', False))
    app.layout = html.Main([
        html.Div([html.Div([html.Small('EXPLORATEUR DE DONNÉES'), html.H1('Comprendre vos opportunités'),
                           html.P(origin_notice, className='data-origin')]),
                  html.A('← Retour à l’application', href='/index.html', target='_top', className='back')], className='dash-head'),
        html.Div(id='kpis', className='dash-kpis'),
        dcc.Tabs(id='dataset', value='offers', children=[dcc.Tab(label='Offres', value='offers'), dcc.Tab(label='Entreprises', value='companies'), dcc.Tab(label='Candidatures', value='applications')]),
        html.Div([
            html.Label(['Indicateur', dcc.Dropdown(id='metric', clearable=False)]),
            html.Label(['Secteur', dcc.Dropdown(id='sector', placeholder='Tous les secteurs')]),
            html.Label(['Type de stage', dcc.Dropdown(id='stage', placeholder='Tous les stages')]),
            html.Label(['Contrat', dcc.Dropdown(id='contract', placeholder='Tous les contrats')]),
            html.Label(['Entreprise connue', dcc.Dropdown(id='company', placeholder='Toutes les entreprises')]),
            html.Label(['Période', dcc.DatePickerRange(id='dates', display_format='DD/MM/YYYY', start_date_placeholder_text='Début', end_date_placeholder_text='Fin')]),
        ], className='dash-filters'),
        dcc.RadioItems(id='kind', value='bar', inline=True, options=[{'label': l, 'value': v} for l,v in [('Barres','bar'),('Courbe','line'),('Camembert','pie'),('Scatter','scatter'),('Histogramme','histogram')]], className='kinds'),
        dcc.Loading(dcc.Graph(id='graph', config={'displaylogo': False, 'toImageButtonOptions': {'format': 'png', 'filename': 'analyse_stages'}})),
        html.Div(id='quality', className='quality'),
        html.Div([html.Button('Exporter les données filtrées (CSV)', id='export', n_clicks=0),
                  html.Button('Actualiser', id='refresh', n_clicks=0)], className='dash-actions'),
        dcc.Download(id='download'), dcc.Interval(id='tick', interval=60000, n_intervals=0),
    ], className='dash-main')

    @app.callback(Output('metric','options'), Output('metric','value'), Output('sector','options'), Output('sector','disabled'),
                  Output('stage','options'), Output('stage','disabled'), Output('contract','options'), Output('contract','disabled'),
                  Output('company','options'), Output('company','disabled'), Output('dates','disabled'),
                  Input('dataset','value'), Input('refresh','n_clicks'))
    def options(tab, refresh):
        df = load_data(path, tab)
        fields = {'companies': ['Secteur'], 'offers': ['Type stage','Type contrat','Date publication'], 'applications': ['statut','date_candidature','nom_entreprise']}[tab]
        metrics = [{'label': c, 'value': c} for c in fields if c in df.columns]
        result = [metrics, metrics[0]['value'] if metrics else None]
        for column in [('Secteur' if tab=='companies' else 'secteur'), 'Type stage', 'Type contrat',
                       ('Nom' if tab=='companies' else 'nom_entreprise' if tab=='applications' else 'entreprise_nom')]:
            values = sorted(df[column].dropna().astype(str).unique()) if column in df else []
            result += [[{'label': v,'value':v} for v in values if v], not bool(values)]
        result += [tab == 'companies']
        return result

    @app.callback(Output('graph','figure'), Output('kpis','children'), Output('quality','children'),
                  Input('dataset','value'), Input('metric','value'), Input('kind','value'), Input('sector','value'),
                  Input('stage','value'), Input('contract','value'), Input('dates','start_date'), Input('dates','end_date'),
                  Input('company','value'), Input('refresh','n_clicks'), Input('tick','n_intervals'))
    def update(tab, metric, kind, sector, stage, contract, start, end, company, refresh, tick):
        df = load_data(path, tab, sector, stage, contract, start, end, company)
        counts = {t: len(rows(path, f'SELECT rowid FROM {t}')) for t in ['entreprises','offres','candidatures']}
        counts[{'companies':'entreprises','offers':'offres','applications':'candidatures'}[tab]]=len(df)
        applications = ([{'statut':value} for value in df['statut'].tolist()] if tab=='applications' and 'statut' in df
                        else rows(path, 'SELECT statut FROM candidatures'))
        contacted = sum(a['statut'] in ('Envoyée','Relancée','Entretien','Acceptée','Refusée') for a in applications)
        response = sum(a['statut'] in ('Entretien','Acceptée','Refusée') for a in applications)
        kpis = [html.Div([html.Small(label),html.Strong(str(value))], className='dash-kpi') for label,value in [
            ('Entreprises',counts['entreprises']),('Offres',counts['offres']),('Candidatures',counts['candidatures']),
            ('Taux de réponse', f'{response/contacted*100:.1f} %' if contacted else 'Non calculable')]]
        quality = [html.P(f'{len(df)} ligne(s) dans le jeu actif après filtres. Les autres compteurs restent des totaux SQLite.')]
        quality.extend(html.P(item) for item in quality_summary(tab,df))
        quality.append(html.P('Taux de réponse : statuts Entretien, Acceptée ou Refusée / candidatures ayant quitté Non envoyée ; calcul selon le statut actuel.'
                              + (' Le taux utilise les candidatures du filtre actif.' if tab=='applications' else ' Le taux est calculé sur toutes les candidatures.')))
        if not df.empty:
            missing = df.isna().sum()
            quality.append(html.P('Valeurs manquantes : '+', '.join(f'{k} ({v})' for k,v in missing.items() if v)[:1800]))
        return figure_for(df,metric,kind), kpis, quality
```

**Lecture des instructions principales :**
- `analytics.py:15-38` lit les tables avec le chemin configuré et sélectionne les filtres.
- `analytics.py:114-140` monte Dash sur Flask à `/analytics/` et construit le layout.
- `analytics.py:158-180` recalcule les indicateurs et la figure selon les filtres.
- `analytics.py:182-190` exporte les données filtrées et réinitialise les filtres.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: calculer des indicateurs depuis sqlite et les actualiser selon les filtres.

**Tests associés.** tests/test_application.py::test_dash_real_routes_and_callbacks; tests/test_analytics_dashboard.py. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Ouvrir `/analytics/`, changer un filtre et vérifier que les KPI correspondent à la base.

**Phrase possible.** « Dash est monté sur Flask et lit le même profil de base SQLite. »

## 10. Matching IA

**Objectif.** Classer des offres selon les compétences et critères d’un profil, avec explication.

**Technologies.** Python, similarité cosinus locale et pondérations configurées.

**Données / tables.** offres; CV sélectionné ou profil transmis.

**Fichiers, symboles et extraits source.**

- `backend/matching.py:56-101` — `cosine, rank, vector`. Mesure de similarité et classement pondéré.

```python
def cosine(a, b, corpus):
    aa, bb = Counter(tokens(a)), Counter(tokens(b))
    if not aa or not bb:
        return 0.0
    sets = [set(tokens(c)) for c in corpus]
    def vector(counter):
        return {t: n * (math.log((len(sets)+1)/(1+sum(t in s for s in sets)))+1) for t, n in counter.items()}
    va, vb = vector(aa), vector(bb)
    return sum(v * vb.get(t, 0) for t,v in va.items()) / (math.sqrt(sum(v*v for v in va.values())) * math.sqrt(sum(v*v for v in vb.values())))


def rank(profile, offers, weights, interpretations=None):
    profile = validate_profile(profile)
    required = {'skills', 'education', 'experience', 'location', 'opportunity'}
    if set(weights) != required or any(type(v) not in (int, float) or not 0 <= v <= 100 for v in weights.values()) or abs(sum(weights.values())-100) > .01:
        raise ValueError('Les cinq pondérations doivent totaliser 100.')
    corpus = [' '.join([str(o.get('Titre') or ''), str(o.get('Description') or '')]) for o in offers]
    results = []
    for offer, description in zip(offers, corpus):
        requirements = skills_from(description)
        matched = [r for r in requirements if any(canonical(r) == canonical(s) for s in profile['skills'])]
        interpretation = (interpretations or {}).get(str(offer['ID']), {})
        for pair in interpretation.get('pairs', []):
            if pair['offer_skill'] not in matched:
                matched.append(pair['offer_skill'])
            if pair['offer_skill'] not in requirements:
                requirements.append(pair['offer_skill'])
        missing = [r for r in requirements if r not in matched]
        city = offer.get('ville') or ''
        components = {
            'skills': len(matched)/len(requirements) if requirements else 0,
            'education': cosine(profile['education']+' '+profile['domain'], description, corpus),
            'experience': cosine(profile['experience'], description, corpus),
            'location': float(bool(city and profile['location'] and norm(city) == norm(profile['location']))),
            'opportunity': float(bool(profile['opportunity'] and norm(profile['opportunity']) == norm(offer.get('Type contrat') or ''))),
        }
        contributions = {k: round(components[k]*weights[k], 2) for k in weights}
        uncertain = len(tokens(offer.get('Description') or '')) < 30 or not requirements or not city
        results.append({
            'offer': offer, 'score': round(sum(contributions.values()), 1), 'components': {k: round(v*100, 2) for k,v in components.items()},
            'weights': weights, 'contributions': contributions, 'matched': matched, 'missing': missing, 'uncertain': uncertain,
            'explanation': interpretation.get('explanation') or f'{len(matched)} compétence(s) retrouvée(s) sur {len(requirements)} repérée(s). Comparaison textuelle du domaine et des projets.',
            'recommendation': interpretation.get('recommendation') or ('Précisez vos projets liés à '+', '.join(missing[:4])+', uniquement si vous les avez réalisés.' if missing else 'Ajoutez des exemples concrets et vérifiables de vos projets.'),
            'limitations': 'Localisation inconnue : composante à zéro.' if not city else '',
        })
    return sorted(results, key=lambda item: (-item['score'], item['offer']['ID']))
```

**Lecture des instructions principales :**
- `matching.py:56-64` vectorise les ensembles de termes et calcule une similarité cosinus.
- `matching.py:67-82` valide le profil et construit les pondérations.
- `matching.py:83-101` classe les offres et renvoie explication, éléments communs et éléments absents.
- `api.py:390-393` exige un consentement et un résumé inchangé avant de transmettre des informations à Gemini.

- `backend/api.py:379-401` — `matching_preview, matching`. Route locale et consentement Gemini facultatif.

```python
def matching_preview():
    _, _, _, sent, digest = selection(body())
    return jsonify(payload=sent, digest=digest)


@api.post('/matching')
def matching():
    data = body()
    profile, weights, results, sent, digest = selection(data)
    mode, notice = 'local', 'Analyse locale, sans transmission externe.'
    if data.get('mode') == 'gemini':
        if data.get('consent') is not True:
            raise ValueError('Votre consentement explicite est obligatoire avant Gemini.')
        if data.get('digest') != digest:
            raise ValueError('Le profil ou les offres ont changé. Relisez le contenu à transmettre.')
        try:
            interpretations = interpret(config(), sent)
            results = rank(profile, offers(), weights, interpretations)
            mode, notice = 'gemini', 'Gemini a interprété les 8 premières offres de la présélection locale. Scores calculés localement ; les autres offres restent en mode local.'
        except Exception as exc:
            code = getattr(exc, 'code', None)
            notice = ('Quota Gemini atteint (429). ' if code == 429 or '429' in str(exc) else 'Gemini indisponible ou réponse non vérifiable. ') + 'Résultats locaux conservés ; aucune nouvelle tentative automatique.'
    return jsonify(mode=mode, notice=notice, results=results, disclaimer='Score indicatif, pas une probabilité d’obtenir le stage.')
```

**Lecture des instructions principales :**
- `matching.py:56-64` vectorise les ensembles de termes et calcule une similarité cosinus.
- `matching.py:67-82` valide le profil et construit les pondérations.
- `matching.py:83-101` classe les offres et renvoie explication, éléments communs et éléments absents.
- `api.py:390-393` exige un consentement et un résumé inchangé avant de transmettre des informations à Gemini.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: classer des offres selon les compétences et critères d’un profil, avec explication.

**Tests associés.** tests/test_application.py::test_local_matching_explainable; test_matching_ranks_representative_profiles. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Comparer un profil fictif à une offre de démonstration; présenter le score comme indicatif.

**Phrase possible.** « Le score aide à prioriser les offres; ce n’est pas une probabilité d’embauche. »

## 11. CV Builder et PDF

**Objectif.** Valider un profil, enregistrer une version chiffrée et générer un PDF local.

**Technologies.** Flask, Fernet, ReportLab.

**Données / tables.** cvs; le contenu enregistré est chiffré.

**Fichiers, symboles et extraits source.**

- `backend/api.py:218-229` — `save_cv`. Validation, chiffrement et sauvegarde de la version.

```python
def save_cv():
    data = body()
    cv = validate_cv(data.get('data'))
    name = text(data.get('name', ''), 150)
    template = data.get('template', 'modern')
    if not name or template not in ('modern', 'ats'):
        raise ValueError('Nom de version ou modèle invalide.')
    encrypted = current_app.extensions['vault'].encrypt(cv)
    with connect(config()['DATABASE']) as db:
        ident = db.execute('INSERT INTO cvs(name,template,payload,created_at,updated_at) VALUES (?,?,?,?,?)',
                           (name, template, encrypted, now(), now())).lastrowid
    return jsonify(id=ident), 201
```

**Lecture des instructions principales :**
- `api.py:218-224` valide les champs du CV, son nom et le modèle demandé.
- `api.py:225-229` chiffre le contenu avec Vault avant insertion SQLite.
- `cv_service.py:68-92` prépare le titre et les paragraphes ReportLab avant l’export PDF.

- `backend/cv_service.py:68-92` — `make_pdf, para`. Composition du PDF.

```python
def make_pdf(data, template='modern'):
    data = validate_cv(data)
    if template not in ('modern', 'ats'):
        raise ValueError('Modèle de CV inconnu.')
    fonts = Path(reportlab.__file__).parent / 'fonts'
    if 'CV' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('CV', str(fonts / 'Vera.ttf')))
        pdfmetrics.registerFont(TTFont('CV-Bold', str(fonts / 'VeraBd.ttf')))
        pdfmetrics.registerFontFamily('CV', normal='CV', bold='CV-Bold', italic='CV', boldItalic='CV-Bold')
    output = io.BytesIO()
    accent = colors.HexColor('#215CF3' if template == 'modern' else '#16243A')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('CVBody', fontName='CV', fontSize=9, leading=14, spaceAfter=5, textColor=colors.HexColor('#26374C'), splitLongWords=True))
    styles.add(ParagraphStyle('CVName', parent=styles['CVBody'], fontName='CV-Bold', fontSize=25, leading=31, textColor=colors.white if template=='modern' else colors.HexColor('#102039'), spaceAfter=6))
    styles.add(ParagraphStyle('CVTitle', parent=styles['CVBody'], fontSize=13, leading=19, textColor=colors.HexColor('#AAC8FF') if template=='modern' else accent, spaceAfter=10))
    styles.add(ParagraphStyle('CVContact', parent=styles['CVBody'], textColor=colors.HexColor('#DFE9FA') if template=='modern' else colors.HexColor('#26374C')))
    styles.add(ParagraphStyle('CVSection', parent=styles['CVBody'], fontName='CV-Bold', fontSize=11, leading=17, textColor=accent, spaceBefore=13, spaceAfter=6, keepWithNext=True))
    styles.add(ParagraphStyle('CVEntry', parent=styles['CVBody'], fontName='CV-Bold', keepWithNext=True))
    def para(value, style='CVBody'):
        return Paragraph(escape(value).replace('\n', '<br/>'), styles[style])
    header = [para(data['name'], 'CVName'), para(data['title'], 'CVTitle')]
    contacts = '  |  '.join(data[k] for k in ('email', 'phone', 'city') if data[k])
    if contacts:
        header.append(para(contacts,'CVContact'))
    for k in ('linkedin', 'github'):
```

**Lecture des instructions principales :**
- `api.py:218-224` valide les champs du CV, son nom et le modèle demandé.
- `api.py:225-229` chiffre le contenu avec Vault avant insertion SQLite.
- `cv_service.py:68-92` prépare le titre et les paragraphes ReportLab avant l’export PDF.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: valider un profil, enregistrer une version chiffrée et générer un pdf local.

**Tests associés.** tests/test_application.py PDF/CV tests. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Créer un CV fictif en base temporaire puis vérifier le PDF extrait.

**Phrase possible.** « Le PDF se génère localement; le CV ne doit pas être partagé depuis le profil historique. »

## 12. Chatbot local

**Objectif.** Répondre aux questions à partir des offres et entreprises présentes dans la base.

**Technologies.** JavaScript, Flask, SQLite, génération textuelle locale.

**Données / tables.** offres, entreprises, assistant_messages.

**Fichiers, symboles et extraits source.**

- `backend/assistant.py:42-65` — `retrieve`. Recherche locale d’offres et préparation des résultats.

```python
def retrieve(path, question, cv_profile=None):
    if not isinstance(question,str) or not question.strip() or len(question)>2000:raise ValueError('Saisissez une question de 1 à 2 000 caractères.')
    q=question.strip(); offers=_offer_rows(path); normalized=norm(q); skills=skills_from(q)
    city=next((c for c in CITY_NAMES if norm(c) in normalized),None)
    new_this_week=any(k in normalized for k in ('cette semaine','nouvelles offres','nouvelle offre','ajoutee recemment','ajoutees recemment'))
    recent=not new_this_week and any(k in normalized for k in ('recemment','dernier','publie','publiee','aujourd'))
    if cv_profile is not None and any(k in normalized for k in ('cv','mon profil','correspond')):
        weights={'skills':55,'education':20,'experience':15,'location':5,'opportunity':5}
        ranked=rank(cv_profile,offers,weights)
        found=[_clean_offer({**r['offer'],'availability':r['offer'].get('availability','unknown')}) for r in ranked[:5]]
        for item,r in zip(found,ranked[:5]):item['match_score']=r['score'];item['matched']=r['matched'];item['missing']=r['missing'];item['uncertain']=r['uncertain']
        return {'question':q,'filters':{'mode':'CV local','skills':cv_profile['skills'],'city':city},'offers':found,'companies':[],
                'last_updated':_latest_update(path),'answer':f"Comparaison locale avec le CV enregistré. {len(found)} offre(s) classée(s); les compétences manquantes sont des termes absents du texte, pas une évaluation de votre niveau."}
    company_question=any(word in normalized for word in ('entreprise','entreprises','societe','societes'))
    if company_question and any(word in normalized for word in ('combien','nombre','total')):
        count=rows(path,'SELECT COUNT(*) AS total FROM entreprises')[0]['total']
        return {'question':q,'filters':{'mode':'comptage SQLite'},'offers':[],'companies':[],
                'company_count':count,'last_updated':_latest_update(path),
                'answer':f'{count} entreprise(s) sont enregistrée(s) dans la base locale. Ce total décrit les lignes SQLite, pas leur activité actuelle.'}
    if company_question and not any(word in normalized for word in ('offre','stage','emploi')):
        companies=rows(path,'SELECT e.rowid AS id,e.Nom,e.Secteur,e.Adresse,e.ville,e."Site Web",i.first_seen AS added_at FROM entreprises e LEFT JOIN company_source_identity i ON i.company_rowid=e.rowid ORDER BY e.Nom')
        if new_this_week or 'recemment' in normalized or 'ajoute' in normalized:
            cutoff=(date.today()-timedelta(days=7)).isoformat()
            companies=[c for c in companies if c.get('added_at') and str(c['added_at'])[:10]>=cutoff]
```

**Lecture des instructions principales :**
- `assistant.py:42-65` sélectionne les offres par termes extraits de la question et traite les résultats SQLite.
- `api.py:838-856` valide la question, choisit le mode et retourne une réponse d’assistant.
- `ui.js:278-279` envoie le message via l’API puis affiche réponse ou erreur.

- `backend/api.py:838-856` — `assistant_chat`. Endpoint de conversation locale.

```python
def assistant_chat():
    data=body();question=data.get('question');mode=data.get('mode','local')
    if mode not in ('local','gemini'):raise ValueError('Mode assistant invalide.')
    found,sent,digest=assistant_preview_data(question);notice_text='Recherche locale dans SQLite. Aucun service externe utilisé.'
    if mode=='gemini':
        if data.get('consent') is not True or data.get('digest')!=digest:
            raise ValueError('Prévisualisez exactement les données et confirmez leur transmission à Gemini.')
        try:
            ai=assistant_gemini_answer(config(),sent,{o['id'] for o in sent['offers']})
            found['answer']=ai['answer'];found['offers']=[o for o in found['offers'] if o['id'] in ai['offer_ids']]
            notice_text='Résumé Gemini des offres locales. Les fiches et liens restent la source de référence.'
        except Exception:
            notice_text='Gemini indisponible ou non vérifiable : réponse locale affichée, sans nouvelle tentative.'
    vault=current_app.extensions['vault']
    if not config().get('PUBLIC_DEMO_MODE'):
        with connect(config()['DATABASE']) as db:
            db.execute('INSERT INTO assistant_messages(role,message,created_at) VALUES (?,?,?)',('user',vault.encrypt({'text':question}),now()))
            db.execute('INSERT INTO assistant_messages(role,message,created_at) VALUES (?,?,?)',('assistant',vault.encrypt({'text':found['answer']}),now()))
    return jsonify(**found,mode='gemini' if mode=='gemini' and notice_text.startswith('Résumé') else 'local',notice=notice_text)
```

**Lecture des instructions principales :**
- `assistant.py:42-65` sélectionne les offres par termes extraits de la question et traite les résultats SQLite.
- `api.py:838-856` valide la question, choisit le mode et retourne une réponse d’assistant.
- `ui.js:278-279` envoie le message via l’API puis affiche réponse ou erreur.

- `dashboard/js/ui.js:262-279` — `repère fonctionnel vérifié dans le fichier`. Affichage des réponses et envoi de message.

```javascript
function assistantResponse(data){const turn=h('section',{class:'chat-turn assistant'},chatMessageBubble('assistant',[data.answer,data.notice,'Dernière mise à jour : '+formatDate(data.last_updated)].filter(Boolean).join('\n\n')));for(const item of data.offers||[])turn.append(chatOfferCard(item));for(const item of data.companies||[])turn.append(h('article',{class:'chat-offer-card'},h('h3',{},item.name||'Entreprise non renseignée'),h('p',{class:'chat-offer-meta'},item.sector||'Secteur non renseigné · Ville non renseignée'),item.website?link('Site web ↗',item.website,'btn secondary'):null));return turn;}
function askGeminiConsent(previewData,onConfirm){
 const consent=h('input',{type:'checkbox','aria-label':'J’accepte le transfert de la prévisualisation à Gemini'}),payload=h('pre',{class:'assistant-gemini-payload'},JSON.stringify(previewData.payload,null,2));
 const dialog=modal('Avant d’utiliser Gemini',h('div',{class:'assistant-consent-dialog'},notice('Seuls la question et au plus cinq extraits d’offres seront transmis. Aucun CV, contact ou dossier de candidature n’est envoyé. Vérifiez le texte ci-dessous. Les conditions de traitement dépendent du compte Google.',true),payload,h('label',{class:'check'},consent,'J’ai lu le contenu exact et j’accepte de le transmettre à Gemini.'),h('div',{class:'actions'},button('Annuler',()=>dialog.close()),button('Confirmer et envoyer',()=>{if(!consent.checked)throw new Error('Cochez votre consentement après lecture.');dialog.close();onConfirm();},true,'send'))));
}
async function openAssistant(){
 const existing=$('.assistant-panel');if(existing){existing.remove();return;}
 let status;try{status=await api('/assistant/status');}catch{status={gemini_available:false,reasons:['État Gemini indisponible.']};}
 const messages=chatMessageList(),input=h('textarea',{'aria-label':'Votre question',autocomplete:'off'}),mode=chatModeSelector(status.gemini_available),modeStatus=badge(status.gemini_available?'Gemini configuré · test réel requis':'Mode local — SQLite',status.gemini_available?'amber':'gray'),suggestions=chatSuggestions(question=>{input.value=question;sendQuestion();});
 mode.addEventListener('change',()=>{modeStatus.textContent=mode.value==='gemini'?'Gemini configuré · test réel requis':'Mode local — SQLite';});
 let composerRef;
 function close(){panel.remove();launcher?.focus();}
 function showError(error){appendChatNode(messages,chatErrorState(error));}
 async function perform(question,selectedMode='local',digest=''){
  const user=chatMessageBubble('user',question);appendChatNode(messages,user,true);input.value='';suggestions.hidden=true;
  const loading=chatLoadingState();appendChatNode(messages,loading,true);composerRef.send.disabled=true;input.disabled=true;mode.disabled=true;
  try{const data=await api('/assistant/chat',{method:'POST',body:{question,mode:selectedMode,...(selectedMode==='gemini'?{consent:true,digest}:{})}});loading.remove();appendChatNode(messages,assistantResponse(data));await updateAlertBadge();}
  catch(error){loading.remove();appendChatNode(messages,chatErrorState(error));}
```

**Lecture des instructions principales :**
- `assistant.py:42-65` sélectionne les offres par termes extraits de la question et traite les résultats SQLite.
- `api.py:838-856` valide la question, choisit le mode et retourne une réponse d’assistant.
- `ui.js:278-279` envoie le message via l’API puis affiche réponse ou erreur.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: répondre aux questions à partir des offres et entreprises présentes dans la base.

**Tests associés.** tests/test_phase5.py assistant tests; tests/test_application.py chat/CSRF tests. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Demander « combien d’offres ? » sur une base temporaire; ne pas utiliser de donnée personnelle.

**Phrase possible.** « Le mode local récupère des lignes SQLite; Gemini est un mode séparé qui demande consentement. »

## 13. Recherche Gemini facultative

**Objectif.** Rechercher avec le fournisseur uniquement si clés, option, consentement et configuration le permettent.

**Technologies.** SDK Gemini optionnel, filtrage de sources, staging.

**Données / tables.** gemini_search_history, collector_staging.

**Fichiers, symboles et extraits source.**

- `backend/gemini_search.py:114-140` — `validate_criteria, _search_prompt`. Validation structurée des critères.

```python
def validate_criteria(data):
    if not isinstance(data,dict):raise ValueError('Critères de recherche invalides.')
    prompt=str(data.get('prompt') or '').strip()
    if not 5<=len(prompt)<=1000:raise ValueError('Le prompt doit contenir entre 5 et 1 000 caractères.')
    city=str(data.get('city') or 'Marrakech').strip()[:100]
    domain=str(data.get('domain') or '').strip()[:120]
    opportunity=str(data.get('opportunity_type') or '').strip()[:80]
    period=str(data.get('period') or '7d')
    if period not in ('24h','7d','30d','custom'):raise ValueError('Période de recherche invalide.')
    start=str(data.get('date_from') or '')[:10];end=str(data.get('date_to') or '')[:10]
    if period=='custom':
        try:date.fromisoformat(start);date.fromisoformat(end)
        except ValueError:raise ValueError('Choisissez une période personnalisée valide.')
        if start>end:raise ValueError('La période de début doit précéder la fin.')
    maximum=data.get('max_results',8)
    if type(maximum) is not int or not 1<=maximum<=10:raise ValueError('Le nombre de résultats doit être entre 1 et 10.')
    return {'prompt':prompt,'city':city,'domain':domain,'opportunity_type':opportunity,'period':period,
            'date_from':start if period=='custom' else None,'date_to':end if period=='custom' else None,'max_results':maximum}


def _search_prompt(criteria):
    safe_prompt=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[email retiré]',criteria['prompt'])
    safe_prompt=re.sub(r'(?<!\w)(?:\+?\d[\d .()/-]{7,}\d)','[téléphone retiré]',safe_prompt)
    safe_prompt=re.sub(r'https?://\S+','[URL retirée]',safe_prompt)
    period={'24h':'24 dernières heures','7d':'7 derniers jours','30d':'30 derniers jours','custom':f"du {criteria['date_from']} au {criteria['date_to']}"}[criteria['period']]
    return json.dumps({'request':safe_prompt,'city':criteria['city'],'domain':criteria['domain'],
        'opportunity_type':criteria['opportunity_type'],'publication_period':period,'max_results':criteria['max_results']},ensure_ascii=False)
```

**Lecture des instructions principales :**
- `gemini_search.py:114-131` valide les critères avant création du prompt.
- `gemini_search.py:143-170` lance le client seulement après vérification, récupère les références de sources et contrôle l’URL publique.
- `api.py:612-634` protège la route derrière la configuration, le consentement et les limites d’exécution.

- `backend/gemini_search.py:143-170` — `run_grounded_search`. Recherche avec résultats sourcés.

```python
def run_grounded_search(config,criteria,client=None):
    readiness=enabled_status(config)
    if not readiness['enabled']:raise ValueError('Recherche Internet indisponible : '+' '.join(readiness['reasons']))
    criteria=validate_criteria(criteria)
    created=False
    if client is None:
        from google import genai
        from google.genai import types
        client=genai.Client(api_key=config['GEMINI_API_KEY'],http_options=types.HttpOptions(timeout=readiness['timeout_ms']))
        created=True
    try:
        from google.genai import types
        request_config=types.GenerateContentConfig(temperature=0.2,max_output_tokens=5000,
            system_instruction=SYSTEM_INSTRUCTION,tools=[types.Tool(google_search=types.GoogleSearch())],
            response_mime_type='application/json',response_json_schema=SEARCH_SCHEMA)
        response=client.models.generate_content(model=SEARCH_MODEL,contents=_search_prompt(criteria),config=request_config)
        raw_text=_get(response,'text')
        if not isinstance(raw_text,str) or not raw_text.strip():raise ValueError('Gemini n’a retourné aucun résultat structuré.')
        try:payload=json.loads(raw_text)
        except json.JSONDecodeError as exc:raise ValueError('Réponse structurée Gemini invalide.') from exc
        candidates_obj=_get(response,'candidates',[]) or []
        metadata=_get(candidates_obj[0],'grounding_metadata',_get(candidates_obj[0],'groundingMetadata')) if candidates_obj else None
        ground=_grounding(metadata) if metadata else {'sources':[],'citations':[],'queries':[],'search_suggestions':[]}
        if not isinstance(payload,dict) or not isinstance(payload.get('candidates'),list):raise ValueError('Format de résultats Gemini invalide.')
        sources_by_url={item['url']:item for item in ground['sources']}
        normalized=[]
        for index,item in enumerate(payload['candidates'][:criteria['max_results']]):
            if not isinstance(item,dict):continue
```

**Lecture des instructions principales :**
- `gemini_search.py:114-131` valide les critères avant création du prompt.
- `gemini_search.py:143-170` lance le client seulement après vérification, récupère les références de sources et contrôle l’URL publique.
- `api.py:612-634` protège la route derrière la configuration, le consentement et les limites d’exécution.

- `backend/api.py:612-634` — `ai_search_gemini`. Route qui vérifie le statut et les préconditions.

```python
def ai_search_gemini():
    data=body();criteria=validate_criteria(data);ready=gemini_search_status(config())
    if not ready['enabled']:raise ValueError('Gemini Search est désactivé. '+' '.join(ready['reasons']))
    if data.get('confirm_cost') is not True:raise ValueError('Confirmez que vous acceptez une éventuelle facturation Google Search Grounding.')
    digest=_ai_session_digest();stamp=datetime.now(timezone.utc).isoformat(timespec='seconds');day=date.today().isoformat()
    with connect(config()['DATABASE']) as db:
        db.execute('BEGIN IMMEDIATE')
        daily=db.execute("SELECT COUNT(*) FROM gemini_search_history WHERE mode='gemini' AND started_at>=?",(day,)).fetchone()[0]
        own=db.execute("SELECT COUNT(*) FROM gemini_search_history WHERE mode='gemini' AND session_digest=? AND started_at>=?",(digest,day)).fetchone()[0]
        latest=db.execute("SELECT started_at FROM gemini_search_history WHERE mode='gemini' AND session_digest=? ORDER BY started_at DESC LIMIT 1",(digest,)).fetchone()
        if daily>=ready['max_daily'] or own>=ready['max_session']:raise ValueError('Plafond logiciel Gemini Search atteint; réessayez un autre jour.')
        if latest:
            try:
                if (datetime.now(timezone.utc)-datetime.fromisoformat(latest['started_at'])).total_seconds()<ready['cooldown_seconds']:
                    raise ValueError('Veuillez respecter le délai entre deux recherches.')
            except ValueError as exc:
                if str(exc).startswith('Veuillez'):raise
        ident=str(uuid.uuid4());db.execute('INSERT INTO gemini_search_history(id,session_digest,mode,prompt,criteria_json,model,status,started_at) VALUES (?,?,?,?,?,?,?,?)',
            (ident,digest,'gemini',_redacted_prompt(criteria['prompt']),json.dumps({k:v for k,v in criteria.items() if k!='prompt'},ensure_ascii=False),ready['model'],'running',stamp))
    job={'status':'running','cancel':threading.Event(),'session_digest':digest,'result':None,'message':'Recherche en cours. Les sources seront à vérifier manuellement.'}
    current_app.extensions['gemini_search_jobs'][ident]=job
    app=current_app._get_current_object();threading.Thread(target=_grounded_worker,args=(app,ident,criteria,digest,True),daemon=True).start()
    return jsonify(id=ident,status='running',message=job['message']),202
```

**Lecture des instructions principales :**
- `gemini_search.py:114-131` valide les critères avant création du prompt.
- `gemini_search.py:143-170` lance le client seulement après vérification, récupère les références de sources et contrôle l’URL publique.
- `api.py:612-634` protège la route derrière la configuration, le consentement et les limites d’exécution.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: rechercher avec le fournisseur uniquement si clés, option, consentement et configuration le permettent.

**Tests associés.** tests/test_phase9.py mock/consent/rights tests. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Montrer l’état désactivé; aucune requête réelle ou payante n’a été faite pendant la validation.

**Phrase possible.** « Le modèle ne transforme pas seul un résultat en offre importée; la vérification et l’approbation restent requises. »

## 14. Alertes

**Objectif.** Comparer une offre au profil configuré et éviter les notifications répétées.

**Technologies.** Python, règles pondérées, SQLite.

**Données / tables.** alert_preferences, alerts, alert_email_log.

**Fichiers, symboles et extraits source.**

- `backend/alerts.py:29-68` — `score_offer, maybe_create_alert`. Validation des préférences, score et création d’alerte.

```python
def score_offer(offer,prefs):
    if not prefs['enabled']:return None
    exp=str(offer.get('Date expiration') or '')[:10]
    try:
        if date.fromisoformat(exp)<date.today():return None
    except ValueError:pass
    text=' '.join(str(offer.get(k) or '') for k in ('Titre','Description','entreprise_nom','ville','competences'))
    normalized=norm(text)
    if prefs['city'] and offer.get('ville') and norm(prefs['city']) not in norm(offer['ville']):return None
    if prefs['contract_type'] and offer.get('Type contrat') and norm(prefs['contract_type']) not in norm(offer['Type contrat']):return None
    if prefs['internship_type'] and offer.get('Type stage') and norm(prefs['internship_type']) not in norm(offer['Type stage']):return None
    skills=prefs['skills'];matched=[s for s in skills if norm(s) in normalized or norm(s) in [norm(x) for x in skills_from(text)]]
    requirements=skills_from(text)
    if prefs['domain']:
        domain_match=norm(prefs['domain']) in normalized
    else:domain_match=0
    city_match=bool(prefs['city'] and offer.get('ville') and norm(prefs['city']) in norm(offer['ville']))
    if skills:
        skill_score=len(matched)/len(skills)
        score=round(skill_score*65+bool(domain_match)*20+bool(city_match)*15,1)
    else:
        score=round(bool(domain_match)*70+bool(city_match)*30,1)
    if score<prefs['minimum_score']:return None
    parts=[]
    if matched:parts.append('Compétences concordantes : '+', '.join(matched))
    if domain_match:parts.append('Domaine présent dans l’annonce')
    if city_match:parts.append('Ville concordante : '+str(offer.get('ville')))
    if not requirements and not skills:parts.append('Aucune compétence explicite détectée dans l’annonce; score limité au domaine et à la ville')
    return {'score':score,'explanation':'; '.join(parts) or 'Score calculé à partir du domaine, de la ville et des champs présents.', 'matched':matched}


def maybe_create_alert(db,offer_id):
    prefs=preferences(db)
    offer=db.execute('SELECT * FROM offres WHERE "ID"=?',(offer_id,)).fetchone()
    if not offer:return None
    result=score_offer(dict(offer),prefs)
    if not result:return None
    db.execute('INSERT OR IGNORE INTO alerts(offer_id,created_at,score,explanation) VALUES (?,?,?,?)',
               (offer_id,now(),result['score'],result['explanation']))
    return result
```

**Lecture des instructions principales :**
- `alerts.py:29-42` contrôle les préférences et leurs seuils.
- `alerts.py:29-57` compare critères d’offre, localisation, expiration et compétences pour un score explicable.
- `alerts.py:60-68` évite de créer deux alertes identiques pour une même offre.

- `backend/api.py:707-784` — `get_alert_preferences, put_alert_preferences, get_alerts, alert_count, mark_alert_read, mark_alerts_read, delete_alert, assistant_cv_profile, values`. Routes de préférences, liste et lecture.

```python
def get_alert_preferences():
    with connect(config()['DATABASE']) as db:value=alert_preferences(db)
    value['email_recipient_saved']=bool(value.pop('email_payload',None))
    return jsonify(value)


@api.put('/alerts/preferences')
def put_alert_preferences():
    incoming=body();values=validate_alert_preferences(incoming)
    encrypted_recipient=None
    if values['email_enabled']:
        if incoming.get('email_consent') is not True:
            raise ValueError('Confirmez explicitement votre accord pour les emails d’alerte.')
        if not config()['SMTP_ENABLED'] or not config()['SMTP_USER'] or not config()['SMTP_PASSWORD']:
            raise ValueError('Configurez SMTP dans .env puis redémarrez avant d’activer les emails.')
        recipient=incoming.get('email_recipient','').strip() if isinstance(incoming.get('email_recipient',''),str) else ''
        if recipient:
            encrypted_recipient=current_app.extensions['vault'].encrypt({'email':email(recipient)})
        else:
            saved=rows(config()['DATABASE'],'SELECT email_payload FROM alert_preferences WHERE id=1')
            encrypted_recipient=saved[0]['email_payload'] if saved else None
            if not encrypted_recipient:raise ValueError('Saisissez un destinataire email pour activer les alertes.')
    with connect(config()['DATABASE']) as db:
        db.execute('''UPDATE alert_preferences SET domain=?,skills_json=?,city=?,internship_type=?,contract_type=?,minimum_score=?,frequency=?,enabled=?,email_enabled=?,email_payload=?,updated_at=? WHERE id=1''',
                   (values['domain'],json.dumps(values['skills'],ensure_ascii=False),values['city'],values['internship_type'],values['contract_type'],values['minimum_score'],values['frequency'],int(values['enabled']),int(values['email_enabled']),encrypted_recipient,now()))
        if not values['email_enabled']:
            db.execute("UPDATE alert_email_log SET status='cancelled',attempted_at=? WHERE status='queued'",(now(),))
            db.execute('UPDATE alert_preferences SET email_next_at=NULL WHERE id=1')
        saved=alert_preferences(db);saved['email_recipient_saved']=bool(saved.pop('email_payload',None))
    if values['email_enabled']:
        ensure_scheduler(current_app._get_current_object())
    return jsonify(saved)


@api.get('/alerts')
def get_alerts():
    return jsonify(rows(config()['DATABASE'],'''SELECT a.id,a.offer_id,a.created_at,a.score,a.explanation,a.is_read,el.status AS email_status,
        o."Titre" AS title,o.entreprise_nom AS company,o.ville AS city,o.source,
        o."Date publication" AS published_at,o."Lien public" AS url,o."Lien annonce" AS fallback_url,
        o."Type stage" AS internship_type,o."Type contrat" AS contract_type
        FROM alerts a JOIN offres o ON o."ID"=a.offer_id LEFT JOIN alert_email_log el ON el.alert_id=a.id ORDER BY a.created_at DESC LIMIT 200'''))


@api.get('/alerts/count')
def alert_count():
    return jsonify(unread=rows(config()['DATABASE'],'SELECT COUNT(*) AS n FROM alerts WHERE is_read=0')[0]['n'])


@api.post('/alerts/<int:ident>/read')
def mark_alert_read(ident):
    with connect(config()['DATABASE']) as db:
        cur=db.execute('UPDATE alerts SET is_read=1 WHERE id=?',(ident,))
        if not cur.rowcount:raise LookupError('Alerte introuvable.')
    return jsonify(ok=True)


@api.post('/alerts/read-all')
def mark_alerts_read():
    with connect(config()['DATABASE']) as db:db.execute('UPDATE alerts SET is_read=1')
    return jsonify(ok=True)


@api.delete('/alerts/<int:ident>')
def delete_alert(ident):
    with connect(config()['DATABASE']) as db:db.execute('DELETE FROM alerts WHERE id=?',(ident,))
    return ('',204)


def assistant_cv_profile():
    with connect(config()['DATABASE']) as db:row=db.execute('SELECT payload FROM cvs ORDER BY updated_at DESC,id DESC LIMIT 1').fetchone()
    if not row:return None
    data=current_app.extensions['vault'].decrypt(row['payload'])
    def values(key):
        items=data.get(key) or []
        return ' '.join(' '.join(str(v) for v in item.values()) if isinstance(item,dict) else str(item) for item in items)
    skills=[s.strip() for s in re.split(r'[,;\n]',str(data.get('technical') or '')) if s.strip()]
    return {'skills':skills[:100],'education':values('education'),'experience':values('experience')+' '+values('projects'),
            'domain':str(data.get('title') or ''),'location':str(data.get('city') or ''),'opportunity':'Stage'}
```

**Lecture des instructions principales :**
- `alerts.py:29-42` contrôle les préférences et leurs seuils.
- `alerts.py:29-57` compare critères d’offre, localisation, expiration et compétences pour un score explicable.
- `alerts.py:60-68` évite de créer deux alertes identiques pour une même offre.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: comparer une offre au profil configuré et éviter les notifications répétées.

**Tests associés.** tests/test_phase5.py alert tests. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Créer une préférence fictive puis tester avec une offre en base temporaire.

**Phrase possible.** « Une alerte reflète les préférences et le score de correspondance; l’email reste désactivé sans consentement. »

## 15. Candidatures

**Objectif.** Créer un suivi, faire évoluer son statut et conserver son historique.

**Technologies.** Flask, SQLite, validation et idempotence d’envoi.

**Données / tables.** candidatures, candidature_history, send_attempts.

**Fichiers, symboles et extraits source.**

- `backend/api.py:174-204` — `create_application, update_application, delete_application, history`. Création, modification, protection contre suppression et historique.

```python
def create_application():
    data = candidature(body())
    with connect(config()['DATABASE']) as db:
        ident = insert_candidature(db, data)
    return jsonify(id=ident, message='Candidature enregistrée.'), 201


@api.route('/candidatures/<int:ident>', methods=['PUT', 'PATCH'])
def update_application(ident):
    values = candidature(body(), partial=True)
    with connect(config()['DATABASE']) as db:
        old = db.execute('SELECT * FROM candidatures WHERE id=?', (ident,)).fetchone()
        if old is None:
            raise LookupError('Candidature introuvable.')
        values['updated_at'] = now()
        db.execute(f"UPDATE candidatures SET {','.join(k+'=?' for k in values)} WHERE id=?", (*values.values(), ident))
        if 'statut' in values and values['statut'] != old['statut']:
            db.execute('INSERT INTO candidature_history(candidature_id,old_status,new_status,changed_at) VALUES (?,?,?,?)',
                       (ident, old['statut'], values['statut'], now()))
    return jsonify(message='Candidature mise à jour.')


@api.delete('/candidatures/<int:ident>')
def delete_application(ident):
    # Conservation de l’historique : suppression physique remplacée par un archivage explicite.
    raise ValueError('Suppression désactivée pour conserver votre historique. Utilisez les statuts et les notes.')


@api.get('/candidatures/<int:ident>/history')
def history(ident):
    return jsonify(rows(config()['DATABASE'], 'SELECT * FROM candidature_history WHERE candidature_id=? ORDER BY id', (ident,)))
```

**Lecture des instructions principales :**
- `api.py:174-178` valide les champs puis délègue l’insertion.
- `api.py:181-193` met à jour uniquement les champs reçus et ajoute une ligne d’historique si le statut change.
- `api.py:196-199` refuse la suppression physique pour conserver l’historique.
- `application_service.py:12-19` enregistre une candidature dans SQLite.

- `backend/application_service.py:12-35` — `insert_candidature, resolve_channel`. Insertion et choix d’action/canal.

```python
def insert_candidature(db, data):
    values = dict(data, created_at=now(), updated_at=now())
    keys = list(values)
    cursor = db.execute(f"INSERT INTO candidatures ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})", tuple(values[k] for k in keys))
    ident = cursor.lastrowid
    db.execute('INSERT INTO candidature_history(candidature_id,old_status,new_status,changed_at) VALUES (?,?,?,?)',
               (ident, None, values.get('statut', 'Non envoyée'), now()))
    return ident


def resolve_channel(offer, company=None):
    if (offer.get('email_verified') == 1 and offer.get('relation_verified') == 1 and company
            and offer.get('entreprise_ref') == company.get('id')):
        try:
            target = email(offer.get('recruitment_email', ''))
            known = [e.strip().lower() for e in (company.get('Emails') or '').split(',')]
            if target in known:
                return {'type': 'smtp', 'email': target, 'label': 'Contact vérifié lié à cette entreprise'}
        except ValueError:
            pass
    link = safe_url(offer.get('Lien public')) or safe_url(offer.get('Lien annonce'))
    if link:
        return {'type': 'external', 'url': link, 'label': 'Candidature sur le site source'}
    return {'type': 'unavailable', 'label': 'Coordonnées de candidature indisponibles'}
```

**Lecture des instructions principales :**
- `api.py:174-178` valide les champs puis délègue l’insertion.
- `api.py:181-193` met à jour uniquement les champs reçus et ajoute une ligne d’historique si le statut change.
- `api.py:196-199` refuse la suppression physique pour conserver l’historique.
- `application_service.py:12-19` enregistre une candidature dans SQLite.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: créer un suivi, faire évoluer son statut et conserver son historique.

**Tests associés.** tests/test_application.py::test_application_partial_update_and_history; external apply mock tests. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Exécuter uniquement les tests sur une base temporaire; ne pas envoyer de vraie candidature.

**Phrase possible.** « Les tests vérifient la préparation et l’historique sans soumettre une vraie candidature. »

## 16. Carte

**Objectif.** Afficher un fond OpenStreetMap et uniquement les marqueurs provenant de coordonnées vérifiées.

**Technologies.** Leaflet, tuiles OSM, API locale.

**Données / tables.** entreprises latitude/longitude avec provenance.

**Fichiers, symboles et extraits source.**

- `backend/api.py:476-483` — `map_data`. Endpoint de données de carte.

```python
def map_data():
    data = companies()
    verified = [c for c in data if c.get('geo_verified_at') and c.get('geo_source') and
                type(c.get('latitude')) in (int,float) and type(c.get('longitude')) in (int,float) and
                -90 <= c['latitude'] <= 90 and -180 <= c['longitude'] <= 180]
    return jsonify(companies=data, verified=verified, maps_enabled=config()['MAPS_ENABLED'] and bool(config()['MAPS_BROWSER_KEY']),
                   browser_key=config()['MAPS_BROWSER_KEY'] if config()['MAPS_ENABLED'] else '',
                   notice='Aucun géocodage automatique. Seules les coordonnées avec provenance et date de vérification sont affichées.')
```

**Lecture des instructions principales :**
- `api.py:476-483` fournit des données géographiques contrôlées.
- `ui.js:218` crée le fond Leaflet centré sur Marrakech.
- `ui.js:220-222` expose chargement et erreur du fond OSM.
- `ui.js:225` n’ajoute que les points transmis comme vérifiés.

- `dashboard/js/ui.js:218-225` — `repère fonctionnel vérifié dans le fichier`. Carte, couche OSM, erreurs et marqueurs validés.

```javascript
 const map=window.L.map(canvas,{scrollWheelZoom:true}).setView([31.6295,-7.9811],12),markers=window.L.layerGroup().addTo(map),tileLayer=window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>'}).addTo(map);
 mapStatus.textContent='Chargement du fond OpenStreetMap…';let tileFailed=false;
 tileLayer.on('loading',()=>{tileFailed=false;mapStatus.textContent='Chargement du fond OpenStreetMap…';});
 tileLayer.on('load',()=>{if(tileFailed)return;mapStatus.textContent=data.verified.length?'Fond OpenStreetMap chargé. Les marqueurs correspondent uniquement aux coordonnées vérifiées.':'Fond OpenStreetMap chargé. Aucune entreprise ne possède de coordonnées vérifiées dans la base.';});
 tileLayer.on('tileerror',()=>{tileFailed=true;mapStatus.textContent='Le fond cartographique est indisponible. Vérifiez la connexion Internet et réessayez; les données locales restent accessibles.';});
 function popup(c,isDemo=false){const box=h('div',{class:'map-popup'},h('strong',{},c.Nom),h('p',{},c.Secteur||'Secteur non renseigné'),h('p',{},c.Adresse||'Adresse non renseignée'),h('p',{},c['Téléphone']||'Téléphone non renseigné'));if(isDemo)box.append(notice('Point fictif : il ne représente aucune entreprise de la base.',true));else{if(c['Site Web'])box.append(link('Site web ↗',c['Site Web']));const destination=c.latitude!=null?c.latitude+','+c.longitude:c.Adresse||c.Nom;box.append(link('Itinéraire ↗','https://www.google.com/maps/dir/?api=1&destination='+encodeURIComponent(destination)));}box.append(button('Ouvrir la fiche entreprise',()=>companyInfo(c),false,'building'));return box;}
 function render(){const q=search.value.trim().toLocaleLowerCase();const filtered=data.companies.filter(c=>(c.Nom||'').toLocaleLowerCase().includes(q)&&(!sector.value||c.Secteur===sector.value)&&(!neighborhood.value||c.quartier===neighborhood.value));const known=new Set(filtered.map(c=>c.id));const realPoints=data.verified.filter(c=>known.has(c.id));const demoVisible=demo.checked?demoPoints.filter(c=>(!q||c.Nom.toLocaleLowerCase().includes(q))&&(!sector.value||c.Secteur===sector.value)):[];const points=[...realPoints,...demoVisible];count.textContent=filtered.length+' entreprises · '+realPoints.length+' coordonnées vérifiées'+(demo.checked?' · points fictifs affichés':'');markers.clearLayers();
 for(const c of realPoints)window.L.marker([c.latitude,c.longitude],{title:c.Nom,alt:c.Nom}).bindPopup(popup(c)).addTo(markers);
```

**Lecture des instructions principales :**
- `api.py:476-483` fournit des données géographiques contrôlées.
- `ui.js:218` crée le fond Leaflet centré sur Marrakech.
- `ui.js:220-222` expose chargement et erreur du fond OSM.
- `ui.js:225` n’ajoute que les points transmis comme vérifiés.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: afficher un fond openstreetmap et uniquement les marqueurs provenant de coordonnées vérifiées.

**Tests associés.** tests/test_map_dash.py map tests. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** La base privée auditée ne contient aucun couple de coordonnées; montrer la carte sans inventer de point.

**Phrase possible.** « Le fond de carte est disponible, mais un marqueur ne s’affiche qu’après validation des coordonnées. »

## 17. Déploiement et configuration

**Objectif.** Exposer Flask à WSGI et garder la démo séparée du profil local.

**Technologies.** Gunicorn/WSGI, variables d’environnement, Render config.

**Données / tables.** base synthétique en hébergement; stockage local privé en soutenance.

**Fichiers, symboles et extraits source.**

- `backend/wsgi.py:1-3` — `bloc de configuration vérifié`. Point WSGI Flask.

```python
"""WSGI entry point used by production servers such as Gunicorn."""
from .web import create_app

```

**Lecture des instructions principales :**
- `backend/wsgi.py:1-3` fournit `app` à Gunicorn.
- `auth_gateway/wsgi.py:1-4` expose la fabrique de la passerelle.
- `render.yaml:1-29` choisit explicitement le jeu public, les variables démo et les services externes désactivés.

- `auth_gateway/wsgi.py:1-4` — `bloc de configuration vérifié`. Point WSGI de la passerelle.

```python
"""Point WSGI de la passerelle. En production, le backend doit rester privé."""
from .app import create_app

app = create_app()
```

**Lecture des instructions principales :**
- `backend/wsgi.py:1-3` fournit `app` à Gunicorn.
- `auth_gateway/wsgi.py:1-4` expose la fabrique de la passerelle.
- `render.yaml:1-29` choisit explicitement le jeu public, les variables démo et les services externes désactivés.

- `render.yaml:1-29` — `repère fonctionnel vérifié dans le fichier`. Configuration Render explicitement en démo.

```text
services:
  - type: web
    name: stages-marrakech-ai-demo
    runtime: python
    plan: free
    buildCommand: pip install -r requirements-production.txt
    startCommand: gunicorn backend.wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -
    healthCheckPath: /health
    envVars:
      - key: DATABASE
        value: database/stages_marrakech_public_demo.db
      - key: PRIVATE_DIR
        value: /tmp/stages_marrakech_private
      - key: BACKUP_DIR
        value: /tmp/stages_marrakech_backups
      - key: COOKIE_SECURE
        value: "true"
      - key: TRUSTED_HOSTS
        value: .onrender.com
      - key: TRUST_PROXY
        value: "true"
      - key: PUBLIC_DEMO_MODE
        value: "true"
      - key: PUBLIC_DEMO_DATA_CONFIRMED
        value: "true"
      - key: GEMINI_ENABLED
        value: "false"
      - key: GEMINI_SEARCH_ENABLED
        value: "false"
```

**Lecture des instructions principales :**
- `backend/wsgi.py:1-3` fournit `app` à Gunicorn.
- `auth_gateway/wsgi.py:1-4` expose la fabrique de la passerelle.
- `render.yaml:1-29` choisit explicitement le jeu public, les variables démo et les services externes désactivés.

**Entrées et sorties.** Entrées: données validées par formulaire, API ou fichier. Sortie: exposer flask à wsgi et garder la démo séparée du profil local.

**Tests associés.** tests/test_installation.py; tests/test_public_demo.py. Ces tests sont automatisés sur des bases temporaires, fixtures ou mocks; ils ne prouvent pas l’usage opérationnel d’un service externe.

**Démo de soutenance.** Présenter la configuration sans publier; aucune URL d’hébergement n’a été vérifiée.

**Phrase possible.** « Le fichier Render sert une démonstration synthétique; il ne prouve ni déploiement ni persistance des comptes. »

## Repères de page et d’interface

- Page d’accueil: `dashboard/index.html:1` et orchestration des routes dans `dashboard/js/app.js`.
- Recherche entreprise: `dashboard/js/ui.js:85-96`.
- Liste des offres: `dashboard/js/ui.js:97-104`.
- Créateur de CV: `dashboard/js/ui.js:155-159` et `dashboard/cv.html`.
- Carte: `dashboard/js/ui.js:218-225`.
- Chatbot: `dashboard/js/ui.js:239-279` et `dashboard/css/phase5.css`.
- Fichiers de style: `dashboard/css/style.css`, `dashboard/css/design.css`, `dashboard/css/cv-preview.css`, `dashboard/css/analytics.css`.
- Routes Flask: `backend/web.py:92-167`; routes métier dans `backend/api.py`.
- Connexion de Dash: `backend/analytics.py:114-197`.
- Le point WSGI est `backend/wsgi.py`; l’hébergement n’a pas été déployé ni validé.

## Démonstrations qui restent sûres

Utilisez un profil fictif pour Matching et Chatbot. Créez tout CV de démonstration sur une base temporaire. Faites le suivi de candidature uniquement avec les tests temporaires. N’envoyez pas de candidature. Ne saisissez ni ne projetez de CV personnel dans la copie publique.
