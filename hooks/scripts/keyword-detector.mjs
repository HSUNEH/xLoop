// UserPromptSubmit: Detect magic keywords and inject skill triggers
// Only injects when keyword is detected — no injection otherwise
const input = process.env.CLAUDE_INPUT || ''
const lower = input.toLowerCase()

const KEYWORDS = {
  excalibur: 'xloop:excalibur',
  ralph: 'xloop:ralph',
  ralplan: 'xloop:ralplan',
  research: 'xloop:research',
  upgrade: 'xloop:upgrade'
}

const detected = Object.entries(KEYWORDS)
  .filter(([kw]) => lower.includes(kw))
  .map(([kw, skill]) => ({ keyword: kw, skill }))

if (detected.length > 0) {
  const names = detected.map(d => d.keyword.toUpperCase()).join(', ')
  console.log(`[MAGIC KEYWORDS DETECTED: ${names}]`)
}
