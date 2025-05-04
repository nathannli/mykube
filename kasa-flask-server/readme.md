there are the 2 parts to this:

1) the docker app. This is the actual flask application/server that does the scrapping
2) the kubenertes config files. this is responsible for creating the pod to house the docker app

The order of the install/build process is:
1) build the docker image locally
2) push the docker image to docker hub
3) deploy the kubernetes pod
    - the kube pod will pull the docker image from docker hub (the image registry)
    - `kubectl apply -f kube-configs/`