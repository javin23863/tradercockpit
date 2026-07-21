# Registers the whole post-close lane. This file is documentation plus an operator-run command;
# it must never be executed by an agent.
#
# Windows Task Scheduler has no timezone support. Bangkok is 11 hours ahead of Eastern during
# EDT and 12 during EST, so two local triggers are required and daily_lane.py's 16:00 ET
# hour-guard drops the wrong one. Tuesday-Saturday local equals Monday-Friday US/Eastern.

$repo = "C:\Users\MSI\Documents\tradercockpit"
$python = "$repo\OpenMontage\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw "Missing required Python: $python" }

$action = New-ScheduledTaskAction -Execute $python `
    -Argument "`"$repo\tools\daily_lane.py`" --at-production-hour" `
    -WorkingDirectory $repo

$localRunDays = @("Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
$triggers = @(
    (New-ScheduledTaskTrigger -Weekly -DaysOfWeek $localRunDays -At 3:05AM),  # 16:05 EDT
    (New-ScheduledTaskTrigger -Weekly -DaysOfWeek $localRunDays -At 4:05AM)   # 16:05 EST
)

# Conservative retry policy: no automatic retry can overwrite a partial evidence folder.
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 6) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "tradercockpit-daily-lane" `
    -Action $action -Trigger $triggers -Settings $settings `
    -Description "16:05 ET Codex content step, 18:00 ET gated PRIVATE post-close handoff; failures log and Telegram, never public." `
    -RunLevel Limited -Force
