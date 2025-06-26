# 🗄️ MechaniAI Database Schema

## Overview
This document outlines the database schema for MechaniAI, designed to support bilingual automotive conversations with context awareness.

## Tables

### 1. conversations
Stores individual conversation sessions.

```sql
CREATE TABLE conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    language TEXT NOT NULL CHECK (language IN ('en', 'ka')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'closed')),
    title TEXT -- Auto-generated conversation title
);
```

### 2. messages
Stores individual messages within conversations.

```sql
CREATE TABLE messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    language TEXT NOT NULL CHECK (language IN ('en', 'ka')),
    original_content TEXT, -- For translations
    is_automotive BOOLEAN, -- Result of automotive relevance check
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3. conversation_contexts
Stores compressed conversation context for performance optimization.

```sql
CREATE TABLE conversation_contexts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    compressed_context TEXT NOT NULL, -- JSON string of compressed conversation
    message_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

## Indexes

```sql
-- Performance indexes
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_conversation_contexts_conversation_id ON conversation_contexts(conversation_id);
CREATE INDEX idx_conversation_contexts_active ON conversation_contexts(conversation_id, is_active);
```

## Row Level Security (RLS)

```sql
-- Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_contexts ENABLE ROW LEVEL SECURITY;

-- Basic policies (can be enhanced later for multi-tenancy)
CREATE POLICY "Allow all operations" ON conversations FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON messages FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON conversation_contexts FOR ALL USING (true);
```

## Usage Patterns

1. **New Conversation**: Insert into `conversations` table
2. **New Message**: Insert into `messages` table with `conversation_id`
3. **Context Management**: When conversation gets long, compress older messages and store in `conversation_contexts`
4. **Retrieval**: Get recent messages + latest compressed context for conversation continuation

## Data Flow

1. User sends message → Insert into `messages`
2. System generates response → Insert assistant message into `messages` 
3. Every N messages → Compress old context into `conversation_contexts`
4. Context retrieval → Get recent messages + active compressed context 