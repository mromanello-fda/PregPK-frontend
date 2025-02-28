FROM python:3.9
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . ./

EXPOSE 7860
CMD ["python", "app.py"]