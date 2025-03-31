import openai
import os
import zipfile
import pandas as pd
import PyPDF2
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load API Key securely
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")  # Set your OpenAI API Key in a .env file

app = FastAPI()

async def extract_text_from_file(file: UploadFile) -> str:
    """Extracts text from various file types (TXT, CSV, PDF, ZIP)."""
    text = ""

    try:
        if file.filename.endswith(".txt"):
            content = await file.read()
            text = content.decode("utf-8")

        elif file.filename.endswith(".csv"):
            content = await file.read()
            df = pd.read_csv(pd.compat.StringIO(content.decode("utf-8")))
            text = df.to_string(index=False)  # Convert CSV content to string

        elif file.filename.endswith(".pdf"):
            content = await file.read()
            with open("temp.pdf", "wb") as temp_pdf:
                temp_pdf.write(content)
            with open("temp.pdf", "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])

        elif file.filename.endswith(".zip"):
            content = await file.read()
            with open("temp.zip", "wb") as temp_zip:
                temp_zip.write(content)
            with zipfile.ZipFile("temp.zip", "r") as zip_ref:
                zip_ref.extractall("temp_extracted")
                for extracted_file in os.listdir("temp_extracted"):
                    extracted_path = os.path.join("temp_extracted", extracted_file)
                    with open(extracted_path, "r", encoding="utf-8") as extracted:
                        text += extracted.read()

    except Exception as e:
        text = f"Error processing file: {str(e)}"

    return text.strip()

@app.post("/api/")
async def answer_assignment(
    question: str = Form(...),
    file: UploadFile = None
):
    try:
        file_content = ""

        if file:
            # Extract content from the uploaded file
            file_content = await extract_text_from_file(file)

        # Prepare prompt for GPT
        messages = [
            {"role": "system", "content": "You are a smart assistant that analyzes file content and answers questions based on provided data."}
        ]

        if file_content:
            messages.append({"role": "user", "content": f"Here is the extracted file content:\n{file_content}"})

        messages.append({"role": "user", "content": question})

        # Query OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use "gpt-4" if desired
            messages=messages,
            max_tokens=500  # Adjust based on response length
        )

        answer = response["choices"][0]["message"]["content"]
        return JSONResponse(content={"answer": answer})

    except Exception as e:
        return JSONResponse(content={"error": f"Internal Server Error: {str(e)}"}, status_code=500)
