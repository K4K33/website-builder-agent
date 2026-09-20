from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "agent": "Website Builder Agent",
        "mode": "local"
    })


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "error": "Message cannot be empty."
        }), 400

    lower = message.lower()

    if lower == "help":
        response = (
            "Available commands:\n\n"
            "show <company> - show a company/project\n"
            "projects - list saved projects\n"
            "resources - show resource usage\n"
            "help - show this help"
        )

    elif lower == "projects":
        try:
            from website_builder_agent.website_builder_agent.utils.state import load_companies

            companies = load_companies()

            if not companies:
                response = "No projects found."
            else:
                lines = ["Projects:"]
                for slug, company in companies.items():
                    name = company.get("name", slug)
                    status = company.get("status", "unknown")
                    lines.append(f"- {name} ({slug}) — {status}")
                response = "\n".join(lines)

        except Exception as exc:
            response = f"Could not load projects: {exc}"

    elif lower.startswith("show "):
        slug = message[5:].strip()

        try:
            import sys
            sys.path.insert(
                0,
                str(
                    Path(__file__).resolve().parent.parent
                    / "website-builder-agent"
                    / "website-builder-agent"
                )
            )

            from utils.state import get_company

            resolved_slug, company = get_company(slug)

            if company is None:
                response = f"Project not found: {slug}"
            else:
                response = (
                    f"Company: {company.get('name', resolved_slug)}\n"
                    f"URL: {company.get('url', '')}\n"
                    f"Status: {company.get('status', 'unknown')}\n"
                    f"Demo: {company.get('demo', {}).get('url', 'not published')}\n"
                    f"Build version: {company.get('build', {}).get('version', 'unknown')}\n"
                    f"QA passed: {company.get('qa', {}).get('overall_pass', False)}"
                )

        except Exception as exc:
            response = f"Could not load project: {exc}"

    elif lower == "resources":
        try:
            import sys
            sys.path.insert(
                0,
                str(
                    Path(__file__).resolve().parent.parent
                    / "website-builder-agent"
                    / "website-builder-agent"
                )
            )

            from utils import resource_manager

            resource_manager.print_report()
            response = (
                "Resource report was generated in the server terminal. "
                "No external API call was made."
            )

        except Exception as exc:
            response = f"Could not read resource usage: {exc}"

    else:
        response = (
            "Command not connected yet. Try:\n\n"
            "show test-company\n"
            "projects\n"
            "resources\n"
            "help"
        )

    return jsonify({
        "message": response,
        "mode": "local"
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8000,
        debug=False
    )
