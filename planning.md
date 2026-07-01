# Provenance Guard: Planning
## Architecture
### Text Submission Workflow
When a creator submits text, it flows through a rate limiter and content normalizer, then enters a detection engine that evaluates the content using three independent signals: LLM judgment (semantic patterns), stylometric heuristics (linguistic statistics), and perplexity calculation (predictability). All of which are weighted and aggregated into a unified confidence score (0.0-1.0) that maps to a transparency label. This label will be then accompanied by plain-language reasoning, returned to the client, and logged for audit purposes.
```
           CREATOR SUBMITS TEXT
                    │
                    ▼
           ┌──────────────────┐
           │   API Endpoint   │
           │     (Flask)      │
           └──────────────────┘
                    │
                    ▼
           ┌──────────────────┐
           │   Rate Limiter   │
           │  (Flask-Limiter) │
           └──────────────────┘
      exceeded      │
      ┌─────────────┴─────────────┐
      │                           │
      ▼                           ▼
ERROR RESPONSE          ┌──────────────────┐
                        │Content Normalizer│
                        │(standardize text)│
                        └──────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │ Detection Engine │
                        └──────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
      ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
      │   Signal 1   │   │   Signal 2   │   │   Signal 3   │
      │ LLM Judgment │   │  Stylometric │   │  Perplexity  │
      │    (Groq)    │   |  Heuristics  │   │  Calculation │
      └──────────────┘   └──────────────┘   └──────────────┘
              │                   │                   │
    (score + reasoning)  (score + reasoning) (score + reasoning)
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  │
                                  ▼
                       ┌────────────────────┐
                       │ Confidence Scoring │
                       │ (aggregate signals)│
                       └────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Unified Confidence Score │
                    │       (0.0 - 1.0)        │
                    └──────────────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │ Label Generator  │
                        │(create user text)│
                        └──────────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │  Transparency Label Text  │
                    │  (plain language output)  │
                    └───────────────────────────┘
                                  │
        ┌─────────────────────────┴──────────────────────┐
        ▼                                                ▼
┌──────────────────┐                            ┌──────────────────┐
│   API Response   │                            │   Audit Logger   │
│- Result          │                            │- Decision log    │
│- Confidence      │                            │- Signals used    │
│- Label Text      │                            │- Confidence      │
└──────────────────┘                            │- Timestamp       │
        │                                       │- User info       │
        │ return to client                      │- Content ID      │
        ▼                                       └──────────────────┘
┌─────────────────┐
│READER SEES LABEL│
└─────────────────┘
```
---

### Appeal Workflow
If a creator contests the classification, they submit a detailed appeal form providing their writing context and proof. The form includes process duration, methodology, AI tool usage, and optional supporting evidence (drafts, timestamps, chat logs), which triggers a status change to "under review," creates an appeal record with a unique identifier, and routes the case to a human reviewer. The reviewer will assess the original signals against the creator's evidence to make a final decision (approve, deny, or request more information).
```
                  CREATOR CONTESTS CLASSIFICATION
                                │
                                ▼
                    ┌───────────────────────┐
                    │    Appeal Handler     │
                    │- Capture reasoning    │
                    │- Validate appeal      │
                    └───────────────────────┘
            ┌───────────────────┴─────────────────┐
            ▼                                     ▼
┌───────────────────────┐            ┌────────────────────────┐
│      Audit Logger     │            │        Notifier        │
│- Content ID           │            │  Email copy of appeal  │
│- Creator appeal info  │            │    form to creator     │
│- Decision ID          │            └────────────────────────┘
└───────────────────────┘                
            │
            ▼
┌───────────────────────┐
│ Content Status Update │
│ Set to "Under Review" │
└───────────────────────┘
            │
            ▼                    ┌───────────────────┐            
 QUEUED FOR HUMAN REVIEW ──────> │  Reviewer opens   │
                                 │ appeals dashboard │
                                 └───────────────────┘
                                            │
                                            ▼
                                ┌──────────────────────┐
                                │Views queue of pending│
                                │  and assigned cases  │
                                └──────────────────────┘
                                            │
                                            ▼
                                  ┌───────────────────┐
                                  │ Selects and opens │
                                  │ a case for review │
                                  └───────────────────┘
                                            │
                                            ▼
                              ┌──────────────────────────┐
                              │Examines and make decision│
                              └──────────────────────────┘
                                    ┌───────┴───────┐
                                    ▼               ▼
                            ┌──────────────┐ ┌──────────────┐
                            │ Approve/Deny │ │ Inconclusive │
                            └──────────────┘ └──────────────┘
                                    │                │
                                    ▼                ▼
                         ┌──────────────────┐ ┌─────────────────┐
                         │ Content resolved │ │ Email questions │
                         │ Email to creator │ │   to creator    │
                         └──────────────────┘ └─────────────────┘
                                   │                   │
                                   ▼                   ▼
                            ┌────────────┐    ┌─────────────────┐
                            │ Close case │    │Awaiting response│
                            └────────────┘    └─────────────────┘
```

