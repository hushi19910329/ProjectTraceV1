<template>
  <aside class="global-sidebar" :class="{ collapsed: sidebarCollapsed }">
    <div class="global-logo">ProjectTrace</div>
    <nav class="global-menu">
      <div v-for="menu in topMenus" :key="menu.key" class="global-menu-block">
        <button
          class="global-menu-item"
          :class="{ active: isActive(menu.key) }"
          @click="handleTopMenuClick(menu)"
        >
          <span class="menu-label">{{ iconFor(menu.key) }} {{ sidebarCollapsed ? "" : menu.label }}</span>
        </button>
        <div v-if="!sidebarCollapsed && isExpanded(menu.key)" class="sub-menu">
          <router-link
            v-for="child in menu.children || []"
            :key="child.key"
            :to="child.path"
            class="sub-menu-item"
            :class="{ active: route.path === child.path }"
          >
            {{ child.label }}
          </router-link>
        </div>
      </div>
    </nav>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useRoute, useRouter } from "vue-router";

import { useAppStore } from "../../stores/app";

const route = useRoute();
const router = useRouter();
const appStore = useAppStore();
const { topMenus, sidebarCollapsed } = storeToRefs(appStore);
const expandedKey = ref("project");

const iconMap = {
  dashboard: "🏠",
  project: "📁",
  requirement: "📌",
  task: "✅",
  test: "🧪",
  collaboration: "⏱️",
  "okr-report": "📊",
  system: "⚙️",
};

function isActive(menuKey) {
  return route.meta.moduleKey === menuKey;
}

function iconFor(menuKey) {
  return iconMap[menuKey] || "📦";
}

function isExpanded(menuKey) {
  return expandedKey.value === menuKey;
}

function handleTopMenuClick(menu) {
  expandedKey.value = menu.key;
  if (sidebarCollapsed.value) {
    appStore.setSidebarCollapsed(false);
  }
  const target = menu.path || menu.children?.[0]?.path;
  if (!target || route.path === target) {
    return;
  }
  router.push(target);
}

watch(
  () => route.meta.moduleKey,
  (value) => {
    if (value) {
      expandedKey.value = String(value);
    }
  },
  { immediate: true }
);
</script>
