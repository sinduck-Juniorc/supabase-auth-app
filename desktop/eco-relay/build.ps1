param([string]$OutputDirectory = "$PSScriptRoot\..\..\.local-test\eco-relay")
$ErrorActionPreference = 'Stop'
$framework = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319"
$metadata = "$env:WINDIR\System32\WinMetadata"
$out = New-Item -ItemType Directory -Force $OutputDirectory
$model = "$PSScriptRoot\..\..\research\ZetaMesh50\models\quality.json"
& "$framework\csc.exe" /nologo /codepage:65001 /optimize+ /target:exe "/out:$($out.FullName)\EcoRelay.exe" `
    "/resource:$model,quality.json" /r:System.Web.Extensions.dll "/r:$framework\System.Runtime.InteropServices.WindowsRuntime.dll" `
    "/r:$framework\System.Runtime.dll" "/r:$framework\System.Runtime.WindowsRuntime.dll" `
    "/r:$metadata\Windows.Devices.winmd" "/r:$metadata\Windows.Foundation.winmd" `
    "/r:$metadata\Windows.Storage.winmd" "$PSScriptRoot\Program.cs"
exit $LASTEXITCODE
