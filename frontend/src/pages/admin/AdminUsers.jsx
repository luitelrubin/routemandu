import { useEffect, useState } from "react";
import { listUsers, createUser, updateUser, deleteUser } from "../../api/admin";

const emptyForm = { username: "", email: "", password: "", is_staff: false };

const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await listUsers();
      setUsers(data);
    } catch (err) {
      console.error(err);
      setError("Couldn't load users.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createUser(form);
      setForm(emptyForm);
      setShowForm(false);
      await refresh();
    } catch (err) {
      setError(
        err?.response?.data
          ? JSON.stringify(err.response.data)
          : "Couldn't create user.",
      );
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (user, field) => {
    try {
      await updateUser(user.id, { [field]: !user[field] });
      await refresh();
    } catch (err) {
      console.error(err);
      setError("Couldn't update user.");
    }
  };

  const handleDelete = async (user) => {
    if (!window.confirm(`Delete user ${user.email}? This can't be undone.`)) return;
    try {
      await deleteUser(user.id);
      await refresh();
    } catch (err) {
      console.error(err);
      setError("Couldn't delete user.");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-900">Users</h2>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
        >
          {showForm ? "Cancel" : "New user"}
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
            placeholder="Username"
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
          />
          <input
            required
            type="email"
            placeholder="Email"
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <input
            required
            type="password"
            minLength={8}
            placeholder="Password"
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={form.is_staff}
              onChange={(e) => setForm({ ...form, is_staff: e.target.checked })}
            />
            Grant admin access
          </label>
          <button
            type="submit"
            disabled={saving}
            className="sm:col-span-2 rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60 transition-colors"
          >
            {saving ? "Creating…" : "Create user"}
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
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Username</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Email</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Agency</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Admin</th>
                <th className="px-3 py-2 text-left font-semibold text-slate-600">Active</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="px-3 py-2 text-slate-800">{user.username}</td>
                  <td className="px-3 py-2 text-slate-600">{user.email}</td>
                  <td className="px-3 py-2 text-slate-600">{user.pta?.name || "—"}</td>
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      checked={user.is_staff}
                      onChange={() => handleToggle(user, "is_staff")}
                    />
                  </td>
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      checked={user.is_active}
                      onChange={() => handleToggle(user, "is_active")}
                    />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <button
                      onClick={() => handleDelete(user)}
                      className="text-xs font-semibold text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AdminUsers;
