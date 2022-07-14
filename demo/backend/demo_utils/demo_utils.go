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

// This is for direct serialization to/from json; below we
// use a proxy struct for compatibility with existing code.
// We probably should just change all the fields to be consistent
// but this was tricky in the frontend code where we had different
// uses, e.g. `this.affiliation` vs. `json.affiliation` so err on
// the safe side for now.
type JsonClaim struct {
	Topic                              string         `json:"topic"`
	Claimer_text                       string         `json:"claimer_text"`
	Source                             string         `json:"source"`
	Sentence                           string         `json:"sentence"`
	Claimer_affiliation                string         `json:"claimer_affiliation"`
	Location                           string         `json:"location"`
	Entity                             string         `json:"entity"`
	X_variable                         string         `json:"x_variable"`
	Stance                             string         `json:"stance"`
	Qnode_x_variable_identity          string         `json:"qnode_x_variable_identity"`
	Qnode_x_variable_type              string         `json:"qnode_x_variable_type"`
	Claimer_qnode                      string         `json:"claimer_qnode"`
	Claimer_type_qnode                 string         `json:"claimer_type_qnode"`
	News_url                           string         `json:"news_url"`
	News_author                        string         `json:"news_author"`
	Render_text                        []RenderText   `json:"render_text"`
	Template                           string         `json:"template"`
	Time_attr                          string         `json:"time_attr"`
	Sentence_L                         string         `json:"sentence_L"`
	Sentence_M                         string         `json:"sentence_M"`
	Sentence_R                         string         `json:"sentence_R"`
	Claimer_search_key                 string         `json:"claimer_search_key"`
	Equivalent_claims_text             string         `json:"equivalent_claims_text"`
	Supporting_claims_text             string         `json:"supporting_claims_text"`
	Refuting_claims_text               string         `json:"refuting_claims_text"`
	Claimer_affiliation_identity_qnode string         `json:"claimer_affiliation_identity_qnode"`
	Claimer_affiliation_type_qnode     string         `json:"claimer_affiliation_type_qnode"`
	Lan                                string         `json:"lan"`
	Generation                         string         `json:"generation"`
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
	bytes, err := ioutil.ReadFile(path0)
	if err != nil  {
		panic(err)
	}	
	var result map[string][]JsonClaim
	err = jsoniter.Unmarshal(bytes, &result)
	if err != nil {
		panic(err)
	}
	json_claims := result["claims"]
	size := len(json_claims)
	var claims []Claim
	claims = append(claims, make([]Claim, size)...)
	for i := range json_claims {
		json_claim := json_claims[i]
		claims[i].Topic = json_claim.Topic
		claims[i].Claimer = json_claim.Claimer_text
		claims[i].Source = json_claim.Source
		claims[i].Sentence =  json_claim.Sentence
		claims[i].Affiliation = json_claim.Claimer_affiliation
		claims[i].Location = json_claim.Location
		claims[i].Entity = json_claim.Entity
		claims[i].X_var = json_claim.X_variable
		claims[i].Stance = json_claim.Stance
		claims[i].X_var_qnode = json_claim.Qnode_x_variable_identity
		claims[i].X_var_type_qnode = json_claim.Qnode_x_variable_type
		claims[i].Claimer_qnode = json_claim.Claimer_qnode
		claims[i].Claimer_type_qnode = json_claim.Claimer_type_qnode
		claims[i].News_url = json_claim.News_url
		claims[i].News_author = json_claim.News_author
		claims[i].Render_text = json_claim.Render_text
		
		// Process Arg
		for j:= range claims[i].Render_text {
			if claims[i].Render_text[j].Arg != "" {
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

		claims[i].Lan = json_claim.Lan
		claims[i].Generation = json_claim.Generation

		claims[i].Template = json_claim.Template
		claims[i].Time_attr = json_claim.Time_attr
		claims[i].Sentence_L = json_claim.Sentence_L
		claims[i].Sentence_M = json_claim.Sentence_M
		claims[i].Sentence_R = json_claim.Sentence_R
		claims[i].Claimer_search_key = strings.Split(json_claim.Claimer_search_key, ",")
		claims[i].Equivalent_claims_text = json_claim.Equivalent_claims_text
		claims[i].Supporting_claims_text = json_claim.Supporting_claims_text
		claims[i].Refuting_claims_text = json_claim.Refuting_claims_text
		claims[i].Claimer_affiliation_identity_qnode = json_claim.Claimer_affiliation_identity_qnode
		claims[i].Claimer_affiliation_type_qnode = json_claim.Claimer_affiliation_type_qnode
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
