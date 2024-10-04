FROM ubuntu:22.04 as builder

ARG PACKAGES="python3.11 unzip python3-pip apt-transport-https ca-certificates sqlite3 pcscd libusb-1.0-0 libusb-0.1-4 udev"
ARG LICENSE
ARG PFX_FILE
ARG ROOT_PFX_FILE
ARG PINCODE

RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc cmake build-essential libboost-dev libxml2-dev \
       python3.11-dev git $PACKAGES && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /cades

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

COPY ./reqs.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r reqs.txt

WORKDIR /tmp
COPY arch ./arch
RUN cd /tmp/arch && tar -xf linux-amd64_deb.tgz && \
    linux-amd64_deb/install.sh cprocsp-rdr-pcsc cprocsp-rdr-rutoken \
      cprocsp-rdr-cryptoki lsb-cprocsp-devel cprocsp-pki-cades \
      cprocsp-rdr-pcsc
RUN dpkg -i /tmp/arch/linux-amd64_deb/cprocsp-pki-cades-64*.deb
#RUN dpkg -i /tmp/arch/linux-amd64_deb/ifd-rutokens*.deb
WORKDIR /tmp/src
RUN git clone https://github.com/CryptoPro/pycades.git pycades
RUN cd pycades && mkdir build && cd build && cmake .. && make -j4

RUN cp /tmp/src/pycades/build/pycades.so /opt/cprocsp/lib/amd64/pycades.so
RUN ln -s /opt/cprocsp/lib/amd64/pycades.so /cades/pycades.so
RUN /opt/cprocsp/sbin/amd64/cpconfig -license -set $LICENSE


FROM ubuntu:22.04

WORKDIR /cades

COPY $PFX_FILE ./certs/signcert.pfx
COPY $ROOT_PFX_FILE ./certs/rootcert.pfx
RUN /opt/cprocsp/bin/amd64/certmgr -install -pfx -file ./certs/signcert.pfx -newpin $PINCODE
RUN /opt/cprocsp/bin/amd64/certmgr -install -store mRoot -f ./certs/rootcert.pfx
COPY --from=builder /opt/cprocsp /opt/cprocsp
COPY --from=builder /opt/cprocsp/lib/amd64/pycades.so /cades/pycades.so

RUN apt-get update && apt-get install -y --no-install-recommends $PACKAGES

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

COPY ./reqs.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r reqs.txt

COPY ./certs ./certs
COPY ./diadoc ./diadoc
COPY ./router ./router
COPY ./apisrv.py .
COPY ./backends.py .
COPY ./config.py .
COPY ./const.py .
COPY ./db.py .
COPY ./logger.py .
COPY ./logic.py .
COPY ./middleware.py .
COPY ./sender.py .
COPY ./singleton.py .
COPY ./tools.py .
COPY ./cades.default.yaml ./cades.yaml

#RUN rm -rf /tmp/*

#ENTRYPOINT ["python", "apisrv.py"]
