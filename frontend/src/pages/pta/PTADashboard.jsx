import { useRef, useState } from "react";
import { connect } from "react-redux";
import { uploadGtfsFeed } from "../../api/gtfs";

const PTADashboard = ({ user }) => {
  const pta = user?.pta;
  const fileInputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

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
    } catch (err) {
      setError(err?.response?.data?.error || "GTFS import failed.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900">My Agency</h1>

      {pta ? (
        <div className="mt-4 flex items-center gap-3 rounded-md border border-slate-200 p-4">
          <span
            className="h-8 w-8 shrink-0 rounded-full border border-slate-200"
            style={{ backgroundColor: pta.color }}
          />
          <div>
            <p className="font-semibold text-slate-900">{pta.name}</p>
            <p className="text-xs text-slate-500">Agency ID: {pta.id}</p>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">
          Your account isn't linked to a transit agency yet.
        </p>
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
            placeholder={`e.g. ${pta?.name || "Agency"} - Summer 2026`}
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
            {result.message} (feed #{result.id})
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
