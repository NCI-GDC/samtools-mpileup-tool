FROM ubuntu:18.04
LABEL maintainer="sli6@uchicago.edu"
LABEL version="1.1"
LABEL description="Python wrapper of multithreading mpileup in samtools-1.1"

RUN apt update -y \
	&& apt install -y \
	bzip2 \
	gcc \
	libncurses-dev \
	make \
	wget \
	zlib1g-dev \
	libbz2-dev \
	liblzma-dev \
    software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa \
    && apt update -y \
    && apt install python3.7 -y \
	&& apt-get clean

RUN	cd /opt/ \
	&& wget http://sourceforge.net/projects/samtools/files/samtools/1.1/samtools-1.1.tar.bz2 \
	&& tar xf samtools-1.1.tar.bz2 \
	&& cd samtools-1.1 \
	&& make \
	&& make install \
	&& cd - \
	&& rm -rf

ADD multi_samtools_mpileup_p3.py /opt/