## Detection Signals

### LLM Judgement
**Property Measured:** Semantic coherence, reasoning patterns, contextual consistency, narrative flow, logical argumentation structure, and stylistic markers that the model has learned to associate with human vs. AI-generated text during training.  

**Output format:** Continuous score from 0.0 to 1.0, where 0.0 indicates "human-written" and 1.0 indicates "AI-generated." Also returns structured reasoning explaining the classification.
  
**Why It Differs Between Human and AI:**
* AI models generate text by predicting the most probable next token based on training data patterns. This produces text that is statistically "smooth" and coherent but often lacks the unpredictable tangents, contradictions, emotional authenticity, and genuine curiosity that human writers display.
* Humans write with intent (persuasion, expression, story), which creates distinctive argument structures, voice, and occasionally deliberate rule-breaking for effect. AI aims for statistical likelihood, not intent.
* The LLM has learned patterns of what AI-generated text "looks like" during training (repetitive phrases, hedging language, list-heavy formatting, generic transitions).

**Blind Spots:**
* Humanization: If AI text is deliberately altered to mimic human writing (prompt-engineered, rewritten, or trained to avoid detection markers), the LLM may fail. It cannot find the deception that targets its own training patterns.
* Specialized writing: In highly technical or specialized topics where the LLM has little training data, it cannot distinguish human from AI writing because both appear equally unfamiliar and high-quality.
* Potential Bias: Any LLM has biases in its training data. Therefore, they may incorrectly flag formal, well structured human writing as AI-generated.
* Future Advancement: As AI models improve and training data shifts, the markers the LLM learned become outdated. A text generated by a future model may not match any "AI signature" the current model recognizes.
* No Confidence in Uncertainty: The LLM returns a confidence score, but that score reflects model uncertainty, not ground truth. A 0.6 confidence doesn't mean the text is ambiguous; it means the model is uncertain about what it learned.

### Stylometric Heuristics
**Property Measured:** Statistical distributions of linguistic features, including word frequency entropy, vocabulary richness (type-token ratio), sentence length uniformity, rare word avoidance, function word patterns, n-gram consistency, and readability metrics.

**Output format:** Six independent subscores (each 0.0 to 1.0), aggregated into a single 0.0 to 1.0 stylometry score using mean function.
* Entropy score: normalized Shannon entropy (lower entropy = higher AI likelihood)
* Lexical diversity: (1 - TTR) normalized (lower diversity = higher AI likelihood)
* Sentence variance: inverse of coefficient of variation (lower variance = higher AI likelihood)
* Rare word ratio: (observed rare words / expected rare words) normalized
* Function word ratio: deviation from reference baseline
* N-gram deviation: chi-squared test against reference corpus

**Why It Differs Between Human and AI:**
* Human writers unconsciously vary their linguistic choices. They use rare words unpredictably, vary sentence length naturally, and have idiosyncratic function word preferences shaped by regional dialect, education, and personality.
* AI models generate text by sampling from probability distributions. Even with randomization, the underlying distributions are learned from training data and tend toward the statistical "center." This results in more predictable word sequences, more uniform sentence lengths, and fewer rare word choices (because rare words have lower training frequency).
* Humans occasionally make grammar mistakes, use colloquialisms, and use deliberate stylistic breaks. AI avoids these because they are low-probability in training data.

