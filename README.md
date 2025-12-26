# kubenetes cluster
- before install edit `/boot/firmware/cmdline.txt`
    - add: `cgroup_memory=1 cgroup_enable=memory` to the end
    - then reboot
- installed via k3s
    - https://docs.k3s.io/quick-start
    - kubectl should come part of this
        - https://docs.k3s.io/cli
- right after installation, you'll get this error when trying to use kubectl: `E1226 01:53:19.805352    3975 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"`
to fix:
```
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown nathan:nathan ~/.kube/config
chmod 600 ~/.kube/config
```




on worker node, to install k3s:
curl -sfL https://get.k3s.io | K3S_URL=https://<raspberrypi5-ip>:6443 K3S_TOKEN=<token> sh -
token is at `sudo cat /var/lib/rancher/k3s/server/node-token`
curl -sfL https://get.k3s.io | K3S_URL=https://195.168.1.7:6443 K3S_TOKEN=K1017a16542e066500b10d8be22688d8fba8f59184a31d43882e7bd3dcf237a7399::server:32ac7bc6962028191fbb7173d86d60cd sh -
then copy the .kube/config file and replace the localhost with the master ip

to check if it's working run:
`kubectl get nodes -o wide`

# changelog
You can find the changelog [here](./CHANGELOG.md).

## how to
`git cliff --unreleased --tag v1.0.7 --prepend CHANGELOG.md`
`gc -m "docs: add changelog for v1.0.7"`
`gt 1.0.7`