# Monitoring

## Endpoints

all endpoints are for prometheus and therefor deliver a `/metrics` path

  * **8001** LPOS metrics endpoint
  * **9100** prometheus node exporter
  * **9323** information about docker containers running on LPOS host (not provided by docker it-self but by the docker-image shayanghani/container-exporter)
  * **8404** information of inbound haproxy (always enabled)
  * **9216** mongodb exporter
