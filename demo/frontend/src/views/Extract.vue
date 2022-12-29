<template>
    <div style="margin-left: 2%;">
      <p align="left">
        <el-button type="text" @click.native="homeClick()" size="large"><h1>Covid-19 Claim Radar Real-Time Extraction</h1></el-button>
      </p>
      <el-input
        type="textarea"
        :rows="10"
        placeholder="Please enter your text here, such as “CDC required people to wear masks in public areas.”"
        style="margin-right: 2%;"
        v-model="text">
      </el-input>
      <p align="left" style="margin-top: 1%;">
        <el-button type="primary" @click.native="extract" :loading.sync="fullscreenLoading">Extract (Fast)</el-button>
        <el-button type="primary" @click.native="extract_all" :loading.sync="fullscreenLoading">Extract (Complete)</el-button>
      </p>
      <p align="left">
        <output>Output:</output>
      </p>
      <div class="circle-corner">
        <p align="left" style="margin-left: 1%;">
            <pre>{{ extracted }}</pre>
        </p>
      </div>
      <!-- <pre>{{ extracted }}</pre> -->
    </div>
</template>
<script>

import axios from 'axios'
axios.defaults.withCredentials = false
const axiosInstance = axios.create({
  method: 'get',
  baseURL: 'http://18.221.187.153:5500',
  timeout: 5000
})

export default {
  name: 'Extract',
  props: {
  },
  created () {
  },
  data () {
    return {
      text: '',
      extracted: ' ',
      fullscreenLoading: false
    }
  },
  methods: {
    extract: function () {
      this.fullscreenLoading = true
      // this.extracted = this.pretty('{"id":1,"name":"A green door","price":12.50,"tags":["home","green"]}')
      axiosInstance({ url: '/claim?rsd=' + this.text }).then(response => {
        this.extracted = response.data
      })
      this.fullscreenLoading = false
    },
    extract_all: function () {
      this.fullscreenLoading = true
      // this.extracted = this.pretty('{"id":1,"name":"A green door","price":12.50,"tags":["home","green"]}')
      axiosInstance({ url: '/claim_all?rsd=' + this.text }).then(response => {
        this.extracted = response.data
      })
      this.fullscreenLoading = false
    },
    pretty: function (value) {
      return JSON.stringify(JSON.parse(value), null, 2)
    },
    homeClick: function () {
      this.$router.push({ name: 'search', params: { } })
    }
  },
  components: {
  }
}
</script>
<style>
  .circle-corner{
    border-top-right-radius: 10px;
    border-top-left-radius: 10px;
    border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px;
    margin-right: 2%;
    background-color: rgb(220,220,220,0.4)
  }
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
  output {
    margin-top: 2%;
    text-align: left;
    font-weight: bold;
    color: rgb(0,0,0);
    font-size: 25px;
  }
  .covid-text-black {
    font-weight: bold;
    color: rgb(0,0,0);
    font-size: 16px;
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
