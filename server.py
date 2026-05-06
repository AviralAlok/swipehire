import json
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)
client = anthropic.Anthropic()

_SYSTEM = (
    "You are an expert technical recruiter. Score each candidate 0-100 against the job description.\n\n"
    "Scoring guide:\n"
    "- 80-100: Exceptional fit — direct role match, all key skills, right experience level\n"
    "- 60-79: Good fit — most requirements met, minor gaps\n"
    "- 35-59: Partial fit — relevant background but meaningful skill gaps or domain mismatch\n"
    "- 0-34: Poor fit — wrong function or domain entirely\n\n"
    "Return ONLY a JSON array, no markdown, no explanation:\n"
    '[{"id": <int>, "score": <0-100>, "reasoning": "<1 concise sentence>"}]'
)

_EXTRACT_SYSTEM = (
    "You are an expert technical recruiter. Given a job description and raw resume texts, "
    "for each resume do two things:\n"
    "1. Extract structured info: name (use \"Candidate <id>\" if unclear), current or target job title, "
    "years of experience as a short string (e.g. \"4 years\"), up to 6 hard skills, up to 6 tools, "
    "up to 4 soft skills, and a 1-2 sentence bio summary.\n"
    "2. Score 0-100 against the job description using this guide:\n"
    "   - 80-100: Exceptional fit — direct role match, all key skills, right level\n"
    "   - 60-79: Good fit — most requirements met, minor gaps\n"
    "   - 35-59: Partial fit — relevant background but meaningful gaps or domain mismatch\n"
    "   - 0-34: Poor fit — wrong function or domain entirely\n\n"
    "Return ONLY a JSON array, no markdown, no explanation:\n"
    '[{"id":<int>,"name":"<str>","title":"<str>","experience":"<str>",'
    '"skills":{"hard":[...],"soft":[...],"tools":[...]},"bio":"<str>","score":<0-100>,"reasoning":"<1 concise sentence>"}]'
)


def _parse_json_response(text):
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


@app.route("/rank", methods=["POST"])
def rank():
    data = request.get_json(force=True)
    jd = (data.get("jd") or "").strip()
    candidates = data.get("candidates") or []

    if not jd or not candidates:
        return jsonify({"error": "Missing jd or candidates"}), 400

    system_text = _SYSTEM + "\n\nCandidate pool:\n" + json.dumps(candidates, ensure_ascii=False)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=[{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": "Job Description:\n" + jd}],
    )

    try:
        scores = _parse_json_response(response.content[0].text)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Failed to parse AI response: {e}", "raw": response.content[0].text}), 502

    scores.sort(key=lambda x: x.get("score", 0), reverse=True)
    return jsonify(scores)


@app.route("/rank-resumes", methods=["POST"])
def rank_resumes():
    data = request.get_json(force=True)
    jd = (data.get("jd") or "").strip()
    resumes = data.get("resumes") or []  # [{id, text}]

    if not jd or not resumes:
        return jsonify({"error": "Missing jd or resumes"}), 400

    resumes = resumes[:25]

    resume_block = "\n\n".join(
        f"--- Resume {r['id']} ---\n{r['text'][:3000]}" for r in resumes
    )
    system_text = _EXTRACT_SYSTEM + "\n\nResume pool:\n" + resume_block

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=[{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": "Job Description:\n" + jd}],
    )

    try:
        candidates = _parse_json_response(response.content[0].text)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Failed to parse AI response: {e}", "raw": response.content[0].text}), 502

    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    return jsonify(candidates)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/banner.svg")
def banner():
    return send_from_directory(".", "banner.svg")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") != "production")
