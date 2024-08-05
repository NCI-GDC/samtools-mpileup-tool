ARG REGISTRY=docker.osdc.io/ncigdc
ARG BASE_CONTAINER_VERSION=latest

FROM ${REGISTRY}/python3.9-builder:${BASE_CONTAINER_VERSION} as builder

COPY ./ /samtools_mpileup_tool

WORKDIR /samtools_mpileup_tool

RUN pip install tox && tox -e build

FROM ${REGISTRY}/python3.9:${BASE_CONTAINER_VERSION}

LABEL org.opencontainers.image.title="samtools_mpileup_tool" \
      org.opencontainers.image.description="GDC Samtools mpileup" \
      org.opencontainers.image.source="https://github.com/NCI-GDC/samtools-mpileup-tool.git" \
      org.opencontainers.image.vendor="NCI GDC"

COPY --from=builder /samtools_mpileup_tool/dist/*.whl /samtools_mpileup_tool/
COPY requirements.txt /samtools_mpileup_tool/

WORKDIR /samtools_mpileup_tool

RUN pip install --no-deps -r requirements.txt \
	&& pip install --no-deps *.whl \
	&& rm -f *.whl requirements.txt

USER app

ENTRYPOINT ["samtools_mpileup_tool"]

CMD ["--help"]
