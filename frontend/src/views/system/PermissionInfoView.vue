<template>
  <section class="card system-guide-page">
    <div class="section-head">
      <div>
        <h2 class="section-title">📘 系统说明中心</h2>
        <p class="section-subtitle">统一维护图标、权限、板块功能与操作规则说明，支持快速定位。</p>
      </div>
    </div>

    <div class="system-guide-layout">
      <aside class="guide-nav">
        <a
          v-for="item in sections"
          :key="item.id"
          class="guide-nav-link"
          :class="{ active: activeSection === item.id }"
          @click="scrollToSection(item.id)"
        >
          {{ item.label }}
        </a>
      </aside>

      <main class="guide-content">
        <section id="icons" class="guide-block">
          <h3>图标说明</h3>
          <p>项目状态：⚪ 未开始、🟡 进行中、⏸️ 已暂停、✅ 已完成。</p>
          <p>任务状态：⚪ 待开始、🟡 进行中、⛔ 阻塞、✅ 已完成、🗑️ 已废弃。</p>
          <p>优先级：🟢 低、🔵 中、🟠 高、🔴 紧急。</p>
        </section>

        <section id="permissions" class="guide-block">
          <h3>权限说明</h3>
          <p>身份标签：用于标识人员业务身份，可多选（前端、后端、测试、运维等）。</p>
          <p>系统角色：用于控制系统操作权限，采用 RBAC，可多角色并集。</p>
          <p>板块权限：控制用户可访问的模块菜单范围。</p>
          <p>项目权限：控制可见项目、可参与项目和保密项目访问范围。</p>
        </section>

        <section id="module-dashboard" class="guide-block">
          <h3>工作台说明</h3>
          <p>用于总览个人待办、项目进度和关键提醒。</p>
        </section>

        <section id="module-project" class="guide-block">
          <h3>项目管理说明</h3>
          <p>支持项目清单、任务清单、关注项目、关注任务。</p>
          <p>支持项目筛选、分页、行展开查看关键信息与任务概览。</p>
        </section>

        <section id="module-requirement" class="guide-block">
          <h3>需求管理说明</h3>
          <p>用于需求池管理、需求拆分与优先级规划。</p>
        </section>

        <section id="module-task" class="guide-block">
          <h3>任务管理说明</h3>
          <p>任务支持主子层级、状态更新历史、提醒、评论、附件和关注。</p>
        </section>

        <section id="module-test" class="guide-block">
          <h3>测试与缺陷说明</h3>
          <p>用于测试计划、缺陷跟踪与质量结果管理。</p>
        </section>

        <section id="module-collaboration" class="guide-block">
          <h3>协作中心说明</h3>
          <p>消息待办聚合评论@、任务提醒和分配通知。</p>
        </section>

        <section id="module-okr-report" class="guide-block">
          <h3>OKR与报表说明</h3>
          <p>用于目标对齐、过程晾晒和统计可视化。</p>
        </section>

        <section id="module-system" class="guide-block">
          <h3>系统管理说明</h3>
          <p>用于账号、角色、权限、标签和系统配置管理。</p>
        </section>
      </main>
    </div>
  </section>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const activeSection = ref("icons");

const sections = [
  { id: "icons", label: "图标说明" },
  { id: "permissions", label: "权限说明" },
  { id: "module-dashboard", label: "工作台" },
  { id: "module-project", label: "项目管理" },
  { id: "module-requirement", label: "需求管理" },
  { id: "module-task", label: "任务管理" },
  { id: "module-test", label: "测试缺陷" },
  { id: "module-collaboration", label: "协作中心" },
  { id: "module-okr-report", label: "OKR报表" },
  { id: "module-system", label: "系统管理" },
];

function normalizeSection(section) {
  const ids = new Set(sections.map((item) => item.id));
  return ids.has(section) ? section : "icons";
}

function scrollToSection(section, updateRoute = true) {
  const target = normalizeSection(section);
  const el = document.getElementById(target);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  activeSection.value = target;
  if (updateRoute) {
    router.replace({ path: route.path, query: { ...route.query, section: target } });
  }
}

onMounted(async () => {
  await nextTick();
  scrollToSection(String(route.query.section || "icons"), false);
});

watch(
  () => route.query.section,
  async (value) => {
    await nextTick();
    scrollToSection(String(value || "icons"), false);
  },
);
</script>

<style scoped>
.system-guide-layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 12px;
}

.guide-nav {
  position: sticky;
  top: 70px;
  align-self: start;
  display: grid;
  gap: 6px;
}

.guide-nav-link {
  display: block;
  padding: 8px 10px;
  border-radius: 6px;
  color: #606266;
  cursor: pointer;
  background: #f5f7fa;
}

.guide-nav-link.active,
.guide-nav-link:hover {
  background: #e8f3ff;
  color: #409eff;
}

.guide-content {
  display: grid;
  gap: 10px;
}

.guide-block {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
}

.guide-block h3 {
  margin: 0 0 8px;
}

.guide-block p {
  margin: 4px 0;
  color: #606266;
}

@media (max-width: 960px) {
  .system-guide-layout {
    grid-template-columns: 1fr;
  }

  .guide-nav {
    position: static;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
