import client from "./client";

/**
 * Upload + import a GTFS zip.
 * - PTA owners: just pass { file, name }.
 * - Admins uploading on behalf of an agency: also pass { ptaId }.
 */
export const uploadGtfsFeed = async ({ file, name, ptaId }, onUploadProgress) => {
  const formData = new FormData();
  formData.append("feed", file);
  if (name) formData.append("name", name);
  if (ptaId) formData.append("pta_id", ptaId);

  const res = await client.post("/gtfs/feed/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });
  return res.data;
};

export const getGtfsFeedInfo = async (ptaId = null) => {
  const url = ptaId ? `/gtfs/feed/?pta_id=${ptaId}` : "/gtfs/feed/";
  const res = await client.get(url);
  return res.data;
};

export const deleteGtfsFeed = async (ptaId = null) => {
  const url = ptaId ? `/gtfs/feed/` : "/gtfs/feed/";
  // For DELETE request, pass pta_id in data if needed or as query param. We support both in backend.
  const config = ptaId ? { data: { pta_id: ptaId } } : {};
  const res = await client.delete(url, config);
  return res.data;
};

export const exportGtfsFeed = async (ptaId = null) => {
  const url = ptaId ? `/gtfs/feed/?export=true&pta_id=${ptaId}` : "/gtfs/feed/?export=true";
  const res = await client.get(url, { responseType: "blob" });
  return res.data;
};
