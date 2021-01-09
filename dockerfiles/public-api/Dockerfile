FROM python:3.7

EXPOSE 7000

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ../../python-libs.txt /usr/src/app/
RUN pip install --no-cache-dir -r python-libs.txt

COPY ../../public-api.py .

ENTRYPOINT ["python3", "public-api.py"]