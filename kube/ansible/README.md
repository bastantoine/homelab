# Ansible configuration

Nodes are configured using the playbooks from https://github.com/k3s-io/k3s-ansible installed through Ansible Galaxy.

Make sure you have installed all the requirements first:

```
ansible-galaxy install -r requirements.yml
```

Available playbooks:
- `k3s.orchestration.site`: Bootstrap new cluster
- `k3s.orchestration.upgrade`: Upgrade existing cluster
- `k3s.orchestration.reboot`: Reboot existing cluster
- `k3s.orchestration.reset`: Reset nodes of existing cluster

They can be used directly:

```
ansible-playbook k3s.orchestration.site
```
