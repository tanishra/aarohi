<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0D1117,100:2D333B&height=180&section=header&text=Aarohi&fontSize=48&fontColor=ffffff&animation=fadeIn&fontAlignY=38" alt="Aarohi Header Banner" />
  <p><strong>Aarohi: Production-Grade Virtual AI Nurse Assistant</strong></p>
  <p>An interactive technical asset engineered to showcase low-latency voice orchestration, 3D avatar synchronization, and complex clinical agentic workflows.</p>
  <p>
    <a href="https://nextjs.org/" target="_blank" rel="noreferrer">
      <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" alt="Next.js" />
    </a>
    <a href="https://openai.com/" target="_blank" rel="noreferrer">
      <img src="https://img.shields.io/badge/OpenAI_GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI" />
    </a>
    <a href="https://livekit.io/" target="_blank" rel="noreferrer">
      <img src="https://img.shields.io/badge/LiveKit-621EE5?style=for-the-badge&logo=livekit&logoColor=white" alt="LiveKit" />
    </a>
    <a href="https://deepgram.com/" target="_blank" rel="noreferrer">
      <img src="https://img.shields.io/badge/Deepgram-13EF95?style=for-the-badge&logo=deepgram&logoColor=black" alt="Deepgram" />
    </a>
    <a href="https://spatialreal.ai/" target="_blank" rel="noreferrer">
      <img src="https://img.shields.io/badge/SpatialReal-FF4F00?style=for-the-badge&logo=webassembly&logoColor=white" alt="SpatialReal" />
    </a>
    <a href="https://www.python.org/" target="_blank" rel="noreferrer">
      <img src="https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    </a>
  </p>
</div>

## Overview
**Aarohi** is a high-fidelity virtual healthcare assistant designed to automate and humanize the patient intake process. By combining real-time 3D avatar rendering with OpenAI's multimodal intelligence, Aarohi engages patients in natural conversation to collect clinical details, perform basic triage, and securely store data for medical review.

---

## System Architecture

```mermaid
graph TD
    User((Patient)) <-->|WebRTC Voice/Video| Frontend[Next.js Frontend]
    Frontend <-->|POST /token| TokenServer[Flask Token Server]
    TokenServer -->|Dispatch| AgentWorker[LiveKit AI Agent]
    
    subgraph "The Brain"
    AgentWorker <-->|Transcripts| STT[Deepgram STT]
    AgentWorker <-->|Reasoning| LLM[OpenAI GPT-4o]
    AgentWorker <-->|Voice| TTS[Google Neural TTS]
    end
    
    AgentWorker -->|Structured Data| DB[(Local SQL / Supabase)]
    Frontend <-->|Rendering| Avatar[SpatialReal 3D Engine]
```

---

<!-- ## Visual Technology: SpatialReal
Aarohi features a professional nurse persona powered by [SpatialReal](https://spatialreal.ai/). Unlike traditional cloud-based video bots, SpatialReal uses on-device 3D rendering via WebAssembly (WASM) to provide a high-fidelity, empathetic presence with industry-leading performance.

| Feature | SpatialReal (On-Device) | Cloud Video Avatars |
| :--- | :--- | :--- |
| **Latency** | <300ms | 300–2000ms |
| **Cost** | 1/100 compute cost | High cloud usage |
| **Quality** | Natural & controllable | Stiff or uncanny output |
| **Bandwidth** | 10–20KB/s | ≥2 Mbps streaming |
| **Integration** | Simple SDK | Complex backend | -->

# SpatialReal
SpatialReal is the next-generation AI infrastructure for empathetic human-AI interactions. We build **real-time**, **high-fidelity**, and **cost-effective** digital avatar interactions through on-device rendering technology.

<Frame>
  <img src="https://mintcdn.com/spatialwalk-6179c111/wCBKRztgNfKgzyVo/images/flow.png?fit=max&auto=format&n=wCBKRztgNfKgzyVo&q=85&s=f1ff8935c8c99e92b7b99555de514fa1" alt="pipeline" width="3300" height="1586" data-path="images/flow.png" />
</Frame>

<p style={{ fontSize: '0.875rem', opacity: 0.75, marginTop: 8 }}>
  In the pipeline diagram: ASR = Automatic Speech Recognition, LLM = Large Language Model, TTS = Text-to-Speech, S2S = Speech-to-Speech (e.g. Gemini Live).
</p>

## Why SpatialReal?

Traditional digital avatar solutions force painful trade-offs between cost, visual quality, and real-time performance. SpatialReal solves this trilemma:

| Metric            | Traditional Cloud Rendering  | SpatialReal On-Device          |
| ----------------- | ---------------------------- | ------------------------------ |
| **Bandwidth**     | 1-2 MB/s (Video Stream)      | 10-20 KB/s (Driver Data)       |
| **Cost**          | High GPU rental costs        | Ultra-low edge compute         |
| **Latency**       | > 3s                         | \< 1.5s                        |
| **Compatibility** | High-speed network dependent | 99% of Android/iOS/Web devices |

## Use Cases

* **Online Education** - Immersive 1-on-1 tutoring with precise lip-sync for language learning and K12
* **Recruitment & Training** - 7x24h AI interviewers and roleplay training simulations
* **Customer Service** - Brand ambassadors with visual eye contact that builds emotional connection

## Creating an account

### Sign Up

Visit [SpatialReal Studio](https://app.spatialreal.ai/) to create your free account.

### SpatialReal Studio

[SpatialReal Studio](https://app.spatialreal.ai/) is your control center where you can:

* Free access to a large avatar library
* Manage your API keys
* Monitor your usage
* Control your subscription

---

## Quick Setup

### 1. Backend (Python 3.12+)
```bash
cd backend
uv sync
# Ensure your .env contains OPENAI_API_KEY, DEEPGRAM_API_KEY, and LIVEKIT credentials
uv run python main.py dev
uv run python token_server.py dev
```

### 2. Frontend (Next.js)
```bash
cd frontend
pnpm install
# Ensure .env contains NEXT_PUBLIC_SPATIALREAL_APP_ID and AVATAR_ID
pnpm dev
```

---

## What Aarohi Does
- **Structured Intake:** Methodically collects Name, Symptoms, Pain Severity, and Medical History.
- **Autonomous DB Submission:** Automatically saves patient reports to an SQL database once the conversation is complete.
- **State-Driven UI:** Automatically redirects users to a success summary page after data validation.
- **Real-Time Knowledge:** Provides current date/time and location-aware information using internal tools.

---

<div align="center">
  <p><strong>Aarogyam AI – Pioneering the Future of Digital Healthcare</strong></p>
</div>
