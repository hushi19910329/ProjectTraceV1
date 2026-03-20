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

      <div class="project-filter-bar">
        <el-form inline class="project-filter-left">
          <el-form-item label="🔍 关键词">
            <el-input v-model="filters.keyword" placeholder="项目名称/描述/目标" clearable @keyup.enter="handleSearch" />
          </el-form-item>
          <el-form-item label="👤 负责人">
            <el-select v-model="filters.owner_id" clearable filterable placeholder="全部负责人">
              <el-option v-for="user in users" :key="user.id" :label="user.real_name" :value="user.id">
                <div class="owner-option">
                  <el-avatar :size="20" :src="user.avatar_url || ''">
                    {{ user.real_name?.slice(0, 1) || user.username?.slice(0, 1) }}
                  </el-avatar>
                  <span>{{ user.real_name }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="📌 状态">
            <el-select v-model="filters.status" clearable placeholder="全部状态">
              <el-option label="未开始" value="not_started" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已暂停" value="paused" />
              <el-option label="已完成" value="done" />
            </el-select>
          </el-form-item>
          <el-form-item label="🏷️ 标签">
            <el-input v-model="filters.tag" placeholder="手动输入标签关键词" clearable @keyup.enter="handleSearch" />
          </el-form-item>
        </el-form>
        <div class="project-filter-actions">
          <el-button type="primary" @click="handleSearch">🔎 筛选</el-button>
          <el-button @click="resetFilters">♻️ 重置</el-button>
        </div>
      </div>

      <div class="tag-quick-bar">
        <span class="minor-text">快捷标签：</span>
        <el-tag
          v-for="tag in visibleTags"
          :key="tag"
          class="compact-tag tag-filter-chip"
          :type="filters.tag === tag ? 'primary' : 'info'"
          effect="plain"
          @click="quickSelectTag(tag)"
        >
          {{ tag }}
        </el-tag>
        <el-button link type="primary" v-if="tagList.has_more && !showAllTags" @click="expandTags">展开更多</el-button>
        <el-button link type="primary" v-if="showAllTags" @click="collapseTags">收起</el-button>
      </div>
    </section>

    <section class="card project-table-card">
      <div class="project-table-wrap">
        <el-table
          ref="projectTableRef"
          :data="projects"
          v-loading="loading"
          style="width: 100%"
          row-key="id"
          height="100%"
        >
          <el-table-column type="expand" width="60">
            <template #default="{ row }">
              <div class="project-expand-panel">
                <div class="summary-grid">
                  <div class="stat-item"><span class="stat-label">📊 项目进度</span><strong>{{ row.task_summary?.progress || 0 }}%</strong></div>
                  <div class="stat-item"><span class="stat-label">✅ 已完成任务</span><strong>{{ row.task_summary?.done || 0 }}</strong></div>
                  <div class="stat-item"><span class="stat-label">🧩 任务总数</span><strong>{{ row.task_summary?.total || 0 }}</strong></div>
                  <div class="stat-item"><span class="stat-label">🗑️ 废弃任务</span><strong>{{ row.task_summary?.abandoned || 0 }}</strong></div>
                </div>
                <div class="top-gap">
                  <strong>近期任务：</strong>
                  <div class="minor-text" v-if="!expandedTasksMap[row.id]">加载中...</div>
                  <div v-else-if="!expandedTasksMap[row.id].length" class="minor-text">暂无任务</div>
                  <div v-else class="comment-list top-gap">
                    <div class="comment-item" v-for="task in expandedTasksMap[row.id]" :key="task.id">
                      <div class="comment-head">
                        <strong>{{ task.title }}</strong>
                        <span class="minor-text">{{ task.progress }}%</span>
                      </div>
                      <div class="minor-text">
                        {{ taskStatusMap[task.status]?.emoji || "❔" }} {{ taskStatusMap[task.status]?.label || task.status }}
                        |
                        子任务: {{ taskSubCountMap[task.id] || 0 }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="code" label="项目编号" min-width="120" />
          <el-table-column prop="name" label="项目名称" min-width="180" />
          <el-table-column label="状态" width="140">
            <template #default="{ row }">
              <el-tooltip :content="statusMap[row.status]?.desc || row.status" placement="top">
                <span>{{ statusMap[row.status]?.emoji || "❔" }} {{ statusMap[row.status]?.label || row.status }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="优先级" width="130">
            <template #default="{ row }">
              <el-tooltip :content="priorityMap[row.priority]?.desc || row.priority" placement="top">
                <span>{{ priorityMap[row.priority]?.emoji || "❔" }} {{ priorityMap[row.priority]?.label || row.priority }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="负责人" min-width="140">
            <template #default="{ row }">
              <div class="owner-cell">
                <el-avatar v-if="row.owner" :size="24" :src="row.owner.avatar_url || ''">
                  {{ row.owner.real_name?.slice(0, 1) || row.owner.username?.slice(0, 1) }}
                </el-avatar>
                <span>{{ row.owner?.real_name || "-" }}</span>
              </div>
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
              <el-tooltip content="已完成任务数量" placement="top">
                <span>✅ {{ row.task_summary.done }}</span>
              </el-tooltip>
              <span> / </span>
              <el-tooltip content="任务总数量（含主任务与子任务）" placement="top">
                <span>🧩 {{ row.task_summary.total }}</span>
              </el-tooltip>
              <span> / </span>
              <el-tooltip content="已废弃任务数量（保留追踪）" placement="top">
                <span>🗑️ {{ row.task_summary.abandoned }}</span>
              </el-tooltip>
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
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="toggleExpand(row)">{{ expandedRowIdSet.has(row.id) ? "收起" : "展开" }}</el-button>
              <el-button link type="primary" @click="goDetail(row.id)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="table-pagination">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          v-model:current-page="pageState.page"
          v-model:page-size="pageState.page_size"
          :page-sizes="[20, 40, 60, 100]"
          @size-change="loadProjects"
          @current-change="loadProjects"
        />
      </div>
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

import { createProject, fetchProjects, fetchProjectTags, fetchProjectTasks, followProject, unfollowProject } from "../../api/projects";
import { fetchUsers } from "../../api/users";
import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const loading = ref(false);
const createDialogVisible = ref(false);
const projectTableRef = ref(null);
const projects = ref([]);
const users = ref([]);
const total = ref(0);
const tagList = reactive({ items: [], has_more: false });
const showAllTags = ref(false);
const expandedRowIdSet = ref(new Set());
const expandedTasksMap = reactive({});
const taskSubCountMap = reactive({});

const listMode = computed(() => (route.path.includes("followed-projects") ? "followed" : "all"));
const pageTitle = computed(() => (listMode.value === "followed" ? "⭐ 关注项目" : "📁 项目清单"));
const visibleTags = computed(() => (showAllTags.value ? tagList.items : tagList.items.slice(0, 12)));

const pageState = reactive({
  page: 1,
  page_size: 20,
});

const statusMap = {
  not_started: { emoji: "⚪", label: "未开始", desc: "项目尚未启动" },
  in_progress: { emoji: "🟡", label: "进行中", desc: "项目正在推进" },
  paused: { emoji: "⏸️", label: "已暂停", desc: "项目临时暂停" },
  done: { emoji: "✅", label: "已完成", desc: "项目已完成交付" },
};

const taskStatusMap = {
  todo: { emoji: "⚪", label: "待开始" },
  in_progress: { emoji: "🟡", label: "进行中" },
  blocked: { emoji: "⛔", label: "阻塞" },
  done: { emoji: "✅", label: "已完成" },
  abandoned: { emoji: "🗑️", label: "已废弃" },
};

const priorityMap = {
  low: { emoji: "🟢", label: "低", desc: "低优先级，可延后处理" },
  medium: { emoji: "🔵", label: "中", desc: "常规优先级，按计划推进" },
  high: { emoji: "🟠", label: "高", desc: "高优先级，需要优先处理" },
  urgent: { emoji: "🔴", label: "紧急", desc: "紧急优先级，需要立即处理" },
};

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
  pageState.page = 1;
  showAllTags.value = false;
  loadProjects();
  loadTagList();
}

function handleSearch() {
  pageState.page = 1;
  loadProjects();
  loadTagList();
}

function quickSelectTag(tag) {
  filters.tag = filters.tag === tag ? "" : tag;
  handleSearch();
}

async function expandTags() {
  showAllTags.value = true;
  await loadTagList();
}

async function collapseTags() {
  showAllTags.value = false;
  await loadTagList();
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
          avatar_url: authStore.currentUser?.avatar_url || "",
        },
      ];
      ElMessage.success("已关注项目");
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "操作失败");
  }
}

