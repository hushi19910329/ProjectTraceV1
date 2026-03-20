import http from "./http";

export function fetchProjects(params = {}) {
  return http.get("/projects", { params });
}

export function createProject(payload) {
  return http.post("/projects", payload);
}

export function fetchProject(projectId) {
  return http.get(`/projects/${projectId}`);
}

export function updateProject(projectId, payload) {
  return http.put(`/projects/${projectId}`, payload);
}

export function fetchProjectTasks(projectId, params = {}) {
  return http.get(`/projects/${projectId}/tasks`, { params });
}

export function fetchProjectTask(projectId, taskId) {
  return http.get(`/projects/${projectId}/tasks/${taskId}`);
}

export function createProjectTask(projectId, payload) {
  return http.post(`/projects/${projectId}/tasks`, payload);
}

export function updateProjectTask(projectId, taskId, payload) {
  return http.put(`/projects/${projectId}/tasks/${taskId}`, payload);
}

export function abandonProjectTask(projectId, taskId, payload) {
  return http.post(`/projects/${projectId}/tasks/${taskId}/abandon`, payload);
}

export function addTaskComment(projectId, taskId, payload) {
  return http.post(`/projects/${projectId}/tasks/${taskId}/comments`, payload);
}

export function uploadTaskAttachment(projectId, taskId, file) {
  const formData = new FormData();
  formData.append("file", file);
  return http.post(`/projects/${projectId}/tasks/${taskId}/attachments`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export function createTaskReminder(projectId, taskId, payload) {
  return http.post(`/projects/${projectId}/tasks/${taskId}/reminders`, payload);
}

export function fetchProjectLogs(projectId) {
  return http.get(`/projects/${projectId}/logs`);
}

export function fetchNotifications() {
  return http.get("/projects/notifications/me");
}

export function markNotificationRead(notificationId) {
  return http.post(`/projects/notifications/${notificationId}/read`);
}

export function markAllNotificationsRead() {
  return http.post("/projects/notifications/read-all");
}

export function downloadAttachment(projectId, attachmentId) {
  return http.get(`/projects/${projectId}/attachments/${attachmentId}/download`, {
    responseType: "blob",
  });
}

export function fetchAllTasks(params = {}) {
  return http.get("/projects/tasks/all", { params });
}

export function followProject(projectId) {
  return http.post(`/projects/${projectId}/follow`);
}

export function unfollowProject(projectId) {
  return http.delete(`/projects/${projectId}/follow`);
}

export function followTask(projectId, taskId) {
  return http.post(`/projects/${projectId}/tasks/${taskId}/follow`);
}

export function unfollowTask(projectId, taskId) {
  return http.delete(`/projects/${projectId}/tasks/${taskId}/follow`);
}
