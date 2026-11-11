# 개인 자료와 V3 키의 로컬 준비

개인 로그 원본 4개와 기존 전체 백업이 현재 클라우드에 남아 있음을 확인했다. Drive에서 삭제된 사실과 클라우드 원본 소실을 동일시하지 않는다. 사용자 PC에 옮겨졌는지는 아직 미확인이다. 먼저 이 대화의 원래 업로드 메시지에 있는 파일을 내려받아 C:\ZetaMesh\.private\logs\originals에 보관한다. 생성된 백업 ZIP의 다운로드는 실패했으므로 그 링크를 복구 완료 증거로 삼지 않는다.

새 키 준비: tools/New-ZetaMeshV3Key.ps1을 Windows PowerShell에서 실행한다. Windows 인증서 기능으로 RSA3072/SHA256 키를 만들고, 사용자가 입력한 암호로 PKCS12(.p12)에 내보내 다시 열어 개인 키를 확인한다. 암호를 파일·채팅·명령 인자에 넣지 않는다. 기존 키는 덮어쓰지 않는다. 정상 내보내기 이후 임시 사용자 인증서를 제거한다. 오류 시 키 파일이나 인증서가 남을 수 있으므로 임의 덮어쓰기 대신 오류를 확인한다.

저장 위치: C:\ZetaMesh\.private\signing\zetamesh-v3-signing.p12. 공개 인증서 .cer와 비밀이 아닌 key-info.json도 같은 폴더에 생성한다. P12와 암호는 따로 백업한다. 파일 폴더는 해당 Windows 사용자 계정의 접근 권한으로 보호해야 하며 공용 폴더나 공개 GitHub에 넣지 않는다. Windows 인증서 도구로 생성한 키이므로 기존 V2 개발키와 다르다.

현재 빌드 스크립트는 이전 개발용 키 별칭·암호를 가정한다. 새 P12의 키 형식·암호를 지원하도록 빌드를 조정하고 Android apksigner로 실제 검사하는 단계는 의존성 설치 이후에 진행한다. 이 단계는 키 준비이며 기존 V2 앱의 업데이트 키를 대체하지 않는다.

서비스 관리 화면은 각 서비스 계정의 웹 대시보드다. Supabase는 https://supabase.com/dashboard 에서 해당 프로젝트 Settings → API Keys를 확인한다. Vercel은 https://vercel.com/dashboard 의 해당 프로젝트 Settings → Environment Variables이며 실제 Vercel 프로젝트 존재·연결은 아직 확인하지 않았다. GitHub는 https://github.com/sinduck-Juniorc/supabase-auth-app 의 코드·브랜치를 뜻한다. GitHub Settings의 비밀 설정과 앱 .env.local은 다른 저장 위치다. Android 로컬 관찰 앱의 키 생성에는 Supabase/Vercel 설정이 필요하지 않다.

검증 범위: 클라우드에서 원본 존재와 Git 추적 제외 규칙을 확인했다. Windows PowerShell이 제공되지 않아 새 키 생성 스크립트는 Windows에서 아직 실행하지 못했다. 생성·비밀키 포함 확인·서명 성공을 미리 주장하지 않는다. 사용자가 요청한 순서에 따라 의존성 설치는 진행하지 않았다.
