# Linux Development via Docker on macOS

This repository is built on a **MacBook** using **Docker** to create a **Linux development environment**.  
All development is performed inside Linux containers for consistency and compatibility.

Although the code is compiled and run in Linux, it can also be developed locally on a Mac by:

- Creating a Linux-based Docker image (e.g., Ubuntu)
- Running the container on macOS using Docker
- Mounting your macOS file system into the container using volumes

This setup enables fully containerized C++ development that integrates seamlessly with local file editing.

---

## 🚀 Development Workflow

### 1. Build the Docker container

This builds an Ubuntu-based image with all dependencies (e.g., CMake, OpenSSL, IXWebSocket):

```sh
./run-build-linux-docker.sh
```

### 2. Run the Docker Container

Run the Docker Image, creates a shell to do development in

```sh
# run the docker image
# specify the mount point
# this will be where r/w access between mac/docker will be

./run-linux-docker.sh $HOME/cpp-crypto 
```


### 3. Build IXWebSocket

***Done in linux*** 

clone the IXWebSocket repo

TLS_ON=TRUE

install headers and lib

```sh
# installs headers to /workspace/install/include
# installs lib     to /workspace/install/lib


./run-build-ixwebsocket.sh
```
