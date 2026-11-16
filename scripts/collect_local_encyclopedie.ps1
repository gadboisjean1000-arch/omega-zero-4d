<#
.SYNOPSIS
    Collecteur local lecture-seule (C:, D:, Copilot, Gemini, Arc, Brave, Opera, Antigravity, Cursor, VS Code)
    pour le Dictionnaire & Encyclopedie Supela Omega-ZERO.
.DESCRIPTION
    Produit un inventaire JSON strictement non-destructif et sans collecte de secrets
    (aucune lecture de Cookies, Login Data, Local State, .env, .ssh, .kdbx ou cles privees).
    Le fichier JSON obtenu peut ensuite etre fusionne via :
      python scripts/build_encyclopedie.py --local-inventory docs/constitution/local_pc_inventory.json
#>
[CmdletBinding()]
param(
    [string[]]$Drives = @("C:", "D:"),
    [string]$OutJson = (Join-Path $PSScriptRoot "..\docs\constitution\local_pc_inventory.json"),
    [int]$MaxTopLevelPerDrive = 500,
    [int]$MaxNotableFilesPerDrive = 1500,
    [switch]$SkipBrowserHistory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

$ExcludedDirNames = @(
    "Windows", "WinSxS", "`$Recycle.Bin", "System Volume Information",
    "Package Cache", "node_modules", ".venv", "__pycache__"
)

$SensitiveFilePattern = '(?i)(cookies|login data|local state|web data|\.env|\.ssh|\.kdbx|\.pfx|\.p12|\.pem|\.key|id_rsa|id_ed25519|netrc|gitcookies)'
$AiDomainRegex = '(?i)(gemini\.google\.com|aistudio\.google\.com|copilot\.microsoft\.com|edgeservices\.bing\.com|bing\.com/chat|chatgpt\.com|chat\.openai\.com|claude\.ai|perplexity\.ai|poe\.com|arc\.net|github\.com|huggingface\.co|mistral\.ai|deepseek\.com)'
$NotableFilePattern = '(?i)(supela|omega|encycloped|dictionnaire|conversations\.json|claude|chatgpt|copilot|gemini|cursor|kilo|cline|antigravity)'

function Test-SafePath([string]$FullName) {
    if ([string]::IsNullOrWhiteSpace($FullName)) { return $false }
    if ($FullName -match $SensitiveFilePattern) { return $false }
    return $true
}

function Walk-BookmarkNode($node, [string]$SourceLabel, [System.Collections.Generic.List[object]]$Acc) {
    if ($null -eq $node) { return }
    if ($node.type -eq "url" -and $node.url -match $AiDomainRegex) {
        $Acc.Add([ordered]@{
            source = $SourceLabel
            titre  = [string]$node.name
            url    = [string]$node.url
            type   = "BOOKMARK_IA"
        })
    }
    if ($null -ne $node.children) {
        foreach ($child in $node.children) { Walk-BookmarkNode $child $SourceLabel $Acc }
    }
}

function Get-BookmarksFromFile([string]$BookmarkPath, [string]$SourceLabel) {
    $acc = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $BookmarkPath)) { return @() }
    try {
        $raw = Get-Content -LiteralPath $BookmarkPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -ne $raw.roots) {
            foreach ($prop in $raw.roots.PSObject.Properties) {
                Walk-BookmarkNode $prop.Value $SourceLabel $acc
            }
        }
    } catch { }
    return $acc.ToArray()
}

function Get-SqliteHistoryAiUrls([string]$HistoryPath, [string]$SourceLabel) {
    $results = @()
    if ($SkipBrowserHistory -or -not (Test-Path -LiteralPath $HistoryPath)) { return $results }
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
    if ($null -eq $py) { return $results }

    $tmpDb = Join-Path ([System.IO.Path]::GetTempPath()) ("omega_hist_" + [guid]::NewGuid().ToString("N") + ".sqlite")
    try {
        Copy-Item -LiteralPath $HistoryPath -Destination $tmpDb -Force
        $pyScript = @"
import json, re, sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
cur = conn.cursor()
pat = re.compile(r'gemini\.google\.com|aistudio\.google\.com|copilot\.microsoft\.com|edgeservices\.bing\.com|bing\.com/chat|chatgpt\.com|chat\.openai\.com|claude\.ai|perplexity\.ai|poe\.com|github\.com', re.I)
rows = []
try:
    for url, title, visits, last_ts in cur.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 5000"):
        if url and pat.search(url):
            rows.append({"source": sys.argv[2], "url": url[:240], "titre": (title or "")[:160], "visits": int(visits or 0), "type": "HISTORIQUE_URL_IA"})
            if len(rows) >= 250:
                break
except Exception:
    pass
print(json.dumps(rows, ensure_ascii=False))
"@
        $jsonOut = & $py.Source -c $pyScript $tmpDb $SourceLabel
        if ($jsonOut) {
            $parsed = $jsonOut | ConvertFrom-Json
            if ($parsed) { $results += $parsed }
        }
    } catch { }
    finally {
        if (Test-Path -LiteralPath $tmpDb) { Remove-Item -LiteralPath $tmpDb -Force -ErrorAction SilentlyContinue }
    }
    return $results
}

