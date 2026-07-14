import { useRef, useState, useEffect } from "react";
import { connect } from "react-redux";
import { uploadGtfsFeed, getGtfsFeedInfo, deleteGtfsFeed, exportGtfsFeed } from "../../api/gtfs";
import { updateAgency } from "../../api/admin";

const PTADashboard = ({ user }) => {
  const pta = user?.pta;
  const fileInputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [updatingAgency, setUpdatingAgency] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const [feedInfo, setFeedInfo] = useState(null);
  const [loadingFeedInfo, setLoadingFeedInfo] = useState(true);

  const [agencyName, setAgencyName] = useState("");
  const [agencyColor, setAgencyColor] = useState("#2563eb");

  const fetchFeedInfo = async () => {
    try {
      const info = await getGtfsFeedInfo();
      setFeedInfo(info);
    } catch (err) {
      console.error("Failed to load feed info", err);
    } finally {
      setLoadingFeedInfo(false);
    }
  };

  useEffect(() => {
    if (pta) {
      fetchFeedInfo();
      setAgencyName(pta.name);
      setAgencyColor(pta.color);
    } else {
      setLoadingFeedInfo(false);
    }
  }, [pta]);

  const handleFileChange = (e) => {
    setFile(e.target.files?.[0] || null);
    setResult(null);
    setError(null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Choose a GTFS .zip file first.");
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);
    setProgress(0);
    try {
      const data = await uploadGtfsFeed({ file, name }, (evt) => {
        if (evt.total) setProgress(Math.round((evt.loaded / evt.total) * 100));
      });
      setResult(data);
      setFile(null);
      setName("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      await fetchFeedInfo();
    } catch (err) {
      setError(err?.response?.data?.error || "GTFS import failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleExport = async () => {
    setError(null);
    setResult(null);
    setExporting(true);
    try {
      const blob = await exportGtfsFeed();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${pta.name.replace(/\s+/g, "_")}_gtfs.zip`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      setError("Failed to export GTFS feed.");
    } finally {
      setExporting(false);
    }
  };

  const handleDelete = async () => {
    setError(null);
    setResult(null);
    if (!window.confirm("Are you sure you want to delete your GTFS feed? This will remove all route schedule data for your agency.")) {
      return;
    }
    setDeleting(true);
    try {
      await deleteGtfsFeed();
      setResult({ message: "GTFS feed deleted successfully." });
      setFeedInfo({ exists: false });
    } catch (err) {
      setError(err?.response?.data?.error || "Failed to delete GTFS feed.");
    } finally {
      setDeleting(false);
    }
  };

  const handleUpdateAgency = async (e) => {
    e.preventDefault();
    setUpdatingAgency(true);
    setError(null);
    setResult(null);
    try {
      await updateAgency(pta.id, { name: agencyName, color: agencyColor });
      setResult({ message: "Agency updated successfully!" });
    } catch (err) {
      setError(err?.response?.data ? JSON.stringify(err.response.data) : "Failed to update agency.");
    } finally {
      setUpdatingAgency(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900">My Agency</h1>

      {pta ? (
        <form onSubmit={handleUpdateAgency} className="mt-4 rounded-md border border-slate-200 p-4 flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <span
              className="h-8 w-8 shrink-0 rounded-full border border-slate-200"
              style={{ backgroundColor: agencyColor }}
            />
            <div>
              <p className="font-semibold text-slate-900">{agencyName || pta.name}</p>
              <p className="text-xs text-slate-500">Agency ID: {pta.id}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
                Agency Name
              </label>
              <input
                required
                type="text"
                value={agencyName}
                onChange={(e) => setAgencyName(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
                Route Color
              </label>
              <input
                type="color"
                value={agencyColor}
                onChange={(e) => setAgencyColor(e.target.value)}
                className="h-9 w-20 rounded border border-slate-300 cursor-pointer"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={updatingAgency}
            className="w-full rounded-md bg- px-4 py-2 bg-blue-600 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-60 transition-colors"
          >
            {updatingAgency ? "Saving..." : "Save Agency Details"}
          </button>
        </form>
      ) : (
        <p className="mt-4 text-sm text-slate-500">
          Your account isn't linked to a transit agency yet.
        </p>
      )}

      {pta && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-slate-900">Current GTFS Feed</h2>
          {loadingFeedInfo ? (
            <p className="text-sm text-slate-400 mt-2">Loading feed status...</p>
          ) : feedInfo && feedInfo.exists ? (
            <div className="mt-4 rounded-md border border-slate-200 p-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <p className="font-semibold text-slate-950">{feedInfo.name}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Uploaded: {new Date(feedInfo.created).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleExport}
                    disabled={exporting}
                    className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60 transition-colors"
                  >
                    {exporting ? "Exporting..." : "Export"}
                  </button>
                  <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60 transition-colors"
                  >
                    {deleting ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-400 mt-2">No feed uploaded yet.</p>
          )}
        </div>
      )}

      <h2 className="mt-8 text-lg font-semibold text-slate-900">Upload GTFS feed</h2>
      <p className="mt-1 text-sm text-slate-500">
        Uploading a new feed replaces your agency's current schedule data.
      </p>

      <form onSubmit={handleUpload} className="mt-4 flex flex-col gap-4">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
            GTFS .zip file
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            onChange={handleFileChange}
            className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-md file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
            Feed name (optional)
          </label>
          <input
            type="text"
            placeholder={`e.g. ${agencyName || pta?.name || "Agency"} - Summer 2026`}
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
          />
        </div>

        <button
          type="submit"
          disabled={uploading}
          className="w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition-colors"
        >
          {uploading ? `Uploading… ${progress}%` : "Upload and import"}
        </button>

        {uploading && (
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full bg-blue-600 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        {error && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        )}
        {result && (
          <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
            {result.message} {result.id ? `(feed #${result.id})` : ""}
          </p>
        )}
      </form>
    </div>
  );
};

const mapStateToProps = (state) => ({
  user: state.auth?.user,
});

export default connect(mapStateToProps)(PTADashboard);
