import client from "./client";

// ---- Users (admin only) ----

export const listUsers = async () => {
  const res = await client.get("/api/users/");
  return res.data;
};

export const createUser = async (payload) => {
  const res = await client.post("/api/users/", payload);
  return res.data;
};

export const updateUser = async (id, payload) => {
  const res = await client.patch(`/api/users/${id}/`, payload);
  return res.data;
};

export const deleteUser = async (id) => {
  await client.delete(`/api/users/${id}/`);
};

// ---- Public Transit Agencies ----
// Admins see/manage every agency; PTA owners only ever see their own
// (the backend filters the list for them), so the same functions work
// for both the admin panel and the PTA owner panel.

export const listAgencies = async () => {
  const res = await client.get("/api/ptas/");
  return res.data;
};

export const createAgency = async (payload) => {
  const res = await client.post("/api/ptas/", payload);
  return res.data;
};

export const updateAgency = async (id, payload) => {
  const res = await client.patch(`/api/ptas/${id}/`, payload);
  return res.data;
};

export const deleteAgency = async (id) => {
  await client.delete(`/api/ptas/${id}/`);
};
