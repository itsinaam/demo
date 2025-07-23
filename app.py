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
import threading, time

load_dotenv()


app = FastAPI(
    docs_url="/api/docs",  # Swagger UI
    redoc_url=None,              
    openapi_url="/api/openapi.json" 
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://app.crogenie.com"],
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
# WEBHOOK_URL = "https://hook.eu2.make.com/71x1fje5qpwvtvhs9yghru88nms0jysd"

# Test Webhook URL
WEBHOOK_URL = "https://hook.eu2.make.com/pon41af5x36qo4fe6592o23e2w7yf5cc"

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
parser = PydanticOutputParser(pydantic_object=CustomerReviewAnalysis)
format_instructions = parser.get_format_instructions()

with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT_TEXT = f.read()

prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("{system_prompt}"),
    HumanMessagePromptTemplate.from_template("{input}")
])



def extract_pdf_text(file_path: str) -> str:
    loader = PyPDFLoader(file_path)
    pages = loader.load()

    full_text = ""
    for i, page in enumerate(pages):
        full_text += f"--- Page {i+1} ---\n"
        full_text += page.page_content + "\n\n"

    return full_text

def send_email_before_report(email: str, webhook_url: str):
    subject = "Report Generation Started"
    body = """
       <html>
     <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 30px; color: #333;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);">
        
        <h2 style="color: #1a73e8; border-bottom: 1px solid #e0e0e0; padding-bottom: 10px;">CRO Genie</h2>
        
        <p style="font-size: 16px;">Hello,</p>
        
        <p style="font-size: 16px;">
            Your report has been <strong>successfully queued for generation</strong>. 
            You will receive an email shortly with the download link.
        </p>
         
        <p style="font-size: 16px;">Thank you for your patience,<br>
        <strong>The CRO Genie Team</strong></p>
        
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
        return "Report generation notice sent."
    except requests.exceptions.RequestException as e:
        print(f"Failed to send early notice: {e}")

def send_links_email(links, email, webhook_url):
        subject = "Your Requested Reports"
        body = """
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f5f7fa; padding: 30px;">
            <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            
            <h2 style="color: #1a73e8;">Your Reports Are Ready!</h2>
            
            <p style="font-size: 16px;">Hello,</p>
            <p style="font-size: 16px;">Thank you for using <strong>CRO Genie</strong>.</p>
            <p style="font-size: 16px;">Your personalized report(s) are now available. Please click the buttons below to download:</p>

            <ul style="list-style: none; padding-left: 0;">
        """
        for idx, link in enumerate(links, 1):
            body += f"""
                <li style="margin-bottom: 20px;">
                <div style="font-size: 16px; margin-bottom: 8px;">
                    <strong>File {idx}:</strong> {link["filename"]}
                </div>
                <a href="{link["url"]}" style="background-color: #1a73e8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Download
                </a>
                </li>
            """

        body += """
            </ul>

            <p style="font-size: 16px; margin-top: 30px;">Thank you,<br><strong>The CRO Genie Team</strong></p>
            <p style="font-size: 12px; color: #999;">Note: These links will expire in 14 hours.</p>
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
            return "Summary email sent."
        except requests.exceptions.RequestException as e:
            print(f"Failed to send summary email: {e}")