**Blind Spots:**
* Formal writing: academic papers, technical documentation, business prose naturally exhibit low entropy, high consistency, and avoidance of rare words. These texts can be classified as AI-generated despite being human-written. Stylometry conflates formal writing with AI writing.
* Genre Insensitivity: Poetry, listicles, and instruction manuals inherently have different stylometric signatures. A heuristic trained on prose may incorrectly classify other genres.
Corpus Dependency: Rare word detection requires a reference corpus. If the reference corpus is outdated or mismatched to the text's domain, rare word thresholds become meaningless. A word that's "rare" in Wikipedia may be "common" in medical literature.
* No Semantic Understanding: Stylometric heuristics measure form, not meaning. They cannot detect if the ideas are original or reused. A human could paste another human's text, and stylometry would have no signal.
* Noise in Short texts: Small paragraphs (< 200 words) produce unreliable entropy and variance statistics. The signal becomes too noisy to be meaningful.
* Humanization: If AI text is run through a post-processing step that adds rare words, varies sentence length artificially, or injects deliberate grammar errors, stylometry becomes useless.

### Perplexity Calculation
**Property Measured:** The predictability of a piece of text, calculated as the exponential of the average negative log-likelihood of the text across all tokens. Lower perplexity means the text more predictable and AI-like, higher perplexity means more surprising, complex, and human-like.

**Output format:** Raw perplexity value normalized to 0.0 to 1.0 scale using min-max normalization. 0.0 indicates "very high perplexity (human-written)" and 1.0 indicates "very low perplexity (AI-generated)."

**Why It Differs Between Human and AI:**
AI text generated by a model will have low perplexity because the reference model learned similar patterns. The text aligns with the reference model's learned distribution. On the other hand, human writing usually contains novel phrasings, unexpected word choices, and reasoning jumps that a general reference model finds perplexing. This produces higher perplexity.

**Blind Spots:**
* Model-Specific Measurement: Perplexity is relative to the specific reference model. The same text can have low perplexity under GPT-2 and high perplexity under a domain-specific medical model. There is no absolute perplexity threshold.
* Human-Like AI: If AI text is generated by a model trained on diverse, high-quality human text, it will have perplexity indistinguishable from actual human writing. Perplexity cannot differentiate between "human-like AI" and "human writing."
* Incoherent Writing: A human writing with low coherence may produce high-perplexity text that looks AI-generated by this metric.
* Domain Mismatch: If the reference model's training data doesn't cover the text's domain, both human and AI text will appear high-perplexity. The signal becomes unreliable.
* No Intent Detection: Perplexity measures predictability, not authenticity or intent. A human could memorize someone else's text and recite it verbatim, producing low perplexity while still being human-written.
* Language Trend: As language evolves and new vocabulary invented, a static reference model becomes outdated. Texts using contemporary slang or new concepts will inflate perplexity.
* Threshold Ambiguity: The perplexity threshold between human-like and AI-like texts This requires empirical calibration. Plus, the threshold may not generalize across domains, languages, or the status quo.

## Uncertainty Representation
**Aggregation Formula:**  
`final_confidence = (signal1 * 0.4) + (signal2 * 0.25) + (signal3 * 0.35)`  
This function aggregates three signal scores with different weights. LLM judgment is most reliable (40%), perplexity is the primary quantitative signal (35%) as it directly measures text predictability using a pretrained language model, and stylometry is calibrated lower (25%) because heuristic-based metrics are sensitive to formal writing styles, genres, and domain-specific conventions.

**Threshold Mapping:**
| Confidence Range | Classification |
| :--- | :--- |
| 0.00 - 0.15 | Your text is Human written |
| 0.15 - 0.30 | Most of Your text is Human Written |
| 0.30 - 0.42 | Your text is Most Likely Human written, may include parts generated by AI |
| 0.42 - 0.50 | Your text is Likely Human written, may include parts generated by AI |
| 0.50 - 0.70 | Your text contains mixed signals, with some parts generated by AI |
| 0.70 - 0.80 | Your text is Likely AI-generated |
| 0.80 - 0.90 | Your text is Most Likely AI-generated |
| 0.90 - 0.97 | Most of Your text is AI-Generated |
| 0.97 - 1.00 | Your text is AI-Generated |

