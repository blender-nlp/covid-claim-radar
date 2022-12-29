<template>
  <v-gallery :images="imgList" class="image-box">
    <a href="javascript:void(0);" :data-image="img.url" :title="img.title" v-for="img in imgList" :key="img.title">
      <div class="bgbox">
        <div style="position:relative;">
          <img :src="img.url">
          <favor-button @click="test"></favor-button>
        </div>
      </div>
    </a>

  </v-gallery>
</template>

<script>
import picNotfind from '@/assets/timg.jpg'
import FavorButton from '@/components/FavorButton.vue'
export default {
  name: 'ImgGallery',
  data () {
    return {
      imgLike: picNotfind,
      isLike: false
    }
  },
  methods: {
    test: function () {
      this.isLike = !this.isLike
      console.log('here!')
    }
  },
  props: {
    imgList: {
      type: Array,
      required: true
    }
  },
  components: {
    'favor-button': FavorButton
  }
}
</script>

<style>
.likeCss{
  color: #FF69B4;
  background-color: #FF69B4;
  border-color: #FF69B4;
}
.el-button--primary{
  color: #fff;
  background-color: #FF69B4;
  border-color: #FF69B4;
}
.el-button--primary:hover{
  background-color: #FF69B4;
  border-color: #FF69B4;
}
.el-button--primary:focus{
  background-color: #FF69B4;
  border-color: #FF69B4;
}
.red {
  color: #fff!important;
  background-color: orange!important;
  font-size: 14px;
}
.blue {
  color: blue!important;
  font-size: 20px;
}
.image-box a {
  clear: both;
  display: inline-block;
  margin: 0 10px 10px 0;
  position: relative;
  text-align: center;
}

.image-box a .bgbox {
  background-color: #FFFFFF;
  height: 150px;
  display: table-cell;
  vertical-align: middle;
  padding: 4px;
  border-radius: 2px;
}

.image-box a .bgbox img {
  width: 200px;
  display: block;
}

.image-box a .img-title {
  bottom: 5px;
  display: block;
  text-align: center;
  color: #999999;
  padding-top: 5px;
}

.image-box a:hover .img-title {
  color: #232323;
}

</style>
