import { useState } from "react";
import { connect } from "react-redux";
import { register } from "../actions/auth";
import { Navigate } from "react-router-dom";

const inputClass =
  "w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100";
const labelClass = "block text-sm font-medium text-slate-700 mb-1";

const Register = ({ register, isAuthenticated }) => {
  const [accountCreated, setAccountCreated] = useState(false);
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const { username, email, password, confirmPassword } = formData;
  const passwordsMismatch =
    confirmPassword.length > 0 && password !== confirmPassword;

  const handleChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.password === formData.confirmPassword) {
      register(username, email, password, confirmPassword);
      setAccountCreated(true);
    }
  };

  if (isAuthenticated) {
    return <Navigate to="/" />;
  }
  if (accountCreated) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center px-4 py-12">
      <h1 className="text-2xl font-bold text-slate-900">Sign up</h1>
      <p className="mt-1 text-sm text-slate-500">Create a new account.</p>

      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <div>
          <label className={labelClass} htmlFor="username">Username</label>
          <input
            className={inputClass}
            type="text"
            id="username"
            name="username"
            onChange={handleChange}
            value={username}
            required
          />
        </div>
        <div>
          <label className={labelClass} htmlFor="email">Email</label>
          <input
            className={inputClass}
            type="email"
            id="email"
            name="email"
            onChange={handleChange}
            value={email}
            required
          />
        </div>
        <div>
          <label className={labelClass} htmlFor="password">Password</label>
          <input
            className={inputClass}
            type="password"
            id="password"
            name="password"
            onChange={handleChange}
            value={password}
            required
          />
        </div>
        <div>
          <label className={labelClass} htmlFor="confirmPassword">Confirm Password</label>
          <input
            className={inputClass}
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            onChange={handleChange}
            value={confirmPassword}
            required
          />
          {passwordsMismatch && (
            <p className="mt-1 text-xs text-red-600">Passwords do not match.</p>
          )}
        </div>
        <button
          type="submit"
          disabled={passwordsMismatch}
          className="mt-2 w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition-colors"
        >
          Sign Up
        </button>
      </form>
    </div>
  );
};

const mapStateToProps = (state) => ({
  isAuthenticated: state.auth.isAuthenticated,
});

export default connect(mapStateToProps, { register })(Register);
