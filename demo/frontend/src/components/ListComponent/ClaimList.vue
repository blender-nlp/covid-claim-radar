<template>
  <el-table
    :data="tableDataProps"
    stripe
    style="width: 100%"
    @cell-click="cellClick"
    @filter-change="changeFilter"
    ref="table_child"
    >
    <el-table-column
      prop="topic"
      label="Topic"
      :column-key="'topicCol'"
      :filters="filterNameItem"
      :filtered-value="filterVal"
      width="180">
      <template slot="header">
        <span style="vertical-align: bottom">Topic</span>
        <!-- <span style="vertical-align: bottom" class="material-icons">
          filter_alt
        </span> -->
      </template>
    </el-table-column>
    <el-table-column
      prop="claimer"
      label="Claimer"
      width="180">
      <template slot-scope="scope">
        <dialog-text  v-if="scope.row.claimer_qnode.startsWith('Q')" style="color:blue; text-decoration:underline; cursor: pointer;" class="text-wrapper" plain>{{ scope.row.claimer }}</dialog-text>
        <dialog-text  v-else class="text-wrapper" plain>{{ scope.row.claimer }}</dialog-text>
      </template>
    </el-table-column>
    <el-table-column
      prop="source"
      label="Source"
      width="120">
        <template slot-scope="scope">
          <dialog-text style="color:blue; text-decoration:underline; cursor: pointer;" class="text-wrapper" plain>{{ scope.row.source }}</dialog-text>
      </template>
    </el-table-column>
    <el-table-column
      prop="stance"
      label="Stance"
      width="100">
    </el-table-column>
    <el-table-column
      prop="language"
      label="Language"
      width="110">
    </el-table-column>
    <el-table-column
      prop="object"
      label="Claim Object"
      width="110">
      <template slot-scope="scope">
        <dialog-text  v-if="scope.row.x_var_qnode.startsWith('Q')" style="color:blue; text-decoration:underline; cursor: pointer;" class="text-wrapper" plain>{{ scope.row.x_var }}</dialog-text>
        <dialog-text  v-else class="text-wrapper" plain>{{ scope.row.x_var }}</dialog-text>
      </template>
    </el-table-column>
    <el-table-column
      prop="sentence"
      label="Sentence">
      <template slot-scope="scope">
        <span>
          <span class="text-wrapper" style="vertical-align: bottom">{{ scope.row.sentence_L }}</span>
          <span class="text-wrapper-2" style="vertical-align: bottom">{{ scope.row.sentence_M }}</span>
          <span class="text-wrapper" style="vertical-align: bottom">{{ scope.row.sentence_R }}</span>
        </span>
      </template>
    </el-table-column>
    <el-table-column
      prop="operation"
      label="Operation"
      width="180">
      <template slot-scope="scope">
       <el-button
          size="mini"
          type="primary"
          plain
          @click="seeClick(scope.row)">See More</el-button>
      </template>
   </el-table-column>
  </el-table>
</template>

<script>
export default {
  name: 'ClaimList',
  props: ['tableDataProps', 'filterNameItem', 'filterVal'],
  data () {
    return {
    }
  },
  methods: {
    // rowClick: function (content) {
    //   this.$emit('rowClicked', content)
    // },
    cellClick: function (content, colInfo) {
      if (colInfo.label == 'Sentence') {
        // this.$emit('rowClicked', content)
      } else if (colInfo.label == 'Topic') {
        // this.$emit('rowClicked', content)
      } else if (colInfo.label == 'Claimer') {
        if(content.claimer_qnode.startsWith('Q')) {
          this.hrefClick(content.claimer_qnode)
        }
      } else if (colInfo.label == 'Source') {
        this.$emit('sourceClicked', content)
      } else if (colInfo.label == 'Claim Object') {
        if(content.x_var_qnode.startsWith('Q')) {
          this.hrefClick(content.x_var_qnode)
        }
      }
    },
    seeClick: function (content) {
      this.$emit('rowClicked', content)
    },
    changeFilter: function (filters) {
      this.$emit('topicFilter', filters.topicCol)
    },
    clearTopicFilter: function () {
      this.$refs.table_child.clearFilter()
    },
    hrefClick: function (qnode) {
      window.open('https://www.wikidata.org/wiki/' + qnode)
    }
    // icons (h, { column }) {
    //   return h(
    //     'div', [
    //       h('span', column.label),
    //       h('el-tooltip', {
    //         props: {
    //           placement: 'top'
    //         }
    //       }, [
    //         h('div', {
    //           slot: 'content',
    //           style: {
    //             'width': '250px',
    //             whiteSpace: 'normal'
    //             // 'margin-bottom': '10px'
    //           }
    //         }, 'Click to filter topic'),
    //         h('i', {
    //           class: 'el-icon-s-tools',
    //           style: 'margin-left:5px;'
    //         })
    //       ])
    //     ]
    //   )
    // }
  }
}
</script>

<style>
  .text-wrapper {
    word-break: break-all;
    word-wrap: break-word;
    white-space: pre-wrap;
  }
  .text-wrapper-2 {
    background-color: rgb(255,255,0,0.4);
    word-break: break-all;
    word-wrap: break-word;
    white-space: pre-wrap;
  }
  .el-table__column-filter-trigger i{
    display: none;
  }
</style>
