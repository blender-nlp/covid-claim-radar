<template>
  <el-button :class="{'red':isLike}" icon="el-icon-star-off"  circle @click.stop="like" ref="like" style="position:absolute; right:0px; bottom:0px;"></el-button>
</template>
<script>
export default {
  name: 'FavorButton',
  data () {
    return {
      isLike: false
    }
  },
  methods: {
    like: function () {
      this.$emit('doSearch', this.text)
      this.isLike = !this.isLike
    }
  }
}

</script>
<style>
.red {
  color: #fff!important;
  background-color: orange!important;
  font-size: 14px;
}

</style>
