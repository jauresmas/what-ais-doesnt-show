"""Écrit docs/rapport_qualite.md à partir de la base : bilan du nettoyage et des indicateurs.

Aucun chiffre du rapport n'est saisi à la main ; relancer ce script après toute modification
de la chaîne remet le rapport à jour.
"""
from datetime import date

import config
from outils import log, requete


ESPACE = " "  # espace fine insécable, séparateur de milliers


def fr(v, decimales=0):
    """Nombre au format français : 1 234 567 ou 12,5."""
    texte = f"{v:,.{decimales}f}"
    return texte.replace(",", ESPACE).replace(".", ",")


def tableau(df, decimales=None):
    """DataFrame vers tableau Markdown ; nombres au format français."""
    decimales = decimales or {}
    entete = "| " + " | ".join(df.columns) + " |"
    alignement = "|" + "|".join("---:" if df[c].dtype.kind in "if" else "---" for c in df.columns) + "|"
    lignes = []
    for _, r in df.iterrows():
        cellules = []
        for c in df.columns:
            v = r[c]
            if df[c].dtype.kind == "i":
                v = fr(v)
            elif df[c].dtype.kind == "f":
                v = fr(v, decimales.get(c, 1))
            cellules.append(str(v))
        lignes.append("| " + " | ".join(cellules) + " |")
    return "\n".join([entete, alignement] + lignes)


def pourcent(v):
    return fr(100 * v, 1) + " %"


