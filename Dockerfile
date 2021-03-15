FROM quay.io/ncigdc/samtools:1.1 AS samtools
FROM quay.io/ncigdc/python37 AS python

ENV BINARY samtools_mpileup_tool
LABEL maintainer="sli6@uchicago.edu"
LABEL version="1.1"
LABEL description="Samtools-1.1"

COPY --from=python / /
COPY --from=samtools /usr/local/bin/ /usr/local/bin/

COPY ./dist/ /opt
WORKDIR /opt

RUN apt-get update \
	&& apt-get install make \
	&& rm -rf /var/lib/apt/lists/*

RUN make init-pip \
  && ln -s /opt/bin/${BINARY} /bin/${BINARY}

ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
ENTRYPOINT ["/tini", "--", "samtools_mpileup_tool"]
CMD ["--help"]
