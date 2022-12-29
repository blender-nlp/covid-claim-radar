package demo_router

import (
	"github.com/gin-gonic/gin"
	"backend/demo_utils"
)

func SetHeader(c *gin.Context) {
	c.Header("Access-Control-Allow-Origin", "*")
	c.Header("Access-Control-Allow-Credentials", "true")
	c.Header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE")
	c.Header("Access-Control-Allow-Headers", "Action, Module, X-PINGOTHER, Content-Type, Content-Disposition")
}

// TODO: Could optimizer, do not need to LoadOption every time, could cache
func OptionRouter(r *gin.Engine) {
	r.GET("/claimer-option", func(c *gin.Context) {
		SetHeader(c)
		c.JSON(200, gin.H{
			"result": demo_utils.LoadOption("./demo_files/claimers.json"),
		})
	})
	r.GET("/affiliation-option", func(c *gin.Context) {
		SetHeader(c)
		c.JSON(200, gin.H{
			"result": demo_utils.LoadOption("./demo_files/affiliation.json"),
		})
	})
	r.GET("/object-option", func(c *gin.Context) {
		SetHeader(c)
		c.JSON(200, gin.H{
			"result": demo_utils.LoadOption("./demo_files/object.json"),
		})
	})
	r.GET("/location-option", func(c *gin.Context) {
		SetHeader(c)
		c.JSON(200, gin.H{
			"result": demo_utils.LoadOption("./demo_files/location.json"),
		})
	})
	r.GET("/topic", func(c *gin.Context) {
		SetHeader(c)
		c.JSON(200, gin.H{
			"result": demo_utils.LoadOption("./demo_files/topic.json"),
		})
	})
	r.GET("/topic-option", func(c *gin.Context) {
		SetHeader(c)
		c.JSON(200, gin.H{
			"result": demo_utils.LoadOption("./demo_files/topic_option.json"),
		})
	})
}

func SourceRouter(r *gin.Engine) {
	r.GET("/backend_source", func(c *gin.Context) {
		SetHeader(c)
		source := c.DefaultQuery("source", "")
		c.JSON(200, gin.H{
			"result": demo_utils.LoadSource(source),
		})
	})
}