## Transparency Label Design
### Template
```
ATTRIBUTION ANALYSIS

<Transparency Label>
Confidence: <Confidence Score (0-100)>%

<Typed description of score reasoning>

*If you believe our analysis is wrong, you can submit an appeal with details about your writing process and any AI tools you used.*
```
### Label 1: 0.00 - 0.15
**Transparency Label:** Your text is Human written

**Score Reasoning:**  
Our analysis found natural variation in word choice, sentence structure, and phrasing patterns typical of human writing. The 
text shows unexpected conceptual jumps and stylistic choices 
consistent with authentic human expression.

### Label 2: 0.15 - 0.30
**Transparency Label:** Most of Your text is Human Written

**Score Reasoning:**  
Our analysis detected predominantly human writing patterns. The text shows natural variation in word choice and sentence structure. There may be small sections that exhibit AI-like characteristics, 
but the overall content appears human-written.

### Label 3: 0.30 - 0.42 
**Transparency Label:** Your text is Most Likely Human written, may include parts generated by AI

**Score Reasoning:**  
Our analysis suggests this is primarily human-authored work. However, we detected some sections with patterns more typical of 
AI-generated text. This could mean:
- You used AI tools to help with specific sections
- Some paragraphs were rewritten multiple times
- The text includes quoted or referenced material

### Label 4: 0.42 - 0.50
**Transparency Label:** Your text is Likely Human written, may include parts generated by AI

**Score Reasoning:**  
Our analysis produced mixed signals. Some patterns suggest human 
authorship, while others align with AI-generated text. This is 
common when:
- You revised and rewrote sections multiple times
- The text spans different topics or writing styles
- You used AI tools for research or brainstorming

### Label 5: 0.50 - 0.70
**Transparency Label:** Your text contains mixed signals, with some parts generated by AI

**Score Reasoning:**  
Our analysis produced conflicting signals:
- Some patterns suggest human writing
- Other patterns align with AI-generated text
- The overall style makes classification difficult

This could indicate:
- A mix of human and AI-generated content
- Formal or technical writing that resembles AI patterns
- Content in a style or genre we classify less reliably

### Label 6: 0.70 - 0.80
**Transparency Label:** Your text is Likely AI-generated

**Score Reasoning:**  
We detected patterns consistent with AI-generated text, including:
- Formal structure and consistent phrasing typical of language models
- Low variation in sentence length and word choice
- Technical terminology arranged in predictable sequences
- Statistical patterns matching AI baseline

### Label 7: 0.80 - 0.90
**Transparency Label:** Your text is Most Likely AI-generated

**Score Reasoning:**  
Our analysis detected strong patterns across multiple detection 
methods that are characteristic of AI-generated text:
- Consistent formal structure throughout
- Limited variation in sentence length and phrasing
- Predictable word sequences and terminology placement
- Uniformity in writing style and tone

### Label 8: 0.90 - 0.97
**Transparency Label:** Most of Your text is AI-Generated

**Score Reasoning:**  
Our analysis detected strong and consistent patterns indicating 
AI generation across nearly all of the content. We found:
- Pervasive formal structure and consistent phrasing
- Minimal variation in writing style
- Predictable vocabulary and sentence patterns throughout
- Multiple indicators aligned on AI-generated classification

### Label 9: 0.97 - 1.00
**Transparency Label:** Your text is AI-Generated

**Score Reasoning:**  
Our analysis detected overwhelming evidence that this content was 
generated by an AI. All of our detection methods consistently 
identified AI-generation patterns:
- Pervasive consistent structure typical of language models
- Uniformity in word choice and phrasing throughout
- Predictable sequences matching AI baseline patterns
- No indicators of human-written variation or originality

## Appeal System
### Who Can Appeal
* Eligibility: The content's creator (verified via email verification)  
* Timing: Appeals accepted within 30 days of original classification  
* Frequency: One appeal per content item; subsequent appeals reviewed only if new evidence is provided

