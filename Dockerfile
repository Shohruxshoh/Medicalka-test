# ---- Base image ----
FROM python:3.12-slim

# Do not write .pyc files; stream logs immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# ---- Dependencies (cached separately from source) ----
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- Application source ----
COPY . .

# ---- Default run command ----
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
