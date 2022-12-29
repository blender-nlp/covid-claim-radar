<template>
  <div>
    <div style="margin-top: 16%;">
      <span class="covid-title">Covid-19 Claim Radar</span>
      <!-- <search-input @doSearch="search"></search-input> -->
      <div style="margin-left: 15%">
        <div id="div-left-search"><el-row><span class="covid-text">Claimer</span></el-row><el-row><claimer-drop-down @claimerChange="myClaimerChange" :value="claimer"></claimer-drop-down></el-row></div>
        <div id="div-left-search"><el-row><span class="covid-text">Affiliation</span></el-row><el-row><affliation-drop-down @affiliationChange="myAffiliationChange" :value="affiliation"></affliation-drop-down></el-row></div>
        <div id="div-left-search"><el-row><span class="covid-text">Object</span></el-row><el-row><object-drop-down @objectChange="myObjectChange" :value="object"></object-drop-down></el-row></div>
        <div id="div-left-search"><el-row><span class="covid-text">Location</span></el-row><el-row><location-drop-down @locationChange="myLocationChange" :value="location"></location-drop-down></el-row></div>
        <div id="div-left-search"><el-row><span class="covid-text">Topic</span></el-row><el-row><topic-drop-down @topicChange="myTopicChange" :value="topic"></topic-drop-down></el-row></div>
        <div id="div-left-search"><el-row><span class="covid-text">&nbsp;</span></el-row><el-row><el-button type="primary" @click.native="search">Search</el-button></el-row></div>
        <!-- <el-col :span="3" style="margin-left: 33%; margin-top: 2%"><el-button type="primary" @click.native="search">Search</el-button></el-col> -->
      </div>
      <br style="clear: both;">
      <div id="div-top-search">
        <el-button type="primary" @click.native="goExtract">Real-Time Extaction Interface</el-button>
      </div>
      <!-- <h2 v-show="err"> Oops! 找不到你想要的Gif </h2> -->
      <!-- <img-gallery v-bind:imgList="imgList"></img-gallery> -->
    </div>
  </div>
</template>
<script>
// import SearchInput from '../components/SearchInput.vue'
// import ImgGallery from '../components/ImgGallery.vue'
import ClaimerDropDown from '../components/SearchComponent/ClaimerDropDown.vue'
import AffliationDropDown from '../components/SearchComponent/AffliationDropDown.vue'
import ObjectDropDown from '../components/SearchComponent/ObjectDropDown.vue'
import LocationDropDown from '../components/SearchComponent/LocationDropDown.vue'
import TopicDropDown from '../components/SearchComponent/TopicDropDown.vue'
import { axiosInstance } from '../axios_config.js'

export default {
  name: 'Search',
  data () {
    return {
      claimer: '',
      affiliation: '',
      object: '',
      location: '',
      topic: [],
      tablelist: []
    }
  },
  methods: {
    search: function () {
      // console.log(this.claimer)
      // console.log(this.affiliation)
      // console.log(this.entity)
      // console.log(this.location)
      axiosInstance({ url: '/backend_search?claimer=' + this.claimer + '&affiliation=' + this.affiliation + '&object=' + this.object + '&location=' + this.location + '&filterTopic=' + this.topic.join(',') }).then(response => {
        // console.log(response.data)
        if (response.data.status === 'success') {
          var list = response.data.result
          this.tablelist = list.map(function (item) {
            var t = {
              topic: item.Topic,
              claimer: item.Claimer,
              source: item.Source,
              sentence: item.Sentence,
              x_var: item.X_var,
              stance: item.Stance,
              x_var_qnode: item.X_var_qnode,
              claimer_qnode: item.Claimer_qnode,
              render_text: item.Render_text,
              news_url: item.News_url,
              news_author: item.News_author,
              template: item.Template,
              x_var_type_qnode: item.X_var_type_qnode,
              claimer_type_qnode: item.Claimer_type_qnode,
              time_attr: item.Time_attr,
              sentence_L: item.Sentence_L,
              sentence_M: item.Sentence_M,
              sentence_R: item.Sentence_R,
              equivalent_claims_text: item.Equivalent_claims_text,
              supporting_claims_text: item.Supporting_claims_text,
              refuting_claims_text: item.Refuting_claims_text,
              claimer_affiliation_identity_qnode: item.Claimer_affiliation_identity_qnode,
              claimer_affiliation_type_qnode: item.Claimer_affiliation_type_qnode,
              language: item.Lan,
              generation: item.Generation
            }
            return t
          })
        } else {
          this.tablelist = []
        }
        // console.log(response.data)
        this.$router.push({ name: 'list', params: { firstCla: this.claimer, firstAff: this.affiliation, firstObj: this.object, firstLoc: this.location, firstTab: this.tablelist, firstPages: response.data.pages, firstTopics: response.data.topics, firstFilterTopics: this.topic } })
      })
    },
    goExtract: function () {
      this.$router.push({ name: 'extract', params: { } })
    },
    myClaimerChange: function (val) {
      this.claimer = val
    },
    myAffiliationChange: function (val) {
      this.affiliation = val
    },
    myObjectChange: function (val) {
      this.object = val
    },
    myLocationChange: function (val) {
      this.location = val
    },
    myTopicChange: function (val) {
      this.topic = val
    }
  },
  components: {
    // 'search-input': SearchInput,
    'claimer-drop-down': ClaimerDropDown,
    'affliation-drop-down': AffliationDropDown,
    'object-drop-down': ObjectDropDown,
    'location-drop-down': LocationDropDown,
    'topic-drop-down': TopicDropDown
    // 'img-gallery': ImgGallery
  }
}

</script>
<style>
#div-left-search{
  float: left;
  margin-left: 3%;
}
#div-top-search{
  float: top;
  margin-top: 3%;
}
.covid-title {
  font-weight: bold;
  color: rgb(255, 255, 255);
  font-size: 64px;
}
.covid-text {
  font-weight: bold;
  color: rgb(255, 255, 255);
  font-size: 32px;
}
</style>
