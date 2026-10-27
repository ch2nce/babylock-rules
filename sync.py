"""uBlock Origin 커뮤니티 필터에서 유튜브 관련 규칙을 뽑아 manual.json과 합쳐 rules.json을 만든다.

- json-prune 계열 스크립틀릿의 경로 → pruneKeys (마지막 키 이름만, 'ad'가 들어간 것만)
- 응답 글자 바꾸기(trusted-rpfr, trusted-replace-fetch/xhr-response) → textReplacements
- json-edit 계열의 [?.키] 배열 항목 지우기 → removeItemKeys
- (m.)youtube.com 일반 숨김 선택자 → hideSelectors (절차형 필터 제외)
네트워크 차단·건너뛰기 버튼·추가 스크립트는 manual.json에서만 관리한다.
"""
import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/"
YEAR = datetime.date.today().year
LISTS = ["filters.txt", "quick-fixes.txt", f"filters-{YEAR}.txt", f"filters-{YEAR - 1}.txt"]
DOMAINS = {"youtube.com", "m.youtube.com", "www.youtube.com"}
PROCEDURAL = re.compile(r":(has-text|upward|xpath|remove|style|matches-|min-text|watch-attr|others|-abp-)")
SCRIPTLET = re.compile(r"^([^#]*)##\+js\((.*)\)\s*$")
COSMETIC = re.compile(r"^([^#]*)##([^+].*)$")
KEY = re.compile(r"^[A-Za-z_]\w*$")
REPLACERS = {"trusted-rpfr", "trusted-replace-fetch-response", "trusted-replace-xhr-response"}
ITEM_KEY = re.compile(r"\[\?\.(\w+)\]")


def unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        s = s[1:-1]
    return s.replace("\\,", ",")


def url_regex(s: str) -> str:
    s = unquote(s)
    if len(s) >= 2 and s.startswith("/") and s.endswith("/"):
        return s[1:-1]
    return re.escape(s) if s else ""


def fetch(name: str) -> str:
    try:
        with urllib.request.urlopen(BASE + name, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:  # 연도별 목록은 없을 수 있다
        print(f"skip {name}: {e}", file=sys.stderr)
        return ""


def for_youtube(domains: str) -> bool:
    ds = [d.strip() for d in domains.split(",") if d.strip()]
    return any(d in DOMAINS for d in ds) and not any(d.startswith("~") and d[1:] in DOMAINS for d in ds)


def split_args(s: str) -> list[str]:
    out, cur, esc = [], "", False
    for ch in s:
        if esc:
            cur += ch
            esc = False
        elif ch == "\\":
            cur += ch
            esc = True
        elif ch == ",":
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return out


def main() -> None:
    prune, hide, items = set(), set(), set()
    replacements = []
    for name in LISTS:
        for line in fetch(name).splitlines():
            line = line.strip()
            if not line or line.startswith("!") or "#@#" in line:
                continue
            m = SCRIPTLET.match(line)
            if m:
                if not for_youtube(m.group(1)):
                    continue
                args = split_args(m.group(2))
                if args and args[0] in REPLACERS and len(args) >= 3:
                    r = {"find": unquote(args[1]), "replace": unquote(args[2]), "url": url_regex(args[3]) if len(args) > 3 else ""}
                    if r["find"] and r not in replacements:
                        replacements.append(r)
                    continue
                if args and args[0].startswith("json-edit") and len(args) > 1:
                    items.update(k for k in ITEM_KEY.findall(args[1]) if "ad" in k.lower())
                    continue
                if args and args[0].startswith("json-prune") and len(args) > 1:
                    for path in args[1].split():
                        last = path.split(".")[-1].replace("[]", "").replace("[-]", "")
                        if KEY.match(last) and "ad" in last.lower():
                            prune.add(last)
                continue
            m = COSMETIC.match(line)
            if m and for_youtube(m.group(1)) and not PROCEDURAL.search(m.group(2)):
                hide.add(m.group(2).strip())

    manual = json.loads((ROOT / "manual.json").read_text(encoding="utf-8"))
    rules = dict(manual)
    rules["pruneKeys"] = sorted(set(manual.get("pruneKeys", [])) | prune)
    rules["hideSelectors"] = sorted(set(manual.get("hideSelectors", [])) | hide)
    rules["removeItemKeys"] = sorted(set(manual.get("removeItemKeys", [])) | items)
    reps = list(manual.get("textReplacements", []))
    reps += [r for r in replacements if r not in reps]
    rules["textReplacements"] = reps
    rules["version"] = int(datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M"))
    rules["community"] = {"pruneKeys": len(prune), "hideSelectors": len(hide), "textReplacements": len(replacements), "removeItemKeys": len(items)}

    out = ROOT / "rules.json"
    old = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    same = {k: v for k, v in old.items() if k != "version"} == {k: v for k, v in rules.items() if k != "version"}
    if same:
        print("no change")
        return
    out.write_text(json.dumps(rules, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"updated: prune {len(rules['pruneKeys'])}, hide {len(rules['hideSelectors'])}")


if __name__ == "__main__":
    main()
