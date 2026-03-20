<template>
  <div class="global-shell" :class="{ collapsed: appStore.sidebarCollapsed }">
    <GlobalSidebar />
    <main class="global-main">
      <GlobalTopbar />
      <section class="page-body">
        <slot />
      </section>
    </main>
  </div>
</template>

<script setup>
import { useAppStore } from "../../stores/app";
import GlobalSidebar from "./GlobalSidebar.vue";
import GlobalTopbar from "./GlobalTopbar.vue";

const appStore = useAppStore();
</script>
