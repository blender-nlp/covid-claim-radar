# ISI demo notes

The UIUC demo runs three servers:

* http (nginx)
* backend (backend/hw.go)
* Real-Time Extraction


## Real-Time Extraction

The Real-Time Extraction server is for running a portion of the system
over short snippets of text in real time.The code for it is not
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


## Install node, go, nginx

```
$ wget https://nodejs.org/download/release/v12.12.0/node-v12.12.0-linux-x64.tar.gz
$ tar xf node-v12.12.0-linux-x64.tar.gz
$ PATH=$PWD/node-v12.12.0-linux-x64/bin:$PATH

$ conda create -y -n uiuc-demo pip python=3.9
$ conda activate uiuc-demo
$ conda install -c conda-forge go

$ wget https://nginx.org/download/nginx-1.23.0.tar.gz
$ tar xf nginx-1.23.0.tar.gz
$ cd nginx-1.23.0
$ ./configure --prefix=/path/to/your/nginx --without-http_rewrite_module --without-http_gzip_module
$ make install
$ cd /path/to/your/nginx

# then apply these changes
$ diff conf/nginx.conf.orig conf/nginx.conf
36,37c36,39
<         listen       80;
---
>         listen       8080;
44c46,47
<             root   html;
---
>             root /path/to/your/covid-claim-radar/demo/frontend/dist;
```

## Build frontend

```
$ cd demo/frontend
$ PATH=/path/to/your/node-v12.12.0-linux-x64/bin:$PATH
$ npm install       # once
$ npm run build     # anytime frontend files change
```

## Process data

```
$ cd backend/demo_files
$ bash -xe process.sh    # works on checked in file; we'll have to adjust this
```

## Launch servers

```
$ (cd /path/to/your/nginx && sbin/nginx -c conf/nginx.conf)
$ cd demo/backend
$ conda activate uiuc-demo
$ go run hw.go
```

Then visit: http://saga29.isi.edu:8080/
