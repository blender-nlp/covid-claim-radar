package demo_search

import (
	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin"
	"backend/demo_utils"
)

func SearchRouter(r *gin.Engine) {
	r.GET("/backend_search", func(c *gin.Context) {
		SetHeader(c)
		

		c.JSON(200, gin.H{
			"result": demo_utils.LoadOption("./demo_files/claimers.json"),
		})
	})
}