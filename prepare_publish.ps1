# Stage a clean, publishable copy of the experiment into .\publish
#
#   powershell -File prepare_publish.ps1                    # full evidence set
#   powershell -File prepare_publish.ps1 -Minimal           # skip bulky raw test output
#   powershell -File prepare_publish.ps1 -SanitizeAll       # also sanitise hash-protected files
#                                                           # (then re-run make_manifest.py
#                                                           #  inside publish\ to re-freeze)
#
# Windows PowerShell 5.1 compatible. Nothing outside .\publish is modified.

param(
    [switch]$Minimal,
    [switch]$SanitizeAll
)

$ErrorActionPreference = 'Stop'

$Src = $PSScriptRoot
$Pub = Join-Path $Src 'publish'
$Model = 'glm-5.3-zcode-campaign'
$RunId = 'tonight'
$LogRoot = Join-Path $Src "logs\run_evaluation\$RunId\$Model"

# --- 1. what goes in -------------------------------------------------------

$Scripts = @(
    'make_predictions.py', 'make_harness_predictions.py', 'make_manifest.py',
    'analyze_results.py', 'extract_failures.py',
    'make_predictions_v2.py', 'analyze_v2.py', 'run_eval_v2.sh'
)
$Docs = @(
    'SCORING.md', 'TECH_REPORT.md', 'V2_PLAN.md', 'RESULTS.md',
    'comparison.md', 'comparison_v2.md', 'MANIFEST_v1.md', 'MANIFEST_v1.json'
)
$Data = @(
    'predictions.jsonl', 'predictions_swebench.jsonl',
    "$Model.$RunId.json"
)
$Tools = @('tools\port_forward.py', 'tools\docker-http-proxy.conf', 'tools\speedtest_dockerhub.py')

# --- 2. copy --------------------------------------------------------------

foreach ($d in @($Pub, "$Pub\runs", "$Pub\runs_v2", "$Pub\logs", "$Pub\tools", "$Pub\notes")) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
}

function Copy-IfExists([string]$rel, [string]$destRoot) {
    $from = Join-Path $Src $rel
    if (-not (Test-Path $from)) { Write-Host "  skip (absent): $rel"; return $false }
    $to = Join-Path $destRoot $rel
    $toDir = Split-Path $to -Parent
    if (-not (Test-Path $toDir)) { New-Item -ItemType Directory -Force -Path $toDir | Out-Null }
    Copy-Item $from $to -Force
    return $true
}

Write-Host '== docs / scripts / data =='
foreach ($f in ($Scripts + $Docs + $Data)) { Copy-IfExists $f $Pub | Out-Null }
foreach ($f in $Tools) { Copy-IfExists $f $Pub | Out-Null }
Copy-IfExists 'report_outline.md' "$Pub\notes" | Out-Null
Copy-IfExists 'prepull_log.txt' "$Pub\notes" | Out-Null

# Instance directories that exist under runs\ but are NOT part of the declared
# 37-instance scope. MANIFEST_v1.json records them under scope.excluded_out_of_scope;
# publishing them would contradict the manifest and the comparison tables.
$OutOfScope = @('django__django-12747')

Write-Host '== runs/ (patch.diff, summary.md, verify.py) =='
$RunDirs = Get-ChildItem (Join-Path $Src 'runs') -Directory
$copied = 0
$inScope = 0
foreach ($d in $RunDirs) {
    if ($OutOfScope -contains $d.Name) {
        Write-Host "  exclude (out of declared scope): $($d.Name)"
        continue
    }
    $inScope++
    foreach ($name in @('patch.diff', 'summary.md', 'verify.py')) {
        $rel = "runs\$($d.Name)\$name"
        if (Copy-IfExists $rel $Pub) { $copied++ }
    }
}
Write-Host "  copied $copied artifact files from $inScope in-scope run directories"

# drop a stale copy from an earlier run of this script
foreach ($name in $OutOfScope) {
    $stale = Join-Path $Pub "runs\$name"
    if (Test-Path $stale) {
        Remove-Item $stale -Recurse -Force
        Write-Host "  removed previously staged out-of-scope directory: runs\$name"
    }
}

Write-Host '== runs_v2/ (v2 scaffold: rules, template, per-instance checklists) =='
$v2src = Join-Path $Src 'runs_v2'
if (Test-Path $v2src) {
    $v2files = Get-ChildItem $v2src -Recurse -File
    foreach ($f in $v2files) {
        $rel = $f.FullName.Substring($Src.Length + 1)
        Copy-IfExists $rel $Pub | Out-Null
    }
    Write-Host "  copied $($v2files.Count) v2 scaffold files"
} else {
    Write-Host '  skip: runs_v2/ not found'
}

Write-Host '== logs/ (report.json, test_output.txt, eval.sh) =='
if (Test-Path $LogRoot) {
    $instDirs = Get-ChildItem $LogRoot -Directory
    $logNames = @('report.json', 'eval.sh')
    if (-not $Minimal) { $logNames += 'test_output.txt' }
    foreach ($d in $instDirs) {
        foreach ($name in $logNames) {
            $rel = "logs\run_evaluation\$RunId\$Model\$($d.Name)\$name"
            Copy-IfExists $rel $Pub | Out-Null
        }
    }
    if ($Minimal) {
        Write-Host "  copied logs for $($instDirs.Count) instances (Minimal: raw test_output.txt omitted)"
        # a previous full run may have staged them already -- drop those copies
        $stale = Get-ChildItem (Join-Path $Pub 'logs') -Recurse -File -Filter 'test_output.txt' -ErrorAction SilentlyContinue
        if ($stale) {
            $stale | Remove-Item -Force
            Write-Host "  removed $($stale.Count) previously staged test_output.txt (Minimal mode)"
        }
    } else {
        Write-Host "  copied logs for $($instDirs.Count) instances (full: incl. raw test_output.txt)"
    }
} else {
    Write-Host "  WARNING: $LogRoot not found; logs were not staged"
}

