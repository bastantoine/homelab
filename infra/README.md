## Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -U pip ansible
ansible-galaxy install -U -r requirements.yml
```

## DNS management

Playbook file: [`playbooks/dns.yml`](playbooks/dns.yml)

This playbook will install bind9 in all dns nodes, configure replication between the master and the replica(s), and configure the zones

Zones:
- `*.lab.bastien-antoine.fr`: manually defined in [`playbooks/files/dns/lab-bastien-antoine-fr.zone`](playbooks/files/dns/lab-bastien-antoine-fr.zone)
- `*.infra.bastien-antoine.fr`: automatically defined by binding each of the name of the VM in Proxmox with their IPs, using  [`playbooks/template/dns/infra-bastien-antoine-fr.zone`](playbooks/template/dns/infra-bastien-antoine-fr.zone.j2)

```bash
ansible-playbook playbooks/dns.yml
```

## Monitoring

Monitoring is done using Grafana + Prometheus, along some Prometheus exporters.

`monitoring` node is configured with Grafana + Prometheus, using the [`playbooks/monitoring.yml`](playbooks/monitoring.yml).

It requires the following ansible collections:
- `prometheus.prometheus`
- `grafana.grafana`

```bash
ansible-playbook playbooks/monitoring.yml -e @vault.yml
```

> [!TIP]
> When running the playbook on macOS, you may encouter an error like:
> > ```
> > +[__NSCFConstantString initialize] may have been in progress in another thread when fork() was called. We cannot safely call it or ignore it in the fork() child process. Crashing instead. Set a breakpoint on objc_initializeAfterForkError to debug. ERROR! A worker was found in a dead state
> > ```
> In this case you may need to set the following variable:
> ```bash
> export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
> ```
> [\[src\]](https://docs.ansible.com/projects/ansible/latest/reference_appendices/faq.html#running-on-macos-as-a-control-node)

### Node-exporter

Each VM and each Proxmox node has a node-exporter installed and are all registered in the common Prometheus.

```bash
ansible-playbook playbooks/node-exporter.yml
```

## Kube

Nodes are configured using the playbooks from [`github.com/k3s-io/k3s-ansible`](https://github.com/k3s-io/k3s-ansible) Ansible collection.

Available playbooks:
- `k3s.orchestration.site`: Bootstrap new cluster
- `k3s.orchestration.upgrade`: Upgrade existing cluster
- `k3s.orchestration.reboot`: Reboot existing cluster
- `k3s.orchestration.reset`: Reset nodes of existing cluster

They can be used directly:

```
ansible-playbook k3s.orchestration.site
```

## Nginx and Docker

Two playbooks to install Nginx and Docker on a given node:

```bash
ansible-playbook playbooks/ansible.yml
```
```bash
ansible-playbook playbooks/docker.yml
```

The playbook `playbooks/docker.yml` install Docker, as well as the `docker` Python package to be able to use any Ansible actions that deals with Docker

They rely on 3 roles:
- Nginx: `geerlingguy.nginx`
- Docker: `geerlingguy.docker` and `geerlingguy.pip`

## Note on the inventory management

Inventory main source is Proxmox, using the `community.proxmox.proxmox` inventory plugin.

Ansible groups are automatically created based on the tags set on the VMs on Proxmox.
