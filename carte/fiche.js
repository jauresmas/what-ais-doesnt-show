// Fiche de zone dans le navigateur : zone prédéfinie, dessinée ou importée, chiffres calculés avec les
// règles de l'outil QGIS (qgis/outils/fiche_zone.py), feuille A4 imprimable en PDF.
// S'appuie sur la page principale : carte, langue, t(), fmt(), T, LIEUX, SYMBOLES.

Object.assign(T.en, {
  hFiche: "Zone sheet", noteFiche: "Pick an area, draw one or import a GeoJSON file: the sheet is computed in your browser with the same rules as the QGIS tool, then prints to an A4 PDF.",
  btnFiche: "Create the sheet", btnDessiner: "Draw an area", btnImporter: "Import GeoJSON", maZone: "My area",
  aideDessin: "Click to add points. Double-click, or click the first point, to close the area. Esc cancels.",
  terminer: "Close the area", annuler: "Cancel", calcul: "Computing the sheet…",
  horsZone: "This area does not overlap the study area.", fichierInvalide: "No polygon found in this file.",
  imprimer: "Print or save as PDF", telCsv: "Figures (CSV)", telZone: "Area (GeoJSON)", copierLien: "Copy link", fermer: "Close",
  lienCopie: "Link copied", lienTropLong: "Area too detailed for a link: download it as GeoJSON instead.",
  kFiche: "Zone sheet · Shore-based AIS · Open data", periode: "13–19 October 2026",
  sousPerso: "Custom area", dansEtude: "within the study area", km2: "km²",
  fInexpl: "unexplained AIS silences", fInexplNav: "vessels", fNavires: "class A vessels tracked", fNaviresApprox: "class A vessels in the area (estimated from H3 cells)",
  fCouverte: "of underway traffic in reliably covered waters",
  fSilences: "AIS silences of 2 hours or more", fReception: "explained by shore reception gaps", fMmsi: "vessels whose MMSI is shared by two transmitters",
  fStat: "slow passages over a cable or pipeline (30 min or more)", fNavStat: "vessels behind these slow passages", fRenc: "ship-to-ship encounters (2 hours or more)",
  fRadar: "radar detections without AIS (Sentinel-1, wind farms excluded)", fRadarRecus: "of radar-seen vessels received by the shore network",
  hGraphe: "Where the AIS silences come from", hLecture: "How to read it",
  lecture: "A silence is a gap of 2 hours or more between two positions of the same vessel. It is called unexplained only once every ordinary cause has been ruled out, in order: service or state vessel, exit from the area, inland waterway, port stay, reception gap, possible port call and possible trip out of coverage.",
  methode: "About these figures. One week of positions broadcast by commercial vessels (AIS class A) and received by Denmark's coastal stations. A silence is counted in the area where it begins. These are signals worth a closer look, not proof of wrongdoing, and no vessel is named. Full method and code: github.com/jauresmas/what-ais-doesnt-show.",
  calculExact: "Figures from the full processing chain.",
  calculNav: "Figures computed in your browser with the same rules; vessel count estimated.",
  sources: "Sources:",
  genere: "Generated on", depuis: "from the web map", projet: "Independent portfolio project · Jaurès Daa-Hingbanon, GIS analyst",
  projection: "Web Mercator", nm: "NM",
});
Object.assign(T.fr, {
  hFiche: "Fiche de zone", noteFiche: "Choisissez une zone, dessinez-la ou importez un fichier GeoJSON : la fiche est calculée dans votre navigateur avec les règles de l'outil QGIS, puis s'imprime en PDF A4.",
  btnFiche: "Créer la fiche", btnDessiner: "Dessiner une zone", btnImporter: "Importer un GeoJSON", maZone: "Ma zone",
  aideDessin: "Cliquez pour poser les sommets. Double-cliquez, ou cliquez sur le premier point, pour fermer la zone. Échap annule.",
  terminer: "Fermer la zone", annuler: "Annuler", calcul: "Calcul de la fiche…",
  horsZone: "Cette zone ne recoupe pas l'aire d'étude.", fichierInvalide: "Aucun polygone dans ce fichier.",
  imprimer: "Imprimer ou enregistrer en PDF", telCsv: "Chiffres (CSV)", telZone: "Zone (GeoJSON)", copierLien: "Copier le lien", fermer: "Fermer",
  lienCopie: "Lien copié", lienTropLong: "Zone trop détaillée pour un lien : téléchargez-la plutôt en GeoJSON.",
  kFiche: "Fiche de zone · AIS côtier · Données ouvertes", periode: "13–19 octobre 2026",
  sousPerso: "Zone personnalisée", dansEtude: "dans l'aire d'étude", km2: "km²",
  fInexpl: "silences AIS inexpliqués", fInexplNav: "navires", fNavires: "navires de classe A suivis", fNaviresApprox: "navires de classe A dans la zone (estimation par mailles H3)",
  fCouverte: "du trafic en route dans des eaux bien couvertes",
  fSilences: "silences AIS de 2 heures ou plus", fReception: "dus aux trous de réception côtière", fMmsi: "navires dont le MMSI est partagé par deux émetteurs",
  fStat: "passages lents au-dessus d'un câble ou d'un pipeline (30 min ou plus)", fNavStat: "navires à l'origine de ces passages lents", fRenc: "rencontres en mer (2 heures ou plus)",
  fRadar: "détections radar sans AIS (Sentinel-1, hors parcs éoliens)", fRadarRecus: "des navires vus au radar reçus par le réseau côtier",
  hGraphe: "D'où viennent les silences AIS", hLecture: "Comment lire",
  lecture: "Un silence est un écart de 2 heures ou plus entre deux positions d'un même navire. Il n'est dit inexpliqué qu'une fois écartées, dans l'ordre, toutes les causes ordinaires : navire de servitude ou d'État, sortie de la zone, navigation intérieure, séjour au port, trou de réception, escale possible et sortie de couverture possible.",
  methode: "À propos de ces chiffres. Une semaine de positions émises par les navires de commerce (AIS classe A) et reçues par les stations côtières danoises. Un silence est compté dans la zone où il commence. Ce sont des signaux à examiner, pas des preuves d'infraction, et aucun navire n'est nommé. Méthode complète et code : github.com/jauresmas/what-ais-doesnt-show.",
  calculExact: "Chiffres issus de la chaîne de traitement complète.",
  calculNav: "Chiffres calculés dans votre navigateur avec les mêmes règles ; nombre de navires estimé.",
  sources: "Sources :",
  genere: "Produite le", depuis: "depuis la carte web", projet: "Projet personnel de démonstration · Jaurès Daa-Hingbanon, géomaticien",
  projection: "Web Mercator", nm: "milles",
  "Danish Straits & Bornholm Basin": "Détroits danois et bassin de Bornholm", "Study area": "Aire d'étude",
  "Within the study area": "Dans l'aire d'étude", "Danish EEZ": "ZEE danoise", "Swedish EEZ": "ZEE suédoise",
  "German EEZ": "ZEE allemande", "Polish EEZ": "ZEE polonaise",
});
const CATEGORIES_FR = ["Position incohérente", "Navire de servitude ou d'État", "Sortie de la zone",
  "Navigation intérieure ou portuaire", "Arrêt au port ou au mouillage", "Réception insuffisante probable",
  "Escale ou détour côtier possible", "Sortie de couverture possible", "Coupure inexpliquée"];
