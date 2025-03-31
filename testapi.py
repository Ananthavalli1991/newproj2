from fastapi import FastAPI, File, Form, UploadFile
import openai
import zipfile
import csv

app = FastAPI()

import logging

logging.basicConfig(level=logging.INFO)

@app.post("/testapi/")
async def answer_question(question: str = Form(...), file: UploadFile = None):
    try:
        logging.info(f"Received question: {question}")
        if file:
            logging.info("Processing file...")
            with zipfile.ZipFile(file.file, "r") as zip_ref:
                zip_ref.extractall("/temp")
                logging.info("File extracted.")
                csv_file_path = "/temp/extract.csv"
                with open(csv_file_path, newline="") as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if "answer" in row:
                            return {"answer": row["answer"]}
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Answer the following question: {question}",
            max_tokens=100
        )
        return {"answer": response.choices[0].text.strip()}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return {"answer": "Error: Unable to process the request."}