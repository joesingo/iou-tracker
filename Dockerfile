FROM python:3.4-slim
WORKDIR /iou
ADD . /iou
RUN pip install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 7000
CMD ["python", "app.py"]
