<template>
  <div class="page-grid">
    <section class="card" v-loading="loadingState.project" v-if="project">
      <div class="section-head">
        <div>
          <h2 class="section-title">📝 {{ project.name }}</h2>
          <p class="section-subtitle">{{ project.description || "暂无项目描述" }}</p>
        </div>
        <div class="toolbar-actions">
          <el-button v-if="authStore.currentUser?.is_superuser" type="primary" plain @click="openProjectEditDialog">
            ✏️ 编辑项目
          </el-button>
          <el-button @click="goBack">返回</el-button>
        </div>
      </div>

      <div class="summary-grid">
        <div class="stat-item"><span class="stat-label">📌 编号</span><strong>{{ project.code }}</strong></div>
        <div class="stat-item"><span class="stat-label">👤 负责人</span><strong>{{ project.owner?.real_name || "-" }}</strong></div>
        <div class="stat-item"><span class="stat-label">📅 周期</span><strong>{{ project.start_date || "-" }} ~ {{ project.end_date || "-" }}</strong></div>
        <div class="stat-item"><span class="stat-label">📊 进度</span><strong>{{ project.task_summary.progress }}%</strong></div>
      </div>
      <div class="top-gap">
        <el-tag v-for="tag in project.tags || []" :key="tag" class="compact-tag">🏷️ {{ tag }}</el-tag>
      </div>
    </section>

    <section class="card" v-loading="loadingState.tasks" v-if="project">
      <div class="section-head">
        <div>
          <h2 class="section-title">🧱 任务列表</h2>
          <p class="section-subtitle">点击“查看”将从右侧弹出 700px 详情抽屉。</p>
        </div>
        <el-button type="primary" @click="openCreateTask">➕ 新建任务</el-button>
      </div>

      <el-table :data="taskTree" row-key="id" :tree-props="{ children: 'children' }" style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="220" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            {{ row.parent_task_id ? "子任务" : "主任务" }}
          </template>
        </el-table-column>
        <el-table-column label="负责人" min-width="120">
          <template #default="{ row }">
            <div class="owner-cell">
              <el-avatar v-if="row.assignee" :size="24" :src="row.assignee.avatar_url || ''">
                {{ row.assignee.real_name?.slice(0, 1) || row.assignee.username?.slice(0, 1) }}
              </el-avatar>
              <span>{{ row.assignee?.real_name || "-" }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="130">
          <template #default="{ row }">
            <el-tooltip :content="taskStatusMap[row.status]?.desc || row.status" placement="top">
              <span>{{ taskStatusMap[row.status]?.emoji || "❔" }} {{ taskStatusMap[row.status]?.label || row.status }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="120">
          <template #default="{ row }">
            <el-tooltip :content="priorityMap[row.priority]?.desc || row.priority" placement="top">
              <span>{{ priorityMap[row.priority]?.emoji || "❔" }} {{ priorityMap[row.priority]?.label || row.priority }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="🏷️ 标签" min-width="170">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags" :key="tag" class="compact-tag" size="small">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="📈 进度" width="130">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openTaskDrawer(row.id)">查看</el-button>
            <el-button link type="success" @click="openCreateSubTask(row)">子任务</el-button>
            <el-button link type="warning" @click="openEditTask(row)">编辑</el-button>
            <el-button link type="danger" :disabled="row.is_abandoned" @click="openAbandonDialog(row)">废弃</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-pagination">
        <div class="minor-text">
          已加载 {{ tasks.length }} / {{ taskListState.total }} 条
        </div>
        <div class="toolbar-actions">
          <el-select v-model="taskListState.page_size" style="width: 130px" @change="resetTaskListAndLoad">
            <el-option :value="20" label="20条/次" />
            <el-option :value="40" label="40条/次" />
            <el-option :value="60" label="60条/次" />
            <el-option :value="80" label="80条/次" />
            <el-option :value="100" label="100条/次" />
          </el-select>
          <el-button type="primary" plain :disabled="!taskListState.has_more" @click="loadMoreTasks">
            查看更多
          </el-button>
        </div>
      </div>
    </section>

    <section class="card" v-loading="loadingState.logs" v-if="project">
      <div class="section-head">
        <div>
          <h2 class="section-title">📜 操作日志</h2>
          <p class="section-subtitle">评论/@、附件、提醒与状态更新均会留痕。</p>
        </div>
      </div>
      <el-timeline v-if="logs.length">
        <el-timeline-item v-for="log in logs" :key="log.id" :timestamp="formatDateTime(log.created_at)" placement="top">
          <strong>{{ log.action }}</strong>
          <div>{{ log.detail }}</div>
          <div class="minor-text">{{ log.operator?.real_name || "-" }}</div>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无操作日志" />
    </section>

    <el-drawer v-model="taskDrawerVisible" title="🔎 任务详情" direction="rtl" size="700px" v-loading="loadingState.taskDetail">
      <div v-if="selectedTask" class="drawer-content">
        <div class="section-head">
          <h3>{{ selectedTask.title }}</h3>
          <el-button type="primary" plain @click="openCreateSubTask">➕ 添加子任务</el-button>
        </div>

        <div class="summary-grid">
          <div class="stat-item">
            <span class="stat-label">📌 状态</span>
            <strong>
              <el-tooltip :content="taskStatusMap[selectedTask.status]?.desc || selectedTask.status" placement="top">
                <span>{{ taskStatusMap[selectedTask.status]?.emoji || "❔" }} {{ taskStatusMap[selectedTask.status]?.label || selectedTask.status }}</span>
              </el-tooltip>
            </strong>
          </div>
          <div class="stat-item"><span class="stat-label">👤 负责人</span><strong>{{ selectedTask.assignee?.real_name || "-" }}</strong></div>
          <div class="stat-item">
            <span class="stat-label">⭐ 优先级</span>
            <strong>
              <el-tooltip :content="priorityMap[selectedTask.priority]?.desc || selectedTask.priority" placement="top">
                <span>{{ priorityMap[selectedTask.priority]?.emoji || "❔" }} {{ priorityMap[selectedTask.priority]?.label || selectedTask.priority }}</span>
              </el-tooltip>
            </strong>
          </div>
          <div class="stat-item"><span class="stat-label">📈 进度</span><strong>{{ selectedTask.progress }}%</strong></div>
        </div>

        <el-form label-width="90px" class="inline-form">
          <div class="form-two-cols">
            <el-form-item label="状态">
              <el-select v-model="taskUpdateForm.status">
                <el-option label="待开始" value="todo" />
                <el-option label="进行中" value="in_progress" />
                <el-option label="阻塞" value="blocked" />
                <el-option label="已完成" value="done" />
              </el-select>
            </el-form-item>
            <el-form-item label="进度">
              <el-input-number v-model="taskUpdateForm.progress" :min="0" :max="100" />
            </el-form-item>
            <el-form-item label="负责人">
              <el-select v-model="taskUpdateForm.assignee_id" filterable clearable>
                <el-option v-for="member in project.members" :key="member.user.id" :label="member.user.real_name" :value="member.user.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="工时">
              <el-input-number v-model="taskUpdateForm.actual_hours" :min="0" />
            </el-form-item>
          </div>
          <el-form-item label="完成标准">
            <el-input v-model="taskUpdateForm.content" type="textarea" :rows="2" placeholder="请填写本次状态更新内容（会保留历史）" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleUpdateTask">💾 保存</el-button>
          </el-form-item>
        </el-form>

        <section class="inner-panel">
          <h3>📜 状态更新历史</h3>
          <div v-if="selectedTask.status_updates?.length" class="comment-list">
            <div v-for="item in selectedTask.status_updates" :key="item.id" class="comment-item">
              <div class="comment-head">
                <strong>{{ item.operator?.real_name || "-" }}</strong>
                <span class="minor-text">{{ formatDateTime(item.created_at) }}</span>
              </div>
              <div class="minor-text">状态: {{ item.status }} | 进度: {{ item.progress }}% | 工时: {{ item.actual_hours }}</div>
              <div>{{ item.content }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无状态更新记录" />
        </section>

        <section class="inner-panel">
          <h3>💬 评论</h3>
          <div v-if="selectedTask.comments.length" class="comment-list">
            <div v-for="comment in selectedTask.comments" :key="comment.id" class="comment-item">
              <div class="comment-head">
                <strong>{{ comment.author?.real_name || "-" }}</strong>
                <span class="minor-text">{{ formatDateTime(comment.created_at) }}</span>
              </div>
              <div>{{ comment.content }}</div>
              <div class="minor-text" v-if="comment.mentioned_users.length">
                @ {{ comment.mentioned_users.map((item) => item.real_name).join("、") }}
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无评论" />
          <el-form label-width="70px">
            <el-form-item label="内容">
              <el-input v-model="commentForm.content" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="@成员">
              <el-select v-model="commentForm.mentioned_user_ids" multiple filterable>
                <el-option v-for="member in project.members" :key="member.user.id" :label="member.user.real_name" :value="member.user.id" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleAddComment">发布评论</el-button>
            </el-form-item>
          </el-form>
        </section>

        <section class="inner-panel">
          <h3>📎 附件与提醒</h3>
          <div class="attachment-list" v-if="selectedTask.attachments.length">
            <div v-for="attachment in selectedTask.attachments" :key="attachment.id" class="attachment-item">
              <span>{{ attachment.file_name }}</span>
              <el-button link type="primary" @click="handleDownloadAttachment(attachment)">下载</el-button>
            </div>
          </div>
          <el-empty v-else description="暂无附件" />
          <el-upload :auto-upload="false" :show-file-list="true" :limit="1" :on-change="handleSelectFile">
            <template #trigger>
              <el-button>选择附件</el-button>
            </template>
          </el-upload>
          <el-button type="primary" class="top-gap" :disabled="!selectedFile" @click="handleUploadAttachment">上传附件</el-button>
          <el-divider />
          <el-form label-width="70px">
            <el-form-item label="提醒人">
              <el-select v-model="reminderForm.user_ids" multiple filterable>
                <el-option v-for="member in project.members" :key="member.user.id" :label="member.user.real_name" :value="member.user.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="内容">
              <el-input v-model="reminderForm.content" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSendReminder">发送提醒</el-button>
            </el-form-item>
          </el-form>
        </section>
      </div>
    </el-drawer>

    <el-dialog v-model="taskDialogVisible" :title="editingTaskId ? '编辑任务' : '新建任务'" width="760px">
      <el-form label-width="100px">
        <div class="form-two-cols">
          <el-form-item label="任务标题">
            <el-input v-model="taskForm.title" />
          </el-form-item>
          <el-form-item label="任务类型">
            <el-select v-model="taskForm.task_type">
              <el-option label="开发" value="development" />
              <el-option label="测试" value="testing" />
              <el-option label="设计" value="design" />
              <el-option label="联调" value="integration" />
              <el-option label="运维" value="ops" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人">
            <el-select v-model="taskForm.assignee_id" filterable clearable>
              <el-option v-for="member in project?.members || []" :key="member.user.id" :label="member.user.real_name" :value="member.user.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="所属节点">
            <el-select v-model="taskForm.node_id" clearable>
              <el-option v-for="node in project?.nodes || []" :key="node.id" :label="node.name" :value="node.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="taskForm.priority">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="urgent" />
            </el-select>
          </el-form-item>
          <el-form-item label="进度">
            <el-input-number v-model="taskForm.progress" :min="0" :max="100" />
          </el-form-item>
          <el-form-item label="计划开始">
            <el-date-picker v-model="taskForm.start_date" value-format="YYYY-MM-DD" type="date" />
          </el-form-item>
          <el-form-item label="计划结束">
            <el-date-picker v-model="taskForm.end_date" value-format="YYYY-MM-DD" type="date" />
          </el-form-item>
        </div>
        <el-form-item label="🏷️ 标签">
          <el-select v-model="taskForm.tags" multiple filterable allow-create default-first-option />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="taskForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeTaskDialog">取消</el-button>
        <el-button type="primary" @click="handleSaveTask">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="abandonDialogVisible" title="废弃任务" width="520px">
      <el-form label-width="90px">
        <el-form-item label="废弃原因">
          <el-input v-model="abandonReason" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="abandonDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="handleAbandonTask">确认废弃</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="projectEditDialogVisible" title="编辑项目" width="760px" v-if="project">
      <el-form label-width="110px">
        <div class="form-two-cols">
          <el-form-item label="项目名称"><el-input v-model="projectEditForm.name" /></el-form-item>
          <el-form-item label="项目状态">
            <el-select v-model="projectEditForm.status">
              <el-option label="未开始" value="not_started" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已暂停" value="paused" />
              <el-option label="已完成" value="done" />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="projectEditForm.priority">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="urgent" />
            </el-select>
          </el-form-item>
          <el-form-item label="项目负责人">
            <el-select v-model="projectEditForm.owner_id" filterable>
              <el-option v-for="user in users" :key="user.id" :label="`${user.real_name} (${user.username})`" :value="user.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="开始日期"><el-date-picker v-model="projectEditForm.start_date" value-format="YYYY-MM-DD" type="date" /></el-form-item>
          <el-form-item label="结束日期"><el-date-picker v-model="projectEditForm.end_date" value-format="YYYY-MM-DD" type="date" /></el-form-item>
        </div>
        <el-form-item label="项目成员">
          <el-select v-model="projectEditForm.member_ids" multiple filterable>
            <el-option v-for="user in users" :key="user.id" :label="`${user.real_name} (${user.username})`" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="🏷️ 标签">
          <el-select v-model="projectEditForm.tags" multiple filterable allow-create default-first-option />
        </el-form-item>
        <el-form-item label="项目目标"><el-input v-model="projectEditForm.goal" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="项目描述"><el-input v-model="projectEditForm.description" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="projectEditDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateProject">保存变更</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import {
  abandonProjectTask,
  addTaskComment,
  addTaskStatusUpdate,
  createProjectTask,
  createTaskReminder,
  downloadAttachment,
  fetchProject,
  fetchProjectLogs,
  fetchProjectTask,
  fetchProjectTasks,
  updateProject,
  updateProjectTask,
  uploadTaskAttachment,
} from "../../api/projects";
import { fetchUsers } from "../../api/users";
import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const loadingState = reactive({
  project: false,
  tasks: false,
  logs: false,
  users: false,
  taskDetail: false,
});
const project = ref(null);
const tasks = ref([]);
const taskTree = ref([]);
const logs = ref([]);
const users = ref([]);
const selectedTask = ref(null);
const selectedFile = ref(null);
const taskDrawerVisible = ref(false);
const taskDialogVisible = ref(false);
const abandonDialogVisible = ref(false);
const projectEditDialogVisible = ref(false);
const editingTaskId = ref(null);
const pendingAbandonTaskId = ref(null);
const abandonReason = ref("");

const defaultTaskForm = () => ({
  title: "",
  description: "",
  task_type: "development",
  assignee_id: null,
  node_id: null,
  parent_task_id: null,
  priority: "medium",
  tags: [],
  progress: 0,
  start_date: "",
  end_date: "",
});

const taskForm = reactive(defaultTaskForm());
const taskListState = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  has_more: false,
});
const taskUpdateForm = reactive({
  status: "todo",
  progress: 0,
  assignee_id: null,
  actual_hours: 0,
  content: "",
});
const commentForm = reactive({ content: "", mentioned_user_ids: [] });
const reminderForm = reactive({ user_ids: [], content: "" });
const projectEditForm = reactive({
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
});

const projectId = computed(() => Number(route.params.projectId));

const taskStatusMap = {
  todo: { emoji: "⚪", label: "待开始", desc: "任务尚未开始处理" },
  in_progress: { emoji: "🟡", label: "进行中", desc: "任务正在执行中" },
  blocked: { emoji: "⛔", label: "阻塞", desc: "任务被依赖或风险阻塞" },
  done: { emoji: "✅", label: "已完成", desc: "任务已完成并关闭" },
  abandoned: { emoji: "🗑️", label: "已废弃", desc: "任务被废弃但保留追踪记录" },
};

const priorityMap = {
  low: { emoji: "🟢", label: "低", desc: "低优先级，可延后处理" },
  medium: { emoji: "🔵", label: "中", desc: "常规优先级，按计划推进" },
  high: { emoji: "🟠", label: "高", desc: "高优先级，需要优先处理" },
  urgent: { emoji: "🔴", label: "紧急", desc: "紧急优先级，需要立即处理" },
};

function resetTaskForm() {
  Object.assign(taskForm, defaultTaskForm());
}

function closeTaskDialog() {
  taskDialogVisible.value = false;
  editingTaskId.value = null;
  resetTaskForm();
}

function openCreateTask() {
  editingTaskId.value = null;
  resetTaskForm();
  taskDialogVisible.value = true;
}

function openCreateSubTask(parentTask = null) {
  editingTaskId.value = null;
  resetTaskForm();
  if (parentTask?.id) {
    taskForm.parent_task_id = parentTask.id;
  } else {
    taskForm.parent_task_id = selectedTask.value?.id || null;
  }
  taskDialogVisible.value = true;
}

function formatDateTime(value) {
  return value ? value.replace("T", " ").slice(0, 16) : "-";
}

function openProjectEditDialog() {
  if (!project.value) {
    return;
  }
  Object.assign(projectEditForm, {
    name: project.value.name,
    description: project.value.description,
    status: project.value.status,
    priority: project.value.priority,
    owner_id: project.value.owner?.id || null,
    start_date: project.value.start_date,
    end_date: project.value.end_date,
    goal: project.value.goal,
    tags: project.value.tags || [],
    member_ids: project.value.members.map((item) => item.user.id),
  });
  projectEditDialogVisible.value = true;
}

function goBack() {
  router.push("/projects/list");
}

async function loadProject() {
  loadingState.project = true;
  try {
    const { data } = await fetchProject(projectId.value);
    project.value = data;
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "项目信息加载失败");
  } finally {
    loadingState.project = false;
  }
}

async function loadTasks(append = false) {
  loadingState.tasks = true;
  try {
    const { data } = await fetchProjectTasks(projectId.value, {
      page: taskListState.page,
      page_size: taskListState.page_size,
    });
    const pageItems = data.items || [];
    if (append) {
      const merged = [...tasks.value, ...pageItems];
      const map = new Map(merged.map((item) => [item.id, item]));
      tasks.value = Array.from(map.values());
    } else {
      tasks.value = pageItems;
    }
    taskListState.total = data.total || 0;
    taskListState.has_more = Boolean(data.has_more);
    taskTree.value = buildTaskTree(tasks.value);
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "任务列表加载失败");
  } finally {
    loadingState.tasks = false;
  }
}