const LIBS = ["https://cdn.jsdelivr.net/npm/@turf/turf@7.1.0/turf.min.js", "https://unpkg.com/h3-js@4.1.0/dist/h3-js.umd.js"];

const F = { donnees: null, zone: null, choix: "study-area", resultat: null, dessin: null };
window.dessinEnCours = false;

// ---------- chargement à la demande ----------
function script(src) {
  return new Promise((ok, ko) => { const s = document.createElement("script"); s.src = src; s.onload = ok; s.onerror = () => ko(new Error(src)); document.head.appendChild(s); });
}
async function charger() {
  if (F.donnees) return F.donnees;
  const json = (n) => fetch(n).then((r) => (r.ok ? r.json() : null));
  const [, , silences, mailles, radar, zones, inexpl, sauts, stat, renc] = await Promise.all([
    ...LIBS.map(script),
    json("donnees/fiche/silences.json"), json("donnees/fiche/mailles.json"), json("donnees/fiche/radar.json"),
    json("donnees/fiche/zones.json"), json("donnees/silences_inexpliques.geojson"), json("donnees/mmsi_partages.geojson"),
    json("donnees/stationnements.geojson"), json("donnees/rencontres.geojson")]);
  F.donnees = { silences, mailles, radar, zones, inexpl, sauts, stat, renc };
  return F.donnees;
}
async function zonesPredefinies() {
  if (!F.zones) F.zones = await fetch("donnees/fiche/zones.json").then((r) => r.json());
  return F.zones;
}

