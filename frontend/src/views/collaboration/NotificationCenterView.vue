<template>
  <div class="page-grid">
    <section class="card">
      <div class="section-head">
        <div>
          <h2 class="section-title">消息待办</h2>
          <p class="section-subtitle">展示任务分配、评论 @提醒和手动提醒消息。</p>
        </div>
        <el-button :disabled="!unreadCount" @click="handleReadAll">全部已读</el-button>
      </div>

      <div class="summary-grid">
        <div class="stat-item">
          <span class="stat-label">总消息</span>
          <strong>{{ notifications.length }}</strong>
        </div>
        <div class="stat-item">
          <span class="stat-label">未读消息</span>
          <strong>{{ unreadCount }}</strong>
        </div>
        <div class="stat-item">
          <span class="stat-label">评论提醒</span>
          <strong>{{ countByType("comment_mention") }}</strong>
        </div>
        <div class="stat-item">
          <span class="stat-label">任务提醒</span>
          <strong>{{ countByType("manual_reminder") + countByType("task_assigned") }}</strong>
        </div>
      </div>
    </section>

    <section class="card">
      <el-table :data="notifications" v-loading="loading" style="width: 100%">
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_read ? 'info' : 'danger'">{{ row.is_read ? "已读" : "未读" }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="notification_type" label="类型" min-width="140" />
        <el-table-column prop="content" label="内容" min-width="260" />
        <el-table-column label="时间" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button link type="primary" @click="goProject(row.project_id)" v-if="row.project_id">查看项目</el-button>
            <el-button link @click="handleRead(row)" :disabled="row.is_read">标记已读</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import { fetchNotifications, markAllNotificationsRead, markNotificationRead } from "../../api/projects";

const router = useRouter();
const loading = ref(false);
const notifications = ref([]);

const unreadCount = computed(() => notifications.value.filter((item) => !item.is_read).length);

function formatDateTime(value) {
  return value ? value.replace("T", " ").slice(0, 16) : "-";
}

function countByType(type) {
  return notifications.value.filter((item) => item.notification_type === type).length;
}

function goProject(projectId) {
  router.push(`/projects/${projectId}`);
}

async function loadNotifications() {
  loading.value = true;
  try {
    const { data } = await fetchNotifications();
    notifications.value = data.items;
  } finally {
    loading.value = false;
  }
}

async function handleRead(row) {
  try {
    await markNotificationRead(row.id);
    row.is_read = true;
    ElMessage.success("已标记为已读");
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "操作失败");
  }
}

async function handleReadAll() {
  try {
    await markAllNotificationsRead();
    notifications.value = notifications.value.map((item) => ({ ...item, is_read: true }));
    ElMessage.success("全部消息已读");
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "操作失败");
  }
}

onMounted(loadNotifications);
</script>
