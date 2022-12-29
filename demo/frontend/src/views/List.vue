<template>
    <div style="margin-left: 2%;">
        <!-- <h1>Covid-19 Claim Radar</h1> -->
        <p align="left">
          <el-button type="text" @click.native="homeClick()" size="large"><h1>Covid-19 Claim Radar</h1></el-button>
        </p>
        <!-- <search-input @doSearch="search"></search-input> -->
        <div style="margin-left: 0%">
            <div id="div-left"><el-row><span class="covid-text-black">Claimer</span></el-row><el-row><claimer-drop-down @claimerChange="myClaimerChange" :value="claimer"></claimer-drop-down></el-row></div>
            <div id="div-left"><el-row><span class="covid-text-black">Claimer Affiliation</span></el-row><el-row><affliation-drop-down  @affiliationChange="myAffiliationChange" :value="affiliation"></affliation-drop-down></el-row></div>
            <div id="div-left"><el-row><span class="covid-text-black">Claim Object</span></el-row><el-row><object-drop-down  @objectChange="myObjectChange" :value="object"></object-drop-down></el-row></div>
            <div id="div-left"><el-row><span class="covid-text-black">Location</span></el-row><el-row><location-drop-down  @locationChange="myLocationChange" :value="location"></location-drop-down></el-row></div>
            <div id="div-left"><el-row><span class="covid-text-black">Topic</span></el-row><el-row><topic-drop-down  @topicChange="myTopicChange" :value="filterTopics"></topic-drop-down></el-row></div>
            <div id="div-left"><el-row><span class="covid-text-white">&nbsp;</span></el-row><el-row><el-button type="primary" @click.native="search">Search</el-button></el-row></div>
            <!-- <el-row>
            <el-col><el-row><span class="covid-text-black">Claimer</span></el-row><el-row><claimer-drop-down @claimerChange="myClaimerChange" :value="claimer"></claimer-drop-down></el-row></el-col>
            <el-col><el-row><span class="covid-text-black">Claimer Affiliation</span></el-row><el-row><affliation-drop-down  @affiliationChange="myAffiliationChange" :value="affiliation"></affliation-drop-down></el-row></el-col>
            <el-col><el-row><span class="covid-text-black">Claim Object</span></el-row><el-row><object-drop-down  @objectChange="myObjectChange" :value="object"></object-drop-down></el-row></el-col>
            <el-col><el-row><span class="covid-text-black">Location</span></el-row><el-row><location-drop-down  @locationChange="myLocationChange" :value="location"></location-drop-down></el-row></el-col>
            <el-col><el-row><span class="covid-text-black">Topic</span></el-row><el-row><topic-drop-down  @topicChange="myTopicChange" :value="filterTopics"></topic-drop-down></el-row></el-col>
            <el-col><el-row><span class="covid-text-white">Search</span></el-row><el-row><el-button type="primary" @click.native="search">Search</el-button></el-row></el-col>
            </el-row> -->
        </div>
        <span class="tip"> Tip: Click table headers to sort by columns</span>
        <!-- <claim-list :tableDataProps="tablelist" @rowClicked="handleRowClick" @sourceClicked="handleSourceClick" :filterNameItem="allTopics" @topicFilter="handleTopicFilter" :filterVal="filterTopics" ref="claim_list_child"></claim-list> -->
        <claim-list :tableDataProps="tablelist" @rowClicked="handleRowClick" @sourceClicked="handleSourceClick" @headerClicked="handleHeaderClick" ref="claim_list_child"></claim-list>
        <el-pagination
            background
            layout="prev, pager, next"
            @current-change="switchPage"
            :current-page.sync="page"
            style="margin-top: 1%; margin-bottom: 1%;"
            :page-count="pages">
        </el-pagination>
        <!-- hide-on-single-page="true" -->
        <el-dialog
        :visible.sync="dialogVisible"
        :modalAppendToBody="false"
        title="Claim Details"
        width="80%">
          <!-- <div class="dialog-title-space"><dialog-title>{{ sentence }}</dialog-title></div> -->
          <div class="dialog-title-space">
            <dialog-title style="vertical-align: bottom">{{ sentence_L }}</dialog-title>
            <dialog-title-highlight style="vertical-align: bottom">{{ sentence_M }}</dialog-title-highlight>
            <dialog-title style="vertical-align: bottom">{{ sentence_R }}</dialog-title>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Topic</dialog-category></div>
            <div class="div-size-text"><dialog-text>{{ topic }}</dialog-text></div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Template</dialog-category></div>
            <div class="div-size-text"><dialog-text>{{ template }}</dialog-text></div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Language</dialog-category></div>
            <div class="div-size-text"><dialog-text>{{ language }}</dialog-text></div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Generation</dialog-category></div>
            <div class="div-size-text"><dialog-text>{{ generation }}</dialog-text></div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Object</dialog-category></div>
            <div class="div-size-text">
              <dialog-text>
                {{ x_var }} <br />
                [Identity Qnode] <el-button v-if="x_var_qnode.startsWith('Q')" type="text" @click.native="hrefClick(x_var_qnode)" size="mini"><dialog-text style="color:blue; text-decoration:underline;">{{ x_var_qnode }}</dialog-text></el-button><dialog-text  v-else class="text-wrapper" plain>{{ x_var_qnode }}</dialog-text> <br />
                [Type Qnode] <el-button v-if="x_var_type_qnode.startsWith('Q')" type="text" @click.native="hrefClick(x_var_type_qnode)" size="mini"><dialog-text style="color:blue; text-decoration:underline;">{{ x_var_type_qnode }}</dialog-text></el-button> <dialog-text  v-else class="text-wrapper" plain>{{ x_var_type_qnode }}</dialog-text>
              </dialog-text>
            </div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Claimer</dialog-category></div>
            <div class="div-size-text">
              <dialog-text>
                {{ show_claimer }} <br />
                [Identity Qnode] <el-button v-if="show_claimer_qnode.startsWith('Q')" type="text" @click.native="hrefClick(show_claimer_qnode)" size="mini"><dialog-text style="color:blue; text-decoration:underline;">{{ show_claimer_qnode }}</dialog-text></el-button><dialog-text  v-else class="text-wrapper" plain>{{ show_claimer_qnode }}</dialog-text> <br />
                [Type Qnode] <el-button v-if="show_claimer_type_qnode.startsWith('Q')" type="text" @click.native="hrefClick(show_claimer_type_qnode)" size="mini"><dialog-text style="color:blue; text-decoration:underline;">{{ show_claimer_type_qnode }}</dialog-text></el-button><dialog-text  v-else class="text-wrapper" plain>{{ show_claimer_type_qnode }}</dialog-text>
              </dialog-text>
            </div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Affiliation</dialog-category></div>
            <div class="div-size-text">
              <dialog-text v-if="affiliation !== ''">
                {{ affiliation }} <br />
                [Identity Qnode] <el-button v-if="claimer_affiliation_identity_qnode.startsWith('Q')" type="text" @click.native="hrefClick(claimer_affiliation_identity_qnode)" size="mini"><dialog-text style="color:blue; text-decoration:underline;">{{ claimer_affiliation_identity_qnode }}</dialog-text></el-button><dialog-text  v-else class="text-wrapper" plain>{{ claimer_affiliation_identity_qnode }}</dialog-text> <br />
                [Type Qnode] <el-button v-if="claimer_affiliation_type_qnode.startsWith('Q')" type="text" @click.native="hrefClick(claimer_affiliation_type_qnode)" size="mini"><dialog-text style="color:blue; text-decoration:underline;">{{ claimer_affiliation_type_qnode }}</dialog-text></el-button><dialog-text  v-else class="text-wrapper" plain>{{ claimer_affiliation_type_qnode }}</dialog-text>
              </dialog-text>
              <dialog-text v-else>None</dialog-text>
              </div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Location</dialog-category></div>
            <div class="div-size-text"><dialog-text v-if="location !== ''">{{ location }}</dialog-text><dialog-text v-else>None</dialog-text></div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Time</dialog-category></div>
            <div class="div-size-text"><dialog-text v-if="time_attr !== ''" style="white-space: pre-wrap;">{{ time_attr }}</dialog-text><dialog-text v-else>None</dialog-text></div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Stance</dialog-category></div>
            <div class="div-size-text"><dialog-text>{{ stance }}</dialog-text></div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Author</dialog-category></div>
            <div class="div-size-text"><dialog-text v-if="news_author !== ''">{{ news_author }}</dialog-text><dialog-text v-else>None</dialog-text></div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Associate <br /> Knowledge Elements</dialog-category></div>
            <div class="div-size-text">
              <span v-for="(item,index) in renderText" :key="index" style="vertical-align: bottom">
                <el-tooltip placement="bottom" :disabled="!item.Tooltip">
                  <div slot="content">
                    <div style="display:flex;">
                      <div style="text-align: left; margin:10px; width: 50px;">Type</div>
                      <div style="text-align: left; margin:10px;">{{ item.Event }}</div>
                    </div>
                    <div style="display:flex;">
                      <div style="text-align: left; margin:10px; width: 50px;">Value</div>
                      <div style="text-align: left; margin:10px;">{{ item.Relation }}</div>
                    </div>
                    <div style="display:flex;">
                      <div style="text-align: left; margin:10px; width: 50px;">Offsets</div>
                      <div style="text-align: left; margin:10px;">{{ item.Offset }}</div>
                    </div>
                    <div style="display:flex;">
                      <div style="text-align: left; margin:10px; width: 50px;">Url</div>
                      <div style="text-align: left; margin:10px;">{{ item.Url }}</div>
                    </div>
                    <div v-if="item.Class !== 'class-entity'" style="display:flex;">
                      <div style="text-align: left; margin:10px; width: 50px;">Args</div>
                      <div v-if="item.Arg !== ''">
                        <div v-for="(arg,argindex) in item.Process_Arg" :key="argindex" style="text-align: left; margin:10px; text-decoration:underline;" @mouseover="showHighlight(arg.Offset)"  @mouseleave="hideHighlight(arg.Offset)"><span class="text-wrapper">{{ arg.Role }}:   {{ arg.Word }}</span></div>
                      </div>
                      <div v-else>
                        <div style="text-align: left; margin:10px; width: 50px;">None</div>
                      </div>
                    </div>
                  </div>
                  <span>
                    <span :ref="item.Offset" :class="[item.Class]" class="text-wrapper" style="vertical-align: bottom">{{ item.Text }}</span>
                    <span v-if="item.Tooltip" :class="[item.Class+'-2']" class="text-wrapper" style="vertical-align: bottom"> [{{ item.Relation }}] </span>
                  </span>
                </el-tooltip>
              </span>
            </div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Equivalent <br />Claims</dialog-category></div>
            <div class="div-size-text"><dialog-text v-if="equivalent_claims_text !== ''" style="white-space: pre-wrap;"> {{ equivalent_claims_text }}</dialog-text><dialog-text v-else style="white-space: pre-wrap;">None</dialog-text></div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Supporting <br />Claims</dialog-category></div>
            <div class="div-size-text"><dialog-text v-if="supporting_claims_text !== ''" style="white-space: pre-wrap;"> {{ supporting_claims_text }}</dialog-text><dialog-text v-else style="white-space: pre-wrap;">None</dialog-text></div>
          </div>
          <div style="display: flex;">
            <div class="div-size"><dialog-category>Refuting <br />Claims</dialog-category></div>
            <div class="div-size-text"><dialog-text v-if="refuting_claims_text !== ''" style="white-space: pre-wrap;"> {{ refuting_claims_text }}</dialog-text><dialog-text v-else style="white-space: pre-wrap;">None</dialog-text></div>
          </div>
          <!-- <div style="display: flex;">
            <div class="div-size"><dialog-category>Related Claims</dialog-category></div>
            <div class="div-size-text"><dialog-text>{{ related_claims }}</dialog-text></div>
          </div> -->

        </el-dialog>

        <el-dialog
        :visible.sync="sourceVisible"
        :modalAppendToBody="false"
        title="Source Text"
        width="80%"
        center>
          <dialog-text class="text-wrapper" plain>{{ sourceText }}</dialog-text>
        </el-dialog>
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
import ClaimList from '../components/ListComponent/ClaimList.vue'
import { axiosInstance } from '../axios_config.js'

