import { useEffect, useState } from "react";
import { listAgencies } from "../../api/admin";
import { getGtfsFeedInfo, deleteGtfsFeed, exportGtfsFeed, uploadGtfsFeed } from "../../api/gtfs";

const AdminGtfs = () => {
  const [agencies, setAgencies] = useState([]);
  const [feedInfos, setFeedInfos] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploadingId, setUploadingId] = useState(null);
  const [exportingId, setExportingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  // System-wide GTFS feed: a single feed that may contain details for any
  // number of agencies at once (e.g. an agency.txt with several rows),
  // managed independently of any one agency's own feed.
  const [systemFeed, setSystemFeed] = useState({ exists: false });
  const [systemError, setSystemError] = useState(null);
  const [systemUploading, setSystemUploading] = useState(false);
  const [systemExporting, setSystemExporting] = useState(false);
  const [systemDeleting, setSystemDeleting] = useState(false);

  const refreshSystemFeed = async () => {
    try {
      const info = await getGtfsFeedInfo();
      setSystemFeed(info);
    } catch (err) {
      console.error("Failed to load system GTFS feed info", err);
      setSystemFeed({ exists: false });
    }
  };

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const agencyData = await listAgencies();
      setAgencies(agencyData);
      
      const feeds = {};
      await Promise.all(
        agencyData.map(async (agency) => {
          try {
            const info = await getGtfsFeedInfo(agency.id);
            feeds[agency.id] = info;
          } catch (err) {
            console.error(`Failed to load feed info for ${agency.id}`, err);
            feeds[agency.id] = { exists: false };
          }
        })
      );
      setFeedInfos(feeds);
    } catch (err) {
      console.error(err);
      setError("Couldn't load agencies and GTFS feeds.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    refreshSystemFeed();
  }, []);

  const handleSystemUpload = async (file) => {
    if (!file) return;
    setSystemUploading(true);
    setSystemError(null);
    try {
      await uploadGtfsFeed({ file });
      await refreshSystemFeed();
    } catch (err) {
      setSystemError(err?.response?.data?.error || "GTFS import failed.");
    } finally {
      setSystemUploading(false);
    }
  };

  const handleSystemExport = async () => {
    setSystemExporting(true);
    setSystemError(null);
    try {
      const blob = await exportGtfsFeed();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "system_gtfs.zip");
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      setSystemError("Failed to export the system GTFS feed.");
    } finally {
      setSystemExporting(false);
    }
  };

  const handleSystemDelete = async () => {
    if (!window.confirm("Delete the system-wide GTFS feed? This will remove all agencies, routes, and schedule data it contains.")) {
      return;
    }
    setSystemDeleting(true);
    setSystemError(null);
    try {
      await deleteGtfsFeed();
      await refreshSystemFeed();
    } catch (err) {
      setSystemError(err?.response?.data?.error || "Failed to delete the system GTFS feed.");
    } finally {
      setSystemDeleting(false);
    }
  };

  const handleUpload = async (agencyId, file) => {
    if (!file) return;
    setUploadingId(agencyId);
    setError(null);
    try {
      await uploadGtfsFeed({ file, ptaId: agencyId });
      await refresh();
    } catch (err) {
      setError(err?.response?.data?.error || `GTFS import failed.`);
    } finally {
      setUploadingId(null);
    }
  };

  const handleExport = async (agency) => {
    setExportingId(agency.id);
    try {
      const blob = await exportGtfsFeed(agency.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${agency.name.replace(/\s+/g, "_")}_gtfs.zip`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      setError(`Failed to export GTFS feed for ${agency.name}.`);
    } finally {
      setExportingId(null);
    }
  };

  const handleDelete = async (agency) => {
    if (!window.confirm(`Delete GTFS feed for agency "${agency.name}"? This will remove all route schedule data for this agency.`)) {
      return;
    }
    setDeletingId(agency.id);
    try {
      await deleteGtfsFeed(agency.id);
      await refresh();
    } catch (err) {
      setError(err?.response?.data?.error || `Failed to delete GTFS feed for ${agency.name}.`);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-900">GTFS Feeds Management</h2>
        <button
          onClick={() => { refresh(); refreshSystemFeed(); }}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="mb-6 rounded-md border border-slate-200 p-4">
        <h3 className="text-sm font-semibold text-slate-900">System GTFS Feed</h3>
        <p className="mt-1 text-xs text-slate-500">
          A single GTFS feed covering any number of agencies at once (e.g. a zip whose
          agency.txt lists several agencies), separate from individual agencies' own feeds below.
        </p>

        {systemError && (
          <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 break-words">
            {systemError}
          </p>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-3">
          <label className={`cursor-pointer rounded-md bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100 transition-colors ${systemUploading ? "opacity-60 pointer-events-none" : ""}`}>
            {systemUploading ? "Uploading..." : "Upload GTFS"}
            <input
              type="file"
              accept=".zip"
              className="hidden"
              onChange={(e) => handleSystemUpload(e.target.files?.[0])}
              disabled={systemUploading}
            />
          </label>

          <button
            onClick={handleSystemExport}
            disabled={!systemFeed?.exists || systemExporting}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition-colors"
          >
            {systemExporting ? "Exporting..." : "Export GTFS"}
          </button>

          <button
            onClick={handleSystemDelete}
            disabled={!systemFeed?.exists || systemDeleting}
            className="rounded-md border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 transition-colors"
          >
            {systemDeleting ? "Deleting..." : "Delete GTFS"}
          </button>
        </div>

        <div className="mt-3 text-xs text-slate-600">
          {systemFeed?.exists ? (
            <>
              <div>
                <span className="font-semibold">{systemFeed.name}</span>{" "}
                <span className="text-slate-400">uploaded {new Date(systemFeed.created).toLocaleString()}</span>
              </div>
              {Array.isArray(systemFeed.agencies) && systemFeed.agencies.length > 0 && (
                <div className="mt-1">
                  Agencies in this feed: {systemFeed.agencies.map((a) => a.name).join(", ")}
                </div>
              )}
            </>
          ) : (
            <span className="text-slate-400">No system-wide feed uploaded</span>
          )}
        </div>
      </div>

      {error && (
        <p className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 break-words">
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-sm text-slate-400">Loading agencies and feeds…</p>
      ) : (
        <div className="overflow-x-auto rounded-md border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Agency</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Feed Name</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Uploaded At</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {agencies.map((agency) => {
                const feed = feedInfos[agency.id];
                const isUploading = uploadingId === agency.id;
                const isExporting = exportingId === agency.id;
                const isDeleting = deletingId === agency.id;

                return (
                  <tr key={agency.id}>
                    <td className="px-3 py-2">
                      <div className="font-semibold text-slate-800">{agency.name}</div>
                      <div className="text-xs text-slate-500 font-mono">{agency.id}</div>
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {feed?.exists ? feed.name : <span className="text-slate-400">No feed uploaded</span>}
                    </td>
                    <td className="px-3 py-2 text-slate-500">
                      {feed?.exists ? new Date(feed.created).toLocaleString() : "—"}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex flex-wrap items-center gap-3">
                        <label className={`cursor-pointer rounded-md bg-blue-50 px-2.5 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100 transition-colors ${isUploading ? "opacity-60 pointer-events-none" : ""}`}>
                          {isUploading ? "Importing..." : "Import ZIP"}
                          <input
                            type="file"
                            accept=".zip"
                            className="hidden"
                            onChange={(e) => handleUpload(agency.id, e.target.files?.[0])}
                            disabled={isUploading}
                          />
                        </label>
                        
                        {feed?.exists && (
                          <>
                            <button
                              onClick={() => handleExport(agency)}
                              disabled={isExporting}
                              className="text-xs font-semibold text-slate-600 hover:underline disabled:opacity-50"
                            >
                              {isExporting ? "Exporting..." : "Export"}
                            </button>
                            <button
                              onClick={() => handleDelete(agency)}
                              disabled={isDeleting}
                              className="text-xs font-semibold text-red-600 hover:underline disabled:opacity-50"
                            >
                              {isDeleting ? "Deleting..." : "Delete"}
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AdminGtfs;