// ---------- calcul (mêmes règles que l'outil QGIS) ----------
function calculer(zone) {
  const D = F.donnees, etude = D.zones.features[0];
  const z = turf.intersect(turf.featureCollection([turf.feature(zone.geometry), etude]));
  if (!z) return null;
  const [x0, y0, x1, y1] = turf.bbox(z);
  const dedans = (c) => c[0] >= x0 && c[0] <= x1 && c[1] >= y0 && c[1] <= y1 && turf.booleanPointInPolygon(c, z);
  const premier = (g) => (g.type === "LineString" ? g.coordinates[0] : g.coordinates[0][0]);

  const comptes = new Array(9).fill(0);
  for (const [lon, lat, k] of D.silences.s) if (dedans([lon, lat])) comptes[k]++;
  const navInexpl = new Set(D.inexpl.features.filter((f) => dedans(premier(f.geometry))).map((f) => f.properties.navire));
  const navMmsi = new Set(D.sauts.features.filter((f) => dedans(premier(f.geometry))).map((f) => f.properties.navire));
  const st = D.stat.features.filter((f) => dedans(f.geometry.coordinates));
  const nbRenc = D.renc.features.filter((f) => dedans(f.geometry.coordinates)).length;

  // trafic en route au prorata de la surface de chaque maille dans la zone (comme l'outil QGIS) ;
  // navires : ceux des mailles dont le centre est dans la zone (estimation, la chaîne compte les positions)
  const M = D.mailles, navires = new Set(), sommetsZone = [], touchees = [];
  turf.coordEach(z, (c) => sommetsZone.push(c));
  let heures = 0, fiables = 0;
  for (let i = 0; i < M.h.length; i++) {
    const [lat, lon] = h3.cellToLatLng(M.h[i]);
    if (lon < x0 - 0.08 || lon > x1 + 0.08 || lat < y0 - 0.05 || lat > y1 + 0.05) continue;
    const anneau = h3.cellToBoundary(M.h[i], true);
    if (anneau[0][0] !== anneau.at(-1)[0] || anneau[0][1] !== anneau.at(-1)[1]) anneau.push(anneau[0]);
    const centre = dedans([lon, lat]), sommets = anneau.slice(0, -1).map(dedans);
    const bb = turf.bbox(turf.lineString(anneau));
    const bordZone = sommetsZone.some(([x, y]) => x >= bb[0] && x <= bb[2] && y >= bb[1] && y <= bb[3]);
    let part;
    if (!bordZone && centre && sommets.every(Boolean)) part = 1;
    else if (!bordZone && !centre && !sommets.some(Boolean)) continue;
    else {
      // seules les mailles coupées par le bord sont découpées, contre le morceau de zone de leur emprise
      const morceau = nettoyer(turf.bboxClip(z, bb)), maille = turf.polygon([anneau]);
      const inter = morceau ? turf.intersect(turf.featureCollection([maille, morceau])) : null;
      if (!inter) continue;
      part = turf.area(inter) / turf.area(maille);
    }
    heures += M.r[i] * part; if (M.f[i]) fiables += M.r[i] * part;
    if (centre) ajouterNavires(M.n[i], navires); else touchees.push(i);
  }
  // zone plus petite qu'une maille : aucun centre dedans, on prend les mailles touchées
  if (!navires.size) touchees.forEach((i) => ajouterNavires(M.n[i], navires));

  let radarSans = 0, juges = 0, recus = 0;
  for (const [lon, lat, d, a, r, s] of D.radar || []) {
    if (!dedans([lon, lat])) continue;
    if (!a && !s) radarSans += d;
    if (r !== null) { juges++; recus += r; }
  }
  return {
    zone: z, exact: false, aire: turf.area(z) / 1e6, comptes,
    nb_silences: comptes.reduce((a, b) => a + b, 0), nb_reception: comptes[5], nb_inexpliquees: comptes[8],
    nav_inexpliquees: navInexpl.size, nav_mmsi_partage: navMmsi.size,
    nb_stationnements: st.length, nav_stationnements: new Set(st.map((f) => f.properties.navire)).size,
    nb_rencontres: nbRenc, nb_navires: navires.size, part_couverte: heures ? fiables / heures : null,
    nb_radar_sans_ais: D.radar ? radarSans : null, part_radar_recus: juges ? recus / juges : null,
  };
}
function ajouterNavires(ecarts, ensemble) { let n = 0; for (const d of ecarts) { n += d; ensemble.add(n); } }
// bboxClip laisse des anneaux vides : on ne garde que les polygones dont l'anneau extérieur subsiste
function nettoyer(f) {
  const g = f.geometry, polys = (g.type === "Polygon" ? [g.coordinates] : g.coordinates)
    .filter((p) => p[0] && p[0].length >= 4).map((p) => p.filter((a) => a.length >= 4));
  return polys.length ? turf.multiPolygon(polys) : null;
}
function resultatPredefini(f) {
  return { ...f.properties, zone: f, exact: true, aire: turf.area(f) / 1e6 };
}

