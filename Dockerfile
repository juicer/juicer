# Latest juicer running on f23
#
# You have to mount the configuration directory and work directory to run:
#
#   docker run -v <myconfigdir>:/root/.config/juicer -v <workdir>:/rpms -w /rpms <image> 'juicer rpm upload -r <rpmname>'
#

FROM fedora:23
USER root

RUN dnf install -y  python2-devel python-argparse rpm-python PyYAML pymongo python-BeautifulSoup python-magic python-progressbar python-requests wget git make

RUN cd root; git clone https://github.com/juicer/juicer.git

RUN cd root/juicer; make install 

RUN mkdir -p /root/.config/juicer

VOLUME ["/root/.config/juicer","/rpms"]

ENTRYPOINT ["/bin/bash", "-c"]
