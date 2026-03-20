import http from "./http";

export function fetchUsers(params = {}) {
  return http.get("/users", { params });
}

export function createUser(payload) {
  return http.post("/users", payload);
}

export function updateUser(userId, payload) {
  return http.put(`/users/${userId}`, payload);
}

export function deleteUser(userId) {
  return http.delete(`/users/${userId}`);
}

export function fetchPermissionModules() {
  return http.get("/users/meta/modules");
}

export function fetchRoles() {
  return http.get("/users/meta/roles");
}
