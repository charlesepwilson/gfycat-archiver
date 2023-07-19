ARG PYTHON_VERSION="3.11"
FROM python:${PYTHON_VERSION}-slim

COPY requirements.txt .
COPY requirements-google.txt .


RUN pip install --no-cache-dir --upgrade -r requirements.txt -r requirements-google.txt

COPY . .

CMD python3 -m gfycat_archiver
