#!/bin/bash
sudo docker rm -f weatherdash
sudo docker run \
	--name weatherdash \
  	--label 'traefik.http.routers.weatherdash.tls=true'  \
  	--network monitoring \
	-p 8200:8080 \
  	--restart unless-stopped \
	-d \
	michaelkelly.org/weatherdash:latest