### Appeal Submission Form 
```
APPEAL REQUEST FORM

Original Classification: [filled by system, cannot be modified]
Original Confidence Score: [filled by system, cannot be modified]
Content ID: [filled by system, cannot be modified]
Email (Required): [filled by user]

Section 1: Your Reasoning (Required)
Explain why you believe our classification is incorrect.
[Text area, 50-500 words]

Section 2: Writing Context (Required)
- When did you write this content? [date]
- How long did the writing process take? [dropdown] hours
- What was your writing process? [dropdown: original composition, revised from drafts, research-based, response to events, others]
- What is your native language? [dropdown]

Section 3: AI Tool Disclosure (Required)
Have you used any AI tools (ChatGPT, Gemini, Claude, etc.) while 
writing this content?
[Radio buttons:
- No.
- Yes, I used the following tools: 
  [Text area, 50-500 words]
]

Section 4: Supporting Evidence (Optional)
Upload files that demonstrate your writing process:
- Draft versions (.txt, .docx, .pdf)
- Notes or outlines (.txt, .docx)
- Chat logs showing research (if applicable)
- Timeline evidence (emails, timestamps)
[Max 5 files, 10MB total]

Section 5: Additional Context (Optional)
Any other information that would help a reviewer understand 
this content's origin?
[Text area, 0-500 words]

[Submit Button] [Cancel]
```

### System Actions
**Immediate (within seconds):**
* Create a Content ID (format: `CTN-YYYY-MM-DD-XXXX`) upon content submission.
* Automatically fill Original Classification, Original Confidence Score, and Content ID when the form is opened

**After completing the form:**
* Validate appeal form completeness (all required fields are filled)
* If incomplete, prevent creator from submitting the form and highlight all incomplete required fields 
* If complete, generate unique appeal_id (format: `APP-YYYY-MM-DD-XXXX`) and show it to the creator on the screen

**After submission:**
* Update content status in audit database to `under review`
* Create appeal record with timestamp
* Log all appeal metadata to Audit Logger
* Send a copy of Appeal Submission Form completed by creator to their email, along with the original content in dispute.


### Audit Log Capture

```json
{
  "appeal_id": "APP-YYYY-MM-DD-XXXX",
  "content_id": "CTN-YYYY-MM-DD-XXXX",
  "creator_email": "creator@example.com",
  "created_at": "YYYY-MM-DDTHH:mm:ssZ",
  "content": "<original submitted text>",
  
  "classification": {
    "result": "<transparency label>",
    "confidence": <confidence score>,
    "signals": {
      "llm_groq": {"score": <signal 1 score>, "reasoning": "<Original LLM reasoning>"},
      "stylometry": {"score": <signal 2 score>, "reasoning": "Entropy score: <score value>, Lexical diversity: <score value>, ..."},
      "perplexity": {"score": <signal 3 score>, "reasoning": "Normalized perplexity <score value> (raw: <raw value>)"}
    }
  },
  
  "appeal_details": {
    "reasoning": "<section 1 text>",
    "writing_process": "<original composition|revised from drafts|research-based|response to events|others>",
    "process_duration_hours": <number>,
    "native_language": "<language>",
    "ai_assisted": <true|false>,
    "ai_tools_detail": "<section 3 text>",
    "supporting_files_count": <number>,
    "supporting_file_names": ["<filename 1>", "<filename 2>", "<filename 3>", ],
    "additional_context": "<Section 5 text>"
  },
  
  "status": "<under review|resolved|reopened>",
  "assigned_reviewer": "<name|email>",
  "assigned_at": "YYYY-MM-DDTHH:mm:ssZ",
  "review_deadline": "YYYY-MM-DDT23:59:59Z"
}
```

### Human Reviewer View

**When a moderator opens the appeals dashboard**

```
APPEALS REVIEW QUEUE

Total pending: <total pending appeals> 
Your queue: <total assigned appeals>

[CASE 1] AAPP-YYYY-MM-DD-XXXX (Created X days ago)
Status: Assigned to you
Original Decision: <transparency label>
Confidence Score: 0.88
Preview: "<original content preview>..."
Signals: LLM (0.92), Stylometry (0.85), Perplexity (0.87) - ALL HIGH
[Open] [Assign to another reviewer]

---

[CASE 2] APP-YYYY-MM-DD-XXXX (Created X hours ago)
Status: Unassigned
Original Decision: <transparency label>
Confidence Score: 0.69 - UNCERTAIN RANGE
Preview: "<original content preview>..."
Signals: LLM (0.68), Stylometry (0.62), Perplexity (0.79) - DISAGREEMENT
[Open] [Assign to me]

---
```