export default {
  name: 'List',
  props: {
    firstCla: {
      type: String,
      default: ''
    },
    firstAff: {
      type: String,
      default: ''
    },
    firstObj: {
      type: String,
      default: ''
    },
    firstLoc: {
      type: String,
      default: ''
    },
    firstTab: {
      type: Promise,
      default: []
    },
    firstPages: {
      type: String,
      default: '1'
    },
    firstTopics: {
      type: Promise,
      default: []
    },
    firstFilterTopics: {
      type: Promise,
      default: []
    }
  },
  created () {
    // console.log(this.$route.params)
    // console.log(this.firstCla)
    this.claimer = this.firstCla
    this.affiliation = this.firstAff
    this.object = this.firstObj
    this.location = this.firstLoc
    this.tablelist = this.firstTab
    this.pages = this.firstPages
    this.allTopics = this.firstTopics
    this.filterTopics = this.firstFilterTopics
    this.search()
  },
  data () {
    return {
      claimer: '',
      affiliation: '',
      object: '',
      location: '',
      tablelist: [],
      // first: true,
      pages: 1,
      page: 1,
      dialogVisible: false,
      topic: '',
      source: '',
      sentence: '',
      sentence_L: '',
      sentence_M: '',
      sentence_R: '',
      show_claimer: '',
      x_var: '',
      stance: '',
      related_claims: [],
      x_var_qnode: '',
      show_claimer_qnode: '',
      topicVisible: false,
      allTopics: [],
      filterTopics: [],
      sourceText: '',
      sourceVisible: false,
      renderText: [{ 'Event': 'Empty' }, { 'Offset': 'Empty' }, { 'Relation': 'Empty' }, { 'Text': 'Empty' }, { 'Url': 'Empty' }, { 'Class': 'class-associate' }],
      news_url: '',
      news_author: '',
      template: '',
      x_var_type_qnode: '',
      show_claimer_type_qnode: '',
      time_attr: '',
      equivalent_claims_text: '',
      supporting_claims_text: '',
      refuting_claims_text: '',
      claimer_affiliation_identity_qnode: '',
      claimer_affiliation_type_qnode: '',
      language: '',
      generation: '',
      sort_label: 'Topic'
    }
  },
  // computed: {
  //   realClaimer: function () {
  //     // return this.first ? this.firstCla : this.claimer
  //     return this.claimer
  //   },
  //   realAff: function () {
  //     // return this.first ? this.firstAff : this.affiliation
  //     return this.affiliation
  //   },
  //   realEnt: function () {
  //     // return this.first ? this.firstEnt : this.entity
  //     return this.entity
  //   },
  //   realLoc: function () {
  //     // return this.first ? this.firstLoc : this.location
  //     return this.location
  //   },
  //   realTab: function () {
  //     // return this.first ? this.firstTab : this.tablelist
  //     return this.tablelist
  //   },
  //   realPages: function () {
  //     // return this.first ? this.firstPages : this.pages
  //     return this.pages
  //   },
  //   realAllTopics: function () {
  //     // return this.first ? this.firstTopics : this.allTopics
  //     return this.allTopics
  //   }
  // },
  methods: {
    search: function () {
      this.page = 1
      // this.$set(this.data, this.page, 1)
      // this.filterTopics = []
      // this.$refs.claim_list_child.clearTopicFilter()
      axiosInstance({ url: '/backend_search?claimer=' + this.claimer + '&affiliation=' + this.affiliation + '&object=' + this.object + '&location=' + this.location + '&filterTopic=' + this.filterTopics.join(',') + '&sort=' + this.sort_label }).then(response => {
        // console.log(response.data)
        // this.first = false
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
          this.pages = response.data.pages
        } else {
          this.tablelist = []
          this.pages = 1
        }
        this.allTopics = response.data.topics
      })
      // console.log(this.pages)
    },
    switchPage: function (val) {
      axiosInstance({ url: '/backend_search?claimer=' + this.claimer + '&affiliation=' + this.affiliation + '&object=' + this.object + '&location=' + this.location + '&page=' + val + '&filterTopic=' + this.filterTopics.join(',') + '&sort=' + this.sort_label }).then(response => {
        // console.log(response.data)
        // this.first = false
        if (response.data.status === 'success') {
          this.pages = response.data.pages
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
          this.pages = 1
        }
        this.allTopics = response.data.topics
      })
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
      this.filterTopics = val
    },
    handleRowClick: function (content) {
      // console.log(content.sentence)
      // console.log(content.render_text)
      this.sentence = content.sentence
      this.topic = content.topic
      this.show_claimer = content.claimer
      this.x_var = content.x_var
      this.stance = content.stance
      this.show_claimer_qnode = content.claimer_qnode
      this.x_var_qnode = content.x_var_qnode
      this.renderText = content.render_text
      this.news_url = content.news_url
      this.news_author = content.news_author
      this.template = content.template
      this.x_var_type_qnode = content.x_var_type_qnode
      this.show_claimer_type_qnode = content.claimer_type_qnode
      this.time_attr = content.time_attr
      this.equivalent_claims_text = content.equivalent_claims_text
      this.supporting_claims_text = content.supporting_claims_text
      this.refuting_claims_text = content.refuting_claims_text
      this.claimer_affiliation_identity_qnode = content.claimer_affiliation_identity_qnode
      this.claimer_affiliation_type_qnode = content.claimer_affiliation_type_qnode
      this.language = content.language
      this.generation = content.generation
      this.sentence_L = content.sentence_L
      this.sentence_M = content.sentence_M
      this.sentence_R = content.sentence_R
      // console.log(content.x_var_qnode)
      this.dialogVisible = true
    },
    handleHeaderClick: function (label) {
      this.sort_label = label
      if (label === 'Claim Object') {
        this.sort_label = 'Object'
      }
      this.search()
    },
    hrefClick: function (qnode) {
      window.open('https://www.wikidata.org/wiki/' + qnode)
    },
    homeClick: function () {
      this.$router.push({ name: 'search', params: { } })
    },
    handleTopicFilter: function (filterTopics) {
      this.page = 1
      this.filterTopics = filterTopics
      axiosInstance({ url: '/backend_search?claimer=' + this.claimer + '&affiliation=' + this.affiliation + '&object=' + this.object + '&location=' + this.location + '&filterTopic=' + filterTopics.join(',') + '&sort=' + this.sort_label }).then(response => {
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
          this.pages = response.data.pages
        } else {
          this.tablelist = []
          this.pages = 1
        }
      })
    },
    handleSourceClick: function (content) {
      // axiosInstance({ url: '/backend_source?source=' + content.source }).then(response => {
      //   this.sourceText = response.data.result.data
      // })
      // this.sourceVisible = true
      window.open(content.news_url)
    },
    showHighlight: function (argOffsets) {
      for (let i = 0; i < argOffsets.length; i++) {
        // console.log(argOffsets[i])
        // console.log(this.$refs)
        // console.log(this.$refs[argOffsets[i]])
        this.$refs[argOffsets[i]][0].classList.add('arg-highlight')
      }
    },
    hideHighlight: function (argOffsets) {
      for (let i = 0; i < argOffsets.length; i++) {
        this.$refs[argOffsets[i]][0].classList.remove('arg-highlight')
      }
    }
    // handleTopicClick: function () {
    //   this.topicVisible = true
    //   axiosInstance({ url: '/topic' }).then(response => {
    //     this.all_topics = response.data.result
    //   })
    // }
  },
  components: {
    // 'search-input': SearchInput,
    'claimer-drop-down': ClaimerDropDown,
    'affliation-drop-down': AffliationDropDown,
    'object-drop-down': ObjectDropDown,
    'location-drop-down': LocationDropDown,
    'topic-drop-down': TopicDropDown,
    'claim-list': ClaimList
    // 'img-gallery': ImgGallery
  }