async function loadUsers() {
  try {
    const { data } = await fetchUsers();
    users.value = data.items || [];
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "用户列表加载失败");
  }
}

async function loadTagList() {
  try {
    const { data } = await fetchProjectTags({
      keyword: filters.tag || undefined,
      limit: showAllTags.value ? 200 : 20,
    });
    tagList.items = data.items || [];
    tagList.has_more = Boolean(data.has_more);
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "标签加载失败");
  }
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
      page: pageState.page,
      page_size: pageState.page_size,
    };
    const { data } = await fetchProjects(params);
    projects.value = data.items || [];
    total.value = data.total || 0;
    expandedRowIdSet.value = new Set();
  } finally {
    loading.value = false;
  }
}

async function loadExpandData(projectId) {
  if (expandedTasksMap[projectId]) {
    return;
  }
  const { data } = await fetchProjectTasks(projectId);
  const allTasks = (data.items || []).slice(0, 8);
  expandedTasksMap[projectId] = allTasks;
  const subMap = {};
  for (const item of data.items || []) {
    if (item.parent_task_id) {
      subMap[item.parent_task_id] = (subMap[item.parent_task_id] || 0) + 1;
    }
  }
  for (const key of Object.keys(subMap)) {
    taskSubCountMap[key] = subMap[key];
  }
}

async function toggleExpand(row) {
  const expanded = expandedRowIdSet.value.has(row.id);
  projectTableRef.value?.toggleRowExpansion(row, !expanded);
  if (!expanded) {
    expandedRowIdSet.value.add(row.id);
    await loadExpandData(row.id);
  } else {
    expandedRowIdSet.value.delete(row.id);
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
    await loadTagList();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "项目创建失败");
  }
}

onMounted(async () => {
  await Promise.allSettled([loadUsers(), loadProjects(), loadTagList()]);
});
</script>
