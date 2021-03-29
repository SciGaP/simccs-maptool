<template>
  <b-badge v-if="type === 'source'" variant="success"
    ><i class="fa fa-arrow-circle-up" aria-hidden="true"></i> Source</b-badge
  >
  <b-badge v-else-if="type === 'sink'" variant="danger"
    ><i class="fa fa-arrow-circle-down" aria-hidden="true"></i> Sink</b-badge
  >
</template>
<script>
export default {
  props: ["type"],
};
</script>
