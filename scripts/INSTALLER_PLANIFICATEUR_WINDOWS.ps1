param([ValidateSet('daily','weekly')][string]$Frequency='daily')
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Python du projet absent. Lancez INSTALLER_WINDOWS.bat avant ce script.' }
$runner = Join-Path $PSScriptRoot 'run_scheduled_collection.py'
$taskName = 'Stages Marrakech AI - collecte autorisée'
Write-Host "Ce script va créer une tâche Windows $Frequency pour les sources autorisées et l’import automatique explicitement activé."
Write-Host 'Sans collecte externe, mode automatique et références d’autorisation documentées, aucune requête ni import ne sera effectué.'
$answer = Read-Host 'Tapez OUI pour créer la tâche (toute autre réponse annule)'
if ($answer -cne 'OUI') { Write-Host 'Aucune tâche créée.'; exit 0 }
$action = New-ScheduledTaskAction -Execute $python -Argument "`"$runner`"" -WorkingDirectory $root
if ($Frequency -eq 'weekly') {
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9:00AM
} else {
    $trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
}
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Description 'Collecte des sources autorisées après activation explicite.' -Force | Out-Null
Write-Host "Tâche créée : $taskName. Pour la supprimer : Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
