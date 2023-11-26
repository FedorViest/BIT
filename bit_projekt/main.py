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

class PDFObject():
    def __init__(self, obj_num, obj_gen, type, obj_stream, jump=None):
        self.obj_num = obj_num
        self.obj_gen = obj_gen
        self.type = type
        self.obj_stream = obj_stream
        self.jump = jump

    def __str__(self):
        return f"{self.obj_num} {self.obj_gen} {self.type} {self.jump} obj\n{self.obj_stream}\nendobj"


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


def find_metadata(metadata):
    # Initialize variables with default values
    format = "Not available"
    author = "Not available"
    creator = "Not available"
    producer = "Not available"
    create_at = "Not available"
    modify_at = "Not available"

    filtered_metadata = {key: metadata[key] for key in ["format", "author", "creator", "producer", "creationDate", "modDate"]}

    # if value in dict empty, set Not available to it
    for key in filtered_metadata:
        if filtered_metadata[key] == '':
            filtered_metadata[key] = "Not available"

    # Check and decode metadata values
    if "format" in metadata:
        format = decode_utf16(filtered_metadata["format"])

    if "author" in metadata:
        author = decode_utf16(filtered_metadata["author"])

    if "producer" in metadata:
        producer = decode_utf16(filtered_metadata["producer"])

    if "creator" in metadata:
        creator = decode_utf16(filtered_metadata["creator"])

    if "creationDate" in metadata:
        create_at = decode_utf16(filtered_metadata["creationDate"])
        if create_at != "Not available":
            date_str = create_at[2:15]  # Extracts "20231025202517"

            # Convert to datetime object
            date_obj = datetime.strptime(date_str, "%Y%m%d%H%M%S")

            # Format the datetime object as dd.mm.yyyy
            formatted_date = date_obj.strftime("%d.%m.%Y")
            create_at = formatted_date

    if "modDate" in metadata:
        modify_at = decode_utf16(filtered_metadata["modDate"])
        if modify_at != "Not available":
            date_str = modify_at[2:15]  # Extracts "20231025202517"

            # Convert to datetime object
            date_obj = datetime.strptime(date_str, "%Y%m%d%H%M%S")

            # Format the datetime object as dd.mm.yyyy
            formatted_date = date_obj.strftime("%d.%m.%Y")
            modify_at = formatted_date

    # Create json from these values

    return {
        "Version": format,
        "Author": author,
        "Creator": creator,
        "Producer": producer,
        "Created at": create_at,
        "Modified at": modify_at
    }


def count_not_available(json_data):
    count = 0
    for value in json_data.values():
        if value == "Not available":
            count += 1
    return count


def get_score(codes):
    words = ["require", "url", "SOAP", "geturl", "launchurl", "geturldata", "request", "connect", "curl", "submitform",
             "location.replace", "websocket", "importdataobject", "importAnFDF", "importAnXFDF", "importXFAData", "setprops"]
    file_extensions = [".exe", ".bat", ".cmd", ".pdf", ".fdf", ".txt", ".vbs", ".js", ".jar", ".msi", ".ps1", ".ps2", ".ps3", ".ps4", ".ps5", ".ps6", ".ps7"]

    regex_patterns = ["https?://\S+"]

    total_score = []

    danger_score = 0

    for code in codes:
        pattern = re.compile(r'\b(?:' + '|'.join(re.escape(word) for word in words) + r')\b',
                             flags=re.IGNORECASE)
        pattern_regex = re.compile(r'\b(?:' + '|'.join(regex_patterns) + r')\b',
                                   flags=re.IGNORECASE)
        pattern_extension = re.compile(r'\b(?:' + '|'.join(re.escape(word) for word in file_extensions) + r')\b',
                                       flags=re.IGNORECASE)
        matches = set(pattern.findall(code) + pattern_regex.findall(code) + pattern_extension.findall(code))
        danger_score = len(matches)

        total_score.append(danger_score)

    return total_score

# make a function from trailer operation on line 232
def detect_trailer_operation(clean_stream, total_score):
    trailers = clean_stream.split("trailer")
    trailer_codes = []
    suspicious_actions = ["submitform", "importdata", "gotoe", "launch", "uri", "url"]
    for trailer in trailers[1:]:
        if any(action in trailer.lower() for action in suspicious_actions):
            trailer_codes.append("WARNING: UNEXPECTED CODE IN TRAILER \n\n" + trailer)
            total_score.append(10)
    if len(trailers) > 2:
        trailers = trailers[1:]
        for trailer in trailers:
            trailer_obj = re.search("obj.*endobj", trailer, re.DOTALL)
            if trailer_obj:
                trailer_codes.append("WARNING: OBJECT IN TRAILER \n\n" + trailer_obj.group(0))
                total_score.append(10)

    return trailer_codes, total_score


