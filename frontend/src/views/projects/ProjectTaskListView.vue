<template>
  <div class="page-grid">
    <section class="card">
      <div class="section-head">
        <div>
          <h2 class="section-title">{{ pageTitle }}</h2>
          <p class="section-subtitle">✅ 任务支持标签、子任务、关注、筛选和右侧抽屉查看详情。</p>
        </div>
      </div>

      <el-form inline>
        <el-form-item label="🔍 关键词">
          <el-input v-model="filters.keyword" placeholder="任务标题/描述" clearable @keyup.enter="loadTasks" />
        </el-form-item>
        <el-form-item label="👤 负责人">
          <el-select v-model="filters.assignee_id" clearable filterable placeholder="全部负责人">
            <el-option v-for="user in users" :key="user.id" :label="user.real_name" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="🏷️ 标签">
          <el-input v-model="filters.tag" placeholder="标签关键词" clearable @keyup.enter="loadTasks" />
        </el-form-item>
        <el-form-item label="📌 状态">
          <el-select v-model="filters.status" clearable placeholder="全部状态">
            <el-option label="待开始" value="todo" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="阻塞" value="blocked" />
            <el-option label="已完成" value="done" />
            <el-option label="已废弃" value="abandoned" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTasks">筛选</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="card">
      <el-table :data="tasks" v-loading="loading" style="width: 100%">
        <el-table-column prop="project_name" label="项目" min-width="140" />
        <el-table-column prop="title" label="任务标题" min-width="200" />
        <el-table-column label="子任务" width="90">
          <template #default="{ row }">
            {{ row.parent_task_id ? "是" : "否" }}
          </template>
        </el-table-column>
        <el-table-column label="负责人" min-width="110">
          <template #default="{ row }">
            {{ row.assignee?.real_name || "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column prop="priority" label="优先级" width="90" />
        <el-table-column label="🏷️ 标签" min-width="180">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags" :key="tag" class="compact-tag" size="small">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="⭐ 关注" width="100">
          <template #default="{ row }">
            <el-button link :type="isTaskFollowed(row) ? 'warning' : 'primary'" @click="toggleTaskFollow(row)">
              {{ isTaskFollowed(row) ? "取消" : "关注" }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDrawer(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-drawer v-model="drawerVisible" title="📝 任务详情" direction="rtl" size="700px">
      <div v-if="activeTask" class="drawer-content">
        <h3>{{ activeTask.title }}</h3>
        <p class="minor-text">所属项目：{{ activeTask.project_name }}</p>
        <p>{{ activeTask.description || "暂无描述" }}</p>
        <div class="summary-grid">
          <div class="stat-item"><span class="stat-label">📌 状态</span><strong>{{ activeTask.status }}</strong></div>
          <div class="stat-item"><span class="stat-label">👤 负责人</span><strong>{{ activeTask.assignee?.real_name || "-" }}</strong></div>
          <div class="stat-item"><span class="stat-label">📈 进度</span><strong>{{ activeTask.progress }}%</strong></div>
          <div class="stat-item"><span class="stat-label">🏷️ 标签</span><strong>{{ activeTask.tags?.join(", ") || "-" }}</strong></div>
        </div>
        <el-divider />
        <el-button type="primary" @click="goProjectDetail(activeTask.project_id)">进入项目详情</el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { fetchAllTasks, fetchProjectTask, followTask, unfollowTask } from "../../api/projects";
import { fetchUsers } from "../../api/users";
import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const loading = ref(false);
const users = ref([]);
const tasks = ref([]);
const drawerVisible = ref(false);
const activeTask = ref(null);

const filters = reactive({
  keyword: "",
  assignee_id: undefined,
  tag: "",
  status: "",
});

const pageTitle = computed(() => (route.path.includes("followed-tasks") ? "⭐ 关注任务" : "✅ 任务清单"));

function resetFilters() {
  filters.keyword = "";
  filters.assignee_id = undefined;
  filters.tag = "";
  filters.status = "";
  loadTasks();
}

function isTaskFollowed(task) {
  return (task.watchers || []).some((item) => item.id === authStore.currentUser?.id);
}

async function toggleTaskFollow(task) {
  try {
    if (isTaskFollowed(task)) {
      await unfollowTask(task.project_id, task.id);
      task.watchers = (task.watchers || []).filter((item) => item.id !== authStore.currentUser?.id);
      ElMessage.success("已取消关注任务");
    } else {
      await followTask(task.project_id, task.id);
      task.watchers = [
        ...(task.watchers || []),
        { id: authStore.currentUser?.id, username: authStore.currentUser?.username, real_name: authStore.currentUser?.real_name },
      ];
      ElMessage.success("已关注任务");
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "操作失败");
  }
}

async function loadUsers() {
  const { data } = await fetchUsers();
  users.value = data.items;
}

async function loadTasks() {
  loading.value = true;
  try {
    const params = {
      keyword: filters.keyword || undefined,
      assignee_id: filters.assignee_id || undefined,
      tag: filters.tag || undefined,
      status: filters.status || undefined,
      followed: route.path.includes("followed-tasks") ? true : undefined,
    };
    const { data } = await fetchAllTasks(params);
    tasks.value = data.items;
  } finally {
    loading.value = false;
  }
}

async function openDrawer(row) {
  const { data } = await fetchProjectTask(row.project_id, row.id);
  activeTask.value = data;
  drawerVisible.value = true;
}

function goProjectDetail(projectId) {
  router.push(`/projects/${projectId}`);
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadTasks()]);
});
</script>
