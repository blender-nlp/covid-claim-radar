<template>
  <div>
    <upload-gif></upload-gif>
  </div>
</template>

<script>
import Upload from '../components/Upload.vue'
export default {
  name: 'Manage',
  components: {
    'upload-gif': Upload
  }
}

</script>
<style>
</style>
