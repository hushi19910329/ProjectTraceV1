<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="logo">ProjectTrace</div>
      <div v-for="menu in topMenus" :key="menu.key" class="menu-group">
        <div class="menu-title">{{ menu.label }}</div>
        <router-link
          v-for="child in menu.children"
          :key="child.key"
          :to="child.path"
          class="nav-link"
        >
          {{ child.label }}
        </router-link>
      </div>
    </aside>
    <main class="page-shell">
      <header class="topbar">
        <div>
          <h1 class="page-title">项目管理平台</h1>
          <p class="page-subtitle">登录、菜单骨架和用户管理已接通。</p>
        </div>
        <div class="topbar-actions" v-if="currentUser">
          <span class="user-pill">{{ currentUser.real_name }}（{{ currentUser.username }}）</span>
          <button class="ghost-btn" @click="handleLogout">退出登录</button>
        </div>
      </header>
      <section class="page-body">
        <slot />
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";

import { useAppStore } from "../../stores/app";
import { useAuthStore } from "../../stores/auth";

const router = useRouter();
const appStore = useAppStore();
const authStore = useAuthStore();

const { topMenus } = storeToRefs(appStore);
const currentUser = computed(() => authStore.currentUser);

function handleLogout() {
  authStore.logout();
  router.push("/login");
}
</script>
