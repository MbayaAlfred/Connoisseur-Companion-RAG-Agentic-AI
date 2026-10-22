# 🍽️ Connoisseur Companion — RAG & Agentic AI Capstone

**IBM RAG and Agentic AI Capstone Project | Completed October 2026 | Final assessment: 60/60 (100%)**

A hands-on California restaurant recommendation capstone exploring structured LLM extraction, multimodal retrieval, specialized AI agents, and a working MCP-enabled chatbot.

![Connoisseur Companion Gradio demo](screenshots/Module-4/M4L3_Design_LLM_MCP_Host.png)

## Project overview

| Module | Focus | Evidence |
|---|---|---|
| 1 — Structured GenAI | Restaurant descriptions to validated JSON; vision recipe captioning; automatic JSON repair | [Screenshots](screenshots/Module-1/) |
| 2 — Multimodal RAG | SentenceTransformer and CLIP embeddings; ChromaDB collections; metadata-filtered retrieval; weighted fusion | [Screenshots](screenshots/Module-2/) |
| 3 — Multi-agent recommendation | Food Style Expert, analysis nodes, preference extraction and chatbot tests | [Screenshots](screenshots/Module-3/) |
| 4 — MCP application | FastMCP server/client; IBM Granite tool-calling ReAct loop; Gradio chatbot | [Code](04-MCP-Application/) · [Screenshots](screenshots/Module-4/) |

## Final chatbot architecture

```text
User → Gradio UI → IBM Granite (LangChain ReAct loop)
                          ↕ dynamic tool discovery / tool calls
                    FastMCP server
                     ├─ get_restaurant_info
                     ├─ recommend_by_vibe
                     └─ get_review
                          ↓
                 Restaurant JSON + culinary map text
```

**Implementation note:** The multimodal ChromaDB work and specialized agent workflows were completed in separate lab modules. The final MCP chatbot uses the three MCP tools above, **not** the Module 2 ChromaDB index. `recommend_by_vibe` performs two-pass case-insensitive keyword matching on structured JSON and raw text, rather than vector semantic search.

## Repository layout

```text
01-Structured-GenAI/       Module 1 overview
02-Multimodal-RAG/         Module 2 overview
03-Multi-Agent-System/     Module 3 overview
04-MCP-Application/       Working Python source and MCP smoke test
data/                     JSON artifacts; original raw culinary map needed
screenshots/              Course evidence grouped by module
requirements.txt          Python dependencies
```

## Run the MCP chatbot

1. Ensure you have permission to use the original course data. Place `California-Culinary-Map.txt` in `data/` (not included in this archive).
2. Create a Python 3.11 virtual environment and install `requirements.txt`.
3. Set `WATSONX_APIKEY` and `WATSONX_AI_PROJECT_ID` in your environment (never commit credentials).
4. Run from the repository root:

```bash
python 04-MCP-Application/tests/test.py
python 04-MCP-Application/src/client.py
python 04-MCP-Application/src/app.py
```

The application has been exercised in the original IBM lab environment. The reorganized repository requires local integration testing with the original raw text file and watsonx credentials.

## Key technologies

Python · IBM watsonx.ai / Granite · LangChain · FastMCP · MCP · Gradio · ChromaDB · SentenceTransformers · CLIP · Pydantic · JSON

## Project outcome

Successfully completed the IBM capstone final assessment with **60/60 (100%)**. Screenshots show lab implementations and the running Gradio chatbot. No real-time restaurant booking or production deployment is claimed.

## Acknowledgment

IBM / Coursera RAG and Agentic AI Capstone Project. Educational project; restaurant data may be synthetic. Verify course content/data sharing rights before making the repository public.
