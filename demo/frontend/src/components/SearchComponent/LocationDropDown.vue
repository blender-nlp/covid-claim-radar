<template>
  <el-select v-model="value" filterable placeholder="Location" @change="valChange" style="width:170px" size="medium">
    <el-option
      v-for="item in options"
      :key="item.value"
      :label="item.label"
      :value="item.value">
    </el-option>
  </el-select>
</template>

<script>
// import { el-select } from 'element-ui'
import { axiosInstance } from '../../axios_config.js'
export default {
  name: 'LocationDropDown',
  props: ['value'],
  data () {
    return {
      options: []
    }
  },
  created () {
    axiosInstance({ url: '/location-option' }).then(response => {
      // console.log(response.data.result)
      // console.log(response)
      this.options = response.data.result
    })
  },
  methods: {
    valChange: function (val) {
      this.$emit('locationChange', val)
    }
  }
}
</script>
