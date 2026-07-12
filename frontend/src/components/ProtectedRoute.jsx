import { connect } from "react-redux";
import { Navigate } from "react-router-dom";

/**
 * Gate a route behind auth state loaded in Redux (see reducers/auth.jsx).
 *
 *   <ProtectedRoute requireAdmin><AdminDashboard /></ProtectedRoute>
 *   <ProtectedRoute requirePta><PTADashboard /></ProtectedRoute>
 *   <ProtectedRoute>{...any logged-in user...}</ProtectedRoute>
 */
const ProtectedRoute = ({
  isAuthenticated,
  user,
  requireAdmin = false,
  requirePta = false,
  children,
}) => {
  // isAuthenticated starts as `null` until checkAuthenticated() resolves;
  // avoid bouncing the user to /login during that brief loading window.
  if (isAuthenticated === null) {
    return (
      <div className="flex h-[60vh] items-center justify-center text-slate-400">
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !user?.is_staff) {
    return <Navigate to="/" replace />;
  }

  if (requirePta && !user?.pta) {
    return <Navigate to="/" replace />;
  }

  return children;
};

const mapStateToProps = (state) => ({
  isAuthenticated: state.auth?.isAuthenticated,
  user: state.auth?.user,
});

export default connect(mapStateToProps)(ProtectedRoute);
