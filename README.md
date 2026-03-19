# xLoop

도메인 리서치와 개발을 자동화하는 Expert Loop 하네스.

YouTube 영상을 검색하고, NotebookLM에 넣어 AI로 심층 분석할 수 있습니다.

## 설치

```bash
cd xLoop
bash setup.sh
notebooklm login  # Google 계정 인증
```

## 사용법

```
/yt-search "AI agents"                          # YouTube 검색
/notebooklm-add "리서치" URL1 URL2              # 노트북에 소스 추가
/notebooklm ask "핵심 내용을 요약해줘"            # 심층 분석
```

### 파이프라인

```
/yt-search → URL 선택 → /notebooklm-add → /notebooklm ask
```

### yt-search 옵션

| 플래그 | 기본값 | 설명 |
|--------|--------|------|
| `--count N` | 20 | 결과 수 |
| `--months N` | 6 | 최근 N개월 필터 |
| `--no-date-filter` | - | 전체 기간 |

## 요구사항

- Python 3.11+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [notebooklm-py](https://github.com/nichochar/notebooklm-py)