// ---------- zone choisie sur la carte ----------
function montrerZone(zone, cadrer = true) {
  const fc = { type: "FeatureCollection", features: zone ? [zone] : [] };
  if (carte.getSource("zone-choisie")) carte.getSource("zone-choisie").setData(fc);
  else {
    carte.addSource("zone-choisie", { type: "geojson", data: fc });
    carte.addLayer({ id: "zone-choisie-fond", type: "fill", source: "zone-choisie", paint: { "fill-color": "#1d1d1b", "fill-opacity": 0.05 } });
    carte.addLayer({ id: "zone-choisie-trait", type: "line", source: "zone-choisie", paint: { "line-color": "#1d1d1b", "line-width": 2, "line-dasharray": [2, 1.2] } });
  }
  if (zone && cadrer) carte.fitBounds(bboxGeo(zone), { padding: 40, duration: 600 });
}
function bboxGeo(f) {
  let x0 = 180, y0 = 90, x1 = -180, y1 = -90;
  const parcours = (c) => (typeof c[0] === "number" ? (x0 = Math.min(x0, c[0]), x1 = Math.max(x1, c[0]), y0 = Math.min(y0, c[1]), y1 = Math.max(y1, c[1])) : c.forEach(parcours));
  parcours(f.geometry.coordinates);
  return [[x0, y0], [x1, y1]];
}
function definirZonePerso(geom) {
  F.zone = { type: "Feature", properties: { nom: t("maZone") }, geometry: geom };
  F.choix = "perso";
  const sel = document.getElementById("zoneChoix");
  let opt = sel.querySelector("option[value=perso]");
  if (!opt) { opt = document.createElement("option"); opt.value = "perso"; sel.appendChild(opt); }
  opt.textContent = t("maZone"); sel.value = "perso";
  montrerZone(F.zone);
}

// ---------- dessin ----------
function dessinCommencer() {
  F.dessin = [];
  window.dessinEnCours = true;
  carte.doubleClickZoom.disable();
  carte.getCanvas().style.cursor = "crosshair";
  document.getElementById("aideDessin").hidden = false;
  document.querySelectorAll(".maplibregl-popup").forEach((p) => p.remove());
  if (!carte.getSource("dessin")) {
    carte.addSource("dessin", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    carte.addLayer({ id: "dessin-fond", type: "fill", source: "dessin", filter: ["==", "$type", "Polygon"], paint: { "fill-color": "#2a78d6", "fill-opacity": 0.12 } });
    carte.addLayer({ id: "dessin-trait", type: "line", source: "dessin", paint: { "line-color": "#2a78d6", "line-width": 2 } });
    carte.addLayer({ id: "dessin-points", type: "circle", source: "dessin", filter: ["==", "$type", "Point"], paint: { "circle-radius": 5, "circle-color": "#fff", "circle-stroke-color": "#2a78d6", "circle-stroke-width": 2 } });
  }
  dessinMaj();
  if (matchMedia("(max-width: 760px)").matches) document.getElementById("carte").scrollIntoView({ behavior: "smooth" });
}
function dessinMaj(curseur) {
  const p = F.dessin || [], pts = curseur ? [...p, curseur] : p, feats = p.map((c) => turf.point(c));
  if (pts.length >= 3) feats.push(turf.polygon([[...pts, pts[0]]]));
  else if (pts.length === 2) feats.push(turf.lineString(pts));
  carte.getSource("dessin").setData(turf.featureCollection(feats));
}
function dessinFin(valider) {
  const p = F.dessin;
  F.dessin = null; window.dessinEnCours = false;
  carte.getCanvas().style.cursor = "";
  setTimeout(() => carte.doubleClickZoom.enable(), 300);
  document.getElementById("aideDessin").hidden = true;
  carte.getSource("dessin").setData(turf.featureCollection([]));
  if (valider && p && p.length >= 3) definirZonePerso({ type: "Polygon", coordinates: [[...p, p[0]]] });
}
async function brancherDessin() {
  await script(LIBS[0]);
  carte.on("click", (e) => {
    if (!F.dessin) return;
    const c = [e.lngLat.lng, e.lngLat.lat];
    if (F.dessin.length >= 3) {
      const p0 = carte.project(F.dessin[0]);
      if (Math.hypot(p0.x - e.point.x, p0.y - e.point.y) < 12) return dessinFin(true);
    }
    F.dessin.push(c); dessinMaj();
  });
  carte.on("dblclick", (e) => { if (F.dessin) { e.preventDefault(); F.dessin.pop(); dessinFin(true); } });
  carte.on("mousemove", (e) => { if (F.dessin && F.dessin.length) dessinMaj([e.lngLat.lng, e.lngLat.lat]); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && F.dessin) dessinFin(false);
    else if (e.key === "Escape" && !document.getElementById("fiche-ecran").hidden) fermerFiche();
  });
}

