FROM python:3

RUN apt-get update \
    && apt-get install -y \
        libopus0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt discomblebot/

RUN git clone https://github.com/azlux/pymumble.git \
    && pip install --no-cache-dir --upgrade -r pymumble/requirements.txt -r discomblebot/requirements.txt

COPY discomblebot discomblebot/

ENV PYTHONPATH=/pymumble:/discomblebot

ENTRYPOINT ["python", "-m", "discomblebot"]

CMD ["-h"]