def send_report_creation_notice(email: str, webhook_url: str):
    subject = "Report Generation Started"
    body = """
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f8; padding: 30px;">
            <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);">
            
            <h2 style="color: #1a73e8; margin-bottom: 20px;">CRO Genie</h2>
            
            <p style="font-size: 16px; color: #333;">Hello,</p>
            
            <p style="font-size: 16px; color: #333;">
                Your report download link has been sent to your email address.
                Please check your inbox to access it.
            </p>
            
            <p style="font-size: 16px; color: #d32f2f;">
                <strong>Note:</strong> The link is valid for 14 hours only.
            </p>
            
            <p style="font-size: 16px; color: #333;">Thank you,<br><strong>The CRO Genie Team</strong></p>
            
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
        return "Report generation notice sent."
    except requests.exceptions.RequestException as e:
        print(f"Failed to send early notice: {e}")

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

def check_pdfs_have_content(pdf_paths):
    for path in pdf_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        try:
            loader = PyPDFLoader(path)
            docs = loader.load()
            has_text = any(doc.page_content.strip() for doc in docs)
            if not has_text:
                # Extract original filename from temp path
                orig_name = os.path.basename(getattr(path, 'orig_filename', path))
                return f"{orig_name} is a empty"
        except Exception as e:
            orig_name = os.path.basename(getattr(path, 'orig_filename', path))
            return f"Error loading {orig_name}: {str(e)}"
    return True


@app.post("/upload")
async def upload_file(
    files: list[UploadFile] = File(...),
    email: EmailStr = Form(...),
    url: str = Form(...)
):
    
    results = []
    links = []
    temp_files = []
    file_exts = []
    file_names = []

    for file in files:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["pdf", "txt", "csv"]:
            results.append({
                "filename": file.filename,
                "error": "Invalid file type"
            })
            continue
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        temp_files.append(tmp_path)
        file_exts.append(ext)
        file_names.append(file.filename)

    # Check all PDFs for content before further processing
    pdf_paths = []
    for path, ext, fname in zip(temp_files, file_exts, file_names):
        if ext == "pdf":
            # Attach original filename to path for error reporting
            class PathWithName(str):
                pass
            p = PathWithName(path)
            p.orig_filename = fname
            pdf_paths.append(p)
    if pdf_paths:
        check_result = check_pdfs_have_content(pdf_paths)
        if check_result is not True:
            # Clean up temp files
            for path in temp_files:
                if os.path.exists(path):
                    os.remove(path)
            return {"error": check_result}
        # All PDFs have content, send before-report email
        send_email_before_report(email, WEBHOOK_URL)

    # Now process each file as before
    for tmp_path, ext, orig_filename in zip(temp_files, file_exts, file_names):
    
        try:
            documents = extract_text(tmp_path, ext)
            full_text = "\n".join([doc.page_content for doc in documents])
        except HTTPException as http_exc:
            results.append({
                "filename": orig_filename,
                "error": str(http_exc.detail)
            })
            os.remove(tmp_path)
            continue
        except Exception as e:
            printError(e)
            results.append({
                "filename": orig_filename,
                "error": "Text extraction failed"
            })
            os.remove(tmp_path)
            continue
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        try:
            client_format = extract_pdf_text("./CROEcho Template - Completed Example.pdf")
            final_prompt = prompt.format_messages(
                system_prompt=f"{SYSTEM_PROMPT_TEXT}\n\n{format_instructions} \n\n You are an expert in conversion, I want to generate the report content which i provide you \n\n {client_format}",
                input=full_text
            )

            response = llm.invoke(final_prompt)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            parsed_json = json.loads(content)
            cleaned = clean_keys(parsed_json)
        except Exception as e:
            printError(e)
            results.append({
                "filename": orig_filename,
                "error": "LLM failed"
            })
            continue

        file_id = str(uuid.uuid4())[:4]
        base_name = os.path.splitext(orig_filename)[0]
        safe_base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        output_filename = f"report_{safe_base_name}_{file_id}.pdf"
        output_key = f"reports/{output_filename}"
        local_pdf_path = os.path.join("pdf", output_filename)
        os.makedirs("pdf", exist_ok=True)

        try:
            generate_review_pdf(cleaned, local_pdf_path, url=url)
            upload_to_s3(local_pdf_path, output_key)
            os.remove(local_pdf_path)
            signed_url = generate_presigned_url(output_key, expiration=3600)
            links.append({
                "filename": orig_filename,
                "url": signed_url
            })
            results.append({
                "filename": orig_filename,
                "uuid": file_id,
                "pdf_download_url": signed_url
            })
        except Exception as e:
            printError(e)
            results.append({
                "filename": orig_filename,
                "error": "PDF upload or presigned URL generation failed"
            })
            continue

    # 2. Send email with links after all files are processed
    send_links_email(links, email, WEBHOOK_URL)

    # 3. Send notice email after 1 minute (once)
    def delayed_notice():
        time.sleep(60)
        send_report_creation_notice(email, WEBHOOK_URL)
    threading.Thread(target=delayed_notice, daemon=True).start()

    return {
        "message": "Upload and PDF generation completed",
        "results": results
    }

