# babylock-rules

'아기 터치잠금' 앱의 아기 플레이어(앱 안 유튜브)가 받아 쓰는 광고 차단 규칙.

- `manual.json` — 직접 고치는 규칙(차단 주소, 숨김, 건너뛰기 버튼, 추가 스크립트 `extraScript`).
- `sync.py` — uBlock Origin 커뮤니티 필터(uAssets)에서 유튜브 규칙을 뽑아 `manual.json`과 합쳐 `rules.json`을 만든다.
- `.github/workflows/sync.yml` — 6시간마다, 그리고 `manual.json`을 고치면 `rules.json`을 다시 만든다.
- 앱은 플레이어를 열 때 `rules.json`을 받고, 실패하면 마지막으로 받은 규칙을 쓴다.

광고가 다시 나오면 `manual.json`을 고쳐 푸시하면 된다. 앱을 다시 설치할 필요는 없다.