# kubenetes cluster
- installed via k3s
    - https://k3s.io/
    - kubectl should come part of this
        - https://docs.k3s.io/cli


on worker node, to install k3s:
curl -sfL https://get.k3s.io | K3S_URL=https://<raspberrypi5-ip>:6443 K3S_TOKEN=<token> sh -
then copy the .kube/config file and replace the localhost with the master ip