from fastapi import FastAPI, File, UploadFile, HTTPException
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import PydanticOutputParser
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from model import *
from pydantic import EmailStr
from textToPdf import generate_review_pdf
import os
import uuid
import tempfile
from dotenv import load_dotenv
import requests
import json
import boto3
import sys
from fastapi import Form

load_dotenv()

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# S3 Setup
BUCKET_NAME = os.getenv('BUCKET_NAME')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID_F')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY_F')

REGION_NAME = 'eu-west-2'

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME
)

# Webhook URL Client
WEBHOOK_URL = "https://hook.eu2.make.com/71x1fje5qpwvtvhs9yghru88nms0jysd"

# Test Webhook URL
# WEBHOOK_URL = "https://hook.eu2.make.com/ptdy9pjfeduf85ayhozdxh6gcqtpcwd8"

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
parser = PydanticOutputParser(pydantic_object=CustomerReviewAnalysis)
format_instructions = parser.get_format_instructions()

with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT_TEXT = f.read()

prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("{system_prompt}"),
    HumanMessagePromptTemplate.from_template("{input}")
])


from langchain_community.document_loaders import PyPDFLoader

def extract_pdf_text(file_path: str) -> str:
    loader = PyPDFLoader(file_path)
    pages = loader.load()

    full_text = ""
    for i, page in enumerate(pages):
        full_text += f"--- Page {i+1} ---\n"
        full_text += page.page_content + "\n\n"

    return full_text

def send_email_via_webhook(url: str, email: str, webhook_url: str):
    subject = "Your Requested Link"
    body = f"""
        <html>
        <head>
        <style>
            .container {{
                font-family: Arial, sans-serif;
                padding: 20px;
                max-width: 600px;
                margin: auto;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                background-color: #f9f9f9;
            }}
            .header {{
                text-align: center;
                color: #2c3e50;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                margin: 20px 0;
                font-size: 16px;
                color: white;
                background-color: #4CAF50;
                text-decoration: none;
                border-radius: 6px;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 12px;
                color: #7f8c8d;
                text-align: center;
            }}
        </style>
        </head>
        <body>
        <div class="container">
            <h2 class="header">Your Report is Ready!</h2>
            <p>Hello,</p>
            <p>Thank you for using <strong>CRO Genie</strong>.</p>
            <p>Your personalized report is now available. Please click the button below to download it:</p>
            <p style="text-align: center;">
                <a href="{url}" class="button" target="_blank">Report Download</a>
            </p>
            <p>If you have any questions or need further assistance, feel free to reach out to our support team.</p>
            <div class="footer">
            &copy; {2025} CRO Genie. All rights reserved.
            </div>
        </div>
        </body>
        </html>
        """

    payload = {
        "to_email": email,
        "subject": subject,
        "body": body,
    }

    try:
        requests.post(webhook_url, json=payload)
        return "Email content successfully sent via webhook."
    except requests.exceptions.RequestException as e:
        print(f"Failed to send email: {e}")

def upload_to_s3(file_path, key):
    try:
        s3.upload_file(
            Filename=file_path,
            Bucket=BUCKET_NAME,
            Key=key,
            ExtraArgs={'ContentType': 'application/pdf'}
        )
    except Exception as e:
        printError(e)
        raise HTTPException(status_code=500, detail="Upload to S3 failed")

def generate_presigned_url(key, expiration=300): # 5 minutes = 300 seconds
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': key},
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        printError(e)
        raise HTTPException(status_code=500, detail="Failed to generate pre-signed URL")

def printError(e):
    error_type = type(e).__name__
    line_number = sys.exc_info()[-1].tb_lineno
    error_name = e.args[0] if e.args else "No additional information available"
    print(f"Error Type: {error_type}\nError Name: {error_name}\nLine: {line_number}")

def extract_text(file_path: str, file_type: str) -> List[Document]:
    if file_type == "pdf":
        loader = PyPDFLoader(file_path)
    elif file_type == "txt":
        loader = TextLoader(file_path)
    elif file_type == "csv":
        loader = CSVLoader(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    documents = loader.load()

    if not documents or all(not doc.page_content.strip() for doc in documents):
        raise HTTPException(status_code=400, detail="Your document is empty. Please upload a valid file.")

    return documents

def clean_keys(data):
    if isinstance(data, dict):
        return {k.lstrip("#").strip(): clean_keys(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_keys(item) for item in data]
    else:
        return data


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    email: EmailStr = Form(...),
    url: str = Form(...)  
):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "txt", "csv"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        documents = extract_text(tmp_path, ext)
        full_text = "\n".join([doc.page_content for doc in documents])
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        printError(e)
        raise HTTPException(status_code=500, detail="Text extraction failed")
    finally:
        os.remove(tmp_path)

    try:
        client_format = extract_pdf_text("./CROEcho Template - Completed Example.pdf")
        final_prompt = prompt.format_messages(
            system_prompt=f"{SYSTEM_PROMPT_TEXT}\n\n{format_instructions} \n\n You are an expert in conversion, I want to generate the report content which i provide you \n\n {client_format}",
            input=full_text
        )

        response = llm.invoke(final_prompt)
        content = response.content.strip()
        # print(content)
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(content)
        cleaned = clean_keys(parsed_json)
        print(cleaned)
    except Exception as e:
        printError(e)
        raise HTTPException(status_code=500, detail="LLM failed")

    file_id = str(uuid.uuid4())[:4]
    output_filename = f"report_{file_id}.pdf"
    output_key = f"reports/{output_filename}"
    local_pdf_path = os.path.join("pdf", output_filename)
    os.makedirs("pdf", exist_ok=True)

    try:
        generate_review_pdf(cleaned, local_pdf_path, url=url)
        upload_to_s3(local_pdf_path, output_key)
        os.remove(local_pdf_path)
        signed_url = generate_presigned_url(output_key, expiration=3600)
        email_response = send_email_via_webhook(signed_url, email, WEBHOOK_URL)
    except Exception as e:
        printError(e)
        raise HTTPException(status_code=500, detail="PDF upload or presigned URL generation failed")

    return {
        "message": "Upload and PDF generation successful",
        "uuid": file_id,
        "pdf_download_url": signed_url,
        "email_response": email_response,
    }