// ---------- import d'un GeoJSON (lu localement, rien n'est envoyé) ----------
async function importer(fichier) {
  await script(LIBS[0]);
  try {
    const g = JSON.parse(await fichier.text());
    const polys = [];
    turf.flattenEach(g, (f) => { if (f.geometry && f.geometry.type === "Polygon") polys.push(f.geometry.coordinates); });
    if (!polys.length) throw new Error();
    const geom = polys.length === 1 ? { type: "Polygon", coordinates: polys[0] } : { type: "MultiPolygon", coordinates: polys };
    definirZonePerso(geom);
  } catch { alert(t("fichierInvalide")); }
}

// ---------- capture de la carte pour la feuille ----------
function attendre(ev) { return new Promise((ok) => carte.once(ev, ok)); }
async function capturerCarte(zone) {
  const conteneur = document.getElementById("carte"), avant = conteneur.getAttribute("style") || "";
  const camera = { center: carte.getCenter(), zoom: carte.getZoom() };
  const vues = ["couverture", "indice"].map((id) => [id, carte.getLayoutProperty(id, "visibility")]);
  vues.forEach(([id]) => carte.setLayoutProperty(id, "visibility", "none"));
  ["zone-choisie-fond", "zone-choisie-trait"].forEach((id) => carte.getLayer(id) && carte.setLayoutProperty(id, "visibility", "none"));

  // voile hors de la zone et contour, comme sur les fiches QGIS
  const trous = [];
  turf.flattenEach(zone, (f) => trous.push(f.geometry.coordinates[0].slice().reverse()));
  carte.addSource("fiche-voile", { type: "geojson", data: turf.polygon([[[-30, 40], [40, 40], [40, 70], [-30, 70], [-30, 40]], ...trous]) });
  carte.addLayer({ id: "fiche-voile", type: "fill", source: "fiche-voile", paint: { "fill-color": "#fbfaf8", "fill-opacity": 0.72 } });
  carte.addSource("fiche-contour", { type: "geojson", data: zone });
  carte.addLayer({ id: "fiche-contour", type: "line", source: "fiche-contour", paint: { "line-color": "#1d1d1b", "line-width": 1.8 } });

  const L = 880, H = 533, densite = carte.getPixelRatio();
  conteneur.setAttribute("style", `position:fixed;left:0;top:0;width:${L}px;height:${H}px;flex:none;z-index:0`);
  carte.setPixelRatio(2.5);
  carte.resize();
  carte.fitBounds(bboxGeo(zone), { padding: 36, animate: false });
  await attendre("idle");
  const image = await new Promise((ok) => { carte.once("render", () => ok(carte.getCanvas().toDataURL("image/png"))); carte.triggerRepaint(); });

  // repères de lecture et échelle, dessinés sur l'image (les étiquettes de la page ne sont pas dans le canevas)
  const r = carte.getCanvas().width / L, cv = document.createElement("canvas");
  cv.width = L * r; cv.height = H * r;
  const x = cv.getContext("2d"), img = new Image();
  await new Promise((ok) => { img.onload = ok; img.src = image; });
  x.drawImage(img, 0, 0); x.scale(r, r);
  for (const [en, fr, nature, lon, lat] of LIEUX) {
    const p = carte.project([lon, lat]);
    if (p.x < 10 || p.y < 10 || p.x > L - 10 || p.y > H - 10) continue;
    const nom = langue === "fr" ? fr : en;
    x.textBaseline = "middle";
    if (nature === "ville") {
      x.fillStyle = "#3d3d3a"; x.beginPath(); x.arc(p.x, p.y, 2.2, 0, 7); x.fill();
      x.font = "12.5px Inter, 'Segoe UI', sans-serif"; x.textAlign = "left";
      x.lineWidth = 3; x.strokeStyle = "rgba(255,255,255,.9)"; x.strokeText(nom, p.x + 5, p.y); x.fillText(nom, p.x + 5, p.y);
    } else {
      x.textAlign = "center";
      x.font = nature === "pays" ? "600 12px Inter, 'Segoe UI', sans-serif" : "italic 12px Inter, 'Segoe UI', sans-serif";
      x.fillStyle = nature === "pays" ? "#a39b8e" : "#5f7a8c";
      if ("letterSpacing" in x) x.letterSpacing = nature === "pays" ? "3px" : "0.5px";
      x.fillText(nom, p.x, p.y);
      if ("letterSpacing" in x) x.letterSpacing = "0px";
    }
  }
  // barre d'échelle en milles nautiques
  const a = carte.unproject([0, H - 30]), b = carte.unproject([L, H - 30]);
  const nmParPx = turf.distance([a.lng, a.lat], [b.lng, b.lat], { units: "nauticalmiles" }) / L;
  const cible = nmParPx * 160, pas = [5, 10, 20, 25, 50, 100, 200].find((v) => v >= cible * 0.6) || 200, w = pas / nmParPx;
  x.fillStyle = "rgba(251,250,248,.88)"; x.fillRect(18, H - 44, w + 64, 30);
  x.strokeStyle = "#1d1d1b"; x.lineWidth = 1.5; x.beginPath(); x.moveTo(28, H - 24); x.lineTo(28 + w, H - 24); x.moveTo(28, H - 29); x.lineTo(28, H - 19); x.moveTo(28 + w, H - 29); x.lineTo(28 + w, H - 19); x.stroke();
  x.fillStyle = "#1d1d1b"; x.font = "11px Inter, 'Segoe UI', sans-serif"; x.textAlign = "left"; x.fillText(`${pas} ${t("nm")}`, 34 + w, H - 24);
  // nord en haut (carte non orientable)
  x.font = "600 12px Inter, 'Segoe UI', sans-serif"; x.textAlign = "center"; x.fillText("N", L - 28, 26);
  x.beginPath(); x.moveTo(L - 28, 34); x.lineTo(L - 34, 50); x.lineTo(L - 28, 46); x.lineTo(L - 22, 50); x.closePath(); x.fill();

  // remise en état
  ["fiche-voile", "fiche-contour"].forEach((id) => { carte.removeLayer(id); carte.removeSource(id); });
  vues.forEach(([id, v]) => carte.setLayoutProperty(id, "visibility", v || "visible"));
  ["zone-choisie-fond", "zone-choisie-trait"].forEach((id) => carte.getLayer(id) && carte.setLayoutProperty(id, "visibility", "visible"));
  conteneur.setAttribute("style", avant);
  carte.setPixelRatio(densite);
  carte.resize(); carte.jumpTo(camera);
  return cv.toDataURL("image/jpeg", 0.9);
}

