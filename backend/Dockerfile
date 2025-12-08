FROM python:3.10-slim

WORKDIR /backend

COPY ./requirement.txt /backend/requirement.txt

RUN pip install --no-cache-dir --upgrade -r /backend/requirement.txt

COPY ./ /backend/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]