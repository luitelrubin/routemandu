import { useEffect } from "react";
import Navbar from "../components/Navbar";
import { connect } from "react-redux";
import { checkAuthenticated, load_user } from "../actions/auth.jsx";

const Layout = (props) => {
  useEffect(() => {
    props.checkAuthenticated();
    props.load_user();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1 flex flex-col">{props.children}</main>
    </div>
  );
};

export default connect(null, { checkAuthenticated, load_user })(Layout);
