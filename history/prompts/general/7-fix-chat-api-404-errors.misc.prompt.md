---
id: "7"
title: "Fix chat API 404 errors"
stage: "misc"
date: "2026-01-04"
surface: "agent"
model: "claude-opus-4-5-20251101"
feature: "Phase III: AI-Powered Todo Chatbot"
branch: "001-task-management-core"
user: "Claude User"
command: "fix chat API 404 errors - frontend using relative URLs"
labels: ["bugfix","frontend","api","chat"]
links:
  spec: "null"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - frontend/src/components/chat/ChatInterface.tsx
tests: []
---

## Prompt

The user reported 404 errors on /api/conversations:
- GET /api/conversations 404 in 1700ms
- POST /api/conversations 404 in 142ms
- POST /api/conversations 404 in 115ms

The issue is the ChatInterface component uses relative URLs (`/api/conversations`) which hit the Next.js dev server (port 3000) instead of the backend (port 8000).

User asked: "nop, it aint working shows that 404, are u sure u created root for that in @frontend\src\services\api.ts that checks at backend"

## Response snapshot

Fixed the 404 errors by:
1. Added `const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`
2. Added `getAuthHeaders()` helper function to include JWT token
3. Updated all fetch calls to use full backend URL and auth headers:
   - `loadConversations` - line 60-63
   - `createNewConversation` - line 74-80
   - `loadMessages` - line 99-103
   - `handleSubmit` (chat API) - line 133-140

Verified backend APIs are working:
- GET /api/conversations returns 200 with `[]`
- GET /api/chat/health returns `{"status":"healthy","service":"chat-api"}`

Frontend builds successfully with `npm run build`.

## Outcome

- ✅ Impact: Fixed chat API 404 errors by using full backend URL
- 🧪 Tests: None (build verification only)
- 📁 Files: 1 modified (ChatInterface.tsx)
- 🔁 Next prompts: Test end-to-end chat functionality with LLM
- 🧠 Reflection: The frontend was using relative URLs which are resolved against the current page's origin. In development, this means port 3000 (Next.js) instead of port 8000 (backend).

## Evaluation notes (flywheel)

- Failure modes observed: Relative URLs in frontend pointing to backend APIs
- Graders run and results (PASS/FAIL): Build passes, backend APIs respond with 200
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test chat functionality with real user authentication
