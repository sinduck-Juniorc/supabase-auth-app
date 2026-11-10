# 버전 2 보존 및 버전 3 개발 규칙

2026-11-10 사용자 승인: 현재 Android 앱 0.2.1과 지금까지의 실험 기록 전체를 버전 2로 고정한다. 제품 단계명 V2와 Android versionName 0.2.1은 서로 다른 표기다.

| 구분 | 위치 | 상태 |
|---|---|---|
| 버전 2 고정 소스 | 태그 zetamesh-v2.0.0 / 브랜치 baseline/v2 | 커밋 1cf897fe85480fdd0773cc8286746a9e739aa405 |
| 이후 버전 3 개발 | 브랜치 development/v3 / 별도 worktree | V2에서 분기, 개발 준비 |
| V2 실험 조건·요약 | versions/v2 | 기존 결과의 의미·한계 보존 |
| V3 작업 이력 | versions/v3 | 변경·검증·실패·회귀 판단 기록 |
| 사용자 원자료 | 별도 개인 백업 ZIP | 공개 GitHub에 업로드하지 않음 |

## 반드시 지킬 규칙

- V2 태그와 baseline/v2를 이동하거나 강제 갱신하지 않는다. Git 태그/브랜치는 기술적으로 변경 가능하므로 이름만 믿지 말고 위 커밋 해시와 개인 백업 해시를 대조한다. 서버 측 삭제 방지 규칙까지 설정한 것은 아니다.
- main에 V3 기능이나 APK를 바로 덮어쓰지 않는다. development/v3에서만 개발하고 검증된 변경을 리뷰한다.
- V3는 별도 applicationId/package org.zetamesh.gnss.v3를 사용한다. V2 org.zetamesh.gnss와 함께 설치하여 V2 앱 데이터와 사용 경로를 보존한다.
- V3의 소스·APK·실험 입력·분석 결과를 V2 결과로 표시하지 않는다. 새 실험 원본은 captures/v3 등 Git 추적 제외 경로에 보관한다.
- V3 APK 배포 전 패키지 식별자, 화면 버전, 로그 버전, 파일 이름, 빌드 해시, 서명을 검사한다. 기존 V2 APK 다운로드 파일을 덮어쓰지 않는다.
- 기능별로 커밋하며 versions/v3/CHANGELOG_ko.md에 목적·변경·시험·실물 미검증 사항과 회귀 판정을 기록한다.

## 개발 환경에서 V2로 복원

작업 중인 V3 디렉터리에서 reset --hard로 기록을 지우지 않는다. 저장소에 별도 작업 폴더를 만든다.

```text
git fetch origin --tags
git rev-parse zetamesh-v2.0.0^{commit}
git worktree add --detach ../zetamesh-v2-restore zetamesh-v2.0.0
```

출력 해시는 1cf897fe85480fdd0773cc8286746a9e739aa405이어야 한다. 의존성 설치·빌드는 고정 소스의 lockfile과 Android README를 따른다. 개인 백업에는 당시 추적 파일 전체와 Git bundle도 있다. 클라우드 SDK와 node_modules 자체를 재배포하는 백업은 아니다.

## 휴대폰에서 V2로 복귀

V3를 중단하고 별도로 보존한 ‘ZetaMesh 실내 관찰’ V2 앱을 연다. V3와 package가 다르면 V2의 삭제·다운그레이드 없이 사용할 수 있다. V2가 설치되지 않았다면 아래 고정 APK를 설치한다. 이미 같은 package의 더 높은 versionCode를 설치한 단말에서 낮은 APK 설치가 항상 가능한 것은 아니다. 이런 경우 임의 삭제하지 말고 먼저 로그·앱 데이터를 보존한다.

[V2 고정 APK](https://github.com/sinduck-Juniorc/supabase-auth-app/raw/refs/tags/zetamesh-v2.0.0/android/gnss-assist/downloads/ZetaMesh-Indoor-Observer.apk)

## 중대한 실패 시

충돌·해제 실패·예상 밖의 지속 전력 사용·로그 손상·관측을 가속으로 잘못 판정하는 회귀가 발견되면 V3 시험을 중단한다. 해당 APK 해시·커밋·입력·오류 로그를 보존하고 실패를 기록한다. 단말은 V2 앱으로, 개발 확인은 V2 worktree로 돌아간다. V3의 실패 기록이나 V2 원자료를 덮어쓰지 않는다.
