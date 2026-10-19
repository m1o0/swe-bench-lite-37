# One-shot packager: stage .\publish, fill in author placeholders, create the git commit,
# then print the exact push commands.
#
#   powershell -File package_for_github.ps1
#   powershell -File package_for_github.ps1 -Minimal
#   powershell -File package_for_github.ps1 -AuthorName "Zhang San" -GitHubUser zhangsan -RepoName swe-bench-lite-37
#   powershell -File package_for_github.ps1 -SanitizeAll      # also sanitise hash-protected files
#
# It never pushes anything by itself, and it never modifies the source experiment files.

param(
    [switch]$Minimal,
    [switch]$SanitizeAll,
    [string]$AuthorName = '',
    [string]$GitHubUser = '',
    [string]$RepoName = '',
    [string]$ContactEmail = ''
)

$ErrorActionPreference = 'Stop'

$Src = $PSScriptRoot
$Pub = Join-Path $Src 'publish'

function Say([string]$msg) { Write-Host $msg }

# --- 0. sanity -------------------------------------------------------------

$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Say 'ERROR: git is not on PATH. Install Git for Windows, reopen the shell, then re-run.'
    exit 1
}

Say '== 1/5 staging publish\ =='
& (Join-Path $Src 'prepare_publish.ps1') -Minimal:$Minimal -SanitizeAll:$SanitizeAll
if (-not (Test-Path $Pub)) { Say "ERROR: $Pub was not created."; exit 1 }

# --- 2. author metadata ----------------------------------------------------

Say ''
Say '== 2/5 author metadata =='

function Get-GitConfigValue([string]$key) {
    $v = (& git config --get $key 2>$null)
    if ($v) { return $v.Trim() }
    return ''
}

if (-not $AuthorName) { $AuthorName = Get-GitConfigValue 'user.name' }
if (-not $GitHubUser) { $GitHubUser = Get-GitConfigValue 'github.user' }
if (-not $ContactEmail) { $ContactEmail = Get-GitConfigValue 'user.email' }
if (-not $RepoName) { $RepoName = 'swe-bench-lite-37' }

$placeholdersLeft = @()

if ($AuthorName) {
    $parts = $AuthorName.Trim() -split '\s+'
    if ($parts.Count -ge 2) {
        $family = $parts[$parts.Count - 1]
        $given = ($parts[0..($parts.Count - 2)] -join ' ')
    } else {
        $family = $parts[0]
        $given = $parts[0]
    }
    foreach ($rel in @('LICENSE', 'CITATION.cff')) {
        $p = Join-Path $Pub $rel
        if (Test-Path $p) {
            $t = [IO.File]::ReadAllText($p)
            $t = $t.Replace('<your name>', $AuthorName)
            $t = $t.Replace('<your family name>', $family)
            $t = $t.Replace('<your given name>', $given)
            [IO.File]::WriteAllText($p, $t, (New-Object Text.UTF8Encoding($false)))
        }
    }
    Say "  author: $AuthorName"
} else {
    Say '  WARNING: no author name found (pass -AuthorName or set git config user.name)'
}

if ($GitHubUser) {
    $p = Join-Path $Pub 'CITATION.cff'
    if (Test-Path $p) {
        $t = [IO.File]::ReadAllText($p)
        $t = $t.Replace('<your-user>', $GitHubUser).Replace('<your-repo>', $RepoName)
        [IO.File]::WriteAllText($p, $t, (New-Object Text.UTF8Encoding($false)))
    }
    Say "  github: $GitHubUser/$RepoName"
} else {
    Say '  WARNING: no GitHub user found (pass -GitHubUser); CITATION.cff keeps placeholders'
}

# --- 3. still-unfilled placeholders? --------------------------------------

foreach ($f in (Get-ChildItem $Pub -Recurse -File)) {
    if (@('.md', '.cff', '.txt', '') -notcontains $f.Extension.ToLower()) { continue }
    $t = [IO.File]::ReadAllText($f.FullName)
    if ($t -match '<your[- ]') {
        $placeholdersLeft += $f.FullName.Substring($Pub.Length + 1)
    }
}
if ($placeholdersLeft.Count -gt 0) {
    Say ''
    Say '  WARNING: placeholders remain in:'
    $placeholdersLeft | ForEach-Object { Say "    $_" }
    Say '  Edit them, or re-run with -AuthorName / -GitHubUser, then: git commit --amend --no-edit'
}

# --- 4. git ignore/attributes, add, guard ---------------------------------

