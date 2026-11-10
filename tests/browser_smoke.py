"""Parcours réels Chrome/Playwright, sur copie anonymisée, sans réseau externe."""
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path
from werkzeug.serving import make_server, WSGIRequestHandler

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.web import create_app


class QuietHandler(WSGIRequestHandler):
    def log_request(self,*args,**kwargs):
        pass


def main():
    from playwright.sync_api import sync_playwright
    target=Path(os.environ.get('STAGES_TEST_OUTPUT') or tempfile.mkdtemp(prefix='stages_browser_'))
    target.mkdir(parents=True,exist_ok=True)
    database=target/'browser_test.db'
    shutil.copy2(ROOT/'database/stages_marrakech.db',database)
    # Seulement la copie : les données personnelles des cinq anciennes démarches ne sont pas montrées.
    with sqlite3.connect(database) as db:
        db.execute("UPDATE candidatures SET nom_entreprise='Entreprise de démonstration',email=NULL,telephone=NULL,commentaire='Donnée anonymisée pour le test navigateur'")
        db.execute("UPDATE entreprises SET Nom='Entreprise de test cartographique',Adresse='Adresse synthétique du test',\"Téléphone\"='0600000000',Secteur='Test cartographique',latitude=31.6295,longitude=-7.9811,geo_source='fixture synthétique uniquement',geo_verified_at='2026-11-06T10:00:00+00:00',quartier='Quartier test',ville='Marrakech' WHERE rowid=(SELECT MIN(rowid) FROM entreprises)")
    app=create_app({'DATABASE':str(database),'PRIVATE_DIR':str(target/'private'),'BACKUP_DIR':str(target/'backups'),
                    'TESTING':True,'SMTP_ENABLED':False,'GEMINI_ENABLED':False,'GEMINI_API_KEY':'','MAPS_ENABLED':False,'MAPS_BROWSER_KEY':''})
    cookie_signer=app.session_interface.get_signing_serializer(app)
    refreshed_session_cookie=cookie_signer.dumps({'authenticated':True,'csrf':'chat-renouvelle-token'})
    expired_session_cookie=cookie_signer.dumps({'csrf':'chat-session-sans-authentification'})
    server=make_server('127.0.0.1',0,app,request_handler=QuietHandler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    executable=os.environ.get('CHROME_PATH')
    if not executable:
        for candidate in [r'C:\Program Files\Google\Chrome\Application\chrome.exe',r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe']:
            if Path(candidate).exists():executable=candidate;break
    errors=[];external=[];tile_requests=[];tile_responses=[];checks=[];network=[];limitations=[];block_tiles={'enabled':False}
    try:
        with sync_playwright() as p:
            (target/'downloads').mkdir(exist_ok=True)
            browser=p.chromium.launch(headless=True,executable_path=executable,downloads_path=str(target/'downloads'))
            print('Chrome lancé.',flush=True)
            context=browser.new_context(viewport={'width':1440,'height':1050},accept_downloads=True)
            def route(req):
                if req.request.url.startswith('https://tile.openstreetmap.org/'):
                    tile_requests.append(req.request.url)
                    req.abort() if block_tiles['enabled'] else req.continue_()
                elif req.request.url.startswith(base) or req.request.url.startswith(('data:','blob:','about:','chrome://resources/','chrome-extension://')):
                    req.continue_()
                else:
                    external.append(req.request.url.split('?')[0]);req.abort()
            context.route('**/*',route)
            page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('requestfailed',lambda req:network.append({'url':req.url,'failure':req.failure}))
            page.on('response',lambda response:network.append({'url':response.url,'status':response.status}) if '/cvs/' in response.url else None)
            page.on('response',lambda response:tile_responses.append({'url':response.url,'status':response.status}) if response.url.startswith('https://tile.openstreetmap.org/') else None)
            page.goto(base+'/index.html')
            print('Page d’accueil ouverte.',flush=True)
            page.get_by_role('dialog').wait_for()
            if page.get_by_role('button',name='Créer mon accès').is_visible():
                page.get_by_label('Mot de passe',exact=True).fill('Mot-de-passe-navigateur-123!')
                page.get_by_role('button',name='Créer mon accès').click()
            else:
                page.get_by_label('Mot de passe',exact=True).fill('Mot-de-passe-navigateur-123!')
                page.get_by_role('button',name='Ouvrir mon espace').click()
            page.get_by_role('heading',name='Bonjour, prêt pour la suite ?').wait_for()
            print('Connexion réussie.',flush=True)
            page.screenshot(path=str(target/'01_accueil.png'),full_page=True);checks.append('Accueil authentifié et statistiques réelles')
            for filename,title in [('entreprises','Les entreprises de votre écosystème'),('offres','Trouvez votre prochaine opportunité'),
                                   ('candidatures','Chaque candidature mérite un suivi'),('cv','Un CV à la hauteur de vos ambitions'),
                                   ('matching','Des opportunités qui vous correspondent'),('carte','Votre réseau, sur la carte'),
                                   ('analyses','Vos données, sous un nouvel angle'),('recherche-ia','Recherche IA sur Internet')]:
                page.goto(base+'/'+filename+'.html');page.get_by_role('heading',name=title).wait_for()
                page.screenshot(path=str(target/('page_'+filename+'.png')),full_page=False)
                checks.append('Navigation '+filename)
            page.goto(base+'/recherche-ia.html')
            page.get_by_role('heading',name='Recherche IA sur Internet').wait_for()
            assert page.get_by_role('button',name='Rechercher avec Gemini Search').is_disabled()
            page.get_by_role('button',name='Tester le parcours de démonstration').click()
            page.get_by_text('MODE DÉMONSTRATION',exact=False).wait_for()
            page.get_by_role('heading',name='Vérification de bout en bout').wait_for()
            page.get_by_text('Base principale modifiée : non',exact=False).wait_for()
            page.screenshot(path=str(target/'phase9_recherche_ia_demo.png'),full_page=True)
            checks.append('Recherche IA : Gemini désactivé par défaut et démonstration isolée affichée')
            # Dash must leave its iframe on return; repeat to confirm session and page shell state.
            for cycle in range(3):
                print(f'Cycle Dash {cycle+1}/3 : ouverture depuis l’accueil.',flush=True)
                page.goto(base+'/index.html')
                page.get_by_role('link',name='Analyses Dash').click()
                frame=page.frame_locator('iframe.iframe-dash')
                frame.get_by_text('Comprendre vos opportunités',exact=True).wait_for()
                frame.locator('#graph .js-plotly-plot').wait_for()
                back=frame.locator('a.back')
                assert back.get_attribute('href')=='/index.html'
                assert back.get_attribute('target')=='_top'
                back.click()
                page.wait_for_url('**/index.html')
                page.get_by_role('heading',name='Bonjour, prêt pour la suite ?').wait_for()
                assert page.locator('.sidebar').count()==1
                assert page.locator('.topbar').count()==1
                assert page.locator('iframe').count()==0
                assert page.get_by_role('dialog').count()==0
                assert context.request.get(base+'/api/auth/session').json()['authenticated'] is True
                print(f'Cycle Dash {cycle+1}/3 : retour accueil vérifié.',flush=True)
                if cycle==0: page.screenshot(path=str(target/'06_dash_return.png'),full_page=False)
            checks.append('Dash → Flask → Accueil répété 3 fois, URL et session conservées, une sidebar, un header, aucun iframe')
            # Dash réel dans son iframe, callbacks et filtres.
            page.goto(base+'/analyses.html')
            frame=page.frame_locator('iframe')
            frame.get_by_text('Comprendre vos opportunités',exact=True).wait_for()
            frame.locator('#graph .js-plotly-plot').wait_for()
            frame.get_by_text('Entreprises',exact=True).last.click()
            frame.locator('#graph .xtick text').filter(has_text='Informatique').wait_for(state='visible')
            checks.append('Dash rendu et changement d’onglet')
            page.screenshot(path=str(target/'05_dash.png'),full_page=True)
            # Création, version chiffrée, téléchargement PDF.
            page.goto(base+'/cv.html');page.get_by_role('button',name='Charger un exemple fictif').click()
            page.get_by_role('button',name='Enregistrer cette version').click()
            page.get_by_text('Version enregistrée et chiffrée.',exact=True).wait_for()
            page.get_by_label('Offre').select_option(index=1)
            page.get_by_role('button',name='Analyser mon CV pour cette offre').click()
            page.get_by_role('heading',name='Éléments du CV à mettre en valeur').wait_for()
            print('Conseils CV affichés.',flush=True)
            checks.append('Conseils CV localisés sur une offre réelle de la base, sans modification du CV')
            with page.expect_download() as download:
                page.get_by_role('button',name='Télécharger le PDF').click()
            pdf=target/'cv_modern.pdf'
            try:
                download.value.save_as(pdf)
            except Exception:
                (target/'download_debug.json').write_text(__import__('json').dumps({'network':network,'page_errors':errors,'external':external,'download_failure':download.value.failure()},indent=2),encoding='utf-8')
                manager=context.new_page();manager.goto('chrome://downloads/')
                reason=manager.evaluate("document.querySelector('downloads-manager')?.shadowRoot.querySelector('downloads-item')?.data?.lastReasonText || ''")
                manager.close()
                if 'Insufficient permissions' not in reason:
                    raise
                # Limite Windows du processus Chrome automatisé, constatée aussi hors application.
                # Ne pas transformer cette limite en succès natif : vérifier séparément le flux HTTP.
                versions=context.request.get(base+'/api/cvs').json()
                response=context.request.get(base+'/api/cvs/'+str(versions[0]['id'])+'/pdf?download=1')
                assert response.status==200 and response.body().startswith(b'%PDF-')
                pdf.write_bytes(response.body())
                limitations.append('Chrome automatisé : écriture du téléchargement refusée par Windows (Insufficient permissions). Événement de téléchargement et réponse HTTP PDF vérifiés ; sauvegarde de contrôle via client HTTP.')
            assert pdf.read_bytes().startswith(b'%PDF-')
            page.screenshot(path=str(target/'02_cv.png'),full_page=True);checks.append('CV, sauvegarde et téléchargement PDF')
            # Matching sans clé, résultat expliqué.
            page.goto(base+'/matching.html');page.get_by_role('button',name='Utiliser un profil fictif').click()
            page.get_by_role('button',name='Analyser sans clé API').click()
            page.get_by_text('Analyse locale, sans transmission externe.',exact=True).wait_for()
            assert page.locator('.offer').count()>0
            for heading in ['Très compatibles','Potentiellement compatibles','À explorer']:
                page.get_by_role('heading',name=heading,exact=True).wait_for()
            page.screenshot(path=str(target/'03_matching.png'),full_page=False);checks.append('Matching local sans clé')
            # Chat local: plusieurs échanges, historique, fermeture/réouverture et petite largeur.
            page.get_by_role('button',name='Ouvrir Assistant Stages Marrakech AI').click()
            chat=page.get_by_role('dialog',name='Assistant Stages Marrakech AI')
            assert chat.get_by_label('Mode').locator('option').count()==2
            question=chat.get_by_label('Votre question')
            # Simule un cookie toujours authentifié avec un CSRF renouvelé après le chargement de cette page.
            context.add_cookies([{'name':'session','value':refreshed_session_cookie,'url':base,'httpOnly':True,'sameSite':'Strict'}])
            question.fill('Offres Python')
            chat.get_by_role('button',name='Envoyer').click()
            chat.locator('.chat-message.assistant').first.wait_for()
            question.fill('Offres SQL')
            chat.get_by_role('button',name='Envoyer').click()
            chat.locator('.chat-message.assistant').nth(1).wait_for()
            # Une session réellement non authentifiée doit afficher une action de reconnexion.
            context.add_cookies([{'name':'session','value':expired_session_cookie,'url':base,'httpOnly':True,'sameSite':'Strict'}])
            question.fill('Une troisième question après expiration')
            chat.get_by_role('button',name='Envoyer').click()
            chat.get_by_role('button',name='Se reconnecter').wait_for()
            # Restaure une session synthétique de test, recharge la page et poursuit les parcours.
            context.add_cookies([{'name':'session','value':refreshed_session_cookie,'url':base,'httpOnly':True,'sameSite':'Strict'}])
            page.goto(base+'/matching.html')
            page.get_by_role('heading',name='Des opportunités qui vous correspondent').wait_for()
            page.get_by_role('button',name='Ouvrir Assistant Stages Marrakech AI').click()
            chat=page.get_by_role('dialog',name='Assistant Stages Marrakech AI')
            question=chat.get_by_label('Votre question')
            question.fill('Offre Xylophone introuvable')
            chat.get_by_role('button',name='Envoyer').click()
            answer=chat.locator('.chat-message.assistant').last
            answer.wait_for();assert 'Aucune' in answer.inner_text()
            chat.get_by_role('button',name='Fermer l’assistant').click()
            page.get_by_role('button',name='Ouvrir Assistant Stages Marrakech AI').click()
            chat=page.get_by_role('dialog',name='Assistant Stages Marrakech AI')
            assert chat.locator('.chat-message').count()>=6
            page.set_viewport_size({'width':390,'height':844})
            box=chat.bounding_box();assert box and box['x']==0 and box['width']>=389 and box['height']>=843
            assert chat.get_by_label('Votre question').is_visible() and chat.get_by_role('button',name='Envoyer').is_visible()
            page.screenshot(path=str(target/'08_chatbot_mobile.png'),full_page=False)
            page.set_viewport_size({'width':1440,'height':1050})
            page.once('dialog',lambda dialog:dialog.accept())
            chat.get_by_role('button',name='Nouvelle conversation').click()
            assert chat.locator('.chat-message').count()==0
            chat.get_by_role('button',name='Fermer l’assistant').click()
            checks.append('Chatbot : deux questions locales, historique, fermeture/réouverture, affichage mobile plein écran')
            # Parcours Postuler : préparation confirmée, sans ouverture du site externe.
            page.locator('.offer').first.get_by_role('button',name='Postuler').click()
            dialog=page.get_by_role('dialog');dialog.get_by_label('CV à utiliser').select_option(index=1)
            dialog.get_by_text('Je confirme l’enregistrement de cette offre et du CV sélectionné dans mes candidatures à préparer.',exact=True).click()
            dialog.get_by_role('button',name='Enregistrer à préparer').click()
            dialog.wait_for(state='hidden');checks.append('Postuler : CV et confirmation, sans envoi')
            page.goto(base+'/candidatures.html');page.get_by_role('heading',name='Chaque candidature mérite un suivi').wait_for()
            assert page.get_by_text('Non envoyée',exact=True).count()>0
            checks.append('Suivi actualisé')
            # Leaflet/OSM: one synthetic coordinate exists only in the anonymized browser-test copy.
            page.goto(base+'/carte.html');page.get_by_role('heading',name='Votre réseau, sur la carte').wait_for()
            page.locator('.leaflet-container').wait_for()
            assert 'OpenStreetMap' in page.locator('.leaflet-control-attribution').inner_text()
            assert page.get_by_role('region',name='Carte interactive OpenStreetMap centrée sur Marrakech').count()==1
            search=page.get_by_label('Recherche sur la carte');search.fill('Entreprise de test cartographique')
            page.get_by_text('1 entreprises · 1 coordonnées vérifiées',exact=True).wait_for()
            marker=page.locator('.leaflet-marker-icon').first;marker.wait_for();marker.click()
            page.locator('.leaflet-popup-content').get_by_text('Adresse synthétique du test',exact=True).wait_for()
            assert page.get_by_role('link',name='Itinéraire ↗').get_attribute('href').startswith('https://www.google.com/maps/dir/')
            page.get_by_role('button',name='Ouvrir la fiche entreprise').click()
            page.get_by_role('dialog').get_by_role('heading',name='Entreprise de test cartographique',level=2).wait_for()
            page.get_by_role('button',name='Fermer').click()
            search.fill('')
            page.get_by_label('Afficher trois points fictifs de démonstration',exact=False).check()
            assert page.locator('.demo-marker').count()==3
            page.locator('.demo-marker').first.click()
            page.get_by_text('Point fictif : il ne représente aucune entreprise de la base.',exact=True).wait_for()
            page.get_by_label('Afficher trois points fictifs de démonstration',exact=False).uncheck()
            assert page.locator('.demo-marker').count()==0
            page.screenshot(path=str(target/'07_leaflet_map_fixture_synthetique.png'),full_page=False)
            assert tile_requests
            checks.append('Leaflet/OSM, attribution, filtres, fiche, itinéraire et marqueurs réels de fixture/fictifs séparés')
            # Return the temporary fixture to the real-data state (zero verified coordinates).
            with sqlite3.connect(database) as test_db:
                test_db.execute("UPDATE entreprises SET latitude=NULL,longitude=NULL,geo_source=NULL,geo_verified_at=NULL,place_id=NULL WHERE rowid=(SELECT MIN(rowid) FROM entreprises)")
            page.goto(base+'/carte.html');page.get_by_role('heading',name='Votre réseau, sur la carte').wait_for()
            page.get_by_text('292 entreprises · 0 coordonnées vérifiées',exact=True).wait_for()
            page.locator('.leaflet-control-attribution').get_by_text('OpenStreetMap').wait_for()
            page.get_by_text('Fond OpenStreetMap chargé. Aucune entreprise ne possède de coordonnées vérifiées dans la base.',exact=True).wait_for()
            assert page.locator('.leaflet-marker-icon').count()==0
            page.screenshot(path=str(target/'08_leaflet_marrakech_sans_coordonnees.png'),full_page=False)
            checks.append('Carte Marrakech toujours visible avec zéro coordonnée géolocalisée')
            block_tiles['enabled']=True
            page.reload()
            page.get_by_text('Le fond cartographique est indisponible. Vérifiez la connexion Internet et réessayez; les données locales restent accessibles.',exact=True).wait_for()
            block_tiles['enabled']=False
            checks.append('Message explicite lorsque le service de tuiles est indisponible')
            # Injection stockée : affichée comme texte, aucun gestionnaire HTML créé.
            csrf=context.request.get(base+'/api/auth/session').json()['csrf']
            attack='<img src=x onerror="window.__xss=1">'
            response=context.request.post(base+'/api/candidatures',headers={'X-CSRF-Token':csrf},data={'nom_entreprise':attack,'date_candidature':'2026-11-03','statut':'Non envoyée'})
            assert response.status==201
            page.goto(base+'/candidatures.html');page.get_by_text(attack,exact=True).wait_for()
            assert page.locator('img[src="x"]').count()==0 and page.evaluate('window.__xss') is None
            checks.append('XSS stockée rendue comme texte')
            # Responsive et navigation clavier.
            page.set_viewport_size({'width':390,'height':844});page.goto(base+'/index.html')
            page.get_by_role('heading',name='Bonjour, prêt pour la suite ?').wait_for()
            assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
            page.get_by_role('button',name='Ouvrir le menu').click();page.locator('.sidebar.open').wait_for()
            page.get_by_role('link',name='Offres de stages',exact=True).click()
            page.get_by_role('heading',name='Trouvez votre prochaine opportunité').wait_for()
            page.keyboard.press('Tab');page.screenshot(path=str(target/'04_mobile.png'),full_page=False)
            checks.append('Mobile 390 px, menu et clavier')
            assert not errors,errors
            assert not external,external
            browser.close()
    finally:
        server.shutdown();thread.join(timeout=5)
    (target/'browser_result.json').write_text(__import__('json').dumps({'checks':checks,'limitations':limitations,'page_errors':errors,'external_requests':external,'openstreetmap_tile_requests':len(tile_requests),'openstreetmap_tile_responses':tile_responses},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{len(checks)} contrôles de parcours terminés ; {len(limitations)} limite(s) explicite(s) ; aucun appel Google/API payant. Tuiles OSM requises : {len(tile_requests)}. Résultats : {target}')


if __name__=='__main__':
    main()
