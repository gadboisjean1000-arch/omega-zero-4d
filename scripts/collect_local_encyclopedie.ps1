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
    [int]$MaxDepth = 16,
    [int]$MaxDirsPerDrive = 50000,
    [switch]$SkipBrowserHistory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

$ExcludedDirNames = @(
    "Windows", "WinSxS", "`$Recycle.Bin", "System Volume Information",
    "Package Cache", "node_modules", ".venv", "__pycache__"
)

$SensitiveFilePattern = '(?i)(cookies|login data|local state|web data|\.env|\.ssh|\.kdbx|\.pfx|\.p12|\.pem|\.key|id_rsa|id_ed25519|netrc|gitcookies)'
$AiDomainRegex = '(?i)(gemini\.google\.com|aistudio\.google\.com|copilot\.microsoft\.com|edgeservices\.bing\.com|bing\.com/chat|chatgpt\.com|chat\.openai\.com|claude\.ai|perplexity\.ai|poe\.com|arc\.net|github\.com/(?:copilot|features/copilot|marketplace/models)|copilot\.github\.com|huggingface\.co|mistral\.ai|deepseek\.com)'
$NotableFilePattern = '(?i)(supela|omega|encycloped|dictionnaire|conversations\.json|claude|chatgpt|copilot|gemini|cursor|kilo|cline|antigravity)'

function Test-SafePath([string]$FullName) {
    if ([string]::IsNullOrWhiteSpace($FullName)) { return $false }
    if ($FullName -match $SensitiveFilePattern) { return $false }
    return $true
}

function Redact-SafeUrl([string]$RawUrl) {
    if ([string]::IsNullOrWhiteSpace($RawUrl)) { return "" }
    $uri = $null
    if (-not [System.Uri]::TryCreate($RawUrl.Trim(), [System.UriKind]::Absolute, [ref]$uri)) {
        return ""
    }
    if ($uri.Scheme -notin @("http", "https")) { return "" }
    $builder = New-Object System.UriBuilder($uri)
    $builder.UserName = ""
    $builder.Password = ""
    $builder.Query = ""
    $builder.Fragment = ""
    $clean = $builder.Uri.AbsoluteUri
    if ($clean.Length -gt 240) { return $clean.Substring(0, 240) }
    return $clean
}

function Redact-GitRemote([string]$RemoteUrl) {
    if ([string]::IsNullOrWhiteSpace($RemoteUrl)) { return "" }
    $trimmed = $RemoteUrl.Trim()
    $uri = $null
    if ([System.Uri]::TryCreate($trimmed, [System.UriKind]::Absolute, [ref]$uri)) {
        if ($uri.Scheme -in @("http", "https", "ssh", "git")) {
            $builder = New-Object System.UriBuilder($uri)
            $builder.UserName = ""
            $builder.Password = ""
            $builder.Query = ""
            $builder.Fragment = ""
            return $builder.Uri.AbsoluteUri
        }
        return ""
    }
    # Redact scp-style userinfo before '@' while keeping host:path if safe
    if ($trimmed -match '^[^@/\s]+@([^:\s]+:.+)$') {
        return ("ssh://" + $Matches[1])
    }
    return ""
}

function Walk-BookmarkNode($node, [string]$SourceLabel, [System.Collections.Generic.List[object]]$Acc) {
    if ($null -eq $node) { return }
    $hasType = $null -ne $node.PSObject.Properties["type"]
    $hasUrl = $null -ne $node.PSObject.Properties["url"]
    if ($hasType -and $hasUrl -and [string]$node.type -eq "url") {
        $rawUrl = [string]$node.url
        if ($rawUrl -match $AiDomainRegex) {
            $safeUrl = Redact-SafeUrl $rawUrl
            if ($safeUrl) {
                $title = if ($null -ne $node.PSObject.Properties["name"]) { [string]$node.name } else { "" }
                $Acc.Add([ordered]@{
                    source = $SourceLabel
                    titre  = $title
                    url    = $safeUrl
                    type   = "BOOKMARK_IA"
                })
            }
        }
    }
    if ($null -ne $node.PSObject.Properties["children"] -and $null -ne $node.children) {
        foreach ($child in $node.children) { Walk-BookmarkNode $child $SourceLabel $Acc }
    }
}

