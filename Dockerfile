# Serves the prepared notes. Live questions need an LLM backend (coach/llm.py); without one they show a plain message.
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY coach coach
COPY curriculum curriculum
COPY content content
COPY web web
RUN useradd --create-home coach && mkdir data && chown coach data
USER coach
EXPOSE 8000
CMD ["uvicorn", "coach.server:app", "--host", "0.0.0.0", "--port", "8000"]
