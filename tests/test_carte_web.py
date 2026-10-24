"""Carte web dans un vrai navigateur (Chromium, rendu WebGL logiciel) : chargement sans erreur, récits,
fiche de zone d'une zone prédéfinie, calcul dans le navigateur comparé aux chiffres de la chaîne.

Sur le poste, NAVIGATEUR=msedge utilise Edge au lieu du Chromium de Playwright.
"""
import functools
import http.server
import json
import os
import threading

import pytest

from conftest import RACINE

sync_api = pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.web


class Silencieux(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def adresse():
    serveur = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Silencieux, directory=str(RACINE)))
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{serveur.server_address[1]}/carte/"
    serveur.shutdown()


@pytest.fixture(scope="module")
def page(adresse):
    with sync_api.sync_playwright() as p:
        nav = p.chromium.launch(channel=os.environ.get("NAVIGATEUR") or None,
                                args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        pg = nav.new_page(viewport={"width": 1440, "height": 900})
        pg.erreurs = []
        pg.on("pageerror", lambda e: pg.erreurs.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and pg.erreurs.append(m.text))
        pg.goto(adresse)
        pg.wait_for_function("typeof carte !== 'undefined' && carte.loaded() && document.querySelectorAll('.recit-choix').length >= 3"
                             " && document.querySelectorAll('#zoneChoix option').length >= 5", timeout=90000)
        yield pg
        nav.close()


def zones():
    return {f["properties"]["zone_id"]: f for f in json.loads((RACINE / "carte/donnees/fiche/zones.json").read_text(encoding="utf-8"))["features"]}


def test_chargement_sans_erreur(page):
    assert page.evaluate("carte.getStyle().layers.length") > 15
    assert page.evaluate("document.querySelectorAll('#tuiles .tuile').length") >= 8
    assert not page.erreurs, page.erreurs


OPTIONS = json.loads((RACINE / "carte/donnees/chiffres.json").read_text(encoding="utf-8")).get("options", [])
RECITS = ["couverture", "silence", "identite"] + (["semaines"] if "semaines" in OPTIONS else [])


@pytest.mark.parametrize("recit", RECITS)
def test_recit(page, recit):
    page.click(f".recit-choix[data-recit={recit}]")
    n = page.evaluate(f"RECITS['{recit}'].etapes.length")
    for i in range(n):
        page.wait_for_function("RC.lecture === null", timeout=30000)
        assert page.evaluate("RC.etape") == i
        assert page.inner_text("#recit .recit-texte").strip()
        if i < n - 1:
            page.click("#recit [data-r=suivant]")
    page.click("#recit [data-r=quitter]")
    assert page.evaluate("carte.getStyle().layers.filter((l) => l.id.startsWith('rc-')).length") == 0
    assert page.evaluate("carte.getLayoutProperty('inexpl-trait', 'visibility') || 'visible'") == "visible"
    assert not page.erreurs, page.erreurs


def test_fiche_zone_predefinie(page):
    z = zones()["swedish-eez"]["properties"]
    page.select_option("#zoneChoix", "swedish-eez")
    page.click("#btnFiche")
    page.wait_for_selector("#fiche-ecran:not([hidden]) .f-titre", timeout=120000)   # capture de la carte en rendu logiciel
    assert page.inner_text(".f-titre") == "Swedish EEZ"
    assert page.inner_text(".f-orange b") == str(z["nb_inexpliquees"])
    assert page.evaluate("document.querySelectorAll('.g-ligne').length") == 9
    page.click("#fiche-outils [data-a=fermer]")
    assert not page.erreurs, page.erreurs


def test_calcul_navigateur_sur_l_aire_d_etude(page):
    """Sur l'aire d'étude, le calcul du navigateur doit retrouver les chiffres de la chaîne (les navires
    sont estimés par mailles H3 : 1 % d'écart toléré)."""
    exact = zones()["study-area"]["properties"]
    calc = page.evaluate("""async () => { await charger();
        const r = calculer(F.donnees.zones.features[0]); delete r.zone; return r; }""")
    for k in ("nb_silences", "nb_reception", "nb_inexpliquees", "nav_inexpliquees", "nav_mmsi_partage",
              "nb_stationnements", "nb_rencontres", "nb_radar_sans_ais"):
        assert calc[k] == exact[k], k
    assert calc["comptes"] == exact["comptes"]
    assert abs(calc["nb_navires"] - exact["nb_navires"]) <= 0.01 * exact["nb_navires"]
    assert abs(calc["part_couverte"] - exact["part_couverte"]) < 0.01
    assert abs(calc["part_radar_recus"] - exact["part_radar_recus"]) < 0.001
