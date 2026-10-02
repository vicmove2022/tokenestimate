# check-live.ps1 -- verify the live site after a push
#
#   powershell -ExecutionPolicy Bypass -File .\check-live.ps1
#
# ASCII labels on purpose: PowerShell 5.1 reads .ps1 files as ANSI unless they
# carry a BOM, so non-ASCII in the source breaks the parser.
# Exit code = number of failures.

$ErrorActionPreference = "Continue"
$base = "https://tokenestimate.com"
$fail = 0

# Expectations come from the deployed dataset, never from literals. A gate with
# hardcoded expected counts reports a healthy site as broken the moment a price
# is added, which is worse than no gate at all.
$expectedModels = 0
$expectedVerified = ""
try {
    $dj = (Invoke-WebRequest "$base/data/model-prices.json" -TimeoutSec 25 -UseBasicParsing).Content | ConvertFrom-Json
    $expectedModels = $dj.models.Count
    $expectedVerified = $dj._meta.lastVerified
} catch {
    Write-Host "cannot read the dataset, cannot derive expectations" -ForegroundColor Red
    exit 1
}

function Hit($path, $note) {
    try {
        $r = Invoke-WebRequest ($base + $path) -TimeoutSec 20 -UseBasicParsing
        $code = $r.StatusCode
        $len  = $r.RawContentLength
        if ($code -ne 200) { $script:fail++ }
        "{0,-4} {1,9}b  {2,-36} {3}" -f $code, $len, $path, $note
    } catch {
        $script:fail++
        "{0,-4} {1,9}   {2,-36} {3}" -f "FAIL", "-", $path, $note
    }
}

Write-Host "`n=== live URL check: $base ===" -ForegroundColor Cyan
Hit "/"                                       "homepage"
Hit "/data/model-prices.json"                "dataset - every pitch cites this"
Hit "/api.html"                              "citation page"
Hit "/CHANGELOG.md"                          "price changelog - the link magnet"
Hit "/llms.txt"                              "AI crawlers"
Hit "/llms-full.txt"                         "AI crawlers, full"
Hit "/embed.html"                            "embed widget"
Hit "/404.html"                              "not-found page"
Hit "/sitemap.xml"                           "sitemap"
Hit "/robots.txt"                            "robots"
Hit "/models/"                               "model hub"
Hit "/providers/"                            "provider hub"
Hit "/compare/"                              "compare hub"
Hit "/models/gpt-5-5/"                       "note: dashes not dots"
Hit "/models/gpt-5-6-sol/"                   "new model page"
Hit "/models/claude-opus-4-7/"               "new model page"
Hit "/models/grok-4-5/"                      "new model page"
Hit "/models/deepseek-v4-pro/"               "model page"
Hit "/providers/anthropic/"                  "provider page"
Hit "/providers/xai/"                        "provider page"
Hit "/compare/cheapest-input/"               "compare cut"
Hit "/compare/cheapest-long-context/"        "compare cut"
Hit "/pricing-patch/pricing-patch-2026-10-02.json" "provenance cited by README"
Hit "/tools/verify.py"                       "pipeline cited by README"

Write-Host "`n=== sitemap ===" -ForegroundColor Cyan
try {
    $sm = (Invoke-WebRequest "$base/sitemap.xml" -TimeoutSec 20 -UseBasicParsing).Content
    $n  = ([regex]::Matches($sm, "<loc>")).Count
    $lm = ([regex]::Matches($sm, "<lastmod>")).Count
    "  URLs      : $n"
    "  lastmod   : $lm"
    foreach ($k in @("gpt-5-6-sol", "claude-opus-4-7", "grok-4-5", "compare/cheapest-input")) {
        $in = $sm -match [regex]::Escape($k)
        "  contains {0,-24} : {1}" -f $k, $(if ($in) { "yes" } else { "NO" })
        if (-not $in) { $fail++ }
    }
} catch { "  FAIL could not read sitemap.xml"; $fail++ }

Write-Host "`n=== dataset ===" -ForegroundColor Cyan
try {
    $j = (Invoke-WebRequest "$base/data/model-prices.json" -TimeoutSec 20 -UseBasicParsing).Content | ConvertFrom-Json
    "  models       : $($j.models.Count)   (derived from the dataset)"
    "  lastVerified : $($j._meta.lastVerified)"
    $need = @("gpt-5.6-sol","claude-opus-4.7","claude-sonnet-5.5","grok-4.5")
    $miss = $need | Where-Object { $j.models.id -notcontains $_ }
    if ($miss) { "  MISSING models : $($miss -join ', ')"; $fail++ }
    else { "  spot-check models : all present" }
} catch { "  FAIL could not parse the dataset"; $fail++ }

Write-Host "`n=== robots.txt ===" -ForegroundColor Cyan
try {
    $rb = (Invoke-WebRequest "$base/robots.txt" -TimeoutSec 20 -UseBasicParsing).Content
    if ($rb -match "Sitemap:\s*https://tokenestimate\.com/sitemap\.xml") {
        "  OK points at the current sitemap"
    } else {
        "  WARN no correct Sitemap line"; $fail++
    }
} catch { "  FAIL"; $fail++ }

Write-Host "`n=== GitHub repo (the CHANGELOG URL in every pitch) ===" -ForegroundColor Cyan
# github.com rate-limits bursts from one IP, so a single miss here is not proof
# the link is dead. Retry before failing the gate.
foreach ($g in @("https://github.com/vicmove2022/tokenestimate",
                 "https://github.com/vicmove2022/tokenestimate/blob/main/CHANGELOG.md",
                 "https://raw.githubusercontent.com/vicmove2022/tokenestimate/main/data/model-prices.json")) {
    $ok = $false
    for ($try = 1; $try -le 3 -and -not $ok; $try++) {
        try {
            $code = (Invoke-WebRequest $g -TimeoutSec 25 -UseBasicParsing).StatusCode
            "  {0,-4} {1}{2}" -f $code, $g, $(if ($try -gt 1) { "  (ok on try $try)" } else { "" })
            $ok = $true
        } catch {
            if ($try -lt 3) { Start-Sleep -Seconds 3 }
        }
    }
    if (-not $ok) { "  FAIL    $g  (3 attempts)"; $fail++ }
}

Write-Host ("`n" + "=" * 58) -ForegroundColor Cyan
if ($fail -eq 0) {
    Write-Host "ALL LIVE. Every URL the outreach copy references returns 200." -ForegroundColor Green
    Write-Host "Next: submit the sitemap in Google Search Console." -ForegroundColor Green
} else {
    Write-Host "$fail check(s) failed. Do not post yet." -ForegroundColor Red
}
exit $fail