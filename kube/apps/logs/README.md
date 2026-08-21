An installation of [`github.com/amir20/dozzle`](https://github.com/amir20/dozzle) using Helm chart from [`github.com/bastantoine/helm-charts`](https://github.com/bastantoine/helm-charts).

```shell
helm repo add bastantoine https://bastantoine.github.io/helm-charts/
helm upgrade logs bastantoine/dozzle --install --namespace monitoring -f ./values.yaml
```
