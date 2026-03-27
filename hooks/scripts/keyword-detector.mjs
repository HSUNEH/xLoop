// UserPromptSubmit: Detect magic keywords and inject skill triggers
// Only injects when keyword is detected — no injection otherwise
const input = process.env.CLAUDE_INPUT || ''
const lower = input.toLowerCase()

// Exact keyword matches
const KEYWORDS = {
  excalibur: 'xloop:excalibur',
  ralph: 'xloop:ralph',
  ralplan: 'xloop:ralplan',
  research: 'xloop:research',
  upgrade: 'xloop:upgrade',
  'opportunity-scout': 'xloop:opportunity-scout',
  'opportunity scout': 'xloop:opportunity-scout',
  'youtube-transcript': 'xloop:youtube-transcript',
  'youtube transcript': 'xloop:youtube-transcript'
}

// Pattern-based detection (regex → skill)
const PATTERNS = [
  // YouTube URL + action context → youtube-transcript
  {
    test: () => /(?:youtube\.com\/watch|youtu\.be\/|youtube\.com\/shorts\/)/.test(lower),
    keyword: 'youtube-url',
    skill: 'xloop:youtube-transcript'
  },
  // Natural language about YouTube content analysis
  {
    test: () => /(?:유튜브|영상|youtube).{0,20}(?:내용|자막|분석|요약|파악|추출|transcript)/.test(lower)
      || /(?:내용|자막|분석|요약|파악|추출).{0,20}(?:유튜브|영상|youtube)/.test(lower),
    keyword: 'youtube-content',
    skill: 'xloop:youtube-transcript'
  },
  // Natural language about trends/opportunities
  {
    test: () => /(?:트렌드|기회|아이디어|사이드\s*프로젝트).{0,20}(?:추천|탐색|찾|분석|조사)/.test(lower)
      || /(?:뭐가? 좋을까|뭐 ?만들|뭐 ?할까|주제 ?추천)/.test(lower),
    keyword: 'opportunity-hint',
    skill: 'xloop:opportunity-scout'
  }
]

const detected = Object.entries(KEYWORDS)
  .filter(([kw]) => lower.includes(kw))
  .map(([kw, skill]) => ({ keyword: kw, skill }))

for (const pattern of PATTERNS) {
  if (pattern.test() && !detected.some(d => d.skill === pattern.skill)) {
    detected.push({ keyword: pattern.keyword, skill: pattern.skill })
  }
}

if (detected.length > 0) {
  const names = detected.map(d => d.keyword.toUpperCase()).join(', ')
  console.log(`[MAGIC KEYWORDS DETECTED: ${names}]`)
}
