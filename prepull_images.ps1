# Pre-pull the SWE-bench instance images for this experiment through mirrors that
# actually serve the `swebench/*` namespace.
#
# Why: the DaoCloud mirror configured in /etc/docker/daemon.json answers
# "this image is not in the allowlist" for swebench/*, and registry-1.docker.io is
# unreachable from this WSL NAT network.  docker.1ms.run / docker.1panel.live /
# hub.rat.dev do serve them (verified with `docker manifest inspect`).
#
# The harness expects the image name `swebench/sweb.eval.x86_64.<id with __ -> _1776_>:latest`,
# so each image is pulled under the mirror-qualified name and then re-tagged locally.
# Nothing here touches predictions or patch.diff.
#
# Usage: pwsh -File prepull_images.ps1
# Output: prepull_log.txt (per-instance result + final skip list)

$ErrorActionPreference = 'Continue'
$env:WSL_UTF8 = 1

$Base = '<EXP_ROOT>'
$Log = Join-Path $Base 'prepull_log.txt'
$Mirrors = @('docker.1ms.run', 'docker.1panel.live', 'hub.rat.dev')
$Throttle = 3

$instances = Get-Content (Join-Path $Base 'predictions_swebench.jsonl') |
    Where-Object { $_.Trim() } |
    ForEach-Object { ($_ | ConvertFrom-Json).instance_id }

"prepull start $(Get-Date -Format s) instances=$($instances.Count) mirrors=$($Mirrors -join ',') throttle=$Throttle" |
    Set-Content -Path $Log -Encoding utf8

$results = $instances | ForEach-Object -Parallel {
    $id = $_
    $repo = 'sweb.eval.x86_64.' + ($id -replace '__', '_1776_')
    $target = 'swebench/' + $repo + ':latest'
    $mirrors = $using:Mirrors

    $present = (wsl.exe -d Ubuntu-22.04 -- docker images -q $target 2>$null | Out-String).Trim()
    if ($present) {
        return [pscustomobject]@{ id = $id; status = 'already-present'; source = '' }
    }

    foreach ($m in $mirrors) {
        $src = $m + '/' + $repo + ':latest'
        wsl.exe -d Ubuntu-22.04 -- timeout 5400 docker pull $src 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            wsl.exe -d Ubuntu-22.04 -- docker tag $src $target 2>$null | Out-Null
            return [pscustomobject]@{ id = $id; status = 'pulled'; source = $m }
        }
    }
    return [pscustomobject]@{ id = $id; status = 'FAILED'; source = '' }
} -ThrottleLimit $Throttle

$results | Sort-Object id | ForEach-Object {
    "{0}`t{1}`t{2}" -f $_.id, $_.status, $_.source
} | Add-Content -Path $Log -Encoding utf8

$failed = $results | Where-Object { $_.status -eq 'FAILED' } | ForEach-Object { $_.id }
$ok = $results | Where-Object { $_.status -ne 'FAILED' }
"prepull done $(Get-Date -Format s) ok=$($ok.Count) failed=$($failed.Count)" | Add-Content -Path $Log -Encoding utf8
"skip list: $(if ($failed) { $failed -join ', ' } else { '(empty)' })" | Add-Content -Path $Log -Encoding utf8

"ok=$($ok.Count) failed=$($failed.Count)"
"skip list: $(if ($failed) { $failed -join ', ' } else { '(empty)' })"