**When reviewer opens a case**:

```
CASE DETAIL VIEW: APP-YYYY-MM-DD-XXXX

ORIGINAL CLASSIFICATION
Result: <transparency label>
Confidence Score: 0.88
Reason: Signals indicate high likelihood of AI assistance

SIGNAL BREAKDOWN
Signal 1 (LLM Groq): 0.92
  Reasoning: <original LLM reasoning>

Signal 2 (Stylometry): 0.85
  Entropy: 4.2 bits (lower end, uniform vocabulary clustering)
  Lexical Diversity: 0.62 (moderate, technical terms repeat)
  Sentence Length Variance: 2.1 std dev (low, consistent structure)
  Rare Word Ratio: 0.08 (8% rare words)
  Function Word Ratio: 0.31 (academic precision markers)
  N-gram Deviation: Low (standard academic phrasing)

Signal 3 (Perplexity): 0.87
  Raw Perplexity: 68.3
  Baseline Human Mean: 95.0
  Baseline AI Mean: 72.0
  Interpretation: Text aligns with AI baseline sequences

---

CREATOR'S APPEAL
Submitted: YYYY-MM-DDTHH:mm:ssZ

Reasoning:
<creator reasoning text>

<Additional context text>

AI tool disclosure:
<None|Disclosure text>

Creator Profile:
- Native Language: <language>
- Writing Process: <original composition|revised from drafts|research-based|response to events>
- Process Duration: <number> hours

Supporting Evidence:
- filename 1 (<size>)
- filename 2 (<size>)
- filename 3 (<size>)
[Download All]

---

DECISION FORM

After reviewing the original decision and appeal:

Decision: [Radio Buttons: Approve Appeal | Deny Appeal | Inconclusive]

Reason:
[Text area]

Recommended Changes to System:
[Text area]

[Submit Decision]
```

**System actions:**  
If Reviewer selects "Approve Appeal" or "Deny Appeal":
- Audit log updated with reviewer decision, reasoning, and `label_decision`
- Case `status` changes to `resolved`
- Creator receives decision notification via email
- Add `decision_id` (format: `DEC-YYYY-MM-DD-XXXX`) to the logging data of the content

If Reviewer selects "Inconclusive":
- Reviewer requests additional information from creator
- System sends automated message to creator with specific questions via submitted email
- `review_deadline` is extended 14 more days

## Edge Cases
### Edge Case 1 
**Scenario:** The submitted text is a formally structured machine learning paper excerpt, written by a non-native speaker. The writing is grammatically perfect, uses precise technical vocabulary, has low sentence length variance (consistent paragraph structure), and low rare word frequency (because technical terms are repeated).  

**Why the system will fail:** ESL speakers learning academic English often adopt formal, structured styles as a deliberate strategy for clarity
academic writing in any language emphasizes consistency and precision
The system conflates "formal and consistent" with "AI-generated"
Non-native speakers are penalized by a system trained on diverse native-speaker data  

**What wil happen:** False positive with high confidence. The appeal mechanism is critical here. The creator provides evidence: "This is my advisor-reviewed draft," "My first language is Mandarin," "This is required by department style guide." A human reviewer can then recognize the legitimate explanation and override the algorithmic decision.  

### Edge Case 2

**Scenario:** The submitted text is a poem using deliberate repetition for effect. The poem uses simple vocabulary and short sentences. Lines like "I walk, I walk, I walk / The path, the path, the path" create a low perplexity score, while the stylometry signal classifies it as "AI-generated." However, the LLM signal correctly identifies the poem as human-written because its internal representations recognize poetic intent. As a result, the combined confidence yeilds an uncertain score.

**Why the system will fail:** Poetry deliberately defies stylometric norms for effect with repetition, low vocabulary diversity, and rhythm. On the other hand, the system is calibrated on prose, not verse. Perplexity signal will treat "simple vocabulary" as "AI-generated" without distinguishing intentional poetic simplicity

**What will happen:** Uncertain label will occur. The creator appeals, explaining: "This is intentional poetic repetition. My style uses minimalist vocabulary for emotional impact." Human review reveals the poem uses established poetic techniques (anaphora, isocolon). The appeal is approved.

