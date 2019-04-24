FROM python:3-alpine

RUN apk add --update --no-cache opus opus-dev binutils git \
	&& rm -rf /var/cache/apk/*

COPY requirements.txt discomblebot/

RUN git clone https://github.com/azlux/pymumble.git \
    && pip install --no-cache-dir --upgrade -r pymumble/requirements.txt -r discomblebot/requirements.txt

COPY discomblebot discomblebot/

ENV PYTHONPATH=/pymumble:/discomblebot

ENTRYPOINT ["python", "-m", "discomblebot"]

CMD ["-h"]
