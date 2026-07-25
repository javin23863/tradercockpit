# Auto-start for the Saturday weekly recap lane. Mirrors daily_autostart.ps1: paired local
# triggers cover EDT/EST and daily_lane.py owns start/resume state and receipts.
#
# Two differences from the daily, both deliberate:
#   - its own mutex, so the two lanes can never serialize behind each other by accident
#   - the weekday guard is inverted: this one runs ONLY on Saturday US/Eastern, and it checks
#     that here as well as in the trigger, because a misfire would mint a bogus weekly- folder
param([switch]$DryRun)

$repo = 'C:\Users\MSI\Documents\tradercockpit'
$python = "$repo\OpenMontage\.venv\Scripts\python.exe"
$et = [System.TimeZoneInfo]::ConvertTime((Get-Date), [System.TimeZoneInfo]::FindSystemTimeZoneById('Eastern Standard Time'))
$prod = 'weekly-{0:yyyy-MM-dd}' -f $et.Date
$dir = "$repo\productions\$prod"

if ($et.DayOfWeek -ne 'Saturday') { if ($DryRun) { 'exit: not Saturday ET' }; exit 0 }

if ($DryRun) {
    if ($et.Hour -eq 12 -or ($et.Hour -eq 13 -and (Test-Path $dir))) {
        "would launch weekly lane: $prod"
    } else {
        'exit: outside start/resume window'
    }
    exit 0
}

$mutex = [Threading.Mutex]::new($false, 'Local\TraderCockpitWeeklyLane')
$acquired = $false
try {
    try { $acquired = $mutex.WaitOne(0) }
    catch [Threading.AbandonedMutexException] { $acquired = $true }
    if (-not $acquired) { exit 0 }

    & $python "$repo\tools\daily_lane.py" --lane weekly --at-production-hour
    exit $LASTEXITCODE
} finally {
    if ($acquired) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
