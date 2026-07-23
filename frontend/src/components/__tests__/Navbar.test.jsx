import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore, combineReducers } from "@reduxjs/toolkit";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Navbar from "../Navbar";
import Auth from "../../reducers/auth";

const rootReducer = combineReducers({ auth: Auth });

const makeStore = (preloadedState) =>
  configureStore({ reducer: rootReducer, preloadedState });

const renderNavbar = (preloadedState) =>
  render(
    <Provider store={makeStore(preloadedState)}>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<Navbar />} />
        </Routes>
      </MemoryRouter>
    </Provider>
  );

describe("Navbar", () => {
  it("shows a sign in link for guests", () => {
    renderNavbar({
      auth: { access: null, refresh: null, isAuthenticated: false, user: null },
    });
    expect(screen.getByText("Sign in")).toBeInTheDocument();
    expect(screen.queryByText("Logout")).not.toBeInTheDocument();
  });

  it("shows the username and logout button for authenticated users", () => {
    renderNavbar({
      auth: {
        access: "tok",
        refresh: "tok",
        isAuthenticated: true,
        user: { username: "alice", is_staff: false, pta: null },
      },
    });
    expect(screen.getAllByText("alice").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Logout").length).toBeGreaterThan(0);
    expect(screen.queryByText("Sign in")).not.toBeInTheDocument();
  });

  it("shows the Admin Panel link only for staff users", () => {
    renderNavbar({
      auth: {
        access: "tok",
        refresh: "tok",
        isAuthenticated: true,
        user: { username: "admin", is_staff: true, pta: null },
      },
    });
    expect(screen.getAllByText("Admin Panel").length).toBeGreaterThan(0);
  });

  it("hides the Admin Panel link for non-staff users", () => {
    renderNavbar({
      auth: {
        access: "tok",
        refresh: "tok",
        isAuthenticated: true,
        user: { username: "alice", is_staff: false, pta: null },
      },
    });
    expect(screen.queryByText("Admin Panel")).not.toBeInTheDocument();
  });

  it("shows the My Agency link only for pta owners", () => {
    renderNavbar({
      auth: {
        access: "tok",
        refresh: "tok",
        isAuthenticated: true,
        user: { username: "owner", is_staff: false, pta: { id: "sajha" } },
      },
    });
    expect(screen.getAllByText("My Agency").length).toBeGreaterThan(0);
  });

  it("logging out dispatches LOGOUT and clears tokens from localStorage", () => {
    window.localStorage.setItem("access", "tok");
    window.localStorage.setItem("refresh", "tok");
    const store = makeStore({
      auth: {
        access: "tok",
        refresh: "tok",
        isAuthenticated: true,
        user: { username: "alice", is_staff: false, pta: null },
      },
    });
    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={["/"]}>
          <Routes>
            <Route path="/" element={<Navbar />} />
          </Routes>
        </MemoryRouter>
      </Provider>
    );

    const [logoutButton] = screen.getAllByText("Logout");
    fireEvent.click(logoutButton);

    expect(store.getState().auth.isAuthenticated).toBe(false);
    expect(window.localStorage.getItem("access")).toBeNull();
  });
});
