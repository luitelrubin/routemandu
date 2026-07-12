import { useState } from "react";
import { Navigate, useParams } from "react-router-dom";
import { activate } from "../actions/auth";
import { connect } from "react-redux";

const Activate = ({ activate }) => {
  const [isActivated, setActivated] = useState(false);
  const { uid, token } = useParams();
  const handleActivate = () => {
    activate(uid, token);
    setActivated(true);
  };
  if (isActivated) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="mx-auto flex w-full max-w-sm flex-1 flex-col items-center justify-center px-4 py-12 text-center">
      <h1 className="text-2xl font-bold text-slate-900">Activate your account</h1>
      <p className="mt-1 text-sm text-slate-500">
        Click below to confirm your email and activate your account.
      </p>
      <button
        onClick={handleActivate}
        className="mt-6 rounded-md border border-blue-600 px-4 py-2 text-sm font-semibold text-blue-600 hover:bg-blue-50 transition-colors"
      >
        Activate
      </button>
    </div>
  );
};

export default connect(null, { activate })(Activate);