function Get-BookmarksFromFile([string]$BookmarkPath, [string]$SourceLabel) {
    $acc = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $BookmarkPath)) { return @() }
    try {
        $raw = Get-Content -LiteralPath $BookmarkPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -ne $raw.PSObject.Properties["roots"] -and $null -ne $raw.roots) {
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
    $tmpWal = "$tmpDb-wal"
    $tmpShm = "$tmpDb-shm"
    try {
        Copy-Item -LiteralPath $HistoryPath -Destination $tmpDb -Force
        if (Test-Path -LiteralPath "$HistoryPath-wal") {
            Copy-Item -LiteralPath "$HistoryPath-wal" -Destination $tmpWal -Force
        }
        if (Test-Path -LiteralPath "$HistoryPath-shm") {
            Copy-Item -LiteralPath "$HistoryPath-shm" -Destination $tmpShm -Force
        }
        $pyScript = @"
import json, re, sqlite3, sys
from urllib.parse import urlsplit, urlunsplit
conn = sqlite3.connect(sys.argv[1])
cur = conn.cursor()
pat = re.compile(r'gemini\.google\.com|aistudio\.google\.com|copilot\.microsoft\.com|edgeservices\.bing\.com|bing\.com/chat|chatgpt\.com|chat\.openai\.com|claude\.ai|perplexity\.ai|poe\.com|github\.com/(?:copilot|features/copilot|marketplace/models)|copilot\.github\.com|huggingface\.co|mistral\.ai|deepseek\.com', re.I)
rows = []
try:
    for url, title, visits, last_ts in cur.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC"):
        if not url or not pat.search(url):
            continue
        p = urlsplit(url)
        if p.scheme not in ('http', 'https') or not p.hostname:
            continue
        netloc = f"{p.hostname}:{p.port}" if p.port else p.hostname
        clean_url = urlunsplit((p.scheme, netloc, p.path or '/', '', ''))[:240]
        rows.append({"source": sys.argv[2], "url": clean_url, "titre": (title or "")[:160], "visits": int(visits or 0), "type": "HISTORIQUE_URL_IA"})
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
        foreach ($tf in @($tmpDb, $tmpWal, $tmpShm)) {
            if (Test-Path -LiteralPath $tf) { Remove-Item -LiteralPath $tf -Force -ErrorAction SilentlyContinue }
        }
    }
    return $results
}

$driveReports = @()
$gitRepos = @()
$notableFiles = @()
$hasGitCmd = ($null -ne (Get-Command git -ErrorAction SilentlyContinue))

