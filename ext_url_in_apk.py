import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

RE_URL = re.compile(r"""https?://[^\x00-\x20\x7f-\xff\s"'<>)\]}\\|^`]+""", re.IGNORECASE)

# URL 끝 문자 제거 대상
TRAILING = ".,;:!?)'\"]}>"

# IPv4 호스트 판별
RE_IPV4 = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")

# 제외 대상 — 앱 로직 무관 네임스페이스/스키마/라이브러리 URL
NOISE = (
    "schemas.android.com", "www.w3.org", "www.apache.org", "xml.org",
    "java.sun.com", "xmlpull.org", "ns.adobe.com", "www.inkscape.org",
    "purl.org", "iptc.org", "ns.useplus.org", "w3.org", "schema.org",
    "goo.gl/android", "developer.android.com", "github.com/google",
)


def is_noise(url):
    return any(n in url for n in NOISE)

def host_of(url):
    m = re.match(r"https?://([^/?#]+)", url, re.IGNORECASE)
    if not m:
        return ""
    host = m.group(1)
    if "@" in host:                   
        host = host.rsplit("@", 1)[1]
    if ":" in host:                    
        h, _, port = host.rpartition(":")
        if port.isdigit():
            host = h
    return host.lower()

def is_valid_url(url):
    host = host_of(url)
    if not host:
        return False
    if RE_IPV4.match(host) or host == "localhost":
        return True
    if "." not in host:
        return False
    tld = host.rsplit(".", 1)[-1]
    return len(tld) >= 2 and tld[0].isalpha()

def urls_in(data, name):
    out = set(RE_URL.findall(data.decode("latin-1", "ignore")))
    if name == "AndroidManifest.xml" or name.endswith((".xml", ".arsc")):
        out |= set(RE_URL.findall(data.decode("utf-16-le", "ignore")))
    return out

def extract(path):
    found = set()
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.endswith("/"):
                continue
            try:
                data = z.read(name)
            except Exception:
                continue
            for raw in urls_in(data, name):
                url = raw.rstrip(TRAILING)
                if not is_valid_url(url):   # 호스트에 TLD 없는 URL 제외
                    continue
                if is_noise(url):
                    continue
                found.add(url)
    return sorted(found)

def find_apks(root):
    p = Path(root)
    if p.is_file():
        return [p]
    if p.is_dir():
        return sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() == ".apk")
    return []

def main():
    ap = argparse.ArgumentParser(description="APK 내 평문 URL 정규식 추출기")
    ap.add_argument("path", help="APK 파일 또는 디렉터리 (디렉터리 지정 시 하위 .apk 재귀 탐색)")
    ap.add_argument("-o", "--output", help="결과 JSON 저장 경로")
    args = ap.parse_args()

    apks = find_apks(args.path)
    if not apks:
        print(f"[!] APK 를 찾을 수 없음: {args.path}", file=sys.stderr)
        sys.exit(1)

    result = {}
    for apk in apks:
        try:
            result[str(apk)] = extract(apk)
        except Exception as e:
            print(f"[!] {apk} 실패: {e}", file=sys.stderr)
            result[str(apk)] = None 

    out = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")

if __name__ == "__main__":
    main()