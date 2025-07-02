🚗 Tegeta MechaniAI - Project Description & Architecture

# Overview
**MechaniAI** is an AI-powered automotive assistant for Tegeta Motors that helps customers diagnose vehicle problems through natural conversation in Georgian and English.

# Core Flow
graph TD
    A[User Input Georgian/English] --> B[Retrieve Previous Conversation Context from Supabase]
    B --> C[Advanced Context Enhancement]
    C --> C1[Vehicle Information Extraction]
    C --> C2[Symptom Categorization] 
    C --> C3[Diagnostic Code Analysis]
    C --> C4[Maintenance History Analysis]
    C --> C5[Safety Priority Assessment]
    C1 --> D[OpenAI Moderation API Check]
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D
    D --> E{OpenAI API check Automotive Related?}
    E -->|No| F[Polite Redirect Response]
    E -->|Yes| G[Generate Expert Mechanic Response with Context Enhancement]
    G --> H[Predictive Analysis & Component Mapping]
    H --> I[Compress & Store Enhanced Context in Supabase]
    I --> J[Translate Response to Georgian if Needed with OpenAI API]
    J --> K[Return Enhanced Response to User]

# Technical Stack
- **Backend**: FastAPI (Python)
- **Database**: Supabase
- **AI**: OpenAI API (GPT-4o-mini, Moderation)
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
1. **Bilingual Support**: Georgian and English with automatic translation
2. **Context-Aware**: Remembers previous conversations with intelligent compression
3. **Safe**: Advanced content moderation and safety priority assessment
4. **Expert**: Professional automotive advice with predictive analysis
5. **Intelligent**: Vehicle extraction, symptom categorization, and diagnostic intelligence
6. **Predictive**: Maintenance forecasting and component failure analysis
7. **Performance Optimized**: Intelligent caching and batch processing
8. **Enterprise Ready**: Robust error handling and concurrent operation support
9. **API Ready**: FastAPI endpoints with health checks and real-time service validation

# Current Status (Phase 4.1 Complete)
- ✅ **Complete Backend Core**: All chat logic, AI services, and database operations
- ✅ **FastAPI Foundation**: Modern API with health checks, CORS, and error handling
- ✅ **212+ Tests Passing**: Comprehensive real-world validation with zero mocks
- ✅ **Production Ready**: Performance optimized, security hardened, scalable architecture
- 🚧 **Next: Chat Endpoints**: REST API for conversation management (Phase 4.2)

---
