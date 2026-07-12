import { useState } from "react";
import { connect } from "react-redux";
import { reset_password_confirm } from "../actions/auth.jsx";
import { Navigate, useParams } from "react-router-dom";

const ResetPasswordConfirm = ({ reset_password_confirm }) => {
  const [requestSent, setRequestSent] = useState(false);
  const [formData, setFormData] = useState({
    new_password: "",
    re_new_password: "",
  });
  const { uid, token } = useParams();
  const { new_password, re_new_password } = formData;
  const handleChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });
  const handleResetPassword = (e) => {
    e.preventDefault();
    reset_password_confirm(uid, token, new_password, re_new_password);
    setRequestSent(true);
  };
  if (requestSent) {
    return <Navigate to="/" />;
  }
  return (
    <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center px-4 py-12">
      <h1 className="text-2xl font-bold text-slate-900">Password reset confirmation</h1>
      <p className="mt-1 text-sm text-slate-500">
        Please enter a new password to log into your account.
      </p>
      <form onSubmit={handleResetPassword} className="mt-6 flex flex-col gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1" htmlFor="new_password">
            Password
          </label>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
            type="password"
            id="new_password"
            name="new_password"
            onChange={handleChange}
            value={new_password}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1" htmlFor="re_new_password">
            Confirm Password
          </label>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
            type="password"
            id="re_new_password"
            name="re_new_password"
            onChange={handleChange}
            value={re_new_password}
            required
          />
        </div>
        <button
          type="submit"
          className="rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
        >
          Confirm password reset
        </button>
      </form>
    </div>
  );
};

export default connect(null, { reset_password_confirm })(ResetPasswordConfirm);