$driveReports = @()
$gitRepos = @()
$notableFiles = @()

foreach ($d in $Drives) {
    $normDrive = $d.TrimEnd('\') + '\'
    if (-not (Test-Path -LiteralPath $normDrive)) {
        $driveReports += [ordered]@{
            lecteur         = $normDrive
            statut          = "ABSENT_SUR_CE_POSTE"
            dossiers_racine = @()
            total_depots_git = 0
            total_fichiers_notables = 0
        }
        continue
    }

    $topDirs = @(Get-ChildItem -LiteralPath $normDrive -Directory -Force -ErrorAction SilentlyContinue |
        Select-Object -First $MaxTopLevelPerDrive | ForEach-Object {
            [ordered]@{ nom = $_.Name; chemin = $_.FullName; modifie_utc = $_.LastWriteTimeUtc.ToString("o") }
        })

    $driveGitCount = 0
    $driveNotableCount = 0
    $stack = New-Object System.Collections.Generic.Stack[string]
    $stack.Push($normDrive)

    while ($stack.Count -gt 0) {
        $curr = $stack.Pop()
        $leaf = Split-Path -Path $curr -Leaf
        if ($ExcludedDirNames -contains $leaf) { continue }

        $subdirs = Get-ChildItem -LiteralPath $curr -Directory -Force -ErrorAction SilentlyContinue
        foreach ($sd in $subdirs) {
            if ($sd.Name -eq ".git") {
                $remote = ""
                if (Get-Command git -ErrorAction SilentlyContinue) {
                    $remote = (& git -C $curr config --get remote.origin.url 2>$null)
                }
                $gitRepos += [ordered]@{
                    chemin = $curr
                    lecteur = $normDrive
                    remote_origin = [string]$remote
                }
                $driveGitCount++
                continue
            }
            if (-not ($ExcludedDirNames -contains $sd.Name)) {
                $stack.Push($sd.FullName)
            }
        }

        if ($driveNotableCount -lt $MaxNotableFilesPerDrive) {
            $files = Get-ChildItem -LiteralPath $curr -File -Force -ErrorAction SilentlyContinue
            foreach ($f in $files) {
                if (-not (Test-SafePath $f.FullName)) { continue }
                if ($f.Name -match $NotableFilePattern -or $f.Extension -in @(".ipynb", ".rego")) {
                    $notableFiles += [ordered]@{
                        chemin       = $f.FullName
                        lecteur      = $normDrive
                        extension    = $f.Extension
                        taille_octets = [long]$f.Length
                        modifie_utc  = $f.LastWriteTimeUtc.ToString("o")
                    }
                    $driveNotableCount++
                    if ($driveNotableCount -ge $MaxNotableFilesPerDrive) { break }
                }
            }
        }
    }

    $driveReports += [ordered]@{
        lecteur                 = $normDrive
        statut                  = "INDEXE_LOCAL"
        dossiers_racine         = $topDirs
        total_depots_git        = $driveGitCount
        total_fichiers_notables = $driveNotableCount
    }
}

# --- Navigateurs & Plateformes IA locales ---
$browserTargets = @(
    @{ id = "copilot_edge"; nom = "Microsoft Edge / Copilot"; root = (Join-Path $env:LOCALAPPDATA "Microsoft\Edge\User Data") },
    @{ id = "gemini_chrome"; nom = "Google Chrome / Gemini"; root = (Join-Path $env:LOCALAPPDATA "Google\Chrome\User Data") },
    @{ id = "brave_leo"; nom = "Brave / Brave Leo"; root = (Join-Path $env:LOCALAPPDATA "BraveSoftware\Brave-Browser\User Data") },
    @{ id = "opera_aria"; nom = "Opera / Aria"; root = (Join-Path $env:APPDATA "Opera Software\Opera Stable") }
)

$arcPackages = @(Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA "Packages") -Directory -Filter "TheBrowserCompany.Arc*" -ErrorAction SilentlyContinue)
foreach ($pkg in $arcPackages) {
    $browserTargets += @{ id = "arc_browser"; nom = "Arc Browser"; root = (Join-Path $pkg.FullName "LocalCache\Local\Arc\User Data") }
}
if ($arcPackages.Count -eq 0) {
    $browserTargets += @{ id = "arc_browser"; nom = "Arc Browser"; root = (Join-Path $env:LOCALAPPDATA "Arc\User Data") }
}

