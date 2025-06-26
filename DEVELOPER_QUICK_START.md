# 🚀 Developer Quick Start Guide
*Get up and running with MechaniAI in 10 minutes*

## 🎯 **What You're Building**
A production-ready AI automotive assistant for **Tegeta Motors** that provides expert vehicle diagnosis through bilingual (Georgian/English) conversations using **GPT-4o-mini**.

## ⚡ **Super Quick Setup**

### **1. Prerequisites Check**
```bash
python3 --version  # Must be 3.13+
git --version      # Any recent version
```

### **2. Clone & Install (3 minutes)**
```bash
# Clone the repository
git clone https://github.com/Toma-Pirtskhelani/MechanicAI.git
cd MechanicAI

# Setup Python environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### **3. Configure Environment (2 minutes)**
```bash
cd backend
# Create your local environment file (never commit this!)
touch .env.local

# Add your credentials to .env.local:
echo "OPENAI_API_KEY=sk-proj-your-real-openai-key-here" >> .env.local
echo "OPENAI_MODEL=gpt-4o-mini" >> .env.local
echo "SUPABASE_URL=https://hhnrdoyskgcwpmjzxdhw.supabase.co" >> .env.local
echo "SUPABASE_KEY=your-supabase-key-here" >> .env.local
echo "DEBUG=false" >> .env.local
```

### **4. Verify Everything Works (2 minutes)**
```bash
# Run the full test suite
python -m pytest tests/ -v

# You should see: 140 passed
# If you see failures, check your API keys
```

## 🎊 **You're Ready!**
If all tests pass, you have a **production-ready** AI automotive assistant with:
- ✅ **GPT-4o-mini** integration (cost-optimized)
- ✅ **Bilingual support** (Georgian/English)
- ✅ **Content moderation** & safety
- ✅ **Expert automotive knowledge**
- ✅ **Context compression** for scalability

## 🔍 **Understanding the Codebase**

### **Key Files to Know**
```
backend/
├── app/
│   ├── config.py              # 🔧 Configuration management
│   ├── services/
│   │   └── openai_service.py  # 🤖 AI service (5 modules complete)
│   └── db/
│       ├── database_service.py    # 🗄️ Database connection
│       └── repositories/
│           └── conversation_repository.py  # 💬 Data operations
├── tests/                     # 🧪 140 comprehensive tests
└── docs/                      # 📚 Technical documentation
```

### **What's Already Built (140 Tests Passing)**
1. **🔧 OpenAI Service** - Chat, moderation, automotive filtering, expert responses, compression
2. **🗄️ Database Layer** - Supabase integration with bilingual conversation support
3. **🔒 Security** - Content moderation, credential protection, error handling
4. **🌍 Bilingual** - Georgian/English support throughout all components
5. **⚡ Performance** - <10s responses, optimized for cost with GPT-4o-mini

## 🚧 **What You'll Build Next**

### **Phase 2.6 - Translation Service (Current)**
```python
# Implement in: backend/app/services/openai_service.py
async def detect_language(self, text: str) -> str:
    """Detect if text is Georgian or English"""
    
async def translate_text(self, text: str, target_language: str) -> str:
    """Translate between Georgian and English"""
```

### **Phase 3 - Chat Logic Integration**
```python
# Create: backend/app/core/chat_service.py
class ChatService:
    """Orchestrate the complete conversation flow"""
```

### **Phase 4 - API Endpoints**
```python
# Create: backend/app/api/routes/chat.py
@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    """FastAPI endpoint for chat interactions"""
```

## 🧪 **Development Workflow**

### **Test-First Development**
```bash
# 1. Write tests first
# tests/test_translation.py

# 2. Run tests (they should fail initially)
pytest tests/test_translation.py -v

# 3. Implement until tests pass
# app/services/openai_service.py

# 4. Commit when all tests pass
git add .
git commit -m "feat: add translation service"
git push origin main
```

### **Key Principles**
- 🚫 **No Mocks** - All tests use real OpenAI and Supabase APIs
- 🌍 **Bilingual First** - Every feature supports Georgian and English
- ⚡ **Performance Focus** - <10s response times validated
- 🔐 **Security** - Never commit real credentials (use .env.local)

## 🆘 **Common Issues & Solutions**

### **API Key Problems**
```bash
# Error: "Invalid API key"
# Check your .env.local file has correct OpenAI key

# Error: "Supabase connection failed"  
# Verify SUPABASE_URL and SUPABASE_KEY in .env.local
```

### **Test Failures**
```bash
# If < 140 tests pass, usually API credentials issue
# Check backend/.env.local has all required variables

# Run specific test category to debug:
pytest tests/test_config_comprehensive.py -v
pytest tests/test_openai_connection.py -v
```

### **Environment Issues**
```bash
# Make sure you're in the virtual environment:
source venv/bin/activate

# And in the backend directory:
cd backend
```

## 🎯 **Your First Task**
1. **Get 140 tests passing** ✅
2. **Read the codebase** (start with `app/services/openai_service.py`)
3. **Understand the architecture** (check `Project_Description_and_Architecture.md`)
4. **Plan translation service** (see Phase 2.6 in `Development_Strategy_and_Plan.md`)
5. **Write tests first** for translation functionality
6. **Implement** until tests pass

## 📚 **Essential Reading**
- `README.md` - Project overview and features
- `Development_Strategy_and_Plan.md` - Detailed roadmap and status
- `backend/docs/recent_updates_summary.md` - Latest achievements
- `backend/docs/database_schema.md` - Database structure

## 💬 **Need Help?**
- **Architecture questions**: Check `Project_Description_and_Architecture.md`
- **Database questions**: See `backend/docs/database_schema.md`
- **Test examples**: Browse `backend/tests/` directory
- **Configuration**: Review `backend/app/config.py`

---

**You're building something amazing! 🚗💨 Tegeta Motors customers will get expert automotive help in their native language through cutting-edge AI technology.**

**Welcome to the team! 🎉** 