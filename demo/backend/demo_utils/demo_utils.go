package demo_utils

import (
	"strings"
	"io/ioutil"
	// "github.com/sbwhitecap/tqdm"
	// "fmt"

	jsoniter "github.com/json-iterator/go"
)

type CusArg struct {
	Role 		string
	Offset   	[]string
	Word		string
}

type ArgList []CusArg

// func (m *ArgList) UnmarshalJSON(b []byte) error {
// 	if *m == nil {
//         *m = make(ArgList,10)
//     }

//     if err := jsoniter.Unmarshal(b, &m); err != nil {
//         return err
//     }
//     return nil
// }

type RenderText struct {
	Event        string
	Text		 string
	Relation     string
	Offset		 string
	Url 		 string
	Tooltip		 bool
	Class        string
	St			 int
	Ed 		 	 int
	Arg 		 string
	Process_Arg  ArgList
}

type Claim struct {
	Topic      	  string
	Claimer    	  string
	Source     	  string
	Sentence   	  string
	Affiliation   string
	Location	  string
	Entity		  string
	X_var		  string
	Stance        string
	X_var_qnode   string
	X_var_type_qnode string
	Claimer_qnode string
	Claimer_type_qnode string
	News_url	  string
	News_author   string
	Render_text   []RenderText
	Template	  string
	Time_attr     string
	Sentence_L    string
	Sentence_M    string
	Sentence_R    string
	Claimer_search_key []string
	Equivalent_claims_text string
	Supporting_claims_text string
	Refuting_claims_text   string
	Claimer_affiliation_identity_qnode string
	Claimer_affiliation_type_qnode string
	Lan			  string
	Generation	  string
}

type TopicFilter struct {
	Text		  string `json:"text"`
	Value		  string `json:"value"`
}

type Option struct {
	Label string `json:"label"`
	Value string `json:"value"`
}

type Source struct {
	Data string `json:"data"`
}

func JsonParse(path0 string) []Claim {
	var claims []Claim

	bytes, _ := ioutil.ReadFile(path0)
	jsonData := jsoniter.Get(bytes, "claims")
	_data := []byte(jsonData.ToString())

	size := jsonData.Size()
	claims = append(claims, make([]Claim, size)...)
	for i := 0; i < size; i++ {
		claims[i].Topic = jsoniter.Get(_data, i, "topic").ToString()
		claims[i].Claimer = jsoniter.Get(_data, i, "claimer_text").ToString()
		claims[i].Source = jsoniter.Get(_data, i, "source").ToString()
		claims[i].Sentence = jsoniter.Get(_data, i, "sentence").ToString()
		claims[i].Affiliation = jsoniter.Get(_data, i, "claimer_affiliation").ToString()
		claims[i].Location = jsoniter.Get(_data, i, "location").ToString()
		claims[i].Entity = jsoniter.Get(_data, i, "entity").ToString()
		claims[i].X_var = jsoniter.Get(_data, i, "x_variable").ToString()
		claims[i].Stance = jsoniter.Get(_data, i, "stance").ToString()
		claims[i].X_var_qnode = jsoniter.Get(_data, i, "qnode_x_variable_identity").ToString()
		claims[i].X_var_type_qnode = jsoniter.Get(_data, i, "qnode_x_variable_type").ToString()
		claims[i].Claimer_qnode = jsoniter.Get(_data, i, "claimer_qnode").ToString()
		claims[i].Claimer_type_qnode = jsoniter.Get(_data, i, "claimer_type_qnode").ToString()
		claims[i].News_url = jsoniter.Get(_data, i, "news_url").ToString()
		claims[i].News_author = jsoniter.Get(_data, i, "news_author").ToString()
		jsoniter.Unmarshal([]byte(jsoniter.Get(_data, i, "render_text").ToString()), &claims[i].Render_text)


		// Process Arg
		for j:= range claims[i].Render_text {
			if claims[i].Render_text[j].Arg != ""{
				args := strings.Split(claims[i].Render_text[j].Arg, "|")
				for k:= range args {
					role_args := strings.Split(args[k], "@")
					role := role_args[0]
					offsets := role_args[1]
					word := role_args[2]
					process_word := word
					process_offsets :=strings.Split(offsets, "^")
					var processed_arg CusArg
					processed_arg.Role = role
					processed_arg.Offset = process_offsets
					processed_arg.Word = process_word
					claims[i].Render_text[j].Process_Arg = append(claims[i].Render_text[j].Process_Arg, processed_arg)
				}
			}
		}
		
		claims[i].Lan = jsoniter.Get(_data, i, "lan").ToString()
		claims[i].Generation = jsoniter.Get(_data, i, "generation").ToString()

		claims[i].Template = jsoniter.Get(_data, i, "template").ToString()
		claims[i].Time_attr = jsoniter.Get(_data, i, "time_attr").ToString()
		claims[i].Sentence_L = jsoniter.Get(_data, i, "sentence_L").ToString()
		claims[i].Sentence_M = jsoniter.Get(_data, i, "sentence_M").ToString()
		claims[i].Sentence_R = jsoniter.Get(_data, i, "sentence_R").ToString()
		claims[i].Claimer_search_key = strings.Split(jsoniter.Get(_data, i, "claimer_search_key").ToString(),",")
		claims[i].Equivalent_claims_text = jsoniter.Get(_data, i, "equivalent_claims_text").ToString()
		claims[i].Supporting_claims_text = jsoniter.Get(_data, i, "supporting_claims_text").ToString()
		claims[i].Refuting_claims_text = jsoniter.Get(_data, i, "refuting_claims_text").ToString()
		claims[i].Claimer_affiliation_identity_qnode = jsoniter.Get(_data, i, "claimer_affiliation_identity_qnode").ToString()
		claims[i].Claimer_affiliation_type_qnode = jsoniter.Get(_data, i, "claimer_affiliation_type_qnode").ToString()
		// gifs[i].Cover_url = jsoniter.Get(_data, i, "cover_url").ToString()
		// gifs[i].Oss_url = ""
		// gifs[i].Word_idx = nil
		// load_strings := strings.Split(jsoniter.Get(_data, i, "recommend").ToString(), " ")
		// for _, s := range load_strings {
		// 	load_num, _ := strconv.Atoi(s)
		// 	gifs[i].Recommend = append(gifs[i].Recommend, load_num)
		// }
	}
	return claims
}

func LoadOption(path0 string) []Option {
	var options []Option
	bytes, _ := ioutil.ReadFile(path0)
	jsoniter.Unmarshal(bytes, &options)
	return options
}

func LoadSource(sourceID string) Source {
	var source []Source
	bytes, _ := ioutil.ReadFile("./demo_files/processed_rsd/"+sourceID+".rsd.txt.json")
	jsoniter.Unmarshal(bytes, &source)
	return source[0]
}