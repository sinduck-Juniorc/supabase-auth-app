param([string]$Root = 'C:\ZetaMesh\.private\signing')
$ErrorActionPreference = 'Stop'
$keyPath = Join-Path $Root 'zetamesh-v3-signing.p12'
$certificatePath = Join-Path $Root 'zetamesh-v3-public.cer'
if ((Test-Path -LiteralPath $keyPath) -or (Test-Path -LiteralPath $certificatePath)) {
    throw '기존 키 또는 인증서가 있습니다. 덮어쓰지 않습니다.'
}
$password = Read-Host 'V3 키 암호를 입력하세요 (별도로 안전하게 보관)' -AsSecureString
$confirm = Read-Host '같은 암호를 다시 입력하세요' -AsSecureString
# SecureString 비교를 위한 메모리는 비교 직후 해제한다. 값은 출력·저장하지 않는다.
$a = [IntPtr]::Zero
$b = [IntPtr]::Zero
try {
    $a = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($confirm)
    if ($password.Length -lt 12 -or
        [Runtime.InteropServices.Marshal]::PtrToStringBSTR($a) -cne [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b)) {
        throw '암호는 12자 이상이어야 하며 두 입력이 같아야 합니다.'
    }
} finally {
    if ($a -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($a) }
    if ($b -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}
New-Item -ItemType Directory -Path $Root -Force | Out-Null
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject 'CN=ZetaMesh V3 Local' -FriendlyName 'ZetaMesh V3 Local' -KeyAlgorithm RSA -KeyLength 3072 -HashAlgorithm SHA256 -KeyExportPolicy Exportable -CertStoreLocation 'Cert:\CurrentUser\My' -NotAfter (Get-Date).AddYears(25)
Export-PfxCertificate -Cert $cert -FilePath $keyPath -Password $password -ChainOption EndEntityCertOnly | Out-Null
$check = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
try {
    $check.Import($keyPath, $password, [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::EphemeralKeySet)
    if (-not $check.HasPrivateKey) { throw '내보낸 파일에서 개인 키를 확인하지 못했습니다.' }
    if ($check.Thumbprint -ne $cert.Thumbprint) { throw '인증서 일치 검사 실패' }
} finally { $check.Dispose() }
Export-Certificate -Cert $cert -FilePath $certificatePath | Out-Null
$cert | Select-Object Subject, Thumbprint, NotAfter | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Root 'key-info.json') -Encoding UTF8
Remove-Item -LiteralPath ('Cert:\CurrentUser\My\' + $cert.Thumbprint)
Write-Host ('V3 로컬 키 생성 및 암호 재열기 검사 성공: ' + $keyPath)
Write-Host '키 파일과 암호는 별도로 백업하세요. 암호를 채팅에 보내지 마세요.'
Write-Host 'Android 빌드 도구의 실제 서명 검증은 의존성 설치 이후 별도로 진행합니다.'