# --- 3. sanitise ----------------------------------------------------------

# Files whose SHA-256 is recorded in MANIFEST_v1.json. Editing them would break the
# hash binding, so by default they are copied verbatim.
$HashedNames = @('patch.diff', 'summary.md', 'verify.py', 'report.json',
                 'test_output.txt', 'predictions.jsonl', 'predictions_swebench.jsonl')

$Replacements = @(
    @('<EXP_ROOT>', '<EXP_ROOT>'),
    @('<EXP_ROOT_POSIX>', '<EXP_ROOT_POSIX>'),
    @('<HOME>', '<HOME>'),
    @('<HOME_POSIX>', '<HOME_POSIX>'),
    @('<HOST>', '<HOST>'),
    @('<WSL_HOST_IP>', '<WSL_HOST_IP>')
)
$TextExt = @('.md', '.json', '.jsonl', '.txt', '.sh', '.py', '.log', '.cff')

$scanned = 0
$edited = 0
$skippedHashed = @()

foreach ($f in (Get-ChildItem $Pub -Recurse -File)) {
    if ($TextExt -notcontains $f.Extension.ToLower()) { continue }
    $scanned++
    if ((-not $SanitizeAll) -and ($HashedNames -contains $f.Name)) {
        $raw = [IO.File]::ReadAllText($f.FullName)
        $needs = $false
        foreach ($pair in $Replacements) { if ($raw.Contains($pair[0])) { $needs = $true } }
        if ($needs) { $skippedHashed += $f.FullName.Substring($Pub.Length + 1) }
        continue
    }
    $text = [IO.File]::ReadAllText($f.FullName)
    $new = $text
    foreach ($pair in $Replacements) { $new = $new.Replace($pair[0], $pair[1]) }
    if ($new -ne $text) {
        [IO.File]::WriteAllText($f.FullName, $new, (New-Object Text.UTF8Encoding($false)))
        $edited++
    }
}
Write-Host "== sanitised: scanned $scanned text files, rewrote $edited =="
if ($skippedHashed.Count -gt 0) {
    Write-Host "  NOTE: $($skippedHashed.Count) hash-protected files still contain personal paths:"
    $skippedHashed | Select-Object -First 10 | ForEach-Object { Write-Host "    $_" }
    if ($skippedHashed.Count -gt 10) { Write-Host "    ... and $($skippedHashed.Count - 10) more" }
    Write-Host "  Options: leave them (hashes stay valid), or re-run with -SanitizeAll and then"
    Write-Host "  re-run make_manifest.py inside publish\ so the manifest describes the sanitised copy."
}

# --- 4. size report -------------------------------------------------------

Write-Host ''
Write-Host '== size by top-level folder =='
$total = 0
foreach ($d in (Get-ChildItem $Pub -Directory | Where-Object { $_.Name -ne '.git' })) {
    $bytes = (Get-ChildItem $d.FullName -Recurse -File | Measure-Object -Property Length -Sum).Sum
    if (-not $bytes) { $bytes = 0 }
    $total += $bytes
    Write-Host ("  {0,-12} {1,10:N1} MB" -f $d.Name, ($bytes / 1MB))
}
$rootBytes = (Get-ChildItem $Pub -File | Measure-Object -Property Length -Sum).Sum
if (-not $rootBytes) { $rootBytes = 0 }
$total += $rootBytes
Write-Host ("  {0,-12} {1,10:N1} MB" -f '(root files)', ($rootBytes / 1MB))
Write-Host ("  {0,-12} {1,10:N1} MB" -f 'TOTAL', ($total / 1MB))

if ($total -gt 50MB) {
    Write-Host ''
    Write-Host '  WARNING: over 50 MB. Re-run with -Minimal to drop the raw test output,'
    Write-Host '  or gzip the bulky files before committing.'
}
$big = Get-ChildItem $Pub -Recurse -File | Where-Object { $_.Length -gt 20MB }
if ($big) {
    Write-Host ''
    Write-Host '  Files over 20 MB (GitHub warns above 50 MB, rejects above 100 MB):'
    $big | ForEach-Object { Write-Host ("    {0,8:N1} MB  {1}" -f ($_.Length / 1MB), $_.FullName.Substring($Pub.Length + 1)) }
}

# --- 5. hand-written assets sanity check ----------------------------------
# These are authored by hand, NOT regenerated from the experiment tree. If publish\
# was wiped, a rebuild would silently ship a repo with no licence and no AI-content
# disclosure, so refuse to stay quiet about it.

$Authored = @('README.md', 'LICENSE', 'NOTICE', 'CITATION.cff', '.gitignore', '.gitattributes')
$missingAuthored = @()
foreach ($f in $Authored) {
    if (-not (Test-Path (Join-Path $Pub $f))) { $missingAuthored += $f }
}
if ($missingAuthored.Count -gt 0) {
    Write-Host ''
    Write-Host '  ERROR: these hand-written files are missing from publish\:'
    $missingAuthored | ForEach-Object { Write-Host "    $_" }
    Write-Host '  This script does NOT recreate them. Restore them before committing, otherwise the'
    Write-Host '  repository ships without a licence, without attribution, and without the required'
    Write-Host '  AI-generated-content disclosure.'
}