$aiPlatformsFound = @()
foreach ($bt in $browserTargets) {
    $present = Test-Path -LiteralPath $bt.root
    $traces = @()
    if ($present) {
        $profiles = @($bt.root)
        $subProfiles = Get-ChildItem -LiteralPath $bt.root -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq "Default" -or $_.Name -like "Profile *" }
        foreach ($sp in $subProfiles) { $profiles += $sp.FullName }
        $profiles = $profiles | Select-Object -Unique
        foreach ($prof in $profiles) {
            $traces += Get-BookmarksFromFile (Join-Path $prof "Bookmarks") $bt.id
            $traces += Get-SqliteHistoryAiUrls (Join-Path $prof "History") $bt.id
        }
        $arcSidebar = Join-Path $bt.root "StorableSidebar.json"
        if (Test-Path -LiteralPath $arcSidebar) {
            $traces += [ordered]@{ source = $bt.id; titre = "Arc StorableSidebar.json"; url = $arcSidebar; type = "PROFIL_ARC" }
        }
    }
    $aiPlatformsFound += [ordered]@{
        id                  = $bt.id
        nom                 = $bt.nom
        present             = $present
        chemin_detecte      = $bt.root
        total_traces_ia     = $traces.Count
        traces_echantillon  = @($traces | Select-Object -First 200)
    }
}

# --- IDE / Agents IA locaux ---
$ideTargets = @(
    @{ id = "antigravity"; nom = "Antigravity (.gemini)"; path = (Join-Path $env:USERPROFILE ".gemini\jetski\brain") },
    @{ id = "cursor"; nom = "Cursor IDE"; path = (Join-Path $env:APPDATA "Cursor\User\globalStorage") },
    @{ id = "vscode_agents"; nom = "VS Code (Copilot / Cline / Kilo)"; path = (Join-Path $env:APPDATA "Code\User\globalStorage") }
)

foreach ($it in $ideTargets) {
    $present = Test-Path -LiteralPath $it.path
    $items = @()
    if ($present) {
        $items = @(Get-ChildItem -LiteralPath $it.path -Depth 2 -ErrorAction SilentlyContinue |
            Where-Object { Test-SafePath $_.FullName } |
            Select-Object -First 150 |
            ForEach-Object {
                [ordered]@{
                    source = $it.id
                    titre  = $_.Name
                    url    = $_.FullName
                    type   = if ($_.PSIsContainer) { "DOSSIER_AGENT_IA" } else { "FICHIER_AGENT_IA" }
                }
            })
    }
    $aiPlatformsFound += [ordered]@{
        id                 = $it.id
        nom                = $it.nom
        present            = $present
        chemin_detecte     = $it.path
        total_traces_ia    = $items.Count
        traces_echantillon = $items
    }
}

$inventory = [ordered]@{
    schema          = "supela-local-pc-inventory/1"
    generated_utc   = (Get-Date).ToUniversalTime().ToString("o")
    machine_name    = $env:COMPUTERNAME
    drives          = $driveReports
    git_repos       = $gitRepos
    notable_files   = $notableFiles
    ai_platforms    = $aiPlatformsFound
    safety_note     = "Lecture seule sans collecte de cookies, mots de passe, tokens ou cles privees."
}

$outDir = Split-Path -Path $OutJson -Parent
if ($outDir -and -not (Test-Path -LiteralPath $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}
$jsonText = $inventory | ConvertTo-Json -Depth 8
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($OutJson, $jsonText + "`n", $utf8NoBom)

Write-Host ("[OK] Inventaire local ecrit : {0}" -f $OutJson) -ForegroundColor Green
Write-Host ("     Disques: {0} | Depots Git: {1} | Fichiers notables: {2} | Plateformes IA: {3}" -f $driveReports.Count, $gitRepos.Count, $notableFiles.Count, $aiPlatformsFound.Count)
