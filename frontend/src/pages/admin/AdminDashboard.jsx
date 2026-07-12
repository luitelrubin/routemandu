import { useState } from "react";
import AdminUsers from "./AdminUsers";
import AdminAgencies from "./AdminAgencies";

const tabs = [
  { key: "users", label: "Users", Component: AdminUsers },
  { key: "agencies", label: "Agencies", Component: AdminAgencies },
];

const AdminDashboard = () => {
  const [active, setActive] = useState("users");
  const ActiveComponent = tabs.find((t) => t.key === active).Component;

  return (
    <div className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900">Admin</h1>
      <p className="mt-1 text-sm text-slate-500">
        Manage user accounts and public transit agencies.
      </p>

      <div className="mt-6 flex gap-1 border-b border-slate-200">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              active === tab.key
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="mt-6">
        <ActiveComponent />
      </div>
    </div>
  );
};

export default AdminDashboard;