foreach ($d in $Drives) {
    $driveLetters = $d.Trim().TrimEnd('\', '/').TrimEnd(':').ToUpperInvariant()
    if ([string]::IsNullOrWhiteSpace($driveLetters)) { continue }
    $normDrive = "${driveLetters}:\"

    if (-not (Test-Path -LiteralPath $normDrive)) {
        $driveReports += [ordered]@{
            lecteur                 = $normDrive
            statut                  = "ABSENT_SUR_CE_POSTE"
            dossiers_racine         = @()
            total_depots_git        = 0
            total_fichiers_notables = 0
            scan_tronque            = $false
            dossiers_inaccessibles  = 0
        }
        continue
    }

    $topDirs = @(Get-ChildItem -LiteralPath $normDrive -Directory -Force -ErrorAction SilentlyContinue |
        Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0 } |
        Select-Object -First $MaxTopLevelPerDrive | ForEach-Object {
            [ordered]@{ nom = $_.Name; chemin = $_.FullName; modifie_utc = $_.LastWriteTimeUtc.ToString("o") }
        })

    $driveGitCount = 0
    $driveNotableCount = 0
    $visitedDirs = 0
    $inaccessibleCount = 0
    $scanTruncated = $false

    $visitedPaths = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    $stack = New-Object 'System.Collections.Generic.Stack[object]'
    $stack.Push(@{ Path = $normDrive; Depth = 0 })

    while ($stack.Count -gt 0) {
        if ($visitedDirs -ge $MaxDirsPerDrive) {
            $scanTruncated = $true
            break
        }
        $frame = $stack.Pop()
        $curr = [string]$frame.Path
        $depth = [int]$frame.Depth
        if (-not $visitedPaths.Add($curr)) { continue }
        $visitedDirs++

        $leaf = Split-Path -Path $curr -Leaf
        if ($leaf -and ($ExcludedDirNames -contains $leaf)) { continue }

        $entries = @()
        try {
            $entries = @(Get-ChildItem -LiteralPath $curr -Force -ErrorAction Stop)
        } catch {
            $inaccessibleCount++
            continue
        }

        $gitMarkerFound = $false
        foreach ($ent in $entries) {
            if ($ent.Name -eq ".git") {
                $gitMarkerFound = $true
                break
            }
        }
        if ($gitMarkerFound) {
            $remote = ""
            if ($hasGitCmd) {
                $rawRemote = (& git -C $curr config --get remote.origin.url 2>$null)
                $remote = Redact-GitRemote ([string]$rawRemote)
            }
            $gitRepos += [ordered]@{
                chemin        = $curr
                lecteur       = $normDrive
                remote_origin = $remote
            }
            $driveGitCount++
        }

        foreach ($ent in $entries) {
            if ($ent.PSIsContainer) {
                if ($ent.Name -eq ".git" -or ($ExcludedDirNames -contains $ent.Name)) { continue }
                if (($ent.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
                if ($depth -lt $MaxDepth) {
                    $stack.Push(@{ Path = $ent.FullName; Depth = ($depth + 1) })
                } else {
                    $scanTruncated = $true
                }
            } elseif ($driveNotableCount -lt $MaxNotableFilesPerDrive) {
                if (-not (Test-SafePath $ent.FullName)) { continue }
                if ($ent.Name -match $NotableFilePattern -or $ent.Extension -in @(".ipynb", ".rego")) {
                    $notableFiles += [ordered]@{
                        chemin        = $ent.FullName
                        lecteur       = $normDrive
                        extension     = $ent.Extension
                        taille_octets = [long]$ent.Length
                        modifie_utc   = $ent.LastWriteTimeUtc.ToString("o")
                    }
                    $driveNotableCount++
                    if ($driveNotableCount -ge $MaxNotableFilesPerDrive) {
                        $scanTruncated = $true
                    }
                }
            }
        }
    }

    $driveStatus = if ($scanTruncated -or $inaccessibleCount -gt 0) { "PARTIELLEMENT_INDEXE" } else { "INDEXE_LOCAL" }
    $driveReports += [ordered]@{
        lecteur                 = $normDrive
        statut                  = $driveStatus
        dossiers_racine         = $topDirs
        total_depots_git        = $driveGitCount
        total_fichiers_notables = $driveNotableCount
        scan_tronque            = $scanTruncated
        dossiers_inaccessibles  = $inaccessibleCount
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
    schema               = "supela-local-pc-inventory/1"
    generated_utc        = (Get-Date).ToUniversalTime().ToString("o")
    machine_name         = $env:COMPUTERNAME
    skip_browser_history = [bool]$SkipBrowserHistory
    drives               = $driveReports
    git_repos            = $gitRepos
    notable_files        = $notableFiles
    ai_platforms         = $aiPlatformsFound
    safety_note          = "Lecture seule sans collecte de cookies, mots de passe, tokens ou cles privees."
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
