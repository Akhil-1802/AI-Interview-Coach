FROM python


WORKDIR /app


# 1. Copy ONLY requirements first
COPY requirement.txt .

# 2. Install dependencies (Cached unless requirements.txt changes)
RUN pip install --no-cache-dir -r requirements.txt

COPY interview_agent.py .
COPY PdfLoader.py .
COPY streamlit_app.py .

EXPOSE 8000
CMD [ "streamlit","run","streamlit_app.py" ]