// ---------- feuille ----------
const pct = (v) => (v == null ? "–" : fmt(100 * v, 0) + " %");
function anneau(part) {
  const v = part == null ? 0 : part, R = 26, C = 2 * Math.PI * R;
  return `<svg viewBox="0 0 64 64" class="anneau" aria-hidden="true"><circle cx="32" cy="32" r="${R}" fill="none" stroke="#e6e3dc" stroke-width="9"/>
    <circle cx="32" cy="32" r="${R}" fill="none" stroke="#1baf7a" stroke-width="9" stroke-dasharray="${(C * v).toFixed(1)} ${C.toFixed(1)}" transform="rotate(-90 32 32)" stroke-linecap="butt"/></svg>`;
}
function graphe(comptes) {
  const libs = langue === "fr" ? CATEGORIES_FR : F.donnees.silences.categories, vmax = Math.max(1, ...comptes);
  return `<div class="graphe">${comptes.map((v, i) => `<div class="g-ligne${i === 8 ? " g-inexpl" : ""}">
    <span class="g-lib">${libs[i]}</span><span class="g-piste"><span style="width:${(100 * v / vmax).toFixed(1)}%"></span></span><b>${fmt(v)}</b></div>`).join("")}</div>`;
}
function legende() {
  const l = [["trait-orange", "cInexpl"], ["trait-violet", "cMmsi"], ["losange", "cStat"], ["rond-vert", "cRenc"], ["carre", "cRadar"], ["hachure", "cLacunes"]];
  const sym = (s) => SYMBOLES[s].replace('id="h"', 'id="h-feuille"').replace("url(#h)", "url(#h-feuille)");
  return `<div class="f-legende">${l.map(([s, k]) => `<span>${sym(s)}${t(k)}</span>`).join("")}</div>`;
}
function rendreFeuille() {
  const R = F.resultat, P = R.zone.properties || {};
  const nom = R.exact ? t(P.nom) : (F.nomPerso || t("maZone"));
  const sous = R.exact ? t(P.sous_titre) : `${t("sousPerso")} · ${t("dansEtude")}`;
  const navires = R.exact ? fmt(R.nb_navires) : "≈ " + fmt(R.nb_navires);
  const petites = [
    [fmt(R.nb_silences), t("fSilences"), ""], [fmt(R.nb_reception), t("fReception"), ""],
    [fmt(R.nav_mmsi_partage), t("fMmsi"), "violet"], [fmt(R.nb_stationnements), t("fStat"), "bleu"],
    [fmt(R.nav_stationnements), t("fNavStat"), "bleu"], [fmt(R.nb_rencontres), t("fRenc"), "vert"],
  ];
  if (R.nb_radar_sans_ais != null) petites.push([fmt(R.nb_radar_sans_ais), t("fRadar"), "encre"], [pct(R.part_radar_recus), t("fRadarRecus"), ""]);
  const date = new Intl.DateTimeFormat(langue === "fr" ? "fr-FR" : "en-GB", { dateStyle: "long" }).format(new Date());
  document.getElementById("feuille").innerHTML = `
    <header class="f-tete">
      <div class="f-kicker">${t("kFiche")}</div><div class="f-periode">${t("periode")}</div>
    </header>
    <h1 class="f-titre" contenteditable="${!R.exact}" spellcheck="false">${nom}</h1>
    <p class="f-sous">${sous} · ${fmt(R.aire)} ${t("km2")}</p>
    <figure class="f-carte"><img src="${F.image}" alt=""></figure>${legende()}
    <section class="f-heros">
      <div class="f-carte-chiffre f-orange"><b>${fmt(R.nb_inexpliquees)}</b><span>${t("fInexpl")}<em>${fmt(R.nav_inexpliquees)} ${t("fInexplNav")}</em></span></div>
      <div class="f-carte-chiffre"><b>${navires}</b><span>${R.exact ? t("fNavires") : t("fNaviresApprox")}</span></div>
      <div class="f-carte-chiffre f-anneau">${anneau(R.part_couverte)}<div><b>${pct(R.part_couverte)}</b><span>${t("fCouverte")}</span></div></div>
    </section>
    <section class="f-bas">
      <div class="f-petites">${petites.map(([v, l, c]) => `<div class="f-petite ${c}"><b>${v}</b><span>${l}</span></div>`).join("")}</div>
      <div class="f-bloc"><h2>${t("hGraphe")}</h2>${graphe(R.comptes)}<p class="f-lecture">${t("lecture")}</p></div>
    </section>
    <footer class="f-pied">
      <p class="f-methode">${t("methode").replace(/^([^.]+\.)/, "<b>$1</b>").replace("github.com/jauresmas/what-ais-doesnt-show",
        '<a href="https://github.com/jauresmas/what-ais-doesnt-show">github.com/jauresmas/what-ais-doesnt-show</a>')} ${R.exact ? t("calculExact") : t("calculNav")}</p>
      <p class="f-sources">${t("sources")} Danish Maritime Authority (AIS) · Marine Regions (CC BY 4.0) · Eurostat GISCO (© EuroGeographics) · EMODnet and BSH (CC BY 4.0) · TeleGeography (CC BY-NC-SA 3.0) · © OpenStreetMap contributors · Radar detections: Powered by Global Fishing Watch (CC BY-NC 4.0) · ${t("projection")}.</p>
      <div class="f-signature"><span>${t("projet")}</span><span>${t("genere")} ${date} ${t("depuis")}</span></div>
    </footer>`;
  const titre = document.querySelector(".f-titre");
  titre.addEventListener("input", () => { F.nomPerso = titre.textContent.trim(); document.title = F.nomPerso; });
  document.title = `${nom} — ${t("hFiche")}`;
  document.getElementById("fiche-outils").innerHTML = `
    <button type="button" class="primaire" data-a="imprimer">${t("imprimer")}</button>
    <button type="button" data-a="csv">${t("telCsv")}</button>
    <button type="button" data-a="zone">${t("telZone")}</button>
    <button type="button" data-a="lien">${t("copierLien")}</button>
    <span class="f-message" role="status"></span>
    <button type="button" class="fermer" data-a="fermer" aria-label="${t("fermer")}">${t("fermer")} ✕</button>`;
  ajuster();
}
function ajuster() {
  const ecran = document.getElementById("fiche-ecran"), f = document.getElementById("feuille"), cadre = document.getElementById("feuille-cadre");
  const k = Math.min(1, (ecran.clientWidth - 24) / 794);
  f.style.transform = `scale(${k})`; cadre.style.width = 794 * k + "px"; cadre.style.height = 1123 * k + "px";
}

