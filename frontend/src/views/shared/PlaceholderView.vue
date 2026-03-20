<template>
  <section class="card">
    <h2>{{ title }}</h2>
    <p class="placeholder-text">{{ description }}</p>
    <p class="placeholder-text">页面目录已经创建完成，后续可以按模块逐步开发具体业务内容。</p>
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
});
</script>
