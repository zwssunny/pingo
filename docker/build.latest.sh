#!/bin/bash

unset KUBECONFIG

cd .. && docker build -f docker/Dockerfile.latest \
             -t zhanws/pingo .

# docker tag zhanws/pingo  zhanws/pingo:$(date +%y%m%d)