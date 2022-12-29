<template>
  <div>
    <p v-show="err"> Oops! 找不到你想要的Gif </p>
    <img-gallery v-bind:imgList="imgList"></img-gallery>
  </div>
</template>
<script>
import ImgGallery from '../components/ImgGallery.vue'
import { axiosInstance } from '../axios_config.js'

export default {
  name: 'Recommend',
  data () {
    return {
      imgList: [],
      imgName: '4fd32a6fae93404a956129260ec0a606',
      err: false
    }
  },
  mounted () {
    axiosInstance({ url: '/backend_recommend?name=' + this.imgName }).then(response => {
      console.log(response.data)
      if (response.data.status === 'succeed') {
        this.err = false
        var list = response.data.result
        this.imgList = list.map(function (item) {
          var t = {
            title: item.Title,
            url: item.Oss_url,
            thumbnail: item.Oss_url
          }
          return t
        })
        console.log(list[0])
      } else {
        this.err = true
        this.imgList = [{
          title: 'Oops! 找不到你想要的Gif',
          url: '../assets/timg.jpg',
          thumbnail: '../assets/timg.jpg'
        }]
      }
    })
  },
  methods: {

  },
  components: {
    'img-gallery': ImgGallery
  }
}

</script>
<style>
</style>
