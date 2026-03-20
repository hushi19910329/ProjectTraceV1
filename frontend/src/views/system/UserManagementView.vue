<template>
  <section class="card">
    <div class="section-head user-page-header">
      <div>
        <h2>用户管理</h2>
        <p class="placeholder-text">支持创建、修改、删除用户，并通过角色分配控制可使用的板块权限。</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">新增用户</el-button>
    </div>

    <el-table :data="users" border style="width: 100%;">
      <el-table-column label="头像" width="86">
        <template #default="{ row }">
          <el-avatar :size="30" :src="row.avatar_url || ''">
            {{ row.real_name?.slice(0, 1) || row.username?.slice(0, 1) }}
          </el-avatar>
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" min-width="140" />
      <el-table-column prop="real_name" label="姓名" min-width="120" />
      <el-table-column prop="mobile" label="手机号" min-width="140" />
      <el-table-column prop="status" label="状态" min-width="100" />
      <el-table-column label="角色" min-width="220">
        <template #default="{ row }">
          <el-tag v-for="role in row.roles" :key="role.id" size="small" style="margin-right: 6px;">
            {{ role.label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="板块权限" min-width="280">
        <template #default="{ row }">
          <el-tag v-for="item in row.module_permissions" :key="item" size="small" style="margin-right: 6px;">
            {{ permissionLabelMap[item] || item }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="table-pagination">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        v-model:current-page="pageState.page"
        v-model:page-size="pageState.page_size"
        :page-sizes="[20, 40, 60, 80, 100]"
        @size-change="loadUsers"
        @current-change="loadUsers"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="620px">
      <el-form label-position="top" :model="form">
        <div class="form-two-cols">
          <el-form-item label="用户名">
            <el-input v-model="form.username" :disabled="isEdit" />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="form.real_name" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="form.mobile" />
          </el-form-item>
          <el-form-item label="头像地址">
            <el-input v-model="form.avatar_url" placeholder="https://.../avatar.png" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option label="active" value="active" />
              <el-option label="disabled" value="disabled" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="头像预览">
          <el-avatar :size="48" :src="form.avatar_url || ''">
            {{ form.real_name?.slice(0, 1) || form.username?.slice(0, 1) || "U" }}
          </el-avatar>
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" show-password :placeholder="isEdit ? '不修改可留空' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="角色分配">
          <el-checkbox-group v-model="form.role_ids">
            <el-checkbox v-for="item in roles" :key="item.id" :label="item.id">
              {{ item.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="权限预览">
          <el-tag
            v-for="item in effectivePermissionLabels"
            :key="item"
            size="small"
            style="margin-right: 6px; margin-bottom: 6px;"
          >
            {{ item }}
          </el-tag>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import { createUser, deleteUser, fetchPermissionModules, fetchRoles, fetchUsers, updateUser } from "../../api/users";

const users = ref([]);
const total = ref(0);
const permissionModules = ref([]);
const roles = ref([]);
const dialogVisible = ref(false);
const isEdit = ref(false);
const editingUserId = ref(null);
const saving = ref(false);
const pageState = reactive({
  page: 1,
  page_size: 20,
});

const form = reactive({
  username: "",
  real_name: "",
  mobile: "",
  avatar_url: "",
  password: "",
  status: "active",
  role_ids: [],
});

const permissionLabelMap = computed(() =>
  Object.fromEntries(permissionModules.value.map((item) => [item.key, item.label])),
);

const roleMap = computed(() =>
  Object.fromEntries(roles.value.map((item) => [item.id, item])),
);

const effectivePermissionLabels = computed(() => {
  const permissionCodes = new Set();
  for (const roleId of form.role_ids) {
    const role = roleMap.value[roleId];
    if (!role) continue;
    for (const code of role.permission_codes) {
      permissionCodes.add(permissionLabelMap.value[code] || code);
    }
  }
  return Array.from(permissionCodes);
});

function resetForm() {
  form.username = "";
  form.real_name = "";
  form.mobile = "";
  form.avatar_url = "";
  form.password = "";
  form.status = "active";
  form.role_ids = [];
}

async function loadUsers() {
  const { data } = await fetchUsers({
    page: pageState.page,
    page_size: pageState.page_size,
  });
  users.value = data.items;
  total.value = data.total || 0;
}

async function loadPermissionModules() {
  const { data } = await fetchPermissionModules();
  permissionModules.value = data.items;
}

async function loadRoles() {
  const { data } = await fetchRoles();
  roles.value = data.items;
}

function openCreateDialog() {
  isEdit.value = false;
  editingUserId.value = null;
  resetForm();
  dialogVisible.value = true;
}

function openEditDialog(user) {
  isEdit.value = true;
  editingUserId.value = user.id;
  form.username = user.username;
  form.real_name = user.real_name;
  form.mobile = user.mobile;
  form.avatar_url = user.avatar_url || "";
  form.password = "";
  form.status = user.status;
  form.role_ids = [...user.role_ids];
  dialogVisible.value = true;
}

async function handleSave() {
  saving.value = true;
  try {
    if (isEdit.value) {
      const payload = {
        real_name: form.real_name,
        mobile: form.mobile,
        avatar_url: form.avatar_url,
        status: form.status,
        role_ids: form.role_ids,
      };
      if (form.password) {
        payload.password = form.password;
      }
      await updateUser(editingUserId.value, payload);
      ElMessage.success("用户更新成功");
    } else {
      await createUser({ ...form });
      ElMessage.success("用户创建成功");
    }
    dialogVisible.value = false;
    pageState.page = 1;
    await loadUsers();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || "保存失败");
  } finally {
    saving.value = false;
  }
}

async function handleDelete(user) {
  await ElMessageBox.confirm(`确认删除用户 ${user.real_name} 吗？`, "删除确认", {
    type: "warning",
  });
  await deleteUser(user.id);
  ElMessage.success("用户删除成功");
  await loadUsers();
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadPermissionModules(), loadRoles()]);
});
</script>

<style scoped>
.user-page-header {
  min-height: 60px;
}
</style>