async function loadMoreTasks() {
  if (!taskListState.has_more) return;
  taskListState.page += 1;
  await loadTasks(true);
}

async function resetTaskListAndLoad() {
  taskListState.page = 1;
  await loadTasks(false);
}

function buildTaskTree(items) {
  const map = new Map();
  for (const raw of items) {
    map.set(raw.id, { ...raw, children: [] });
  }
  const roots = [];
  for (const task of map.values()) {
    if (task.parent_task_id && map.has(task.parent_task_id)) {
      map.get(task.parent_task_id).children.push(task);
    } else {
      roots.push(task);
    }
  }
  return roots;
}

async function loadUsers() {
  loadingState.users = true;
  try {
    const { data } = await fetchUsers({ page: 1, page_size: 100 });
    users.value = data.items;
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "用户列表加载失败");
  } finally {
    loadingState.users = false;
  }
}

async function loadLogs() {
  loadingState.logs = true;
  try {
    const { data } = await fetchProjectLogs(projectId.value);
    logs.value = data.items;
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "操作日志加载失败");
  } finally {
    loadingState.logs = false;
  }
}

async function refreshAll() {
  taskListState.page = 1;
  await Promise.allSettled([loadProject(), loadTasks(false), loadLogs(), loadUsers()]);
  if (selectedTask.value) {
    await openTaskDrawer(selectedTask.value.id);
  }
}

