from fastapi import FastAPI, UploadFile, Request
from fastapi.templating import Jinja2Templates
from pdfreader import *
from datetime import datetime
from fastapi.staticfiles import StaticFiles

import fitz
import re

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Create a simple HTML form for file upload
html_form = """
<!DOCTYPE html>
<html>
<head>
    <title>PDF Upload</title>
</head>
<body>
    <h1>Upload a PDF File</h1>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="pdf_file">
        <input type="submit" value="Upload">
    </form>
</body>
</html>
"""


@app.get("/")
async def root(request: Request, message:str = None):
    return templates.TemplateResponse("index.html", {"request": request, "content": None, "message": message})


# Function to decode a value if it's encoded as UTF-16
def decode_utf16(value):
    try:
        decoded_value = value.decode('utf-16')
        return decoded_value
    except Exception as e:
        return value

@app.post("/upload/")
async def upload_pdf(pdf_file: UploadFile, request: Request):
    if pdf_file.content_type == 'application/pdf':

        pdf_document = fitz.open(stream=pdf_file.file.read(), filetype="pdf")
        page_texts = []

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            page_text = page.get_text("text")
            page_texts.append(page_text)

        clean_stream = str(pdf_document.stream).replace('\\r', '').replace('\\n', '')
        pattern = r"\/JS \((.*?\))"
        js = re.findall(pattern, clean_stream, re.DOTALL)
        pdf_document.close()


        #pdf_reader = PDFDocument(pdf_file.file)

        # Initialize variables with default values
        author = "Not available"
        creator = "Not available"
        producer = "Not available"
        create_at = "Not available"
        modify_at = "Not available"

        """# Check and decode metadata values
        if "Author" in pdf_reader.metadata:
            author = decode_utf16(pdf_reader.metadata["Author"])

        if "Producer" in pdf_reader.metadata:
            producer = decode_utf16(pdf_reader.metadata["Producer"])

        if "Creator" in pdf_reader.metadata:
            creator = decode_utf16(pdf_reader.metadata["Creator"])

        if "CreationDate" in pdf_reader.metadata:
            create_at = decode_utf16(pdf_reader.metadata["CreationDate"])
            create_at = create_at.strftime("%d.%m.%Y %H:%M")

        if "ModDate" in pdf_reader.metadata:
            modify_at = decode_utf16(pdf_reader.metadata["ModDate"])
            modify_at = modify_at.strftime("%d.%m.%Y %H:%M")"""

        #create json from these values
        json = {
            "Author": author,
            "Creator": creator,
            "Producer": producer,
            "Created at": create_at,
            "Modified at": modify_at
        }

        javascript_code_list = [
            "console.log('Hello, World!');",
            "function add(a, b) { return a + b; }",
            "var x = 10; var y = 20; var result = x + y;"
            "var x = 10; var y = 20; var result = x + y;"
            "var x = 10; var y = 20; var result = x + y;",
            "var x = 10; var y = 20; var result = x + y;"
            "var x = 10; var y = 20; var result = x + y;"
            "var x = 10; var y = 20; var result = x + y;",
            "var x = 10; var y = 20; var result = x + y;"
            "var x = 10; var y = 20; var result = x + y;"
            "var x = 10; var y = 20; var result = x + y;"
        ]

        modified_javascript_code_list = []
        for code in javascript_code_list:
            code = code.strip()
            code_parts = code.split(';')
            modified_code = '\n' + ';\n'.join(code_parts[:-1]) + ';' + code_parts[-1]
            modified_javascript_code_list.append(modified_code)

        javascript_code_list = modified_javascript_code_list

        for j in js:
            javascript_code_list.append(j)

        # You can now work with 'text_content' as needed
        return templates.TemplateResponse("index.html", {"request": request, "message": "PDF file uploaded and parsed successfully.", "content": json, "javascript_code_list": javascript_code_list})
    else:
        return await root(request, "No file uploaded or incorrect file type uploaded. Please upload supported file type.")

        #return templates.TemplateResponse("index.html", {"request": request, "message": "No file uploaded, please upload a file first."})
