# Registers the Saturday weekly recap lane. This file is documentation plus an operator-run
# command; it must never be executed by an agent.
#
# Windows Task Scheduler has no timezone support. Bangkok is 11 hours ahead of Eastern during
# EDT and 12 during EST, so two local triggers are required and weekly_autostart.ps1's
# 12:00 ET hour-guard drops the wrong one.
#
# Unlike the daily, the two triggers land on DIFFERENT local days:
#     Saturday 12:05 ET (EDT, +11) -> Saturday 23:05 local
#     Saturday 12:05 ET (EST, +12) -> Sunday   00:05 local
# Do not "tidy" these onto one day - that silently drops half the year.

$repo = "C:\Users\MSI\Documents\tradercockpit"
$pwshExe = (Get-Command pwsh).Source
$script = "$repo\tools\weekly_autostart.ps1"
if (-not (Test-Path -LiteralPath $script)) { throw "Missing required script: $script" }

$action = New-ScheduledTaskAction -Execute $pwshExe `
    -Argument "-NonInteractive -NoProfile -File `"$script`"" `
    -WorkingDirectory $repo

$triggers = @(
    (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday -At 11:05PM),  # 12:05 ET, EDT
    (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday   -At 12:05AM)   # 12:05 ET, EST
)

# Conservative retry policy: no automatic retry can overwrite a partial evidence folder.
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 6) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "tradercockpit-weekly-recap" `
    -Action $action -Trigger $triggers -Settings $settings `
    -Description "12:00 ET Saturday Codex weekly-market-recap content step. Stops at an approval-ready package and Telegrams; it never publishes." `
    -RunLevel Limited -Force