def parse_objects(objects_regex, type_pattern, js_pattern):
    objects = []
    js = []
    for obj in objects_regex:
        obj_num = int(obj.split(' ')[0])
        obj_gen = int(obj.split(' ')[1])
        type = re.search(type_pattern, obj, re.DOTALL)
        if type:
            type = type.group(1)
        else:
            type = None
        try:
            temp_stream = re.search("obj.*endobj", obj, re.DOTALL).string
        except AttributeError:
            temp_stream = re.search("obj.*?>>", obj, re.DOTALL).string if re.search("obj.*?>>", obj,
                                                                                    re.DOTALL) else None
        js.append(re.search(js_pattern, temp_stream, re.DOTALL))

        js[-1] = js[-1].string if js[-1] else None
        objects.append(PDFObject(obj_num, obj_gen, type, temp_stream, js[-1]))

    return objects, js


def detect_codes(objects, final):
    for obj in objects:
        obj_stream_lower = obj.obj_stream.lower()
        if obj.type == "/Action":
            if obj.jump is not None:
                numbers = re.search("(\d+) (\d+) ?R", obj.jump)
                if numbers:
                    numbers = numbers.group(0)
                    # get 6 and 0 from ['/JS 6 0 R  >>endobj']
                    obj_num = int(numbers.split(' ')[0])
                    obj_gen = int(numbers.split(' ')[1])
                    # get object with obj_num and obj_gen
                    for o in objects:
                        if o.obj_num == obj_num and o.obj_gen == obj_gen:
                            # get javascript code from object
                            final.append(o.obj_stream)

            elif obj.jump is None:
                suspicious_actions = ["submitform", "importdata", "gotoe", "launch", "uri", "url"]
                if "/s" in obj_stream_lower:
                    # check if any of the suspicious actions are in the object stream
                    if any(action in obj_stream_lower for action in suspicious_actions):
                        if "/uri" in obj_stream_lower or "/url" in obj_stream_lower:
                            final.append(obj.obj_stream)
                        elif "/filespec /f" in obj_stream_lower:
                            final.append(obj.obj_stream)
        else:
            suspicious_actions = ["<template>", "<submit"]
            if any(action in obj_stream_lower for action in suspicious_actions):
                final.append(obj.obj_stream)

    return final


def open_pdf(pdf_file):
    pdf_document = fitz.open(stream=pdf_file.file.read(), filetype="pdf")
    page_texts = []

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        page_text = page.get_text("text")
        page_texts.append(page_text)

    clean_stream = str(pdf_document.stream).replace('\\r', '').replace('\\n', '')
    json = {}
    json["File name"] = pdf_file.filename
    # add metadata to json
    json.update(find_metadata(pdf_document.metadata))
    metadata_score = count_not_available(json)
    pdf_document.close()

    return clean_stream, json, metadata_score


@app.post("/upload/")
async def upload_pdf(pdf_file: UploadFile, request: Request):
    if pdf_file.content_type == 'application/pdf':

        clean_stream, json, metadata_score = open_pdf(pdf_file)

        js_pattern = r"/JS.*?endobj"
        type_pattern = r"/Type\s+([^<\s]+)"
        js = re.findall(js_pattern, clean_stream, re.DOTALL)
        final = []
        total_score = []
        final = js

        objects_regex = re.findall('\d+ \d+ obj.*?endobj', clean_stream, re.DOTALL)
        if not objects_regex:
            objects_regex = re.findall(r'\d+ \d+ obj.*?>>', clean_stream, re.DOTALL)

        # get objects from pdf stream
        objects, js = parse_objects(objects_regex, type_pattern, js_pattern)

        # get malicious content from objects
        final = detect_codes(objects, final)

        # get malicious content from trailers
        trailer_codes, total_score = detect_trailer_operation(clean_stream, total_score)

        malicious_code_list = []
        for j in final:
            malicious_code_list.append(j)
        total_score += get_score(malicious_code_list)
        malicious_code_list += trailer_codes
        if len(malicious_code_list) == 0:
            malicious_code_list.append("No suspicious code found in this PDF file.")
            total_score.append(0)
        malicious_code_list = list(zip(malicious_code_list, total_score))

        # You can now work with 'text_content' as needed
        return templates.TemplateResponse("index.html", {"request": request, "message": "PDF file uploaded and parsed successfully.", "content": json, "metadata_score": metadata_score, "malicious_code_list": malicious_code_list, "score": sum(total_score) + metadata_score})
    else:
        return await root(request, "No file uploaded or incorrect file type uploaded. Please upload supported file "
                                   "type.")
