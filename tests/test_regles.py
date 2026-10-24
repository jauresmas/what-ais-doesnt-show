"""Règles sans base ni SIG : classe de couverture d'une maille, pseudonymes des navires."""
import re

import pandas as pd
import pytest

from regles import classe_couverture, pseudonymiser


def maille(**v):
    base = {"bonne": False, "nb_navires": 20, "nb_navires_perdus": 0, "taux_perte": 0.0,
            "taux_reception": 0.95, "nb_intervalles": 500}
    return {**base, **v}


@pytest.mark.parametrize("mesures, attendu", [
    (dict(bonne=True, taux_perte=0.5), "Reliable"),                       # le test « bonne » prime
    (dict(nb_navires=4, nb_navires_perdus=2, taux_perte=0.33), "Poor"),    # assez de navires attendus, beaucoup perdus
    (dict(nb_navires=2, nb_navires_perdus=1, taux_perte=0.33, nb_intervalles=40), "Not enough traffic"),
    (dict(nb_intervalles=40), "Not enough traffic"),
    (dict(taux_reception=0.6), "Poor"),
    (dict(taux_reception=None, nb_intervalles=200), "Poor"),              # réception inconnue : pas de bénéfice du doute
    (dict(taux_reception=0.85, taux_perte=0.1), "Degraded"),
])
def test_classe_couverture(mesures, attendu):
    assert classe_couverture(maille(**mesures)) == attendu


def test_pseudonymes_stables_et_sales():
    mmsi = pd.Series([219000001, 219000001, 265123456])
    a, b = pseudonymiser(mmsi, "sel-a"), pseudonymiser(mmsi, "sel-b")
    assert all(re.fullmatch(r"V-[0-9A-F]{6}", p) for p in a)
    assert a[0] == a[1] != a[2]                      # même navire, même pseudonyme
    assert list(a) != list(b)                        # sans le sel, pas de correspondance
    assert not any(str(m) in p for m, p in zip(mmsi, a))
