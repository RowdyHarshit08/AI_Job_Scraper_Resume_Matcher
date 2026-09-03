from flask import Flask, request, render_template
from parser import extract_resume

app = Flask(__name__)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("resume")
        if not file:
            return "No file uploaded", 400

        path = "uploaded_" + file.filename
        file.save(path)

        text, info = extract_resume(path)

        if "error" in info:
            return f"Error: {info['error']}", 500

        return f"""
        <h2>Resume Parsed Successfully</h2>
        <p><b>Name:</b> {info.get('name')}</p>
        <p><b>Email:</b> {info.get('email')}</p>
        <p><b>Skills:</b> {", ".join(info.get('skills', []))}</p>
        """

    return render_template("upload.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
