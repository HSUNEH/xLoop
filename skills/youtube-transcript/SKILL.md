---
name: youtube_transcript
description: YouTube 영상의 자막/트랜스크립트를 추출하여 대화에 출력합니다
disable-model-invocation: true
argument-hint: <YouTube URL>
---

# YouTube Transcript

YouTube 영상의 자막을 추출하여 깨끗한 텍스트로 출력합니다. 영상 내용을 파악하고 분석할 수 있습니다.

## 사용법

- `/youtube_transcript URL` - 해당 영상의 자막 추출 및 분석

## 실행 절차

$ARGUMENTS URL의 자막을 추출합니다. 아래 단계를 순서대로 실행하세요.

### 1단계: 메타데이터 추출

```bash
yt-dlp --dump-json --skip-download "$ARGUMENTS" 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('TITLE:', d.get('title', 'N/A'))
print('CHANNEL:', d.get('channel', 'N/A'))
print('DURATION:', d.get('duration_string', 'N/A'))
print('UPLOAD_DATE:', d.get('upload_date', 'N/A'))
dur = d.get('duration', 0)
if dur > 3600:
    print('WARNING: 1시간 이상의 긴 영상입니다. 전체 요약보다 특정 질문을 추천합니다.')
print('---DESCRIPTION_START---')
print(d.get('description', 'N/A'))
print('---DESCRIPTION_END---')
"
```

메타데이터 추출 결과를 기록해 두세요. 나중에 출력 포맷에 사용합니다.

### 2단계: 자막 다운로드 (2-pass)

```bash
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

# Pass 1: 수동 자막 시도
yt-dlp --write-subs \
  --sub-format json3 \
  --sub-langs "ko,ko-orig,en,en-orig,en-en,ja,ja-orig" \
  --skip-download \
  -o "$WORK_DIR/%(id)s" \
  "$ARGUMENTS" 2>/dev/null

# 수동 자막이 없으면 자동생성 자막으로 폴백
if ! ls "$WORK_DIR"/*.json3 1>/dev/null 2>&1; then
  yt-dlp --write-auto-subs \
    --sub-format json3 \
    --sub-langs "ko,ko-orig,en,en-orig,en-en,ja,ja-orig" \
    --skip-download \
    -o "$WORK_DIR/%(id)s" \
    "$ARGUMENTS" 2>/dev/null
fi

# 자막 파일 확인
ls "$WORK_DIR"/*.json3 2>/dev/null
```

자막 파일이 하나도 없으면 아래 메시지를 사용자에게 전달하세요:
> 이 영상에는 사용 가능한 자막이 없습니다. 영상 설명(Description)을 참고하거나, NotebookLM을 통한 분석을 시도해 보세요.

### 3단계: 자막 파일 선택

다운로드된 json3 파일이 여러 개일 경우 아래 우선순위로 하나를 선택합니다:

**언어 우선순위:** ko > en > ja
**타입 우선순위:** 수동 자막(짧은 코드, 예: `en`) > 자동생성(변형 코드, 예: `en-orig`, `en-en`)

```bash
# 자막 파일 선택: ko > en > ja, 수동 자막 우선
SELECTED=""
for lang in ko en ja; do
  for f in "$WORK_DIR"/*."$lang".json3; do
    [ -f "$f" ] && SELECTED="$f" && break 2
  done
  for f in "$WORK_DIR"/*."$lang"-*.json3; do
    [ -f "$f" ] && SELECTED="$f" && break 2
  done
done
echo "Selected: $SELECTED"
```

선택된 파일명에서 언어 코드를 확인하세요 (예: `.ko.json3` → 한국어, `.en.json3` → 영어).

### 4단계: json3 파싱 (event-level concatenation)

```bash
python3 -c "
import json,sys,re
d=json.load(sys.stdin)
parts=[]
for e in d.get('events',[]):
    t=''.join(s.get('utf8','') for s in e.get('segs',[]))
    t=t.replace('\n',' ').strip()
    if t:
        parts.append(t)
print(re.sub(r' +',' ',' '.join(parts)))
" < "$SELECTED"
```

### 5단계: 결과 출력

위 단계에서 얻은 정보를 아래 형식으로 정리하여 사용자에게 출력하세요:

```
## 영상 정보
- **제목:** {title}
- **채널:** {channel}
- **길이:** {duration}
- **업로드일:** {upload_date}
- **URL:** {원본 URL}

## 설명
{description}

## 자막 ({언어} / {수동|자동생성})
{파싱된 자막 텍스트}
```

출력 후 사용자가 추가 질문(요약, 분석, 특정 내용 검색 등)을 하면 자막 내용을 기반으로 답변하세요.

## 오류 처리

- **자막 없음:** 사용자에게 안내하고 영상 설명을 대안으로 제시
- **비공개/연령제한 영상:** Safari 쿠키로 재시도 → Chrome 쿠키로 재시도 → 공개 영상이면 쿠키 없이 시도
  ```bash
  yt-dlp --cookies-from-browser safari --skip-download ...
  yt-dlp --cookies-from-browser chrome --skip-download ...
  ```
- **HTTP 429 (속도 제한):** 잠시 대기 후 한 번 재시도, 실패하면 사용자에게 안내
- **1시간 이상 영상:** 메타데이터 추출 시 경고 출력됨. 사용자에게 전체 요약 대신 특정 질문을 권장
- **임시 파일:** `trap`으로 항상 정리됨
