🚗 Tegeta MechaniAI - Project Description & Architecture

# Overview
**MechaniAI** is an AI-powered automotive assistant for Tegeta Motors that helps customers diagnose vehicle problems through natural conversation in Georgian and English.

# Core Flow
graph TD
    A[User Input Georgian/English] --> B[Retrieve Previous Conversation Context from Supabase]
    B --> C[Enhance Message with Context]
    C --> D[OpenAI Moderation API Check]
    D --> E{OpenAI API check Automotive Related?}
    E -->|No| F[Polite Redirect Response]
    E -->|Yes| G[Generate Expert Mechanic Response with OpenAI API]
    G --> H[Compress & Store Conversation in Supabase using OpenAI API]
    H --> I[Translate the response to Georgian if Needed with OpenAI API]
    I --> J[Return Response to User]

# Technical Stack
- **Backend**: FastAPI (Python)
- **Database**: Supabase
- **AI**: OpenAI API (GPT-4, Moderation)
- **Frontend**: Next.js + TypeScript
- **Testing**: Pytest with real API integration

# Project Structure
tegeta-mechani-ai/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Business logic
│   │   ├── db/           # Database operations
│   │   └── services/     # External services
│   ├── tests/            # Test files
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js app
│   └── package.json
└── .env.example


# Key Features
1. **Bilingual Support**: Georgian and English
2. **Context-Aware**: Remembers previous conversations
3. **Safe**: Content moderation
4. **Expert**: Professional automotive advice
5. **Simple**: Clean, focused implementation

---
