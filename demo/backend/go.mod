module backend

replace (
	// cloud.google.com/go => github.com/googleapis/google-cloud-go v0.39.1-0.20190528154449-61166ef30553

	golang.org/x/crypto => github.com/golang/crypto v0.0.0-20190313024323-a1f597ede03a

	golang.org/x/exp => github.com/golang/exp v0.0.0-20190510132918-efd6b22b2522

	golang.org/x/lint => github.com/golang/lint v0.0.0-20190409202823-959b441ac422

	golang.org/x/net => github.com/golang/net v0.0.0-20190318221613-d196dffd7c2b

	golang.org/x/oauth2 => github.com/golang/oauth2 v0.0.0-20190523182746-aaccbc9213b0

	golang.org/x/sync => github.com/golang/sync v0.0.0-20190227155943-e225da77a7e6

	golang.org/x/sys => github.com/golang/sys v0.0.0-20190318195719-6c81ef8f67ca

	golang.org/x/text => github.com/golang/text v0.3.0

	golang.org/x/time => github.com/golang/time v0.0.0-20190308202827-9d24e82272b4

	golang.org/x/tools => github.com/golang/tools v0.0.0-20190529010454-aa71c3f32488

	google.golang.org/appengine => github.com/golang/appengine v1.6.1-0.20190515044707-311d3c5cf937

	google.golang.org/genproto => github.com/google/go-genproto v0.0.0-20190522204451-c2c4e71fbf69

	google.golang.org/grpc => github.com/grpc/grpc-go v1.21.0

)

go 1.13

require (
	github.com/aliyun/aliyun-oss-go-sdk v2.0.3+incompatible
	github.com/baiyubin/aliyun-sts-go-sdk v0.0.0-20180326062324-cfa1a18b161f // indirect
	github.com/clod-moon/goconf v0.0.0-20191014062510-03cddbcd7da9
	github.com/dchest/captcha v0.0.0-20170622155422-6a29415a8364
	github.com/dgrijalva/jwt-go v3.2.0+incompatible
	github.com/gin-gonic/gin v1.4.0
	github.com/go-ego/cedar v0.0.0-20191004180323-cb5a33716058 // indirect
	github.com/go-ego/gse v0.0.0-20191023154054-6406076ccec8
	github.com/go-sql-driver/mysql v1.4.1
	github.com/json-iterator/go v1.1.6
	github.com/mozillazg/go-pinyin v0.15.0
	github.com/patrickmn/go-cache v2.1.0+incompatible
	github.com/satori/go.uuid v1.2.0 // indirect
	github.com/sbwhitecap/tqdm v0.0.0-20170314014342-7929e3102f57
	github.com/stretchr/testify v1.3.0
	github.com/tensorflow/tensorflow v2.0.0+incompatible
	github.com/unrolled/secure v1.0.5
	golang.org/x/crypto v0.0.0-20190308221718-c2843e01d9a2
	golang.org/x/time v0.0.0-00010101000000-000000000000 // indirect
	google.golang.org/appengine v0.0.0-00010101000000-000000000000 // indirect
)
