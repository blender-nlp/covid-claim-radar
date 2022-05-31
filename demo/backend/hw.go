package main

import (
	// "backend/cache"
	// "sort"
	"strings"
	"math"

	// "backend/cookie"
	// "backend/database"
	// "backend/ossUpload"
	// "backend/recommend"
	// "backend/search"
	"backend/demo_utils"

	// "backend/utils"
	// "math/rand"

	"fmt"
	"strconv"
	// "time"

	// "backend/word"

	"github.com/gin-gonic/gin"
	// "github.com/go-ego/gse"
	_ "github.com/go-sql-driver/mysql"
	// "github.com/unrolled/secure"
	"backend/demo_router"
	// goini "github.com/clod-moon/goconf"
)

func isContain(items []string, item string) bool {
	for _, eachItem := range items {
		if eachItem == item {
			return true
		}
	}
	return false
}

func isIntersect(itemsA []string, itemsB []string) bool {
	for _, eachItemA := range itemsA {
		for _, eachItemB := range itemsB {
			if eachItemB == eachItemA{
				return true
			}
		}
	}
	return false
}

func generateTopic(Slice []demo_utils.Claim) []demo_utils.TopicFilter {
    keys := make(map[string]bool)
    list := []demo_utils.TopicFilter{}
 
    // If the key(values of the slice) is not equal
    // to the already present value in new slice (list)
    // then we append it. else we jump on another element.
    for _, entry := range Slice {
        if _, value := keys[entry.Topic]; !value {
            keys[entry.Topic] = true
			var topic demo_utils.TopicFilter
			topic.Text = entry.Topic
			topic.Value = entry.Topic
            list = append(list, topic)
        }
    }
    return list
}

func RouterSet() *gin.Engine {
	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()
	claims := demo_utils.JsonParse("./demo_files/claims.json")
	topic := generateTopic(claims)

	r.GET("/", func(c *gin.Context) {
		demo_router.SetHeader(c)

		msg := c.DefaultQuery("msg", "000")
		fmt.Println(msg)
		c.JSON(200, gin.H{
			"message": "hello world! --sent by GO",
		})
	})

	r.GET("/backend_search", func(c *gin.Context) {
		demo_router.SetHeader(c)

		sent_per_page := 10
		affiliation := c.DefaultQuery("affiliation", "")
		claimer := c.DefaultQuery("claimer", "")
		ent_ids := strings.Split(claimer, ",")
		object := c.DefaultQuery("object", "")
		location := c.DefaultQuery("location", "")
		filter_topics := c.DefaultQuery("filterTopic", "")
		filter_topics_list := strings.Split(filter_topics, ",")
		// for i:= range claims[0].Render_text {
		// 	fmt.Println(claims[0].Render_text[i].Process_Arg)
		// }
		// fmt.Println(claimer)
		// fmt.Println(ent_ids)
		// fmt.Println(filter_topics_list)
		// fmt.Println(len(filter_topics_list))
		str_page := c.DefaultQuery("page", "1")
		page, _ := strconv.Atoi(str_page)

		var results []demo_utils.Claim
		for i := range claims {
			claim := claims[i]
			affiliation_match := ((affiliation == "") || (affiliation == "None") || (claim.Affiliation == affiliation))
			claimer_match := ((claimer == "") || (claimer == "None") || (isIntersect(claim.Claimer_search_key, ent_ids)))
			object_match := ((object == "") || (object == "None") || (claim.X_var == object))
			location_match := ((location == "") || (location == "None") || (claim.Location == location))
			topic_match := ((filter_topics == "") || (filter_topics == "None") || (isContain(filter_topics_list, claim.Topic)))
			if location_match && object_match && claimer_match && affiliation_match && topic_match {
				results = append(results,claim)
			}
		}
		
		var status string
		status = "success"

		if len(results) == 0 {
			status = "fail"
		}

		var pages int
		pages = int(math.Ceil( float64(len(results)) / float64(sent_per_page)))

		// topic := generateTopic(results)
		// topic := generateTopic(claims)

		c.JSON(200, gin.H{
			"result": results[int((page-1)*sent_per_page):int(math.Min(float64(page*sent_per_page),float64(len(results))))],
			"status": status,
			"pages": pages,
			"topics": topic,
		})
	})

	demo_router.OptionRouter(r)
	demo_router.SourceRouter(r)

	return r
}

func main() {
	r := RouterSet()
	r.Run(":8080")
}
