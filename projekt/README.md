# PDF File Analyzer

This is a semestral project for the subject Information Technologies Security. Its main purpose is to provide users with the output if pdf file is possibly malicious or if it is safe.

Disclaimer: This tool can detect malicious content, however, it is crucial to understand that no automated tool can guarantee absolute security. Always complement the tool's findings with personal judgment and always double-check the files you receive through email.

---

**Python verion** - Python 3.10.1
**Pip version** - 23.2.1

---

## Installation and run guide

1. Clone this repository from https://github.com/FedorViest/BIT/ and move to *project* directory (you only need project directory, so you can delete the rest of files)
2. Create virtual environment using command `python -m venv venv`
3. Navigate to /venv/Scripts and type in command `. activate`
4. Navigate back to project root directory (where main.py is)
5. Install requirements with command `pip install -r requirements.txt`
6. To run the program type in `uvicorn main:app --host 127.0.0.1 --port 8000` (you can change host and port to suit your preferences)


---


