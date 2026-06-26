# Provenance Guard: Planning
## Architecture
### Text Submission Workflow
```
           CREATOR SUBMITS TEXT
                    │
                    ▼
           ┌──────────────────┐
           │   API Endpoint   │
           └──────────────────┘
                    │
                    ▼
           ┌──────────────────┐
           │   Rate Limiter   │
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
      │   Signal 1:  │   │   Signal 2:  │   │   Signal 3:  │
      │      LLM     │   │  Stylometric │   │  Perplexity  │
      │    Judgment  │   |  Heuristics  │   │  Calculation │
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
        │ return to client                      └──────────────────┘
        ▼
┌──────────────────┐
│READER SEES LABEL │
└──────────────────┘
```
---

### Appeals Workflow
```

CREATOR CONTESTS CLASSIFICATION
            │
            ▼
┌──────────────────────────┐
│    Appeal Handler        │
│ - Capture reasoning      │
│ - Validate appeal        │
└──────────────────────────┘
            │
            ▼
┌──────────────────────────┐
│      Audit Logger        │
│ - Creator appeal         │
│ - Original decision ID   │
└──────────────────────────┘
            │
            ▼
┌──────────────────────────┐
│ Content Status Update    │
│ Set to "Under Review"    │
└──────────────────────────┘
            │
            ▼
QUEUED FOR HUMAN REVIEW
```
