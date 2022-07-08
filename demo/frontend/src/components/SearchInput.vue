<template>
  <transition>
    <!-- name="el-zoom-in-center" -->
    <div class="searchDiv">
      <el-input placeholder="请输入内容" v-model="text" class="searchClass" @keyup.enter.native='doSearch'>
        <el-button slot="append" icon="el-icon-search" @click='doSearch'>
        </el-button>
      </el-input>
    </div>
  </transition>
</template>
<script>
export default {
  name: 'SearchInput',
  data () {
    return {
      'text': ''
    }
  },
  methods: {
    doSearch: function () {
      this.$emit('doSearch', this.text)
    }
  }
}

</script>
<style>
.searchDiv {
  width: 30%;
  min-width: 350px;
  text-align: center;
  transition-duration: 0.5s;
  margin: 0 auto;
}

.searchDiv:hover {
  width: 50%;
  min-width: 350px;
  text-align: center;
}

.searchDiv:active {
  width: 50%;
  text-align: center;
}

.searchClass {
  width: 50%;
  text-align: center;
  border: 1px solid #c5c5c5;
  border-radius: 20px;
  background: #f4f4f4;
}

.searchClass .el-input-group__prepend {
  border: none;
  background-color: transparent;
  padding: 0 10px 0 30px;
}

.searchClass .el-input-group__append {
  border: none;
  background-color: transparent;
}

.searchClass .el-input__inner {

  height: 36px;
  line-height: 36px;
  border: none;
  background-color: transparent;
  transition-duration: 3s;
}

.searchClass .el-icon-search {
  font-size: 20px;
}

.searchClass .centerClass {
  height: 100%;
  line-height: 100%;
  display: inline-block;
  vertical-align: middle;
  text-align: right;
}

.searchClass .line {
  width: 1px;
  height: 26px;
  background-color: #c5c5c5;
  margin-left: 14px;
}

.searchClass:hover {
  border: 1px solid #D5E3E8;
  background: #fff;
}

.searchClass:hover .line {
  background-color: #D5E3E8;
}

.searchClass:hover .el-icon-search {
  color: #409eff;
  font-size: 20px;
}

</style>
