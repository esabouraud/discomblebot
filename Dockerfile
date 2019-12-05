FROM python:3-alpine AS discomblebot-builder

RUN apk add --update --no-cache git protobuf gcc musl-dev \
	&& rm -rf /var/cache/apk/*

COPY requirements.txt discomblebot/

ENV PYTHONDONTWRITEBYTECODE=1

RUN python -m venv --system-site-packages /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN git clone https://github.com/azlux/pymumble.git \
    && pip install --no-cache-dir --upgrade -r pymumble/requirements.txt \
    && pip install --no-cache-dir --upgrade -r discomblebot/requirements.txt

COPY discomblebot discomblebot/

RUN protoc --python_out=. discomblebot/bot_msg.proto

FROM python:3-alpine

RUN apk add --update --no-cache opus binutils \
	&& rm -rf /var/cache/apk/* \
    && ln -s /usr/lib/libopus.so.0 /usr/lib/libopus.so

COPY --from=discomblebot-builder /opt/venv /opt/venv

COPY --from=discomblebot-builder pymumble/pymumble_py3/ /discomble/pymumble_py3/

COPY --from=discomblebot-builder discomblebot/ /discomble/discomblebot/

ENV PATH="/opt/venv/bin:$PATH"

ENV PYTHONPATH="/discomble"

ENTRYPOINT ["python", "-m", "discomblebot"]

CMD ["-e"]
