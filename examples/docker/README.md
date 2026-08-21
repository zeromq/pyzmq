Original repository: https://github.com/NumesSanguis/pyzmq-docker

# Docker & ZeroMQ
## Overview
Example project to demonstrate how you can turn Python scripts
into micro-services in Docker containers, which can communicate over ZeroMQ.
The examples here can be run as just Python-Python, Docker-Docker (`docker-compose`) or Docker-Python (`docker run`).

Examples are using a Publisher-Subscriber pattern to communicate.
This means that the publisher micro-service just send messages out to a port,
without knowing who is listening and a subscriber micro-service receiving data,
without knowing where the data comes from.

With ZeroMQ, only 1 micro-service can `socket.bind(url)` to 1 address.
However, you can have unlimited micro-services `socket.connect(url)` to an address.
This means that you can either have many-pub to 1-sub (examples in this Git repo) or 1-pub to many-sub on 1 ip:port combination.


## Install Docker
* [General Docker instructions](https://docs.docker.com/install/#supported-platforms)
* [Docker Toolbox for Windows 7/8/10 Home](https://docs.docker.com/toolbox/overview/)
* [Docker for Windows 10  Pro, Enterprise or Education](https://docs.docker.com/docker-for-windows/install/#what-to-know-before-you-install)
* Ubuntu: [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/) and [docker-compose](https://docs.docker.com/compose/install/) and `sudo usermod -a -G docker $USER`


## 1. Python-Python
1. Open a terminal and navigate to folder `pyzmq-docker/sub`
2. Execute `python main.py`
3. Open a terminal and navigate to folder `pyzmq-docker/pub`
4. Execute `python main.py`
5. See subscriber receiving messages from the publisher!

Notes:
* Steps 1-2, can be reversed with steps 3-4.
* Make sure you've installed PyZMQ in your Python installation (`conda install pyzmq` or `pip install pyzmq`)


## 2. Docker-Docker with docker-compose
1. Open a terminal and navigate to folder `pyzmq-docker`
2. Execute`docker-compose up --build`
3. See a Dockerized subscriber receiving messages from a Dockerized publisher! (That's really everything? 0.o)

Notes:
* If you didn't make any changes to your Docker container, you can Execute `docker-compose up` without `--build`
  to skip the build process.
* Advantages of `docker-compose`:
  * You need only 1 `docker-compose.yml` to start multiple Docker micro-services
  * It connects the `pub` micro-service to the `sub` micro-service with `tcp://sub:5550`.
    Docker automatically turns `sub` into the IP of the subscriber micro-service.


## 3. Docker-Python with docker run
Notes:
* Make sure you've installed PyZMQ in your Python installation (`conda install pyzmq` or `pip install pyzmq`)

### 3a. pub-Docker, sub-Python
1. Open a terminal and navigate to folder `pyzmq-docker/sub`
2. Execute `python main.py`
3. Open file `pub/Dockerfile` and change `"yo.ur.i.p"` to your machine IP (something similar to: `"192.168.99.1"`)
4. Open a terminal and navigate to folder `pyzmq-docker/pub`
5. Execute `docker build . -t foo/pub`
6. Execute `docker run -it foo/pub`
7. See that your subscriber receives messages from your Dockerized publisher.

Notes:
* Step 5 can be skipped after the first time if no changes were made to the Docker/Python files.
* Steps 1-2 can be reversed with steps 3-6.

### 3b. pub-Python, sub-Docker
1. Open a terminal and navigate to folder `pyzmq-docker/sub`
2. Execute `docker build . -t foo/sub`
3. Execute `docker run  -p 5551:5551 -it foo/sub` (maps port of Docker container to localhost)
4. Open a terminal and navigate to folder `pyzmq-docker/pub`
5. Execute `python main.py`
6. See that your Dockerized subscriber receives messages from your publisher.

Notes:
* Steps 1-3 can be reversed with steps 4-5.
* Add a name to a container by adding `--name foo-sub` to `docker run `
* In case of container name already in use, remove that container with: `docker rm foo-sub`



## Other
### Inspiration
Stackoverflow question: https://stackoverflow.com/questions/53802691/pyzmq-dockerized-pub-sub-sub-wont-receive-messages

### Useful Docker commands

    sudo usermod -a -G docker $USER  # add current user to group docker on Linux systems (Ubuntu)

    docker build . -t foo/sub  # build docker image
    docker run -it foo/sub  # run build docker image and enter interactive mode
    docker run -p 5551:5551 -it foo/sub  # same as above with mapping Docker port to host
    docker run -p 5551:5551 --name foo-sub -it foo/sub  # same as above with naming container
    docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' pyzmq-docker_sub_1  # get ip of container
    docker rm foo-sub  # remove container by name
    
    docker-compose up  # run docker-compose.yml
    docker-compose build / docker-compose up --build  # rebuild images in docker-compose.yml

    docker image ls  # show docker images
    docker container ls  # show docker containers
    docker exec -it pyzmq-docker_pub_1  # enter bash in container
    docker attach pyzmq-docker_sub_1  # get

    To detach the tty without exiting the shell, use the escape sequence Ctrl+p + Ctrl+q
    
    docker rm $(docker ps -a -q)  # Delete all containers
    docker rmi $(docker images -q)  # Delete all images
    
    
### Debug docker-machine IP not found (probably not necessary)
Docker machine working check:
* Open a terminal and Execute command: `docker-machine ip`
  * Should return a Docker machine IP (likely `192.168.99.100`)
  * If not, see section "Debug" (e.g. `Error: No machine name(s) specified and no "default" machine exists`)

Debug attempts:
* Execute the command `docker-machine ls`.
* If nothing shows up, we have to add a new machine with `docker-machine create default`.
* If that gives the error `Error with pre-create check: "VBoxManage not found.
  Make sure VirtualBox is installed and VBoxManage is in the path"`,
  see if `which virtualbox` and `which VBoxManage` return paths.
  If not, you likely need to install VirtualBox. Else, see debug links.
* Debug links:
  * https://github.com/docker/machine/issues/4590
  * Windows: https://stackoverflow.com/questions/39966083/docker-machine-no-machine-name-no-default-exists
  * Install VirtualBox: https://stackoverflow.com/questions/45836296/error-with-pre-create-check-vboxmanage-not-found-make-sure-virtualbox-is-inst
