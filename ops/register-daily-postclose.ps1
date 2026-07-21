# Registers 'tradercockpit-daily-postclose' — the unattended 18:00 US/Eastern weekday lane.
# NOT run automatically. The operator runs this once, from an elevated PowerShell.
#
# Windows Task Scheduler has no timezone support: triggers fire in machine-local time
# (Asia/Bangkok). 18:00 US/Eastern is 05:00 ICT under EDT and 06:00 ICT under EST, so both
# triggers are registered and tools/daily_postclose.py --at-publish-hour stands down on the
# one that is not actually 18:00 ET. Exactly one run per weekday reaches the pipeline.
#
# Pass the production folder for the day; the daily lane creates it before the close.

param(
    [Parameter(Mandatory = $true)][string]$Production
)

$repo = "C:\Users\MSI\Documents\tradercockpit"
$python = "$repo\OpenMontage\.venv\Scripts\python.exe"

$action = New-ScheduledTaskAction -Execute $python `
    -Argument "$repo\tools\daily_postclose.py $Production --at-publish-hour" `
    -WorkingDirectory $repo

$weekdays = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
$triggers = @(
    (New-ScheduledTaskTrigger -Weekly -DaysOfWeek $weekdays -At 5:00AM),   # 18:00 EDT
    (New-ScheduledTaskTrigger -Weekly -DaysOfWeek $weekdays -At 6:00AM)    # 18:00 EST
)

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "tradercockpit-daily-postclose" `
    -Action $action -Trigger $triggers -Settings $settings `
    -Description "Unattended post-close daily: gates, machine approval, render, publish. Clean=public, warning=private+Telegram, hard fail=no publish." `
    -RunLevel Limited -Force
