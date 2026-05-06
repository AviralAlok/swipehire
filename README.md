# SwipeHire

A Tinder-style recruiter tool. Paste a job description, get candidates ranked by AI match score, then swipe right to save or left to pass.

![SwipeHire](banner.svg)

## How it works

1. Recruiter pastes a JD
2. Flask backend sends the JD + candidate pool to Claude (Sonnet) via the Anthropic API
3. Claude scores each candidate 0–100 with a one-sentence reasoning
4. Candidates are sorted by score and presented as swipeable cards
5. Saved candidates appear in a shortlist at the end

The candidate pool is prompt-cached on the backend, so only the JD changes between requests — making repeat queries fast and cheap.

## Stack

- **Frontend** — vanilla HTML/CSS/JS, single file (`index.html`)
- **Backend** — Python Flask (`server.py`)
- **AI** — Claude Sonnet via Anthropic API

## Setup

**1. Clone the repo**
```
git clone https://github.com/AviralAlok/swipehire.git
cd swipehire
```

**2. Install dependencies**
```
pip install flask flask-cors anthropic python-dotenv
```

**3. Add your API key**

Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get a key at [platform.claude.com](https://platform.claude.com) → API Keys.

**4. Start the backend**
```
python server.py
```

**5. Open the frontend**

Open `index.html` directly in your browser.

## Candidate pool

12 seed candidates across 4 domains:
- **Engineering** — Frontend, Full Stack, Backend (Python), Backend (Java)
- **Product** — PM, Senior PM (Fintech)
- **Operations** — Head of Ops, Biz Ops Manager, Ops Analyst
- **Quant / Finance** — Quant Analyst, Quant Researcher (HFT), Quant Trader (Goldman/JPM)
