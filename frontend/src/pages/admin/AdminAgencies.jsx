import { useEffect, useState } from "react";
import {
  listAgencies,
  createAgency,
  updateAgency,
  deleteAgency,
  listUsers,
} from "../../api/admin";

const emptyForm = { id: "", name: "", color: "#2563eb", owner: "" };

const AdminAgencies = () => {
  const [agencies, setAgencies] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const [agencyData, userData] = await Promise.all([listAgencies(), listUsers()]);
      setAgencies(agencyData);
      setUsers(userData);
    } catch (err) {
      console.error(err);
      setError("Couldn't load agencies.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  // Only users without an agency already can be assigned as a new owner.
  const availableOwners = users.filter((u) => !u.pta);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createAgency(form);
      setForm(emptyForm);
      setShowForm(false);
      await refresh();
    } catch (err) {
      setError(
        err?.response?.data
          ? JSON.stringify(err.response.data)
          : "Couldn't create agency.",
      );
    } finally {
      setSaving(false);
    }
  };

  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: "", color: "" });

  const startEdit = (agency) => {
    setEditingId(agency.id);
    setEditForm({ name: agency.name, color: agency.color });
  };

  const handleUpdate = async (agencyId) => {
    try {
      await updateAgency(agencyId, { name: editForm.name, color: editForm.color });
      setEditingId(null);
      await refresh();
    } catch (err) {
      console.error(err);
      setError("Couldn't update agency.");
    }
  };

  const handleDelete = async (agency) => {
    if (!window.confirm(`Delete agency "${agency.name}"? This can't be undone.`)) return;
    try {
      await deleteAgency(agency.id);
      await refresh();
    } catch (err) {
      console.error(err);
      setError("Couldn't delete agency.");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-900">Transit Agencies</h2>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
        >
          {showForm ? "Cancel" : "New agency"}
        </button>
      </div>

      {error && (
        <p className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 break-words">
          {error}
        </p>
      )}

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="mb-6 grid grid-cols-1 sm:grid-cols-2 gap-3 rounded-md border border-slate-200 p-4"
        >
          <input
            required
            placeholder="Agency ID (e.g. KTM)"
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.id}
            onChange={(e) => setForm({ ...form, id: e.target.value })}
          />
          <input
            required
            placeholder="Agency name"
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <label className="flex items-center gap-2 text-sm text-slate-700">
            Route color
            <input
              type="color"
              className="h-8 w-14 rounded border border-slate-300"
              value={form.color}
              onChange={(e) => setForm({ ...form, color: e.target.value })}
            />
          </label>
          <select
            required
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.owner}
            onChange={(e) => setForm({ ...form, owner: e.target.value })}
          >
            <option value="">Select owner…</option>
            {availableOwners.map((u) => (
              <option key={u.id} value={u.id}>
                {u.username} ({u.email})
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={saving}
            className="sm:col-span-2 rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60 transition-colors"
          >
            {saving ? "Creating…" : "Create agency"}
          </button>
        </form>
      )}

      {loading ? (
        <p className="text-sm text-slate-400">Loading…</p>
      ) : (
        <div className="overflow-x-auto rounded-md border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">ID</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Name</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Color</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Owner</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {agencies.map((agency) => {
                const isEditing = editingId === agency.id;
                return (
                  <tr key={agency.id}>
                    <td className="px-3 py-2 font-mono text-xs text-slate-500">{agency.id}</td>
                    <td className="px-3 py-2 text-slate-800">
                      {isEditing ? (
                        <input
                          required
                          className="rounded-md border border-slate-300 px-2 py-1 text-sm w-full"
                          value={editForm.name}
                          onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        />
                      ) : (
                        agency.name
                      )}
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="color"
                        className="h-7 w-11 rounded border border-slate-300"
                        value={isEditing ? editForm.color : agency.color}
                        disabled={!isEditing}
                        onChange={(e) => {
                          if (isEditing) {
                            setEditForm({ ...editForm, color: e.target.value });
                          }
                        }}
                      />
                    </td>
                    <td className="px-3 py-2 text-slate-600">
                      {agency.owner_detail?.email || agency.owner}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {isEditing ? (
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => handleUpdate(agency.id)}
                            className="text-xs font-semibold text-green-600 hover:underline"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="text-xs font-semibold text-slate-500 hover:underline"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => startEdit(agency)}
                            className="text-xs font-semibold text-blue-600 hover:underline"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(agency)}
                            className="text-xs font-semibold text-red-600 hover:underline"
                          >
                            Delete
                          </button>
                        </div>
                      )}
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

export default AdminAgencies;