//   mounted () {
//     this.setData()
//   },
//   watch: {
//     '$route': 'setData'
//   }
}
</script>
<style>
  #div-left{
      float: left;
      margin-left: 10px;
  }
  h1 {
    margin-top: 2%;
    text-align: left;
    font-weight: bold;
    color: rgb(0,0,0);
    font-size: 32px;
  }
  .covid-text-black {
    font-weight: bold;
    color: rgb(0,0,0);
    font-size: 16px;
  }
  .tip {
    color: rgb(0,0,0);
    font-size: 13px;
  }
  .covid-text-white {
    font-weight: bold;
    color: rgb(255,255,255);
    font-size: 16px;
  }
  dialog-title {
    color: rgb(0,0,0);
    font-size: 18px;
  }
  dialog-title-highlight {
    color: rgb(0,0,0);
    background-color: rgb(255,255,0,0.4);
    font-size: 18px;
  }
  .dialog-title-space {
    margin: 20px;
  }
  dialog-category {
    font-weight: bold;
    color: rgb(0,0,0);
    font-size: 15px;
    /* white-space: pre-wrap; */
  }
  dialog-text {
    color: rgb(0,0,0);
    font-size: 15px;
  }
  .div-size {
    width: 200px;
    /* height: 40px; */
    margin: 10px;
    text-align: left;
  }
  .div-size-text {
    width: 70%;
    /* height: 40px; */
    margin: 10px;
    text-align: left;
  }
  .text-wrapper {
    word-break: break-all;
    word-wrap: break-word;
    white-space: pre-wrap;
  }
  .class-black {
    color: black;
    font-size: 15px;
  }
  .class-event {
    background-color: rgb(255, 0, 0, 0.4);
    /* color: black; */
    font-size: 15px;
  }
  .class-event-2 {
    color: rgb(255, 0, 0);
    font-size: 15px;
  }
  .class-entity {
    background-color: rgb(0, 0, 255, 0.4);
    /* color: black; */
    font-size: 15px;
  }
  .class-entity-2 {
    color: blue;
    font-size: 15px;
  }
  .class-relation {
    background-color: rgb(0, 255, 0, 0.4);
    /* color: black; */
    font-size: 15px;
  }
  .class-relation-2 {
    color: green;
    font-size: 15px;
  }
  .arg-highlight {
    background-color: yellow;
  }
</style>
