#! /bin/bash

set -e

FRONTEND=$(dirname $0)
cd ${FRONTEND}

if ! ls node_modules >/dev/null 2>&1; then
    npm install
else
    echo "skipping npm install; rm -rf node_models if packages changed"
fi

host_ip=$(node -e 'console.log(require("ip").address())')
cat src/axios_config.js.template | sed "s/<HOST_IP>/$host_ip/" >src/axios_config.js
echo "Generated src/axios_config.js"
npm run build