## AI Tool Plan
### M3: Submission Endpoint + First Signal 
**AI tool:** Claude

**What I'll give it as input:**
- Detection Signals > LLM Judgment (full section)
- Text Submission Workflow (diagram and description)
- Uncertainty Representation > Threshold Mapping (table)

**What I expect it to produce:**
- Flask application skeleton with `/submit` POST endpoint accepting `{text: string}`
- Rate limiter middleware (10 requests per minute per IP)
- Content normalizer function (whitespace, line breaks, HTML entities)
- LLM judgment signal function returning `{score: 0.0-1.0, reasoning: string}`
- Error handlers for rate limit exceeded and validation failures

**How I'll verify:**
- Call `/submit` with 3 texts: (1) human-written, (2) AI-generated, (3) mixed
- Confirm score is within 0.0-1.0 range and reasoning is coherent
- Send 11 rapid requests and verify the 11th is rejected
- Post malformed requests (missing text, empty string) and confirm HTTP 400 response
 
### M4: Other Signals + Confidence Scoring
**AI tool:** Claude

**What I'll give it as input:**
- Detection Signals > Stylometric Heuristics (full section)
- Detection Signals > Perplexity Calculation (full section)
- Uncertainty Representation > Aggregation Formula (weights: 0.4, 0.35, 0.25)
- Uncertainty Representation > Threshold Mapping (full table)

**What I expect it to produce:**
- Stylometric heuristics function returning `{score: 0.0-1.0, subscores: {entropy, lexical_diversity, sentence_variance, rare_word_ratio, function_word_ratio, ngram_deviation}, reasoning: string}`
- Perplexity calculation function returning `{score: 0.0-1.0, raw_perplexity: float, reasoning: string}`
- Confidence scoring function that aggregates three signals using weighted formula
- Updated `/submit` endpoint that calls all three signals and returns `{confidence: float, signals: {llm, stylometry, perplexity}}`

**How I'll verify:**
- Test 5 texts: expect scores <0.20 (human), 0.20-0.30 (mostly human), 0.40-0.60 (mixed), 0.70-0.80 (mostly AI), >0.90 (AI)
- Verify all three signal scores are 0.0-1.0
- Confirm final score equals (signal1*0.4 + signal2*0.35 + signal3*0.25)
- Check AI and human texts differ by at least 0.3
- Validate subscores vary: high-variance text has lower entropy, repetitive text has lower diversity

### M5: Production Layer (Labels + Appeals)
**AI tool:** Claude

**What I'll give it as input:**
- Transparency Label Design > Template and all 9 label variants (Labels 1-9)
- Appeal Workflow (diagram and description)
- Appeal System > Who Can Appeal, Appeal Submission Form, System Actions
- Appeal System > Audit Log Capture (JSON schema)
- Appeal System > Human Reviewer View (queue and case detail views)

**What I expect it to produce:**
- Label generator function mapping confidence score to label text and reasoning
- `/appeal` POST endpoint accepting email, reasoning, writing context, AI tool disclosure, file metadata
- Appeal form validator checking all required fields
- ID generators: Content ID (`CTN-YYYY-MM-DD-XXXX`), Appeal ID (`APP-YYYY-MM-DD-XXXX`)
- Appeal logger writing to database with full JSON audit schema
- Status updater setting content to `under review` after appeal
- Reviewer dashboard query returning pending appeals with signal breakdown
- Decision handler processing reviewer decision (Approve/Deny/Inconclusive) and updating audit log

**How I'll verify:**
- Call label generator at boundaries: 0.12 returns "Human written", 0.88 returns "Most Likely AI-generated", all 9 ranges produce correct labels
- Submit complete appeal form and verify response contains valid appeal_id
- Submit incomplete forms and verify error highlighting on missing fields
- Check appeal submission creates audit log entry with correct schema and ISO 8601 timestamp
- Verify content status changes from initial classification to `under review`
- Confirm reviewer dashboard displays pending appeals with signal breakdown
- Test all threshold boundaries (0.15, 0.30, 0.42, 0.50, 0.70, 0.80, 0.90, 0.97) and verify label changes at each