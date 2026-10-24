// Récits guidés : trois histoires racontées pas à pas sur la carte, dont deux rejouées dans le temps.
// Données : donnees/recits.json (09_carte_web.py), donnees/fiche/radar.json, donnees/chiffres.json.
// S'appuie sur la page principale : carte, langue, t(), fmt(), T, chiffres.

Object.assign(T.en, {
  hRecits: "Stories", noteRecits: "Three cases told step by step, two of them replayed hour by hour.",
  rCouvTitre: "A blind spot the satellite confirms", rCouvAccroche: "Where shore stations stop hearing ships.",
  rSilTitre: "A silent fishing vessel and a radar echo", rSilAccroche: "Seven hours without AIS, one satellite pass.",
  rMmsiTitre: "One identity, two transmitters", rMmsiAccroche: "A ship that jumps 125 nautical miles in a minute.",
  etape: "Step", sur: "of", precedent: "Back", suivant: "Next", quitter: "Exit", lire: "Play", pause: "Pause", commencer: "Start",
  rCouv1: "South of Bornholm and in Pomeranian Bay, Danish shore stations are far away. The coverage measured from the traffic itself is poor here (red cells): vessels are often lost while crossing.",
  rCouv2: "Sentinel-1 sees ships whether they broadcast or not. Of the {n} vessels the satellite saw and identified in poorly covered cells, {k} were not received by the Danish shore network at that minute (orange). In reliably covered cells: {kf} out of {nf}.",
  rCouv3: "Across the area, the share received follows the coverage map: {pf} in reliable cells, {pm} in poor ones. A source that owes nothing to shore AIS confirms where it falls short, and that is where an independent detection adds the most.",
  rSil1: "{date}. A fishing vessel ({navire}) heads through the Kattegat, in waters where shore stations receive nine neighbours in ten.",
  rSil2: "{h}: its AIS falls silent. Other vessels around keep being received, so it is not a reception gap.",
  rSil3: "{h}: Sentinel-1 passes over. One echo matches no AIS at all, less than 5 km from where the vessel should be on its way (orange ring).",
  rSil4: "{h}: the AIS comes back {d} nautical miles further on, after {duree} hours. Nothing ordinary explains this silence. A faulty transmitter remains possible: it is a case worth a closer look, not proof of anything.",
  rMmsi1: "Under a single MMSI, a cargo vessel ({navire}) reports its position about once a minute, as AIS requires.",
  rMmsi2: "Then a position {d} nautical miles away, a minute later, and back again (violet lines): {n} impossible jumps in {h} hours.",
  rMmsi3: "No ship sails at 1,000 knots: two transmitters share one identity, through a misconfigured unit or a deliberate copy. AIS alone cannot tell which position is genuine; an independent geolocation can.",
  legRecu: "received by shore AIS", legNonRecu: "identified, not received by shore AIS", legSansAis: "no AIS at all", legProche: "no AIS, near the silent vessel",
  legAttendu: "expected position at the pass (5 km ring)", legSaut: "impossible jump", legPos: "reported position",
  rSemTitre: "Chronic or one-off?", rSemAccroche: "The same analysis, four weeks in a row.",
  rSem1: "One week of shore coverage, measured from the traffic itself (the study week). A blind spot seen in a single week may be bad luck: weather, a station down.",
  rSem2: "Over four weeks, {c} cells are poor at least three weeks out of four (dark red), about {km} km²: {pays}. These are structural gaps of the shore network, where an independent detection pays off week after week.",
  rSem3: "Unexplained silences, on the contrary, do not come back: {n} in four weeks, from {v} different vessels, and only {f} areas of 250 km² saw one in two different weeks (orange outline). If they were an artefact of the method, they would recur in the same places.",
  legChronique: "chronic blind spot", legRecurrent: "recurring (2 weeks)", legPonctuel: "one-off (1 week)", legFoyer: "area with silences in 2 weeks",
  Germany: "German", Sweden: "Swedish", Poland: "Polish", Denmark: "Danish", Norway: "Norwegian", enEaux: "{n} in {p} waters",
});
Object.assign(T.fr, {
  hRecits: "Récits", noteRecits: "Trois cas racontés pas à pas, dont deux rejoués heure par heure.",
  rCouvTitre: "Un angle mort confirmé par satellite", rCouvAccroche: "Là où les stations côtières n'entendent plus les navires.",
  rSilTitre: "Un navire de pêche silencieux et un écho radar", rSilAccroche: "Sept heures sans AIS, un passage de satellite.",
  rMmsiTitre: "Une identité, deux émetteurs", rMmsiAccroche: "Un navire qui saute de 125 milles en une minute.",
  etape: "Étape", sur: "sur", precedent: "Retour", suivant: "Suite", quitter: "Quitter", lire: "Lecture", pause: "Pause", commencer: "Commencer",
  rCouv1: "Au sud de Bornholm et dans la baie de Poméranie, les stations côtières danoises sont loin. La couverture mesurée à partir du trafic lui-même y est mauvaise (mailles rouges) : les navires sont souvent perdus en traversant.",
  rCouv2: "Sentinel-1 voit les navires, qu'ils émettent ou non. Sur les {n} navires vus et identifiés par le satellite dans les mailles mal couvertes, {k} n'étaient pas reçus par le réseau côtier danois à cette minute (orange). Dans les mailles bien couvertes : {kf} sur {nf}.",
  rCouv3: "Sur toute la zone, la part reçue suit la carte de couverture : {pf} dans les mailles fiables, {pm} dans les mauvaises. Une source qui ne doit rien à l'AIS côtier confirme où il est en défaut, et c'est là qu'une détection indépendante apporte le plus.",
  rSil1: "{date}. Un navire de pêche ({navire}) traverse le Cattégat, dans des eaux où les stations côtières reçoivent neuf voisins sur dix.",
  rSil2: "{h} : son AIS se tait. Les autres navires alentour restent reçus : ce n'est pas un trou de réception.",
  rSil3: "{h} : Sentinel-1 passe. Un écho ne correspond à aucun AIS, à moins de 5 km de l'endroit où le navire devrait se trouver sur sa route (cercle orange).",
  rSil4: "{h} : l'AIS revient {d} milles plus loin, après {duree} heures. Aucune explication ordinaire ne justifie ce silence. Un émetteur défaillant reste possible : c'est un cas à examiner, pas une preuve.",
  rMmsi1: "Sous un seul MMSI, un cargo ({navire}) annonce sa position environ une fois par minute, comme l'AIS l'exige.",
  rMmsi2: "Puis une position à {d} milles de là, une minute plus tard, et retour (traits violets) : {n} sauts impossibles en {h} heures.",
  rMmsi3: "Aucun navire ne file 1 000 nœuds : deux émetteurs partagent une même identité, par erreur de configuration ou par copie délibérée. L'AIS seul ne dit pas quelle position est la vraie ; une géolocalisation indépendante, si.",
  legRecu: "reçu par l'AIS côtier", legNonRecu: "identifié, non reçu par l'AIS côtier", legSansAis: "aucun AIS", legProche: "aucun AIS, près du navire silencieux",
  legAttendu: "position attendue au passage (cercle de 5 km)", legSaut: "saut impossible", legPos: "position annoncée",
  rSemTitre: "Chronique ou ponctuel ?", rSemAccroche: "La même analyse, quatre semaines de suite.",
  rSem1: "Une semaine de couverture côtière, mesurée à partir du trafic lui-même (la semaine d'étude). Un angle mort vu une seule semaine peut tenir au hasard : météo, station en panne.",
  rSem2: "Sur quatre semaines, {c} mailles sont mauvaises au moins trois semaines sur quatre (rouge foncé), soit environ {km} km² : {pays}. Ce sont des manques durables du réseau côtier, là où une détection indépendante sert semaine après semaine.",
  rSem3: "Les silences inexpliqués, au contraire, ne reviennent pas : {n} en quatre semaines, venant de {v} navires différents, et seules {f} zones de 250 km² en ont vu deux semaines différentes (contour orange). S'ils tenaient à un défaut de la méthode, ils reviendraient aux mêmes endroits.",
  legChronique: "angle mort chronique", legRecurrent: "récurrent (2 semaines)", legPonctuel: "ponctuel (1 semaine)", legFoyer: "zone à silences deux semaines",
  Germany: "allemandes", Sweden: "suédoises", Poland: "polonaises", Denmark: "danoises", Norway: "norvégiennes", enEaux: "{n} dans les eaux {p}",
});

