from flask import Flask, render_template, request, Response
import requests
import html

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma2:2b"


def generate_content(original_content, platform, tone):
    prompt = f"""
You are an expert social media content writer.

Transform the original content into a post suitable for {platform}.

Writing tone: {tone}

Requirements:
- Preserve the original meaning and factual accuracy.
- Adapt the length and style to the selected platform.
- Make the content engaging and easy to understand.
- Include relevant hashtags when appropriate.
- Return only the finished post.
- Do not invent facts.

Original content:
{original_content}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )

    response.raise_for_status()

    result = response.json().get("response", "").strip()

    if not result:
        raise ValueError("The AI returned empty content.")

    return result


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    content = request.form.get("content", "").strip()
    platforms = request.form.getlist("platforms")
    tone = request.form.get("tone", "Professional")

    if not content:
        return "Please enter some content.", 400

    if not platforms:
        return "Please select at least one platform.", 400

    results = {}

    try:
        for platform in platforms:
            results[platform] = generate_content(
                content,
                platform,
                tone
            )

    except requests.RequestException as error:
        app.logger.exception("Could not connect to Ollama.")
        return (
            "Could not connect to the AI model. "
            "Please check that Ollama is running and try again.",
            502
        )

    except (ValueError, KeyError) as error:
        app.logger.exception("AI content generation failed.")
        return "The AI could not generate valid content. Please try again.", 500

    except Exception:
        app.logger.exception("Unexpected content generation error.")
        return "An unexpected error occurred. Please check the terminal.", 500

    return render_template(
        "result.html",
        original_content=content,
        tone=tone,
        results=results
    )

@app.route("/download", methods=["POST"])
def download():
    content = request.form.get("original_content", "")
    tone = request.form.get("tone", "Professional")
    platforms = request.form.getlist("platforms")
    results = {}

    for platform in platforms:
        results[platform] = request.form.get(
            f"content_{platform}", ""
        )

    output = [
        "AI MULTI-PLATFORM CONTENT REPURPOSING WORKFLOW",
        "=" * 50,
        "",
        "ORIGINAL CONTENT:",
        content,
        "",
        f"WRITING TONE: {tone}",
        ""
    ]

    for platform, text in results.items():
        output.extend([
            "=" * 50,
            platform.upper(),
            "=" * 50,
            text,
            ""
        ])

    file_content = "\n".join(output)

    return Response(
        file_content,
        mimetype="text/plain",
        headers={
            "Content-Disposition":
                "attachment; filename=repurposed_content.txt"
        }
    )
if __name__ == "__main__":
    app.run(debug=True)