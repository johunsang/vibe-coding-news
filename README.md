# vibe-coding-news

매일 아침, 바이브코딩·AI 코딩 도구 소식을 개발자 관점으로 정리해 주는 **Agent Skill** 입니다.
Claude Code, Codex, Cursor, Copilot, Gemini CLI, MCP, 코딩 에이전트 소식을 모아 출처·사진·다운로드 링크까지 붙인 브리핑 한 장을 만들고, 원하면 **내 말투로 SNS 글 초안**까지 써 줍니다.

An [Agent Skill](https://agentskills.io) that turns the last 24 hours of AI-coding news into a developer briefing with primary sources, images and download links, plus optional social post drafts in your own voice.

## 무엇을 모으나

API 키 없이 동작합니다. Python 3.8+ 만 있으면 됩니다.

| 출처 | 방법 | 가져오는 것 |
|---|---|---|
| GitHub | REST API (`gh` 있으면 자동 사용) | 24시간 내 새 저장소(별 순), Claude Code·Codex·Gemini CLI·Cline·Continue·MCP 서버 최신 릴리스 |
| Hacker News | Algolia API | 키워드별 20점 이상 글, 토론 링크 |
| Lobsters | JSON | ai·vibecoding 태그 |
| Techmeme | RSS | 업계 큰 뉴스 |
| Simon Willison | Atom | 새 모델·도구 실사용기 |
| dev.to | API | 인기 후기 |
| Hugging Face | Daily Papers API | 코딩 에이전트 논문 |

Reddit(429)과 Bluesky 공개 API(403)는 차단이 잦아 넣지 않았습니다.

## 결과물

```
vibe-news/
├── 2026-10-28.md          # 브리핑: TOP 5, 릴리스, 보안, GitHub, 커뮤니티, 해볼 것, 출처 표
├── drafts-2026-10-28.md   # (선택) SNS 초안 3개, 글 하나에 이슈 하나
├── raw-2026-10-28.json    # 수집 원본
└── images/2026-10-28/     # 기사 대표 이미지 (개인 참고용)
```

규칙
- 모든 링크는 `https://` 전체 주소, **1차 원문** + **다운로드 링크** 필수
- 확인 못 한 건 "미확인"으로 표시, 루머·광고 제외
- 아무것도 대신 게시하지 않습니다. 초안은 파일로만.

## 설치

Claude Code:

```bash
git clone https://github.com/johunsang/vibe-coding-news ~/.claude/skills/vibe-coding-news
```

다른 에이전트(Codex, Cursor 등 Agent Skills 지원 도구)는 각 도구의 skills 폴더에 같은 폴더를 넣으면 됩니다.

## 사용

에이전트에게 이렇게 말하면 됩니다.

- "오늘 바이브코딩 소식 정리해줘"
- "AI 코딩 뉴스 브리핑 만들고 내 말투로 스레드 초안 3개"

매일 자동으로 돌리려면 에이전트의 예약 기능(Claude Code 데스크톱 Scheduled tasks, cron 등)에 위 문장을 등록하세요.

스크립트만 따로 써도 됩니다.

```bash
python3 scripts/collect.py --hours 24 --out raw.json
python3 scripts/media.py check https://github.com/anthropics/claude-code
python3 scripts/media.py image https://techcrunch.com/... ./images/01-techcrunch
```

## 설정 (선택)

`config.example.json` 을 `config.json` 으로 복사해 바꿉니다: 출력 폴더, 언어, 키워드, 지켜볼 GitHub 저장소, 추가 RSS, 말투 가이드 경로.

## 내 말투로 초안 쓰기

`references/style-learning.md` 절차대로 내 글 100개 이상을 모아 말투 가이드를 만들고 `config.json` 의 `style_guide` 에 경로를 넣으면, 초안이 그 말투를 따릅니다. 본인 글만, 본인 동의로만 수집합니다.

## 주의

- 이미지와 기사 요약은 개인 참고용입니다. 재게시할 때는 각 매체의 권리를 확인하세요.
- microsoft.com·npmjs.com·sec.gov 는 스크립트 요청에 403을 줍니다. 링크가 죽은 게 아니라 봇 차단입니다(`media.py check` 가 `blocked` 로 표시).

## License

MIT © 2026 TENMILES (Keke Studio)