const RC = { donnees: null, radar: null, actif: null, etape: 0, t: 0, lecture: null, visibilite: null };
const SIGNAUX = ["inexpl-halo", "inexpl-trait", "inexpl-debut", "inexpl-fin", "mmsi-trait", "mmsi-points", "stationnements", "rencontres", "radar"];
const VUES = ["couverture", "indice", "recurrence", "foyers-fond", "foyers-trait"];

// ---------- outils ----------
const heure = (t0, m) => new Intl.DateTimeFormat(langue === "fr" ? "fr-FR" : "en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "UTC" }).format(new Date(Date.parse(t0) + m * 60000)) + " UTC";
const jour = (t0, m) => new Intl.DateTimeFormat(langue === "fr" ? "fr-FR" : "en-GB", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" }).format(new Date(Date.parse(t0) + m * 60000));
const remplir = (texte, v) => texte.replace(/\{(\w+)\}/g, (_, k) => v[k] ?? "");
const fc = (features) => ({ type: "FeatureCollection", features });
const point = (c, p = {}) => ({ type: "Feature", properties: p, geometry: { type: "Point", coordinates: c } });
const ligne = (cs, p = {}) => ({ type: "Feature", properties: p, geometry: { type: "LineString", coordinates: cs } });
function cercle([lon, lat], km) {
  const pts = [];
  for (let i = 0; i <= 48; i++) {
    const a = (i / 48) * 2 * Math.PI;
    pts.push([lon + (km / (111.32 * Math.cos((lat * Math.PI) / 180))) * Math.cos(a), lat + (km / 110.57) * Math.sin(a)]);
  }
  return { type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [pts] } };
}
const marge = () => (matchMedia("(max-width: 760px)").matches ? 24 : { top: 40, right: 50, bottom: 40, left: 430 });
function source(id, donnees) {
  if (carte.getSource(id)) carte.getSource(id).setData(donnees);
  else carte.addSource(id, { type: "geojson", data: donnees });
}
function couche(def) { if (!carte.getLayer(def.id)) carte.addLayer(def); }
const pourcent = (v) => fmt(100 * v, 0) + " %";

// ---------- les trois récits ----------
const RECITS = {
  couverture: {
    titre: "rCouvTitre", accroche: "rCouvAccroche", couleur: "#d8693f",
    etapes: [
      { cadre: [[13.3, 54.05], [16.6, 56.05]], vues: ["couverture"], texte: () => t("rCouv1") },
      { cadre: [[13.3, 54.05], [16.6, 56.05]], vues: ["couverture"], radar: true, legende: ["recu", "nonrecu"],
        texte: () => { const v = valid(); return remplir(t("rCouv2"), { n: fmt(v.Poor.n), k: fmt(v.Poor.n - v.Poor.recus), nf: fmt(v.Reliable.n), kf: fmt(v.Reliable.n - v.Reliable.recus) }); } },
      { cadre: [[8.6, 53.7], [16.9, 58.4]], vues: ["couverture"], radar: true, legende: ["recu", "nonrecu"],
        texte: () => { const v = valid(); return remplir(t("rCouv3"), { pf: pourcent(v.Reliable.part), pm: pourcent(v.Poor.part) }); } },
    ],
  },
  semaines: {
    titre: "rSemTitre", accroche: "rSemAccroche", couleur: "#a63c14", option: "semaines",
    etapes: [
      { cadre: [[8.6, 53.7], [16.9, 58.4]], vues: ["couverture"], texte: () => t("rSem1") },
      { cadre: [[8.6, 53.7], [16.9, 58.4]], vues: ["recurrence"], legende: ["chronique", "recurrent", "ponctuel"],
        texte: () => {
          const m = semaines.mailles, pays = Object.entries(semaines.chroniques_par_pays || {}).sort((a, b) => b[1] - a[1])
            .map(([p, n]) => remplir(t("enEaux"), { n: fmt(n), p: t(p) })).join(", ");
          return remplir(t("rSem2"), { c: fmt(m.Chronic || 0), km: fmt(semaines.chroniques_km2), pays });
        } },
      { cadre: [[11.8, 54.3], [16.4, 56.4]], vues: ["recurrence", "foyers-fond", "foyers-trait"], points: true, attenuer: true, legende: ["chronique", "foyer", "semaines"],
        texte: () => { const i = semaines.inexpliquees; return remplir(t("rSem3"), { n: fmt(i.total), v: fmt(i.navires), f: fmt(semaines.foyers) }); } },
    ],
  },
  silence: {
    titre: "rSilTitre", accroche: "rSilAccroche", couleur: "#eb6834", temps: true,
    duree: () => RC.donnees.silence.trace.at(-1)[2],
    etapes: [
      { segment: (S) => [0, S.debut - 1], texte: (S) => remplir(t("rSil1"), { date: jour(S.t0, S.debut).replace(/^./, (c) => c.toUpperCase()), navire: S.navire }) },
      { segment: (S) => [S.debut, S.passe - 1], texte: (S) => remplir(t("rSil2"), { h: heure(S.t0, S.debut) }) },
      { segment: (S) => [S.passe, S.fin - 1], legende: ["recu", "nonrecu", "sansais", "proche", "attendu"], texte: (S) => remplir(t("rSil3"), { h: heure(S.t0, S.passe) }) },
      { segment: (S) => [S.fin, S.trace.at(-1)[2]], legende: ["sansais", "proche", "attendu"], texte: (S) => remplir(t("rSil4"), { h: heure(S.t0, S.fin), d: fmt(S.distance_nm, 0), duree: fmt(S.duree_h, 1) }) },
    ],
  },
  identite: {
    titre: "rMmsiTitre", accroche: "rMmsiAccroche", couleur: "#4a3aa7", temps: true,
    duree: () => RC.donnees.identite.positions.at(-1)[2],
    etapes: [
      { segment: (M) => [0, M.sauts[0][4] - 1], legende: ["pos"], texte: (M) => remplir(t("rMmsi1"), { navire: M.navire }) },
      { segment: (M) => [M.sauts[0][4], Math.round(M.positions.at(-1)[2] * 0.75)], legende: ["pos", "saut"], texte: (M) => remplir(t("rMmsi2"), { d: fmt(M.distance_nm, 0), n: M.sauts.length, h: M.duree_h }) },
      { segment: (M) => [Math.round(M.positions.at(-1)[2] * 0.75) + 1, M.positions.at(-1)[2]], legende: ["pos", "saut"], texte: () => t("rMmsi3") },
    ],
  },
};
function valid() {
  const v = {};
  for (const r of chiffres.validation_radar || []) v[r.classe] = r;
  return v;
}

// ---------- dessin des couches propres aux récits ----------
function couchesRecit() {
  source("rc-radar", fc([]));
  couche({ id: "rc-radar-recu", type: "circle", source: "rc-radar", filter: ["==", ["get", "etat"], 0],
    paint: { "circle-radius": 3.2, "circle-color": "#8d9aa4", "circle-stroke-color": "#fff", "circle-stroke-width": 0.8 } });
  couche({ id: "rc-radar-nonrecu", type: "circle", source: "rc-radar", filter: ["==", ["get", "etat"], 1],
    paint: { "circle-radius": 4.6, "circle-color": "#eb6834", "circle-stroke-color": "#fff", "circle-stroke-width": 1.2 } });
  couche({ id: "rc-radar-sansais", type: "symbol", source: "rc-radar", filter: [">=", ["get", "etat"], 2],
    layout: { "icon-image": "carre", "icon-size": 1.05, "icon-allow-overlap": true } });
  couche({ id: "rc-radar-proche", type: "circle", source: "rc-radar", filter: ["==", ["get", "etat"], 3],
    paint: { "circle-radius": 13, "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": "#eb6834", "circle-stroke-width": 2.5 } });
  source("rc-semaines", fc([]));
  couche({ id: "rc-semaines-pts", type: "circle", source: "rc-semaines",
    paint: { "circle-radius": 5, "circle-color": ["match", ["get", "rang"], 0, "#f7c5a8", 1, "#f19a6b", 2, "#e46a35", "#b8461c"],
      "circle-stroke-color": "#52514e", "circle-stroke-width": 1 } });
  source("rc-attendu", fc([]));
  couche({ id: "rc-attendu-zone", type: "fill", source: "rc-attendu", filter: ["==", "$type", "Polygon"], paint: { "fill-color": "#eb6834", "fill-opacity": 0.08 } });
  couche({ id: "rc-attendu-cercle", type: "line", source: "rc-attendu", filter: ["==", "$type", "Polygon"], paint: { "line-color": "#eb6834", "line-width": 1.6, "line-dasharray": [2, 1.5] } });
  couche({ id: "rc-attendu-route", type: "line", source: "rc-attendu", filter: ["==", "$type", "LineString"], paint: { "line-color": "#eb6834", "line-width": 1.6, "line-dasharray": [1, 1.6], "line-opacity": 0.8 } });
  source("rc-trace", fc([]));
  couche({ id: "rc-trace-ligne", type: "line", source: "rc-trace", filter: ["==", "$type", "LineString"], paint: { "line-color": "#1d1d1b", "line-width": 2.2, "line-opacity": 0.85 } });
  couche({ id: "rc-trace-pos", type: "circle", source: "rc-trace", filter: ["==", ["get", "role"], "pos"],
    paint: { "circle-radius": 6, "circle-color": "#1d1d1b", "circle-stroke-color": "#fff", "circle-stroke-width": 2 } });
  couche({ id: "rc-trace-muet", type: "circle", source: "rc-trace", filter: ["==", ["get", "role"], "muet"],
    paint: { "circle-radius": 7, "circle-color": "#fff", "circle-stroke-color": "#eb6834", "circle-stroke-width": 2.5 } });
  source("rc-mmsi", fc([]));
  couche({ id: "rc-mmsi-saut", type: "line", source: "rc-mmsi", filter: ["==", "$type", "LineString"],
    paint: { "line-color": "#4a3aa7", "line-width": ["case", ["get", "recent"], 2.6, 1], "line-opacity": ["case", ["get", "recent"], 0.95, 0.35], "line-dasharray": [2, 1.5] } });
  couche({ id: "rc-mmsi-pos", type: "circle", source: "rc-mmsi", filter: ["==", "$type", "Point"],
    paint: { "circle-radius": ["case", ["get", "dernier"], 6, 3.4], "circle-color": "#4a3aa7",
      "circle-opacity": ["get", "opacite"], "circle-stroke-color": "#fff", "circle-stroke-width": ["case", ["get", "dernier"], 2, 0] } });
}
const IDS_RECIT = ["rc-semaines-pts", "rc-radar-recu", "rc-radar-nonrecu", "rc-radar-sansais", "rc-radar-proche", "rc-attendu-zone", "rc-attendu-cercle", "rc-attendu-route",
  "rc-trace-ligne", "rc-trace-pos", "rc-trace-muet", "rc-mmsi-saut", "rc-mmsi-pos"];
const SOURCES_RECIT = ["rc-semaines", "rc-radar", "rc-attendu", "rc-trace", "rc-mmsi"];

// état du récit « silence » à l'instant m (minutes depuis t0)
function dessinerSilence(m) {
  const S = RC.donnees.silence, avant = S.trace.filter((p) => p[2] <= Math.min(m, S.debut)), apres = S.trace.filter((p) => p[2] >= S.fin && p[2] <= m);
  const f = [];
  if (avant.length > 1) f.push(ligne(avant.map((p) => [p[0], p[1]])));
  if (apres.length > 1) f.push(ligne(apres.map((p) => [p[0], p[1]])));
  const debut = S.trace.filter((p) => p[2] <= S.debut).at(-1), fin = S.trace.find((p) => p[2] >= S.fin);
  if (m < S.debut && avant.length) f.push(point(avant.at(-1).slice(0, 2), { role: "pos" }));
  else if (m < S.fin && debut) f.push(point(debut.slice(0, 2), { role: "muet" }));
  else if (apres.length) { f.push(point(apres.at(-1).slice(0, 2), { role: "pos" })); if (debut) f.push(point(debut.slice(0, 2), { role: "muet" })); }
  carte.getSource("rc-trace").setData(fc(f));
  const attendu = [];
  if (m >= S.passe && debut && fin) {
    const k = (S.passe - debut[2]) / (fin[2] - debut[2]), c = [debut[0] + k * (fin[0] - debut[0]), debut[1] + k * (fin[1] - debut[1])];
    attendu.push(cercle(c, 5), ligne([debut.slice(0, 2), fin.slice(0, 2)]));
  }
  carte.getSource("rc-attendu").setData(fc(attendu));
  const radar = m >= S.passe ? S.radar.map(([x, y, e]) => point([x, y], { etat: e })) : [];
  carte.getSource("rc-radar").setData(fc(m >= S.fin ? radar.filter((p) => p.properties.etat >= 2) : radar));
}
// état du récit « MMSI » : positions des six dernières heures, sauts déjà survenus
function dessinerMmsi(m) {
  const M = RC.donnees.identite, f = [], fenetre = 360;
  const vues = M.positions.filter((p) => p[2] <= m && p[2] > m - fenetre);
  vues.forEach((p, i) => f.push(point([p[0], p[1]], { opacite: 0.25 + 0.75 * (1 - (m - p[2]) / fenetre), dernier: i === vues.length - 1 })));
  for (const [x1, y1, x2, y2, ts] of M.sauts) if (ts <= m) f.push(ligne([[x1, y1], [x2, y2]], { recent: m - ts < 90 }));
  carte.getSource("rc-mmsi").setData(fc(f));
}

// ---------- déroulé ----------
async function chargerRecits() {
  if (RC.donnees) return;
  const [d, r] = await Promise.all([fetch("donnees/recits.json").then((x) => x.json()), fetch("donnees/fiche/radar.json").then((x) => x.json())]);
  RC.donnees = d; RC.radar = r;
  if (semaines) RC.semaines = await fetch("donnees/inexpliquees_semaines.geojson").then((x) => (x.ok ? x.json() : null)).catch(() => null);
}
async function commencer(cle) {
  await chargerRecits();
  if (RC.actif) arreterLecture();
  else RC.visibilite = Object.fromEntries([...SIGNAUX, ...VUES].filter((id) => carte.getLayer(id)).map((id) => [id, carte.getLayoutProperty(id, "visibility") || "visible"]));
  RC.actif = cle; RC.etape = 0;
  document.querySelectorAll(".maplibregl-popup").forEach((p) => p.remove());
  SIGNAUX.forEach((id) => carte.getLayer(id) && carte.setLayoutProperty(id, "visibility", "none"));
  couchesRecit();
  document.getElementById("recit").hidden = false;
  history.replaceState(null, "", "#recit=" + cle);
  allerA(0, true);
}
function quitter() {
  arreterLecture();
  IDS_RECIT.forEach((id) => carte.getLayer(id) && carte.removeLayer(id));
  SOURCES_RECIT.forEach((id) => carte.getSource(id) && carte.removeSource(id));
  Object.entries(RC.visibilite || {}).forEach(([id, v]) => carte.setLayoutProperty(id, "visibility", v));
  if (carte.getLayer("recurrence")) carte.setPaintProperty("recurrence", "fill-opacity", 0.92);
  RC.actif = null;
  document.getElementById("recit").hidden = true;
  history.replaceState(null, "", location.pathname);
  carte.fitBounds([[8.6, 53.7], [16.9, 58.4]], { padding: 20, duration: 900 });
}
function donneesRecit() { return RC.actif === "silence" ? RC.donnees.silence : RC.donnees.identite; }
function allerA(i, lancer) {
  const R = RECITS[RC.actif], e = R.etapes[i];
  RC.etape = i;
  VUES.forEach((id) => carte.getLayer(id) && carte.setLayoutProperty(id, "visibility", (e.vues || []).includes(id) ? "visible" : "none"));
  if (R.temps) {
    const D = donneesRecit(), [a, b] = e.segment(D);
    if (i === 0 || !RC.cadre) { carte.fitBounds(D.cadre, { padding: marge(), duration: 1000 }); RC.cadre = true; }
    regler(a);
    if (lancer) lire(b);
  } else {
    RC.cadre = false;
    carte.fitBounds(e.cadre, { padding: marge(), duration: 1100 });
    carte.getSource("rc-radar").setData(fc(e.radar ? RC.radar.filter((d) => d[3] && d[4] !== null).map((d) => point([d[0], d[1]], { etat: d[4] ? 0 : 1 })) : []));
    // les mailles s'éclaircissent quand les points des silences doivent ressortir
    if (carte.getLayer("recurrence")) carte.setPaintProperty("recurrence", "fill-opacity", e.attenuer ? 0.4 : 0.92);
    const jours = semaines ? semaines.semaines.map((w) => w.semaine) : [];
    carte.getSource("rc-semaines").setData(fc(e.points && RC.semaines ? RC.semaines.features.map((f) => point(f.geometry.coordinates, { rang: jours.indexOf(f.properties.semaine) })) : []));
  }
  rendreCarte();
}
function etapeDe(m) {
  const R = RECITS[RC.actif], D = donneesRecit();
  let k = 0;
  R.etapes.forEach((e, i) => { if (m >= e.segment(D)[0]) k = i; });
  return k;
}
function regler(m) {
  const D = donneesRecit();
  RC.t = Math.max(0, Math.min(m, RECITS[RC.actif].duree()));
  (RC.actif === "silence" ? dessinerSilence : dessinerMmsi)(RC.t);
  const k = etapeDe(RC.t);
  if (k !== RC.etape) { RC.etape = k; rendreCarte(); }
  const curseur = document.getElementById("recit-curseur");
  if (curseur) { curseur.value = RC.t; document.getElementById("recit-heure").textContent = `${jour(D.t0, RC.t)} · ${heure(D.t0, RC.t)}`; }
}
// lecture : un segment dure environ 7 secondes, quelle que soit sa longueur en heures
function lire(jusqua) {
  arreterLecture();
  const fin = jusqua ?? RECITS[RC.actif].duree(), depart = RC.t, duree = Math.max(2500, Math.min(9000, (fin - depart) * 25));
  const t0 = performance.now();
  const pas = (now) => {
    const k = Math.min(1, (now - t0) / duree);
    regler(depart + k * (fin - depart));
    if (k < 1) RC.lecture = requestAnimationFrame(pas); else { RC.lecture = null; majBouton(); }
  };
  RC.lecture = requestAnimationFrame(pas);
  majBouton();
}
function arreterLecture() { if (RC.lecture) cancelAnimationFrame(RC.lecture); RC.lecture = null; majBouton(); }
function majBouton() {
  const b = document.getElementById("recit-lire");
  if (b) { b.textContent = RC.lecture ? "❚❚" : "▶"; b.setAttribute("aria-label", t(RC.lecture ? "pause" : "lire")); }
}

const LEGENDES = {
  recu: ['<svg viewBox="0 0 14 14"><circle cx="7" cy="7" r="3.6" fill="#8d9aa4" stroke="#fff"/></svg>', "legRecu"],
  nonrecu: ['<svg viewBox="0 0 14 14"><circle cx="7" cy="7" r="4.6" fill="#eb6834" stroke="#fff"/></svg>', "legNonRecu"],
  sansais: ['<svg viewBox="0 0 14 14"><rect x="3" y="3" width="8" height="8" fill="#fff" stroke="#52514e" stroke-width="1.6"/></svg>', "legSansAis"],
  proche: ['<svg viewBox="0 0 14 14"><circle cx="7" cy="7" r="5.6" fill="none" stroke="#eb6834" stroke-width="1.6"/><rect x="4.5" y="4.5" width="5" height="5" fill="#fff" stroke="#52514e"/></svg>', "legProche"],
  attendu: ['<svg viewBox="0 0 14 14"><circle cx="7" cy="7" r="5.4" fill="rgba(235,104,52,.1)" stroke="#eb6834" stroke-dasharray="2 1.5"/></svg>', "legAttendu"],
  saut: ['<svg viewBox="0 0 14 14"><line x1="1" y1="12" x2="13" y2="2" stroke="#4a3aa7" stroke-width="2" stroke-dasharray="2.5 2"/></svg>', "legSaut"],
  pos: ['<svg viewBox="0 0 14 14"><circle cx="7" cy="7" r="3" fill="#4a3aa7"/></svg>', "legPos"],
  chronique: ['<svg viewBox="0 0 14 14"><rect x="1" y="2" width="12" height="10" fill="#a63c14"/></svg>', "legChronique"],
  recurrent: ['<svg viewBox="0 0 14 14"><rect x="1" y="2" width="12" height="10" fill="#e0784a"/></svg>', "legRecurrent"],
  ponctuel: ['<svg viewBox="0 0 14 14"><rect x="1" y="2" width="12" height="10" fill="#f6cdb3"/></svg>', "legPonctuel"],
  foyer: ['<svg viewBox="0 0 14 14"><path d="M4 1.5 L10 1.5 L13 7 L10 12.5 L4 12.5 L1 7 Z" fill="rgba(235,104,52,.12)" stroke="#eb6834" stroke-width="1.5"/></svg>', "legFoyer"],
};
// une pastille par semaine, du plus clair (la plus ancienne) au plus foncé (la semaine d'étude)
function legendeSemaines() {
  const teintes = ["#f7c5a8", "#f19a6b", "#e46a35", "#b8461c"];
  const jourSem = (d) => new Intl.DateTimeFormat(langue === "fr" ? "fr-FR" : "en-GB", { day: "numeric", month: "short", timeZone: "UTC" }).format(new Date(d));
  return semaines.semaines.map((w, i) => `<span><svg viewBox="0 0 14 14"><circle cx="7" cy="7" r="4.5" fill="${teintes[i]}" stroke="#fff"/></svg>${jourSem(w.semaine)}</span>`).join("");
}
function rendreCarte() {
  const R = RECITS[RC.actif], e = R.etapes[RC.etape], D = R.temps ? donneesRecit() : null, n = R.etapes.length;
  const temps = R.temps ? `<div class="recit-temps">
      <button type="button" id="recit-lire" class="recit-lire" aria-label="${t("lire")}">${RC.lecture ? "❚❚" : "▶"}</button>
      <input type="range" id="recit-curseur" min="0" max="${R.duree()}" step="1" value="${RC.t}" aria-label="${t("lire")}">
      <span id="recit-heure" class="recit-heure">${jour(D.t0, RC.t)} · ${heure(D.t0, RC.t)}</span></div>` : "";
  document.getElementById("recit").innerHTML = `
    <div class="recit-tete"><span class="recit-pastille" style="background:${R.couleur}"></span>
      <span class="recit-kicker">${t("etape")} ${RC.etape + 1} ${t("sur")} ${n}</span>
      <button type="button" class="recit-quitter" data-r="quitter" aria-label="${t("quitter")}">✕</button></div>
    <h3>${t(R.titre)}</h3>
    <p class="recit-texte" aria-live="polite">${e.texte(D)}</p>
    ${(e.legende || []).length ? `<div class="recit-legende">${e.legende.map((k) => k === "semaines" ? legendeSemaines() : `<span>${LEGENDES[k][0]}${t(LEGENDES[k][1])}</span>`).join("")}</div>` : ""}
    ${temps}
    <div class="recit-nav">
      <div class="recit-points">${R.etapes.map((_, i) => `<button type="button" class="${i === RC.etape ? "actif" : ""}" data-r="aller" data-i="${i}" aria-label="${t("etape")} ${i + 1}"></button>`).join("")}</div>
      <button type="button" data-r="precedent" ${RC.etape === 0 ? "disabled" : ""}>← ${t("precedent")}</button>
      <button type="button" class="primaire" data-r="${RC.etape === n - 1 ? "quitter" : "suivant"}">${RC.etape === n - 1 ? t("quitter") : t("suivant") + " →"}</button>
    </div>`;
  const c = document.getElementById("recit-curseur");
  if (c) c.addEventListener("input", () => { arreterLecture(); regler(+c.value); });
}
document.addEventListener("click", (ev) => {
  const b = ev.target.closest("#recit [data-r], #recit #recit-lire, .recit-choix");
  if (!b) return;
  if (b.classList.contains("recit-choix")) return commencer(b.dataset.recit);
  if (b.id === "recit-lire") return RC.lecture ? arreterLecture() : lire(RC.t >= RECITS[RC.actif].duree() ? (regler(0), undefined) : undefined);
  const n = RECITS[RC.actif].etapes.length;
  if (b.dataset.r === "quitter") quitter();
  if (b.dataset.r === "suivant" && RC.etape < n - 1) allerA(RC.etape + 1, true);
  if (b.dataset.r === "precedent" && RC.etape > 0) allerA(RC.etape - 1, true);
  if (b.dataset.r === "aller") allerA(+b.dataset.i, true);
});
document.addEventListener("keydown", (e) => {
  if (!RC.actif || e.target.closest("input, select, [contenteditable=true]")) return;
  if (e.key === "Escape") quitter();
  if (e.key === "ArrowRight") allerA(Math.min(RC.etape + 1, RECITS[RC.actif].etapes.length - 1), true);
  if (e.key === "ArrowLeft") allerA(Math.max(RC.etape - 1, 0), true);
});

function rendrePanneauRecits() {
  const ordre = ["couverture", "silence", "identite", "semaines"];
  document.getElementById("recits-liste").innerHTML = ordre.map((cle) => [cle, RECITS[cle]]).filter(([, R]) => !R.option || semaines).map(([cle, R]) => `
    <button type="button" class="recit-choix" data-recit="${cle}">
      <span class="recit-pastille" style="background:${R.couleur}"></span>
      <span><b>${t(R.titre)}</b><span>${t(R.accroche)}</span></span><span class="recit-fleche" aria-hidden="true">→</span>
    </button>`).join("");
}
document.addEventListener("carte-prete", () => {
  rendrePanneauRecits();
  document.querySelectorAll(".langue button").forEach((b) => b.addEventListener("click", () => {
    rendrePanneauRecits();
    if (RC.actif) rendreCarte();
  }));
  const h = decodeURIComponent(location.hash);
  if (h.startsWith("#recit=") && RECITS[h.slice(7)] && (!RECITS[h.slice(7)].option || semaines)) commencer(h.slice(7));
});
