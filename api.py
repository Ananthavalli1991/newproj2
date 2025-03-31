import openai
import os
import zipfile
import pandas as pd
import PyPDF2
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load API Key securely
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def extract_text_from_file(file_path):
    """Extracts text from various file types (TXT, CSV, PDF, ZIP)."""
    text = ""

    if file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    elif file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
        text = df.to_string(index=False)  # Convert CSV content to string

    elif file_path.endswith(".pdf"):
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])

    elif file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(app.config["UPLOAD_FOLDER"])
            for extracted_file in os.listdir(app.config["UPLOAD_FOLDER"]):
                extracted_path = os.path.join(app.config["UPLOAD_FOLDER"], extracted_file)
                text += extract_text_from_file(extracted_path)  # Recursively process extracted files

    return text.strip()

@app.route("/api/", methods=["POST"])
def answer_assignment():
    question = request.form.get("question")
    file = request.files.get("file")
    file_content = ""

    # If a file is uploaded, extract its content
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        file_content = extract_text_from_file(file_path)

    # Generate answer using GPT-4o-mini
    messages = [
        {"role": "system", "content": "You are a smart assistant that analyzes file content and answers questions based on provided data."}
    ]
    
    if file_content:
        messages.append({"role": "user", "content": f"Here is the extracted file content:\n{file_content}"})
    
    messages.append({"role": "user", "content": question})

    llm_response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages
    )["choices"][0]["message"]["content"]

    return jsonify({"answer": llm_response})

def handler(request, *args, **kwargs):
    return app(request.environ, start_response)
