# Demo

This is the demo code of paper "COVID-19 Claim Radar: A Structured Claim Extraction and Tracking System". You can check our deployed demo [here](http://18.221.187.153/)



## Requirments

Node.js == v12.12.0

Go == v1.13.1

npm == v6.11.3

Python3

(Higer version may cause error)



# Usage

### Environment Setup

0. Make sure your server has at least one open and idle port. In the following instructions, we assume this port is 80.

1. Install nginx

   ```bash
   sudo apt-install nginx
   ```

2. Configure nginx

   Find your nginx configuration file (For Linux users: this file could be ``/etc/nginx/nginx.conf``, but could also in other paths, depending on your system configuration), then configure nginx:

   ```nginx
    server {
           listen       80;
           listen       [::]:80;
           server_name  _;
           root         {PROJ_DIR}/frontend/dist;
   
           index index.html index.htm index.nginx-debian.html;
           # Load configuration files for the default server block.
           # include /etc/nginx/default.d/*.conf;
   
           location / {
                   # First attempt to serve request as file, then
                   # as directory, then fall back to displaying a 404.
                   try_files $uri $uri/ /index.html =404;
           }
   
           error_page 404 /404.html;
           location = /404.html {
           }
   
           error_page 500 502 503 504 /50x.html;
           location = /50x.html {
           }
       }
   ```

   where ``{PROJ_DIR}`` denotes the path of this demo.

   3. Start nginx server

      ```bash
      sudo service nginx start
      ```



### Deploy Frontend

```bash
cd {PROJ_DIR}/demo/frontend
npm run build
```



### Deploy Backend

1. Preprocess data

   ```bash
   cd {PROJ_DIR}/demo/backend/demo_files
   bash process.sh
   ```

   If you want to use your own data to replace our data, you could refer to the data format in ``{PROJ_DIR}/demo/backend/demo_files`` and process your data the same format as ours.

2. Deploy

   ```bash
   cd ~/demo/backend
   go run hw.go
   ```

   This may need an hour to build. Once the build is finish, you will find that the website is working normally.

