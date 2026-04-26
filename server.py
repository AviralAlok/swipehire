import json
from flask import Flask, request, jsonify
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
        system=[
            {
                "type": "text",
                "text": system_text,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": "Job Description:\n" + jd}],
    )

    scores = json.loads(response.content[0].text)
    scores.sort(key=lambda x: x["score"], reverse=True)
    return jsonify(scores)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
