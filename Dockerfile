FROM python


WORKDIR /app

COPY interview_agent.py .
COPY PdfLoader.py .
COPY streamlit_app.py .
COPY requirement.txt .


RUN pip install -r requirement.txt
EXPOSE 8000
CMD [ "streamlit","run","streamlit_app.py" ]