async function ouvrirFiche() {
  const ecran = document.getElementById("fiche-ecran"), attente = document.getElementById("fiche-attente");
  attente.textContent = t("calcul"); attente.hidden = false; document.body.classList.add("fiche-calcul");
  try {
    await charger();
    let res;
    if (F.choix === "perso") res = calculer(F.zone);
    else res = resultatPredefini(F.donnees.zones.features.find((f) => f.properties.zone_id === F.choix));
    if (!res) { alert(t("horsZone")); return; }
    F.resultat = res;
    F.image = await capturerCarte(res.zone);
    ecran.hidden = false; document.body.classList.add("fiche-ouverte");
    rendreFeuille();
    history.replaceState(null, "", lienFiche() || location.pathname);
  } catch (e) { console.error(e); alert(e.message); }
  finally { attente.hidden = true; document.body.classList.remove("fiche-calcul"); }
}
function fermerFiche() {
  document.getElementById("fiche-ecran").hidden = true; document.body.classList.remove("fiche-ouverte");
  history.replaceState(null, "", location.pathname);
  document.title = "What AIS doesn't show — web map";
}

// lien partageable : zone prédéfinie par son identifiant, zone libre par ses sommets (3 décimales)
function lienFiche() {
  if (F.choix !== "perso") return `#fiche=${F.choix}`;
  if (F.zone.geometry.type !== "Polygon") return null;
  const c = turf.simplify(F.zone, { tolerance: 0.002 }).geometry.coordinates[0].slice(0, -1);
  const h = "#zone=" + c.map(([x, y]) => `${x.toFixed(3)},${y.toFixed(3)}`).join(";");
  return h.length < 1800 ? h : null;
}
function telecharger(nom, contenu, type) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([contenu], { type })); a.download = nom; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
function nomFichier() {
  return (document.querySelector(".f-titre")?.textContent || "zone").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "").toLowerCase() || "zone";
}
document.addEventListener("click", async (e) => {
  const b = e.target.closest("#fiche-outils button"); if (!b) return;
  const R = F.resultat, msg = document.querySelector(".f-message");
  if (b.dataset.a === "imprimer") window.print();
  if (b.dataset.a === "fermer") fermerFiche();
  if (b.dataset.a === "csv") {
    const cles = ["nb_navires", "nb_silences", "nb_reception", "nb_inexpliquees", "nav_inexpliquees", "nav_mmsi_partage", "nb_stationnements",
      "nav_stationnements", "nb_rencontres", "part_couverte", "nb_radar_sans_ais", "part_radar_recus"];
    const lignes = [["indicateur", "valeur"], ["zone", document.querySelector(".f-titre").textContent.trim()], ["aire_km2", R.aire.toFixed(0)],
      ["calcul", R.exact ? "chaine PostGIS" : "navigateur"], ...cles.map((k) => [k, R[k] ?? ""]),
      ...F.donnees.silences.categories.map((c, i) => ["silences: " + c, R.comptes[i]])];
    telecharger(nomFichier() + ".csv", lignes.map((l) => l.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n"), "text/csv");
  }
  if (b.dataset.a === "zone") telecharger(nomFichier() + ".geojson", JSON.stringify({ type: "FeatureCollection", features: [{ type: "Feature", properties: { nom: document.querySelector(".f-titre").textContent.trim() }, geometry: R.zone.geometry }] }), "application/geo+json");
  if (b.dataset.a === "lien") {
    const h = lienFiche();
    if (!h) { msg.textContent = t("lienTropLong"); return; }
    const url = location.origin + location.pathname + h;
    try { await navigator.clipboard.writeText(url); msg.textContent = t("lienCopie"); } catch { prompt("", url); }
    setTimeout(() => (msg.textContent = ""), 2500);
  }
});

// ---------- panneau ----------
async function brancherPanneau() {
  const sel = document.getElementById("zoneChoix");
  const remplir = async () => {
    const z = await zonesPredefinies(), garde = sel.value;
    sel.innerHTML = z.features.map((f) => `<option value="${f.properties.zone_id}">${t(f.properties.nom === "Danish Straits & Bornholm Basin" ? "Study area" : f.properties.nom)}</option>`).join("")
      + (F.zone ? `<option value="perso">${t("maZone")}</option>` : "");
    sel.value = garde || F.choix;
  };
  await remplir();
  sel.addEventListener("change", async () => {
    F.choix = sel.value;
    const z = await zonesPredefinies();
    montrerZone(F.choix === "perso" ? F.zone : z.features.find((f) => f.properties.zone_id === F.choix));
  });
  document.getElementById("btnFiche").addEventListener("click", ouvrirFiche);
  document.getElementById("btnDessiner").addEventListener("click", dessinCommencer);
  document.getElementById("btnTerminer").addEventListener("click", () => dessinFin(true));
  document.getElementById("btnAnnuler").addEventListener("click", () => dessinFin(false));
  document.getElementById("fichierZone").addEventListener("change", (e) => { if (e.target.files[0]) importer(e.target.files[0]); e.target.value = ""; });
  document.querySelectorAll(".langue button").forEach((b) => b.addEventListener("click", () => {
    remplir();
    if (!document.getElementById("fiche-ecran").hidden) rendreFeuille();
  }));
  window.addEventListener("resize", () => { if (!document.getElementById("fiche-ecran").hidden) ajuster(); });

  // ouverture directe par un lien partagé
  const h = decodeURIComponent(location.hash);
  if (h.startsWith("#fiche=")) { const id = h.slice(7); if ([...sel.options].some((o) => o.value === id)) { sel.value = F.choix = id; ouvrirFiche(); } }
  else if (h.startsWith("#zone=")) {
    const c = h.slice(6).split(";").map((p) => p.split(",").map(Number));
    if (c.length >= 3 && c.every((p) => p.length === 2 && p.every(Number.isFinite))) { definirZonePerso({ type: "Polygon", coordinates: [[...c, c[0]]] }); ouvrirFiche(); }
  }
}
document.addEventListener("carte-prete", () => { brancherDessin(); brancherPanneau(); });
