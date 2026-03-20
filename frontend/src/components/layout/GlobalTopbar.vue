<template>
  <header class="global-topbar">
    <div class="topbar-left">
      <el-button circle @click="appStore.toggleSidebar">
        <el-icon v-if="appStore.sidebarCollapsed"><Expand /></el-icon>
        <el-icon v-else><Fold /></el-icon>
      </el-button>
      <strong class="topbar-title">{{ pageTitle }}</strong>
    </div>

    <div class="topbar-center">
      <el-input
        v-model="keyword"
        clearable
        class="topbar-search"
        placeholder="搜索菜单、页面"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <div class="topbar-right">
      <el-button circle @click="goSystemGuide" title="系统说明">
        <span class="help-icon">❓</span>
      </el-button>

      <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notify-badge">
        <el-button circle @click="goNotifications">
          <el-icon><Bell /></el-icon>
        </el-button>
      </el-badge>

      <el-dropdown @command="handleCommand">
        <div class="user-entry">
          <UserAvatarIcon :size="32" />
          <span class="user-name">{{ currentUser?.real_name || currentUser?.username || "用户" }}</span>
          <el-icon><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人信息</el-dropdown-item>
            <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>

</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { ArrowDown, Bell, Expand, Fold, Search } from "@element-plus/icons-vue";
import { useRoute, useRouter } from "vue-router";

import UserAvatarIcon from "./UserAvatarIcon.vue";
import { fetchNotifications } from "../../api/projects";
import { useAppStore } from "../../stores/app";
import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const appStore = useAppStore();

const keyword = ref("");
const unreadCount = ref(0);

const currentUser = computed(() => authStore.currentUser);
const pageTitle = computed(() => route.meta.title || appStore.appName || "ProjectTrace");

function allMenuEntries() {
  const entries = [];
  for (const top of appStore.topMenus || []) {
    entries.push({ label: top.label, path: top.path || "" });
    for (const child of top.children || []) {
      entries.push({ label: child.label, path: child.path || "" });
    }
  }
  return entries;
}

function handleSearch() {
  const q = keyword.value.trim().toLowerCase();
  if (!q) {
    return;
  }
  const target = allMenuEntries().find((item) => item.label.toLowerCase().includes(q));
  if (!target || !target.path) {
    ElMessage.warning("未找到匹配页面");
    return;
  }
  router.push(target.path);
}

function goNotifications() {
  router.push("/collaboration/messages");
}

function goSystemGuide() {
  const sectionMap = {
    dashboard: "module-dashboard",
    project: "module-project",
    requirement: "module-requirement",
    task: "module-task",
    test: "module-test",
    collaboration: "module-collaboration",
    "okr-report": "module-okr-report",
    system: "module-system",
  };
  const moduleKey = String(route.meta.moduleKey || "");
  router.push({
    path: "/system/guide",
    query: {
      section: sectionMap[moduleKey] || "icons",
      from: moduleKey || "unknown",
    },
  });
}

async function doLogout() {
  try {
    await ElMessageBox.confirm("确认退出当前登录吗？", "退出确认", {
      confirmButtonText: "确认退出",
      cancelButtonText: "取消",
      type: "warning",
    });
    authStore.logout();
    router.push("/login");
  } catch {
    // User canceled.
  }
}

function handleCommand(command) {
  if (command === "logout") {
    doLogout();
    return;
  }
  if (command === "profile") {
    ElMessage.info("个人信息页稍后补充");
  }
}

async function loadUnreadCount() {
  try {
    const { data } = await fetchNotifications();
    unreadCount.value = (data.items || []).filter((item) => !item.is_read).length;
  } catch {
    unreadCount.value = 0;
  }
}

onMounted(loadUnreadCount);
</script>
