param([string]$Root = 'C:\ZetaMesh')
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$items = @(
    [PSCustomObject]@{ Branch = 'main'; Commit = 'b86009ff700dbc26c1016b3ec675f7cee3baafb1'; Sha256 = '6c129ab7548e0ce826114ed8a5e4eadf29a51c04dc04c6a951c52224dbc30075'; Url = 'https://codeload.github.com/sinduck-Juniorc/supabase-auth-app/zip/b86009ff700dbc26c1016b3ec675f7cee3baafb1' },
    [PSCustomObject]@{ Branch = 'baseline/v2'; Commit = '1cf897fe85480fdd0773cc8286746a9e739aa405'; Sha256 = 'b70fb0cad2d2abea1eecc7669bc7b24ef3b8bd6f266a0003f969167b3edcc65d'; Url = 'https://codeload.github.com/sinduck-Juniorc/supabase-auth-app/zip/1cf897fe85480fdd0773cc8286746a9e739aa405' },
    [PSCustomObject]@{ Branch = 'development/v3'; Commit = 'ce71322012f0db69184ddb0a3b37bdef66759639'; Sha256 = '7f4aa995afdfe6cc44109e5ce4197360f24fac485771645ae9a333221a8c51db'; Url = 'https://codeload.github.com/sinduck-Juniorc/supabase-auth-app/zip/ce71322012f0db69184ddb0a3b37bdef66759639' }
)
foreach ($item in $items) {
    $destination = Join-Path $Root ($item.Branch.Replace('/', [IO.Path]::DirectorySeparatorChar))
    if (Test-Path -LiteralPath $destination) {
        throw "기존 경로가 있어 중단했습니다. 덮어쓰지 않습니다: $destination"
    }
}
New-Item -ItemType Directory -Path $Root -Force | Out-Null
$staging = Join-Path $Root ('.restore-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $staging | Out-Null
$prepared = @()
foreach ($item in $items) {
    Write-Host ("다운로드 및 검증: " + $item.Branch)
    $name = $item.Branch.Replace('/', '-')
    $zip = Join-Path $staging ($name + '.zip')
    Invoke-WebRequest -UseBasicParsing -Uri $item.Url -OutFile $zip
    if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Sha256) {
        throw "ZIP 해시가 다릅니다. 복원을 중단합니다: $name"
    }
    $unpacked = Join-Path $staging $name
    Expand-Archive -LiteralPath $zip -DestinationPath $unpacked
    $children = @(Get-ChildItem -LiteralPath $unpacked -Force)
    if ($children.Count -ne 1 -or -not $children[0].PSIsContainer) { throw "압축 구조 오류: $name" }
    $source = $children[0].FullName
    if (-not (Test-Path -LiteralPath (Join-Path $source 'package.json'))) { throw "프로젝트 파일 누락: $name" }
    $prepared += [PSCustomObject]@{ Source = $source; Item = $item }
}
$report = @()
foreach ($entry in $prepared) {
    $destination = Join-Path $Root ($entry.Item.Branch.Replace('/', [IO.Path]::DirectorySeparatorChar))
    if (Test-Path -LiteralPath $destination) { throw "복원 도중 경로가 생성됐습니다: $destination" }
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Move-Item -LiteralPath $entry.Source -Destination $destination
    $report += [PSCustomObject]@{ Branch = $entry.Item.Branch; Commit = $entry.Item.Commit; Sha256 = $entry.Item.Sha256; Path = $destination }
    Write-Host ("복원됨: " + $destination)
}
$reportPath = Join-Path $Root ('restore-report-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json')
$report | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $reportPath -Encoding UTF8
Remove-Item -LiteralPath $staging -Recurse -Force
Write-Host '세 폴더의 소스 파일 복원을 마쳤습니다. 설치·빌드·실물 실행은 별도 단계입니다.'
Write-Host ("복원 기록: " + $reportPath)
Start-Process explorer.exe -ArgumentList ('"' + $Root + '"')
