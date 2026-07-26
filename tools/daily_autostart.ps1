# Auto-start for the post-close daily video lane (operator ruling 2026-07-22: "Both").
# The paired local triggers cover EDT/EST; daily_lane owns start/resume state and receipts.
param([switch]$DryRun)

$repo = 'C:\Users\MSI\Documents\tradercockpit'
$python = "$repo\OpenMontage\.venv\Scripts\python.exe"
$et = [System.TimeZoneInfo]::ConvertTime((Get-Date), [System.TimeZoneInfo]::FindSystemTimeZoneById('Eastern Standard Time'))
$prod = 'daily-{0:yyyy-MM-dd}' -f $et.Date
$dir = "$repo\productions\$prod"

if ($DryRun) {
    if ($et.DayOfWeek -in 'Saturday','Sunday') { 'exit: weekend'; exit 0 }
    if ($et.Hour -eq 16 -or ($et.Hour -eq 17 -and (Test-Path $dir))) {
        "would launch daily_lane: $prod"
    } else {
        'exit: outside start/resume window'
    }
    exit 0
}

$mutex = [Threading.Mutex]::new($false, 'Local\TraderCockpitDailyLane')
$acquired = $false
try {
    try { $acquired = $mutex.WaitOne(0) }
    catch [Threading.AbandonedMutexException] { $acquired = $true }
    if (-not $acquired) { exit 0 }

    & $python "$repo\tools\daily_lane.py" --at-production-hour
    exit $LASTEXITCODE
} finally {
    if ($acquired) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
