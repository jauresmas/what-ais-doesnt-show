<#
Copie la base du projet (instance locale du projet, port 5434) dans un autre serveur PostgreSQL,
par défaut le service Windows sur le port 5432, pour l'ouvrir dans pgAdmin, DBeaver ou QGIS.

Le mot de passe est demandé une seule fois, en saisie masquée ; il ne reste ni à l'écran, ni dans
l'historique, ni dans un fichier. Les objets appartiennent ensuite à l'utilisateur de connexion.

    .\scripts\copier_base.ps1                      base « what_ais » sur localhost:5432, utilisateur postgres
    .\scripts\copier_base.ps1 -Remplacer           recrée la base si elle existe déjà (nouvelle sauvegarde)
    .\scripts\copier_base.ps1 -Verifier            contrôle seulement la base déjà copiée
    .\scripts\copier_base.ps1 -Base ais -Port 5433 -Utilisateur moi
#>
param(
    [string]$Base = "what_ais",
    [int]$Port = 5432,
    [string]$Utilisateur = "postgres",
    [switch]$Remplacer,
    [switch]$Verifier
)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8   # messages de PostgreSQL en UTF-8 : accents lisibles
$bin = "C:\Program Files\PostgreSQL\15\bin"
$racine = Split-Path $PSScriptRoot -Parent
$sauvegarde = Join-Path $racine "donnees\sauvegarde\what_ais.dump"

# contrôle : les mêmes chiffres que dans la base du projet. Requête sans aucun accent : sous Windows,
# un argument de ligne de commande passe par la page de code ANSI et PostgreSQL refuserait les octets
$controle = "SELECT (SELECT count(*) FROM ais.position) AS positions, (SELECT count(*) FROM ais.navire) AS navires, " +
            "(SELECT count(*) FROM indic.coupure) AS silences, " +
            "(SELECT count(*) FROM indic.coupure WHERE categorie LIKE 'coupure inexpliqu%') AS inexpliques, " +
            "postgis_lib_version() AS postgis, h3_get_extension_version() AS h3"

# 1. sauvegarde de la base du projet (instance du projet, sans mot de passe)
if (-not $Verifier -and ($Remplacer -or -not (Test-Path $sauvegarde))) {
    New-Item -ItemType Directory -Force (Split-Path $sauvegarde) | Out-Null
    Write-Host "Sauvegarde de la base du projet (port 5434)..."
    & "$bin\pg_dump.exe" -h localhost -p 5434 -U ais -d ais -Fc -Z 6 -f $sauvegarde
    if ($LASTEXITCODE -ne 0) { throw "Sauvegarde impossible : l'instance du projet tourne-t-elle ? (python scripts\00_base.py)" }
}
if (-not $Verifier) { Write-Host ("Sauvegarde : {0:N0} Mo" -f ((Get-Item $sauvegarde).Length / 1MB)) }

# 2. mot de passe, saisi une fois et gardé le temps du script dans une variable d'environnement du processus
$secret = Read-Host "Mot de passe de l'utilisateur $Utilisateur sur le port $Port" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
$env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
$env:PGCLIENTENCODING = "UTF8"
try {
    $existe = & "$bin\psql.exe" -h localhost -p $Port -U $Utilisateur -d postgres -w -t -A -c "SELECT 1 FROM pg_database WHERE datname = '$Base'"
    if ($LASTEXITCODE -ne 0) { throw "Connexion refusée sur le port $Port (mot de passe ou utilisateur)." }
    if ($Verifier) {
        if ($existe -ne "1") { throw "La base $Base n'existe pas sur le port $Port." }
        & "$bin\psql.exe" -h localhost -p $Port -U $Utilisateur -d $Base -w -c $controle
        if ($LASTEXITCODE -ne 0) { throw "Contrôle impossible : la base $Base est incomplète." }
        return
    }
    if ($existe -eq "1") {
        if (-not $Remplacer) { throw "La base $Base existe déjà sur le port $Port : relancer avec -Remplacer pour la recréer." }
        Write-Host "Suppression de l'ancienne base $Base..."
        & "$bin\psql.exe" -h localhost -p $Port -U $Utilisateur -d postgres -w -q -c "DROP DATABASE $Base WITH (FORCE)"
    }
    # 3. base neuve, puis restauration en parallèle (extensions PostGIS et h3 comprises)
    & "$bin\psql.exe" -h localhost -p $Port -U $Utilisateur -d postgres -w -q -c "CREATE DATABASE $Base ENCODING 'UTF8' TEMPLATE template0"
    if ($LASTEXITCODE -ne 0) { throw "Création de la base $Base impossible." }
    Write-Host "Restauration dans $Base (quelques minutes)..."
    & "$bin\pg_restore.exe" -h localhost -p $Port -U $Utilisateur -d $Base -w --no-owner --no-privileges -j 4 $sauvegarde
    if ($LASTEXITCODE -ne 0) { Write-Warning "pg_restore signale des erreurs (voir ci-dessus) : le contrôle dira si la base est complète." }
    # 4. contrôle
    & "$bin\psql.exe" -h localhost -p $Port -U $Utilisateur -d $Base -w -c $controle
    if ($LASTEXITCODE -ne 0) { throw "Contrôle impossible : la base $Base est incomplète." }
    Write-Host "Base $Base prête sur localhost:$Port (schémas ais, ref, indic, qualite, et semaine après 10_semaines.py)."
}
finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}
