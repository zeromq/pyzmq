FROM python:3.6
RUN pip install pandas cython
RUN pip install -vv https://github.com/zeromq/pyzmq/archive/master.tar.gz --install-option=--zmq=bundled
RUN mkdir /data && mkdir /perf
ADD *.py /perf/

WORKDIR /data
ENTRYPOINT ["python", "/perf/collect.py"]
CMD ["thr"]
