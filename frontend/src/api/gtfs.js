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
