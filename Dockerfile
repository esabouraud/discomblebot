FROM python:3-alpine AS discomblebot-builder

RUN apk add --update --no-cache opus opus-dev binutils git protobuf \
	&& rm -rf /var/cache/apk/*

COPY requirements.txt discomblebot/

RUN git clone https://github.com/azlux/pymumble.git \
    && pip install --user --no-cache-dir --upgrade -r pymumble/requirements.txt
    && pip install --user --no-cache-dir --upgrade -r discomblebot/requirements.txt

COPY discomblebot discomblebot/

RUN protoc --python_out=. discomblebot/bot_msg.proto


FROM python:3-alpine

RUN apk add --update --no-cache opus binutils \
	&& rm -rf /var/cache/apk/*
    && ln -s /usr/lib/libopus.so.0 /usr/lib/libopus.so

COPY --from=discomblebot-builder /root/.local /root/.local

COPY --from=discomblebot-builder pymumble/pymumble_py3/ /discomble/pymumble_py3/

COPY --from=discomblebot-builder discomblebot/ /discomble/discomblebot/

ENV PYTHONPATH=/discomble

ENTRYPOINT ["python", "-m", "discomblebot"]

CMD ["-e"]
