import { Fragment, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { logout } from "../actions/auth.jsx";
import { connect } from "react-redux";

const navLink =
  "px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors";
const primaryBtn =
  "px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors";
const ghostBtn =
  "px-4 py-2 text-sm font-semibold text-slate-700 rounded-md hover:bg-slate-100 transition-colors";

const Navbar = ({ logout, isAuthenticated, user }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    setMenuOpen(false);
    navigate("/");
  };

  const guestLinks = () => (
    <Fragment>
      <Link to="/login" className={primaryBtn}>
        Sign in
      </Link>
    </Fragment>
  );

  const authLinks = () => (
    <Fragment>
      {user?.is_staff && (
        <Link to="/admin" className={navLink}>
          Admin Panel
        </Link>
      )}
      {user?.pta && (
        <Link to="/agency" className={navLink}>
          My Agency
        </Link>
      )}
      <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
        <span className="text-sm text-slate-500 hidden sm:inline">
          {user?.username}
        </span>
        <button onClick={handleLogout} className={ghostBtn}>
          Logout
        </button>
      </div>
    </Fragment>
  );

  return (
    <nav className="sticky top-0 z-[1000] bg-white border-b border-slate-200 shadow-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="flex h-14 items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-bold text-lg text-slate-900">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-blue-600 text-white text-sm">
              R
            </span>
            Routemandu
          </Link>

          <div className="hidden md:flex items-center gap-1">
            {isAuthenticated ? authLinks() : guestLinks()}
          </div>

          <button
            className="md:hidden p-2 text-slate-600"
            onClick={() => setMenuOpen((o) => !o)}
            aria-label="Toggle menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

        {menuOpen && (
          <div className="md:hidden flex flex-col gap-1 pb-3">
            {isAuthenticated ? authLinks() : guestLinks()}
          </div>
        )}
      </div>
    </nav>
  );
};

const mapStateToProps = (state) => ({
  isAuthenticated: state.auth?.isAuthenticated,
  user: state.auth?.user,
});

export default connect(mapStateToProps, { logout })(Navbar);
