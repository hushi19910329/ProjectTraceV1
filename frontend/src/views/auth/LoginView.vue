<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">ProjectTrace</h1>
      <p class="login-subtitle">使用用户名密码或手机号密码登录</p>
      <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="用户名 / 手机号">
          <el-input v-model="form.account" placeholder="请输入用户名或手机号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-alert
          v-if="errorMessage"
          :title="errorMessage"
          type="error"
          :closable="false"
          style="margin-bottom: 16px;"
        />
        <el-button type="primary" style="width: 100%;" :loading="submitting" @click="handleSubmit">
          登录
        </el-button>
      </el-form>

      <div class="login-hint">
        <div>默认账号：`admin` / `admin123`</div>
        <div>默认手机号：`13800000000` / `admin123`</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "../../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  account: "admin",
  password: "admin123",
});

const errorMessage = ref("");
const submitting = ref(false);

async function handleSubmit() {
  errorMessage.value = "";
  submitting.value = true;
  try {
    await authStore.login({ ...form });
    router.push("/dashboard");
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || "登录失败，请检查账号或密码";
  } finally {
    submitting.value = false;
  }
}
</script>
