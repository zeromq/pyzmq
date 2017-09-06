BASE_IMAGE=python:3.6
IMAGE=pyzmq-perf
VOLUME=pyzmq-perf

ifeq ($(DOCKER_MACHINE_NAME), "")
	OUT_PATH=$(PWD)
	FETCH=true
else
	OUT_PATH=/tmp/data
	FETCH=docker-machine scp $(DOCKER_MACHINE_NAME):$(OUT_PATH)/*.pickle ./
endif

RUN=docker run --rm -v $(VOLUME):/data -it $(IMAGE)

build:
	docker build -t $(IMAGE) .

volume:
	docker volume inspect pyzmq-perf &> /dev/null || docker volume create $(VOLUME)

rm-volume:
	- docker volume rm pyzmq-perf

thr:
	$(RUN) thr
	# fill in 10k-100k for the crossover
	$(RUN) thr --min 4 --max 5 --points 6
lat:
	$(RUN) lat

run: build volume thr lat

get-data:
	docker run --rm -v $(OUT_PATH):/out/ -v $(VOLUME):/data -it $(BASE_IMAGE) sh -c 'cp /data/* /out/'
	$(FETCH)