async function openTaskDrawer(taskId) {
  loadingState.taskDetail = true;
  try {
    const { data } = await fetchProjectTask(projectId.value, taskId);
    selectedTask.value = data;
    taskDrawerVisible.value = true;
    Object.assign(taskUpdateForm, {
      status: data.status,
      progress: data.progress,
      assignee_id: data.assignee?.id || null,
      actual_hours: data.actual_hours,
      content: "",
    });
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "任务详情加载失败");
  } finally {
    loadingState.taskDetail = false;
  }
}

function openEditTask(row) {
  editingTaskId.value = row.id;
  Object.assign(taskForm, {
    title: row.title,
    description: row.description,
    task_type: row.task_type,
    assignee_id: row.assignee?.id || null,
    node_id: row.node_id,
    parent_task_id: row.parent_task_id || null,
    priority: row.priority,
    tags: row.tags || [],
    progress: row.progress,
    start_date: row.start_date,
    end_date: row.end_date,
  });
  taskDialogVisible.value = true;
}

function openAbandonDialog(row) {
  pendingAbandonTaskId.value = row.id;
  abandonReason.value = "";
  abandonDialogVisible.value = true;
}

function handleSelectFile(uploadFile) {
  selectedFile.value = uploadFile.raw;
}

async function handleSaveTask() {
  try {
    if (editingTaskId.value) {
      await updateProjectTask(projectId.value, editingTaskId.value, taskForm);
      ElMessage.success("任务更新成功");
    } else {
      await createProjectTask(projectId.value, taskForm);
      ElMessage.success(taskForm.parent_task_id ? "子任务创建成功" : "任务创建成功");
    }
    closeTaskDialog();
    await refreshAll();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "任务保存失败");
  }
}