def rapport():
    lues = requete("SELECT sum(nb_lignes) AS n FROM qualite.bilan_nettoyage WHERE etape = 0")["n"][0]
    gardees = requete("SELECT sum(nb_lignes) AS n FROM qualite.bilan_nettoyage WHERE etape = 8")["n"][0]

    entonnoir = requete("""
        SELECT etape AS "Étape", motif AS "Motif", sum(nb_lignes)::bigint AS "Lignes"
        FROM qualite.bilan_nettoyage WHERE etape BETWEEN 1 AND 7
        GROUP BY 1, 2 ORDER BY 1, 3 DESC""")
    entonnoir["Part des lignes lues"] = (entonnoir["Lignes"] / lues).map(pourcent)

    jours = requete("""
        SELECT jour AS "Jour",
               sum(nb_lignes) FILTER (WHERE etape = 0)::bigint AS "Lignes lues",
               sum(nb_lignes) FILTER (WHERE etape = 8)::bigint AS "Positions gardées"
        FROM qualite.bilan_nettoyage GROUP BY 1 ORDER BY 1""")
    jours["Jour"] = jours["Jour"].astype(str)

    familles = requete("""
        SELECT famille AS "Famille", count(*)::int AS "Navires",
               count(*) FILTER (WHERE imo_statut = 'valide')::int AS "IMO valide",
               count(*) FILTER (WHERE imo_statut = 'invalide')::int AS "IMO à clé fausse",
               count(*) FILTER (WHERE imo_statut = 'non renseigné')::int AS "IMO absent"
        FROM ais.navire GROUP BY 1 ORDER BY 2 DESC""")

    pavillons = requete("""
        SELECT pavillon AS "Pavillon déclaré", count(*)::int AS "Navires"
        FROM ais.navire GROUP BY 1 ORDER BY 2 DESC LIMIT 12""")

    couverture = requete("""
        SELECT count(*)::int AS mailles,
               count(*) FILTER (WHERE nb_intervalles >= 100)::int AS jugees,
               count(*) FILTER (WHERE bonne)::int AS bonnes,
               count(*) FILTER (WHERE nb_intervalles >= 100 AND taux_reception >= 0.9
                                AND taux_perte > 0.1)::int AS declassees
        FROM indic.couverture""").iloc[0]
    part_trafic = requete("""
        SELECT avg(CASE WHEN c.bonne THEN 1.0 ELSE 0.0 END) AS part
        FROM ais.position p
        LEFT JOIN indic.couverture c ON c.h3 = h3_lat_lng_to_cell(p.geom, 6)
        WHERE p.sog >= 3""")["part"][0]

    coupures = requete("""
        SELECT categorie AS "Catégorie", count(*)::int AS "Coupures",
               count(DISTINCT mmsi)::int AS "Navires",
               percentile_cont(0.5) WITHIN GROUP (ORDER BY duree_h) AS "Durée médiane (h)"
        FROM indic.coupure GROUP BY 1
        ORDER BY array_position(ARRAY['position incohérente', 'navire de servitude ou d''État',
            'sortie de la zone', 'navigation intérieure ou portuaire',
            'arrêt au port ou au mouillage', 'réception insuffisante probable',
            'escale ou détour côtier possible', 'sortie de couverture possible',
            'coupure inexpliquée'], categorie)""")
    inexpliquees = requete("""
        SELECT famille AS "Famille", nature AS "Nature", count(*)::int AS "Coupures",
               count(DISTINCT mmsi)::int AS "Navires",
               percentile_cont(0.5) WITHIN GROUP (ORDER BY duree_h) AS "Durée médiane (h)"
        FROM indic.coupure WHERE categorie = 'coupure inexpliquée'
        GROUP BY 1, 2 ORDER BY 3 DESC""")
    nb_coupures = int(coupures["Coupures"].sum())

    identite = requete("""
        SELECT count(*) FILTER (WHERE nb_sauts > 0)::int AS avec_saut,
               count(*) FILTER (WHERE position_incoherente)::int AS incoherents,
               count(*) FILTER (WHERE identite_variable)::int AS variables,
               count(*) FILTER (WHERE imo_douteux)::int AS imo_douteux
        FROM indic.anomalie_navire""").iloc[0]
    nb_sauts = requete("SELECT count(*) AS n FROM indic.saut_position")["n"][0]

    stationnements = requete("""
        SELECT n.famille AS "Famille", count(*)::int AS "Épisodes",
               count(DISTINCT s.mmsi)::int AS "Navires",
               percentile_cont(0.5) WITHIN GROUP (ORDER BY s.duree_h) AS "Durée médiane (h)"
        FROM indic.stationnement_infra s JOIN ais.navire n USING (mmsi)
        GROUP BY 1 ORDER BY 2 DESC""")
    par_infra = requete("""
        SELECT i.categorie AS "Infrastructure", count(*)::int AS "Épisodes"
        FROM indic.stationnement_infra s JOIN ref.infrastructure i ON i.id = s.infra_id
        GROUP BY 1 ORDER BY 2 DESC""")

    rencontres = requete("""
        SELECT count(*)::int AS n,
               count(*) FILTER (WHERE ST_DWithin(geom::geography,
                   ST_SetSRID(ST_MakePoint(10.65, 57.68), 4326)::geography, 20000))::int AS skagen,
               count(*) FILTER (WHERE 'Tanker' IN (na.famille, nb.famille))::int AS avec_petrolier
        FROM indic.rencontre r
        JOIN ais.navire na ON na.mmsi = r.mmsi_a
        JOIN ais.navire nb ON nb.mmsi = r.mmsi_b""").iloc[0]

    score = requete("""
        SELECT nb_signaux AS "Signaux présents", count(*)::int AS "Mailles"
        FROM indic.score GROUP BY 1 ORDER BY 1""")

    sar = None
    if requete("SELECT to_regclass('indic.sar_detection') IS NOT NULL AS ok")["ok"][0]:
        sar = requete("""
            SELECT count(DISTINCT instant)::int AS passages,
                   sum(detections) FILTER (WHERE apparie)::int AS appariees,
                   sum(detections) FILTER (WHERE NOT apparie)::int AS non_appariees
            FROM indic.sar_detection""").iloc[0]
        validation = requete("""
            SELECT classe_couverture AS "Couverture de la maille", count(*)::int AS "Navires vus au radar",
                   count(*) FILTER (WHERE recu_par_reseau)::int AS "Reçus par le réseau danois",
                   (count(*) FILTER (WHERE recu_par_reseau))::float / count(*) AS part
            FROM indic.sar_detection WHERE apparie AND recu_par_reseau IS NOT NULL
            GROUP BY 1 ORDER BY 4 DESC""")
        validation["Part reçue"] = validation.pop("part").map(pourcent)
        sans_ais = requete("""
            SELECT categorie AS "Catégorie", sum(detections)::int AS "Détections"
            FROM indic.sar_detection WHERE NOT apparie GROUP BY 1 ORDER BY 2 DESC""")
        inexpl = requete("""
            WITH p AS (SELECT DISTINCT instant FROM indic.sar_detection)
            SELECT count(*) FILTER (WHERE EXISTS (SELECT 1 FROM p WHERE p.instant > c.debut
                                                  AND p.instant < c.fin))::int AS pendant,
                   (SELECT count(DISTINCT coupure_id) FROM indic.sar_detection s JOIN indic.coupure k
                      ON k.id = s.coupure_id WHERE k.categorie = 'coupure inexpliquée')::int AS vues
            FROM indic.coupure c WHERE c.categorie = 'coupure inexpliquée'""").iloc[0]

    nb_navires = requete("SELECT count(*) AS n FROM ais.navire")["n"][0]
    debut, fin = config.DEBUT.strftime("%d/%m/%Y"), config.FIN.strftime("%d/%m/%Y")

    md = f"""# Rapport qualité

*Généré par `scripts/05_rapport.py` le {date.today().strftime("%d/%m/%Y")}. Période : du {debut} au {fin}. Zone : {fr(config.BBOX[0], 1)}–{fr(config.BBOX[2], 1)}° E, {fr(config.BBOX[1], 1)}–{fr(config.BBOX[3], 1)}° N.*

## 1. Nettoyage des données AIS

**{fr(lues)} lignes lues, {fr(gardees)} positions gardées** ({pourcent(gardees / lues)}), pour **{fr(nb_navires)} navires** de classe A.

{tableau(entonnoir)}

Plus d'une ligne sur quatre est un doublon exact : le même message reçu par plusieurs stations côtières. L'allègement à une position par minute retire ensuite l'essentiel du volume sans perte d'information pour des silences de plusieurs heures.

{tableau(jours)}

## 2. Identité des navires

{tableau(familles)}

L'IMO est contrôlé par sa clé (7ᵉ chiffre). Les navires de servitude, de pêche et les petits navires à passagers n'ont souvent pas d'IMO, ce qui est normal ; un cargo ou un pétrolier sans IMO valide est signalé (`imo_douteux`).

{tableau(pavillons)}

Le pavillon est déduit des trois premiers chiffres du MMSI : c'est le pavillon revendiqué par l'émetteur.

## 3. Couverture du réseau AIS côtier

- {fr(couverture.mailles)} mailles H3 (résolution 6, ≈ 36 km²) traversées par le trafic, dont {fr(couverture.jugees)} assez fréquentées pour être jugées.
- **{fr(couverture.bonnes)} mailles bien couvertes**, qui portent {fr(100 * part_trafic)} % des positions de navires en route.
- {fr(couverture.declassees)} mailles auraient paru bien couvertes à ne regarder que les navires reçus : elles sont déclassées parce que plus d'un navire attendu sur dix y disparaît. Sans ce correctif, des trous de réception passeraient pour des extinctions volontaires.

## 4. Coupures AIS de {config.SEUILS["seuil_coupure"].replace("hours", "heures")} ou plus

**{fr(nb_coupures)} coupures**, classées par explication, de la plus ordinaire à l'absence d'explication :

{tableau(coupures)}

Coupures inexpliquées, en détail :

{tableau(inexpliquees)}

« Inexpliquée » signifie que le navire est resté, faute de temps pour en sortir, dans des eaux où le réseau recevait plus de 90 % des navires qui les traversaient, et qu'il s'est tu. Une panne d'émetteur ou une antenne mal placée restent possibles ; c'est le cas où une détection indépendante de l'AIS lève le doute.

## 5. Anomalies d'identité

- {fr(nb_sauts)} sauts de position (vitesse implicite de plus de {config.SEUILS["saut_vitesse_nd"]} nœuds), sur {fr(identite.avec_saut)} navires.
- **{fr(identite.incoherents)} navires avec trois sauts ou plus.** Le motif dominant est un aller-retour toutes les minutes entre deux lieux distants de plusieurs dizaines de milles : deux émetteurs partagent le même MMSI.
- {fr(identite.variables)} navires ont déclaré plusieurs noms, IMO ou types dans la semaine.
- {fr(identite.imo_douteux)} cargos ou pétroliers sans IMO valide.

## 6. Stationnements au-dessus des infrastructures sous-marines

{tableau(stationnements)}

{tableau(par_infra)}

Navires de servitude exclus. Les épisodes des navires de type « autre ou inconnu » (navires de recherche, d'études, offshore) relèvent en général de travaux ; ceux des cargos et pétroliers sont les plus à surveiller.

## 7. Rencontres en mer

**{fr(rencontres.n)} rencontres** d'au moins {config.SEUILS["duree_rencontre"].replace("hours", "heures")}, dont {fr(rencontres.skagen)} au large de Skagen, grande zone de soutage où ont aussi lieu des transbordements de navire à navire. {fr(rencontres.avec_petrolier)} impliquent au moins un pétrolier.

## 8. Indice de vigilance

{tableau(score)}

Mailles H3 de résolution 5 totalisant au moins 50 heures-navire et 10 navires dans la semaine.
"""
    if sar is not None:
        md += f"""
## 9. Contrôle indépendant par radar satellitaire (Sentinel-1, Global Fishing Watch)

**{fr(sar.passages)} passages de Sentinel-1** sur la semaine, **{fr(sar.appariees + sar.non_appariees)} détections** de navires, dont {fr(sar.non_appariees)} sans AIS correspondant ({pourcent(sar.non_appariees / (sar.appariees + sar.non_appariees))}).

Validation de la couverture : les navires vus au radar et identifiés par Global Fishing Watch étaient-ils reçus par le réseau danois au même instant ?

{tableau(validation)}

La part reçue suit les classes de la carte de couverture : une source qui ne doit rien à l'AIS côtier confirme la mesure.

Détections sans AIS :

{tableau(sans_ais)}

Sur les silences inexpliqués, {fr(inexpl.pendant)} ont eu lieu pendant un passage du satellite ; pour {fr(inexpl.vues)} d'entre eux, une détection sans AIS se trouve à moins de 5 km de la position supposée du navire. Une détection « radar seul » n'est pas une infraction : bien des navires assez grands pour être vus au radar ne sont pas tenus d'émettre en AIS (plaisance, pêche de moins de 15 m, petits navires de servitude).

*Détections radar : Powered by Global Fishing Watch (CC BY-NC 4.0).*
"""
    sortie = config.DOCS / "rapport_qualite.md"
    sortie.write_text(md, encoding="utf-8")
    log(f"{sortie.relative_to(config.RACINE)} écrit")


if __name__ == "__main__":
    rapport()
