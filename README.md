# Voice Phishing APK URL Extractor

APK 안에 **평문으로 적힌 URL**을 정규식으로 추출하는 스크립트입니다.
보이스피싱 등 악성앱 정적 분석에서 C2 서버·피싱 도메인 같은 흔적을 1차로 수집하는 용도로 쓸 수 있습니다.

## 주요 기능

- APK 내부 전체 파일(dex / 리소스 / assets / so 등)을 순회하며 `http(s)` URL 추출
- dex(ASCII·UTF-8)와 매니페스트/리소스(UTF-16)를 각각 처리해 문자열이 서로 붙는 문제 방지
- 출력 가능한 ASCII만 매칭하여 바이너리 잡데이터가 URL 뒤에 붙지 않음
- `schemas.android.com`, `w3.org` 등 앱 로직과 무관한 네임스페이스/라이브러리 URL 제외
- 호스트 형태 검증 — IPv4 또는 TLD를 갖춘 도메인만 통과 (`http://record/`, `https://github` 같은 형태 제거)
- 디렉터리 입력 시 하위의 모든 `.apk`를 재귀 탐색
- 결과를 JSON으로 출력

## 요구사항

- Python 3.7 이상

## 사용법

```bash
# 단일 APK
python apk_urls.py app.apk

# 디렉터리 하위의 모든 .apk 재귀 탐색
python apk_urls.py ./samples

# 결과를 JSON 파일로 저장
python apk_urls.py ./samples -o out.json
```

### 인자 / 옵션

| 인자 / 옵션 | 설명 |
|------|------|
| `path` | APK 파일 또는 디렉터리 (디렉터리 지정 시 하위 `.apk` 재귀 탐색) |
| `-o`, `--output` | 결과 JSON을 파일로 저장 |

## 출력 형식

APK 경로를 키로, 추출된 URL 목록을 값으로 갖는 JSON입니다.

```json
{
  "samples/sub1/app.apk": [
    "http://1.2.3.4:8080/report?x=1",
    "https://api.example-c2.com/c2",
    "https://cdn.example-bad.net/v2/upload",
    "https://pay.fake-bank.co.kr/login"
  ],
  "samples/sub2/clean.apk": []
}
```

- URL이 없거나 전부 제외 대상이면 빈 목록(`[]`)
- 분석에 실패한 APK는 `null`

## 동작 방식

- APK는 ZIP 구조이므로 압축 해제 없이 내부 파일을 직접 읽음
- dex 등 ASCII 계열 파일: 원본 바이트에서 바로 매칭 (문자열 종단 널에서 자동 종료)
- `AndroidManifest.xml` · `.xml` · `.arsc`: UTF-16으로 추가 디코드하여 매칭
- 추출한 URL은 중복 제거 후 정렬
