param(
    [ValidateSet('battery', 'ble')]
    [string]$Mode = 'battery',
    [ValidateRange(1, 100)]
    [int]$Count = 20,
    [string]$Adb = 'adb'
)

$ErrorActionPreference = 'Stop'
$probe = 'org.zetamesh.gnss.v3/org.zetamesh.gnss.TrekkingProbe'
$probeArgs = @('shell', 'am', 'instrument', '-w', '-r', '-e', 'mode', $Mode)
if ($Mode -eq 'ble') {
    $probeArgs += @('-e', 'count', $Count.ToString())
}

$output = & $Adb @probeArgs $probe
$exitCode = $LASTEXITCODE
$output
if ($exitCode -ne 0 -or -not (@($output) -match '^INSTRUMENTATION_CODE:\s*-1\s*$')) {
    exit 1
}
exit 0
