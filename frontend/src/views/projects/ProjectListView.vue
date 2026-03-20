<template>
  <div class="page-grid">
    <section class="card">
      <div class="section-head">
        <div>
          <h2 class="section-title">{{ pageTitle }}</h2>
          <p class="section-subtitle">📁 支持检索、负责人筛选、标签筛选与快速关注。</p>
        </div>
        <el-button v-if="authStore.currentUser?.is_superuser && listMode === 'all'" type="primary" @click="createDialogVisible = true">
          ➕ 新建项目
        </el-button>
      </div>

      <el-form inline>
        <el-form-item label="🔍 关键词">
          <el-input v-model="filters.keyword" placeholder="项目名称/描述/目标" clearable @keyup.enter="loadProjects" />
        </el-form-item>
        <el-form-item label="👤 负责人">
          <el-select v-model="filters.owner_id" clearable filterable placeholder="全部负责人">
            <el-option v-for="user in users" :key="user.id" :label="user.real_name" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="🏷️ 标签">
          <el-input v-model="filters.tag" placeholder="标签关键词" clearable @keyup.enter="loadProjects" />
        </el-form-item>
        <el-form-item label="📌 状态">
          <el-select v-model="filters.status" clearable placeholder="全部状态">
            <el-option label="未开始" value="not_started" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已暂停" value="paused" />
            <el-option label="已完成" value="done" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadProjects">筛选</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="card">
      <el-table :data="projects" v-loading="loading" style="width: 100%">
        <el-table-column prop="code" label="项目编号" min-width="120" />
        <el-table-column prop="name" label="项目名称" min-width="180" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="priority" label="优先级" width="100" />
        <el-table-column label="负责人" min-width="120">
          <template #default="{ row }">
            {{ row.owner?.real_name || "-" }}
          </template>
        </el-table-column>
        <el-table-column label="🏷️ 标签" min-width="180">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags" :key="tag" class="compact-tag" size="small">{{ tag }}</el-tag>
            <span v-if="!row.tags?.length" class="minor-text">-</span>
          </template>
        </el-table-column>
        <el-table-column label="📊 指标" min-width="220">
          <template #default="{ row }">
            ✅ {{ row.task_summary.done }} / 🧱 {{ row.task_summary.total }} / 🚫 {{ row.task_summary.abandoned }}
          </template>
        </el-table-column>
        <el-table-column label="⭐ 关注" width="120">
          <template #default="{ row }">
            <el-button
              link
              :type="isProjectFollowed(row) ? 'warning' : 'primary'"
              @click="toggleFollowProject(row)"
            >
              {{ isProjectFollowed(row) ? "取消关注" : "关注" }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goDetail(row.id)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="createDialogVisible" title="新建项目" width="760px">
      <el-form label-width="110px">
        <div class="form-two-cols">
          <el-form-item label="项目编号">
            <el-input v-model="projectForm.code" />
          </el-form-item>
          <el-form-item label="项目名称">
            <el-input v-model="projectForm.name" />
          </el-form-item>
          <el-form-item label="项目状态">
            <el-select v-model="projectForm.status">
              <el-option label="未开始" value="not_started" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已暂停" value="paused" />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="projectForm.priority">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="urgent" />
            </el-select>
          </el-form-item>
          <el-form-item label="项目负责人">
            <el-select v-model="projectForm.owner_id" filterable>
              <el-option v-for="user in users" :key="user.id" :label="`${user.real_name} (${user.username})`" :value="user.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="项目成员">
            <el-select v-model="projectForm.member_ids" multiple filterable>
              <el-option v-for="user in users" :key="user.id" :label="`${user.real_name} (${user.username})`" :value="user.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="开始日期">
            <el-date-picker v-model="projectForm.start_date" value-format="YYYY-MM-DD" type="date" />
          </el-form-item>
          <el-form-item label="结束日期">
            <el-date-picker v-model="projectForm.end_date" value-format="YYYY-MM-DD" type="date" />
          </el-form-item>
        </div>
        <el-form-item label="🏷️ 标签">
          <el-select v-model="projectForm.tags" multiple filterable allow-create default-first-option />
        </el-form-item>
        <el-form-item label="项目目标">
          <el-input v-model="projectForm.goal" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input v-model="projectForm.description" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateProject">保存项目</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { createProject, fetchProjects, followProject, unfollowProject } from "../../api/projects";
import { fetchUsers } from "../../api/users";
import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const loading = ref(false);
const createDialogVisible = ref(false);
const projects = ref([]);
const users = ref([]);

const listMode = computed(() => {
  if (route.path.includes("followed-projects")) {
    return "followed";
  }
  return "all";
});

const pageTitle = computed(() => (listMode.value === "followed" ? "⭐ 关注项目" : "📁 项目清单"));

const filters = reactive({
  keyword: "",
  owner_id: undefined,
  tag: "",
  status: "",
});

const defaultProjectForm = () => ({
  code: "",
  name: "",
  description: "",
  status: "not_started",
  priority: "medium",
  owner_id: null,
  start_date: "",
  end_date: "",
  goal: "",
  tags: [],
  member_ids: [],
  nodes: [{ name: "项目启动", description: "默认初始化节点", sequence: 1 }],
});

const projectForm = reactive(defaultProjectForm());

function resetProjectForm() {
  Object.assign(projectForm, defaultProjectForm());
}

function resetFilters() {
  filters.keyword = "";
  filters.owner_id = undefined;
  filters.tag = "";
  filters.status = "";
  loadProjects();
}

function goDetail(projectId) {
  router.push(`/projects/${projectId}`);
}

function isProjectFollowed(project) {
  return (project.watchers || []).some((item) => item.id === authStore.currentUser?.id);
}

async function toggleFollowProject(project) {
  try {
    if (isProjectFollowed(project)) {
      await unfollowProject(project.id);
      project.watchers = (project.watchers || []).filter((item) => item.id !== authStore.currentUser?.id);
      ElMessage.success("已取消关注项目");
    } else {
      await followProject(project.id);
      project.watchers = [
        ...(project.watchers || []),
        {
          id: authStore.currentUser?.id,
          username: authStore.currentUser?.username,
          real_name: authStore.currentUser?.real_name,
        },
      ];
      ElMessage.success("已关注项目");
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "操作失败");
  }
}

async function loadUsers() {
  const { data } = await fetchUsers();
  users.value = data.items;
}

async function loadProjects() {
  loading.value = true;
  try {
    const params = {
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      owner_id: filters.owner_id || undefined,
      tag: filters.tag || undefined,
      followed: listMode.value === "followed" ? true : undefined,
    };
    const { data } = await fetchProjects(params);
    projects.value = data.items;
  } finally {
    loading.value = false;
  }
}

async function handleCreateProject() {
  try {
    const payload = {
      ...projectForm,
      nodes: projectForm.nodes.filter((item) => item.name).map((item, index) => ({ ...item, sequence: index + 1 })),
    };
    await createProject(payload);
    ElMessage.success("项目创建成功");
    createDialogVisible.value = false;
    resetProjectForm();
    await loadProjects();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "项目创建失败");
  }
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadProjects()]);
});
</script>
