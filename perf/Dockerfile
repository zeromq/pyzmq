FROM python:3.11
RUN pip install pandas
RUN pip install --pre pyzmq
RUN mkdir /data && mkdir /perf
ADD *.py /perf/

WORKDIR /data
ENTRYPOINT ["python3", "/perf/collect.py"]
CMD ["thr"]
