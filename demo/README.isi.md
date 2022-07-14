# ISI demo notes

The UIUC demo runs three servers:

* http (nginx)
* backend (backend/hw.go)
* Real-Time Extraction

For local deployment, we run the servers on the same node.  We run
http on port 8000 and the backend server on port 8080.  We will not
run real-time extraction.


## Real-Time Extraction

The Real-Time Extraction server is for running a portion of the system
over short snippets of text in real time.  The code for it is not
checked into any repo I know of.  Code was shared with us by tar'ing
up from uiuc's actual server.  That code lives here:

```
/nas/gaia/users/joelb/demo_from_ziqi/claim_api.zip
```

It appears to use bits and pieces of the "official" code base, e.g.

```
claim_api/api/app.py
```

is the server that runs on port 5500.  It duplicates portions of this
checked in file:

https://github.com/blender-nlp/covid-claim-radar/blob/main/claim_detection/run.py

It is likely not needed for the upcoming demo work.  It seems to be
too slow for anything more than a single short sentence.


## Install node, go

```
$ cd covid-claim-radar/demo
$ wget https://nodejs.org/download/release/v12.12.0/node-v12.12.0-linux-x64.tar.gz -O - | tar xzf -
$ #wget https://nodejs.org/dist/v12.12.0/node-v12.12.0-darwin-x64.tar.gz -O - | tar xzf -    # for mac
$ PATH=$(echo $PWD/node-v12.12.0-*/bin):$PATH

$ wget https://go.dev/dl/go1.18.4.linux-amd64.tar.gz -O - | tar xzf -
$ #wget https://go.dev/dl/go1.18.4.darwin-amd64.tar.gz -O - | tar xzf -   # for mac
$ PATH=$PWD/go/bin:$PATH
```

## Install/configure nginx

Note: for local development, you can skip nginx and just use python's
simple HTTP server instead.  See below.

```
$ wget https://nginx.org/download/nginx-1.23.0.tar.gz -O o | tar xzf -
$ NGINX_INSTALL=$PWD/nginx
$ cd nginx-1.23.0
$ ./configure --prefix=$NGINX_INSTALL --without-http_rewrite_module --without-http_gzip_module
$ make install

# then apply these changes into $NGINX_INSTALL/conf/nginx.conf
36,37c36,39
<         listen       80;       # keep this for "production"
---
>         listen       8000;     # use 8000 for dev
44c46,47
<             root   html;
---
>             root /path/to/your/covid-claim-radar/demo/frontend/dist;
```

## Build frontend

```
$ cd demo/frontend
$ ./build_frontend.sh
```

## Process data

```
$ cd demo/backend/demo_files
$ bash -xe process.sh      # TODO: works on checked in files; needs to be parameterized
```

## Launch servers

```
$ (cd $NGINX_INSTALL && sbin/nginx -c conf/nginx.conf)
$ #(cd demo/frontend/dist && python -m http.server 8000)  # for local dev, you could skip nginx and just do this
$ cd demo/backend
$ go run hw.go
```

Then visit: `http://<HOST>:8000/`

To test the backend server from the command line:
```
$ curl -X GET "http://<HOST>:8080/backend_search?claimer=&affiliation=&object=&location=&filterTopic=&sort=Topic" | jq . | less
```
