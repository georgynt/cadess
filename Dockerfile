ARG PACKAGES="curl python3.11 unzip python3-pip apt-transport-https ca-certificates sqlite3 pcscd libusb-1.0-0 libusb-0.1-4 udev postgresql-client postgresql-common"
FROM repo.atol.ru/docker-remote/ubuntu:22.04 AS builder
ARG PACKAGES

RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc cmake build-essential libboost-dev libxml2-dev \
      python3 python3-dev python3.11-dev libpython3.11-dev git ${PACKAGES} && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /cades

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3-config python3-config /usr/bin/python3.11-config 1 && \
    update-alternatives --install /usr/bin/python-config python-config /usr/bin/python3.11-config 1

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

WORKDIR /tmp

RUN curl -sfOL https://repo.atol.ru/artifactory/other/billing-cades/linux-amd64_deb.tgz && \
    tar -xf linux-amd64_deb.tgz && \
    linux-amd64_deb/install.sh cprocsp-rdr-pcsc cprocsp-rdr-rutoken \
      cprocsp-rdr-cryptoki lsb-cprocsp-devel cprocsp-pki-cades \
      cprocsp-rdr-pcsc cprocsp-legacy && \
    dpkg -i /tmp/linux-amd64_deb/cprocsp-pki-cades-64*.deb && \
    rm -rf linux-amd64_deb*

WORKDIR /tmp/src

RUN git clone https://github.com/CryptoPro/pycades.git pycades
RUN sed -ri 's/SET\(Python_INCLUDE_DIR.+$/SET(Python_INCLUDE_DIR "\/usr\/include\/python3.11")/gI' pycades/CMakeLists.txt
RUN cd pycades && \
    make || make rebuild-library

RUN cp /tmp/src/pycades/build/src/pycades/pycades.so /opt/cprocsp/lib/amd64/pycades.so && \
    ln -s /opt/cprocsp/lib/amd64/pycades.so /cades/pycades.so

FROM repo.atol.ru/docker-remote/ubuntu:22.04
ARG PACKAGES

SHELL ["/bin/bash", "-exo", "pipefail", "-c"]

ENV TZ="Europe/Moscow" \
    DOCKER="1"

RUN ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime && \
    echo ${TZ} > /etc/timezone

ARG PINCODE
ARG LICENSE
ARG PFX_FILE
ARG ROOT_PFX_FILE
ARG CADES_VERSION_TAG

ENV LICENSE="${LICENSE}" \
    PINCODE="${PINCODE}" \
    CADES_VERSION_TAG="${CADES_VERSION_TAG}"

RUN apt-get update && \
    apt-get install -y --no-install-recommends ${PACKAGES}

WORKDIR /tmp

RUN curl -sfOL https://repo.atol.ru/artifactory/other/billing-cades/linux-amd64_deb.tgz && \
    tar -xf linux-amd64_deb.tgz && \
    linux-amd64_deb/install.sh cprocsp-rdr-pcsc cprocsp-rdr-rutoken \
      cprocsp-rdr-cryptoki lsb-cprocsp-devel cprocsp-pki-cades \
      cprocsp-rdr-pcsc cprocsp-legacy && \
    dpkg -i /tmp/linux-amd64_deb/cprocsp-pki-cades-64*.deb && \
    rm -rf linux-amd64_deb*

WORKDIR /cades

COPY --from=builder /opt/cprocsp/lib/amd64/pycades.so /cades/pycades.so

RUN if [[ -n "${LICENSE}" ]]; then /opt/cprocsp/sbin/amd64/cpconfig -license -set ${LICENSE}; fi

COPY certs/${PFX_FILE}.pfx ./certs/signcert.pfx
COPY certs/${ROOT_PFX_FILE} ./certs/rootcert.crt

RUN /opt/cprocsp/bin/amd64/certmgr -install -pfx -file ./certs/signcert.pfx -newpin ${PINCODE} -pin ${PINCODE} && \
    /opt/cprocsp/bin/amd64/certmgr -inst -store mRoot -f ./certs/rootcert.crt

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ .
COPY ./cades.default.yaml ./cades.yaml

RUN if [[ -n "${CADES_VERSION_TAG}" ]]; then sed -ri "s/VERSION=.+$/VERSION='${CADES_VERSION_TAG}'/g" apisrv.py; fi

ENTRYPOINT ["python", "apisrv.py"]
