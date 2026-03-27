---
description: "PPT 슬라이드 자동 생성 — 자료조사부터 고퀄리티 PPTX까지. 멀티에이전트 팀이 리서치→구조화→디자인→변환을 자동으로 수행"
allowed-tools: ["Read", "Glob", "Grep", "Bash", "Write", "Agent", "WebSearch", "WebFetch"]
---

# Slide Generator — PPT 멀티에이전트 팀

자료조사 → 구조화 → HTML 슬라이드 디자인 → PPTX 변환까지 자동으로 수행하는 멀티에이전트 팀.
Builder Josh의 ppt_team_agent 아키텍처 기반.

사용자의 요청: $ARGUMENTS

---

## 팀 구조

```
사용자 요청
    │
    ▼
┌─────────────────────┐
│  1. Research Agent   │  웹 리서치 → 자료 수집/검증
│  (서브에이전트)       │  → research-result.md 생성
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  2. Organizer Agent  │  리서치 결과 → 슬라이드 구조 설계
│  (서브에이전트)       │  → slide-outline.md 생성
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  3. Design Skill     │  구조 → HTML 슬라이드 생성
│  (스킬)              │  → slides/*.html 생성
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  4. PPTX Skill       │  HTML → PPTX 변환
│  (스킬)              │  → presentation.pptx 생성
└─────────────────────┘
```

## 실행 흐름

### Step 1: 요청 분석

사용자의 요청에서 추출:
- **주제**: 프레젠테이션 핵심 주제
- **목적**: 발표, 보고, 제안, 교육 등
- **대상**: 청중 특성
- **슬라이드 수**: 명시 없으면 10~15장
- **디자인 톤**: 명시 없으면 미니멀/프로페셔널

### Step 2: Research Agent 실행

research-agent 서브에이전트를 호출하여 주제에 대한 자료 조사를 수행한다.

```
Agent 호출:
- subagent_type 또는 Agent tool로 research-agent 실행
- 주제, 목적, 청중 정보를 전달
- 출력: research-result.md (핵심 포인트, 통계, 트렌드, 사례, 출처)
```

research-agent는 `$CLAUDE_PLUGIN_ROOT/agents/research-agent.md`에 정의된 절차에 따라:
1. 주제 분석 → 핵심 키워드 추출
2. WebSearch로 최신 정보, 통계, 트렌드 수집
3. 출처 신뢰성 검증
4. 구조화된 리서치 결과 마크다운으로 정리

### Step 3: Organizer Agent 실행

organizer-agent 서브에이전트를 호출하여 리서치 결과를 슬라이드 구조로 변환한다.

```
Agent 호출:
- organizer-agent 실행
- research-result.md를 입력으로 전달
- 출력: slide-outline.md (슬라이드별 상세 콘텐츠)
```

organizer-agent는 `$CLAUDE_PLUGIN_ROOT/agents/organizer-agent.md`에 정의된 절차에 따라:
1. 리서치 자료 심층 분석
2. 스토리라인 설계 (도입→본론→결론)
3. 슬라이드별 상세 콘텐츠 작성 (제목, 핵심 메시지, 본문, 시각 요소, 발표자 노트)
4. slide-outline.md 파일 생성

**사용자 확인**: "이 슬라이드 구성으로 진행할까요?" → 수정 요청 가능

### Step 4: Design Skill로 HTML 슬라이드 생성

slide-outline.md의 각 슬라이드를 HTML로 변환한다.
`$CLAUDE_PLUGIN_ROOT/tools/design-skill/SKILL.md`의 디자인 시스템을 따른다.

핵심 규격:
- **크기**: 720pt × 405pt (16:9)
- **폰트**: Pretendard (CDN)
- **스타일**: 미니멀, 타이포 중심, 모노톤 + 포인트컬러

각 슬라이드를 `slides/slide-01.html`, `slides/slide-02.html`, ... 형식으로 생성.

### Step 5: PPTX Skill로 변환

HTML 슬라이드들을 PPTX로 변환한다.

```bash
# slides/ 디렉토리 확인
ls slides/*.html

# html2pptx.js 실행
node $CLAUDE_PLUGIN_ROOT/tools/pptx-skill/scripts/html2pptx.js

# 또는 직접 PptxGenJS 사용
node -e "
import PptxGenJS from 'pptxgenjs';
// ... 변환 로직
"
```

변환 후 결과 파일 경로를 사용자에게 알려준다.

### Step 6: 검증 + 전달

- 생성된 PPTX 파일 확인
- 썸네일 생성 (선택)
  ```bash
  python $CLAUDE_PLUGIN_ROOT/tools/pptx-skill/scripts/thumbnail.py presentation.pptx output-thumbnail
  ```
- 파일 경로 안내

## Rules

- 한국어로 응답
- Step 3 후 반드시 사용자 확인 (슬라이드 구성 검토)
- 한 슬라이드 = 한 메시지 원칙
- 모든 데이터에 출처 포함
- 색상 코드에 # 접두사 사용 금지 (PptxGenJS 규칙)
- HTML 슬라이드는 720pt × 405pt 고정
- Pretendard 폰트 사용

## Anti-Patterns

- 텍스트만 가득한 슬라이드 금지
- 모든 슬라이드가 같은 레이아웃 금지
- 출처 없는 데이터 금지
- 발표 원고를 슬라이드에 그대로 쓰지 말 것