Say ''
Say '== 3/5 git init + add =='
Push-Location $Pub
try {
    if (-not (Test-Path '.git')) {
        & git init | Out-Null
        & git symbolic-ref HEAD refs/heads/main
        Say '  initialised a new repository on branch main'
    } else {
        Say '  existing .git found - staging into it'
    }

    & git add -A

    $staged = & git -c core.quotepath=false diff --cached --name-only
    $stagedCount = 0
    if ($staged) { $stagedCount = @($staged).Count }

    Say ''
    Say '== 4/5 guards =='
    Say "  staged files: $stagedCount"

    # GitHub hard-rejects files over 100 MB; refuse before creating a bad commit.
    $tooBig = Get-ChildItem $Pub -Recurse -File |
        Where-Object { $_.FullName -notlike "*\.git\*" -and $_.Length -gt 95MB }
    if ($tooBig) {
        Say '  ERROR: files over 95 MB would be rejected by GitHub:'
        $tooBig | ForEach-Object { Say ("    {0,8:N1} MB  {1}" -f ($_.Length / 1MB), $_.FullName.Substring($Pub.Length + 1)) }
        Say '  Re-run the packager with -Minimal, or gzip those files, then retry.'
        exit 1
    }
    Say '  size guard: ok (no file over 95 MB)'

    # evidence files must stay byte-identical to what the manifest hashed
    $manifestPath = Join-Path $Pub 'MANIFEST_v1.json'
    if (Test-Path $manifestPath) {
        Say '  note: MANIFEST_v1.json was copied verbatim so the recorded SHA-256 values still hold'
    }

    # --- 5. commit -------------------------------------------------------
    Say ''
    Say '== 5/5 commit =='

    $cfgName = Get-GitConfigValue 'user.name'
    $cfgMail = Get-GitConfigValue 'user.email'
    if (-not $cfgName -or -not $cfgMail) {
        if ($AuthorName -and $GitHubUser) {
            & git config user.name $AuthorName
            & git config user.email "$GitHubUser@users.noreply.github.com"
            Say "  set repo-local identity: $AuthorName <$GitHubUser@users.noreply.github.com>"
        } elseif ($AuthorName -and $ContactEmail) {
            & git config user.name $AuthorName
            & git config user.email $ContactEmail
            Say "  set repo-local identity: $AuthorName <$ContactEmail>"
        } else {
            Say '  ERROR: git identity is not configured. Run one of:'
            Say '    git config --global user.name  "Your Name"'
            Say '    git config --global user.email "you@example.com"'
            Say '  then re-run this script.'
            exit 1
        }
    }

    $msg = 'SWE-bench Lite 37: blind-written patches, official harness grading, frozen manifest'
    & git commit -m $msg | Out-Null
    $hash = (& git rev-parse --short HEAD).Trim()
    $branch = (& git rev-parse --abbrev-ref HEAD).Trim()

    Say ''
    Say '  committed.'
    Say "    branch : $branch"
    Say "    commit : $hash"
    Say "    files  : $stagedCount"

} finally {
    Pop-Location
}

# --- 6. push instructions --------------------------------------------------

Say ''
Say '============================================================'
Say ' READY TO PUSH'
Say '============================================================'
Say ''
Say "Repository folder: $Pub"
Say ''
Say 'Option A - GitHub CLI (creates the remote and pushes in one go):'
Say "  cd `"$Pub`""
Say "  gh repo create $RepoName --public --source . --remote origin --push"
Say ''
Say 'Option B - plain git:'
Say "  cd `"$Pub`""
Say "  git remote add origin https://github.com/$GitHubUser/$RepoName.git"
Say '  git push -u origin main'
Say ''
Say 'Before you push, confirm:'
Say '  1. the model provider''s terms allow publishing the generated patches and write-ups'
Say '     (see NOTICE, item 3)'
if ($Minimal) {
    Say '  2. this is the -Minimal package: raw test_output.txt was NOT included;'
    Say '     logs/**/report.json + eval.sh still carry the official per-instance verdict'
} else {
    Say '  2. logs/**/eval.sh embeds the benchmark test_patch (MIT, attribution in NOTICE)'
}
if ($placeholdersLeft.Count -gt 0) {
    Say '  3. placeholders are still present in: ' + ($placeholdersLeft -join ', ')
} else {
    Say '  3. author placeholders: all filled in'
}
Say ''
Say 'To redo the commit after editing something:'
Say '  git add -A ; git commit --amend --no-edit'
Say ''
Say 'To re-run on top of the existing repo (after a new v2 evaluation, for example):'
Say '  powershell -File package_for_github.ps1 -Minimal ; cd publish ; git add -A ; git commit -m "v2 results"'
