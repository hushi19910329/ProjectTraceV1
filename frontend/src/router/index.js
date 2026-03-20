import { createRouter, createWebHistory } from "vue-router";

import LoginView from "../views/auth/LoginView.vue";
import NotificationCenterView from "../views/collaboration/NotificationCenterView.vue";
import DashboardView from "../views/dashboard/DashboardView.vue";
import ProjectDetailView from "../views/projects/ProjectDetailView.vue";
import ProjectListView from "../views/projects/ProjectListView.vue";
import ProjectTaskListView from "../views/projects/ProjectTaskListView.vue";
import PlaceholderView from "../views/shared/PlaceholderView.vue";
import UserManagementView from "../views/system/UserManagementView.vue";
import PermissionInfoView from "../views/system/PermissionInfoView.vue";
import { useAuthStore } from "../stores/auth";

const routes = [
  {
    path: "/login",
    name: "login",
    component: LoginView,
    meta: { title: "登录", public: true, hideLayout: true },
  },
  {
    path: "/",
    redirect: "/dashboard",
  },
  {
    path: "/dashboard",
    name: "dashboard",
    component: DashboardView,
    meta: { title: "工作台", moduleKey: "dashboard" },
  },
  {
    path: "/projects",
    name: "projects-root",
    redirect: "/projects/list",
    meta: { title: "项目管理", moduleKey: "project" },
  },
  {
    path: "/projects/list",
    name: "projects",
    component: ProjectListView,
    meta: { title: "📁 项目清单", moduleKey: "project" },
  },
  {
    path: "/projects/tasks",
    name: "project-task-list",
    component: ProjectTaskListView,
    meta: { title: "✅ 任务清单", moduleKey: "project" },
  },
  {
    path: "/projects/followed-projects",
    name: "project-followed-projects",
    component: ProjectListView,
    meta: { title: "⭐ 关注项目", moduleKey: "project" },
  },
  {
    path: "/projects/followed-tasks",
    name: "project-followed-tasks",
    component: ProjectTaskListView,
    meta: { title: "⭐ 关注任务", moduleKey: "project" },
  },
  {
    path: "/projects/:projectId",
    name: "project-detail",
    component: ProjectDetailView,
    meta: { title: "📝 项目详情", moduleKey: "project" },
  },
  {
    path: "/requirements",
    name: "requirements",
    component: PlaceholderView,
    props: { title: "需求中心", description: "需求中心页预留完成。" },
    meta: { title: "需求中心", moduleKey: "requirement" },
  },
  {
    path: "/requirements/backlog",
    name: "requirements-backlog",
    component: PlaceholderView,
    props: { title: "需求池", description: "需求池页预留完成。" },
    meta: { title: "需求池", moduleKey: "requirement" },
  },
  {
    path: "/tasks",
    name: "tasks",
    component: PlaceholderView,
    props: { title: "任务看板", description: "任务看板页预留完成。" },
    meta: { title: "任务看板", moduleKey: "task" },
  },
  {
    path: "/tasks/calendar",
    name: "tasks-calendar",
    component: PlaceholderView,
    props: { title: "任务日历", description: "任务日历页预留完成。" },
    meta: { title: "任务日历", moduleKey: "task" },
  },
  {
    path: "/quality/tests",
    name: "quality-tests",
    component: PlaceholderView,
    props: { title: "测试中心", description: "测试中心页预留完成。" },
    meta: { title: "测试中心", moduleKey: "test" },
  },
  {
    path: "/quality/bugs",
    name: "quality-bugs",
    component: PlaceholderView,
    props: { title: "缺陷中心", description: "缺陷中心页预留完成。" },
    meta: { title: "缺陷中心", moduleKey: "test" },
  },
  {
    path: "/collaboration/timesheet",
    name: "timesheet",
    component: PlaceholderView,
    props: { title: "工时管理", description: "工时管理页预留完成。" },
    meta: { title: "工时管理", moduleKey: "collaboration" },
  },
  {
    path: "/collaboration/messages",
    name: "messages",
    component: NotificationCenterView,
    meta: { title: "消息待办", moduleKey: "collaboration" },
  },
  {
    path: "/insight/okr",
    name: "okr",
    component: PlaceholderView,
    props: { title: "OKR中心", description: "OKR 中心页预留完成。" },
    meta: { title: "OKR中心", moduleKey: "okr-report" },
  },
  {
    path: "/insight/reports",
    name: "reports",
    component: PlaceholderView,
    props: { title: "统计报表", description: "统计报表页预留完成。" },
    meta: { title: "统计报表", moduleKey: "okr-report" },
  },
  {
    path: "/system/users",
    name: "system-users",
    component: UserManagementView,
    meta: { title: "用户管理", moduleKey: "system" },
  },
  {
    path: "/system/permissions",
    name: "system-permissions",
    component: PermissionInfoView,
    meta: { title: "权限说明", moduleKey: "system" },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  if (to.meta.public) {
    if (authStore.isAuthenticated && to.path === "/login") {
      return "/dashboard";
    }
    return true;
  }

  if (!authStore.isAuthenticated) {
    return "/login";
  }

  if (!authStore.currentUser) {
    try {
      await authStore.loadCurrentUser();
    } catch {
      authStore.logout();
      return "/login";
    }
  }

  const moduleKey = to.meta.moduleKey;
  if (moduleKey && !authStore.allowedModuleKeys.includes(moduleKey)) {
    const firstAllowed = authStore.allowedModuleKeys[0];
    const fallbackMap = {
      dashboard: "/dashboard",
      project: "/projects/list",
      requirement: "/requirements",
      task: "/tasks",
      test: "/quality/tests",
      collaboration: "/collaboration/timesheet",
      "okr-report": "/insight/okr",
      system: "/system/users",
    };
    return fallbackMap[firstAllowed] || "/dashboard";
  }

  return true;
});

router.afterEach((to) => {
  document.title = `${to.meta.title || "ProjectTrace"} - ProjectTrace`;
});

export default router;