async function handleUpdateProject() {
  try {
    await updateProject(projectId.value, projectEditForm);
    projectEditDialogVisible.value = false;
    ElMessage.success("项目更新成功");
    await refreshAll();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "项目更新失败");
  }
}

async function handleUpdateTask() {
  if (!selectedTask.value) {
    return;
  }
  if (!taskUpdateForm.content?.trim()) {
    ElMessage.warning("请先填写本次状态更新说明");
    return;
  }
  try {
    await addTaskStatusUpdate(projectId.value, selectedTask.value.id, taskUpdateForm);
    ElMessage.success("任务更新成功");
    await refreshAll();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "任务更新失败");
  }
}

async function handleAbandonTask() {
  try {
    await abandonProjectTask(projectId.value, pendingAbandonTaskId.value, { reason: abandonReason.value });
    ElMessage.success("任务已废弃");
    abandonDialogVisible.value = false;
    await refreshAll();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "任务废弃失败");
  }
}

async function handleAddComment() {
  if (!selectedTask.value) {
    return;
  }
  try {
    await addTaskComment(projectId.value, selectedTask.value.id, commentForm);
    commentForm.content = "";
    commentForm.mentioned_user_ids = [];
    ElMessage.success("评论已发布");
    await openTaskDrawer(selectedTask.value.id);
    await loadLogs();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "评论失败");
  }
}

async function handleUploadAttachment() {
  if (!selectedTask.value || !selectedFile.value) {
    return;
  }
  try {
    await uploadTaskAttachment(projectId.value, selectedTask.value.id, selectedFile.value);
    selectedFile.value = null;
    ElMessage.success("附件上传成功");
    await openTaskDrawer(selectedTask.value.id);
    await loadLogs();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "附件上传失败");
  }
}

async function handleDownloadAttachment(attachment) {
  try {
    const { data } = await downloadAttachment(projectId.value, attachment.id);
    const blob = new Blob([data], { type: attachment.file_type || "application/octet-stream" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = attachment.file_name;
    link.click();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "附件下载失败");
  }
}

async function handleSendReminder() {
  if (!selectedTask.value) {
    return;
  }
  try {
    await createTaskReminder(projectId.value, selectedTask.value.id, reminderForm);
    reminderForm.user_ids = [];
    reminderForm.content = "";
    ElMessage.success("提醒已发送");
    await loadLogs();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "提醒发送失败");
  }
}

onMounted(refreshAll);
</script>
