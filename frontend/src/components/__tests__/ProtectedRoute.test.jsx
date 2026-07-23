import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { createStore } from "redux";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "../ProtectedRoute";

const makeStore = (authState) =>
  createStore(() => ({ auth: authState }));

const renderWithProviders = (authState, ui) =>
  render(
    <Provider store={makeStore(authState)}>
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/" element={<div>Home Page</div>} />
          <Route path="/protected" element={ui} />
        </Routes>
      </MemoryRouter>
    </Provider>
  );

describe("ProtectedRoute", () => {
  it("shows a loading state while isAuthenticated is null", () => {
    renderWithProviders(
      { isAuthenticated: null, user: null },
      <ProtectedRoute>
        <div>Secret</div>
      </ProtectedRoute>
    );
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    expect(screen.queryByText("Secret")).not.toBeInTheDocument();
  });

  it("redirects to /login when not authenticated", () => {
    renderWithProviders(
      { isAuthenticated: false, user: null },
      <ProtectedRoute>
        <div>Secret</div>
      </ProtectedRoute>
    );
    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });

  it("renders children when authenticated with no extra requirements", () => {
    renderWithProviders(
      { isAuthenticated: true, user: { username: "alice" } },
      <ProtectedRoute>
        <div>Secret</div>
      </ProtectedRoute>
    );
    expect(screen.getByText("Secret")).toBeInTheDocument();
  });

  it("redirects home when requireAdmin is set but user is not staff", () => {
    renderWithProviders(
      { isAuthenticated: true, user: { username: "alice", is_staff: false } },
      <ProtectedRoute requireAdmin>
        <div>Admin Page</div>
      </ProtectedRoute>
    );
    expect(screen.getByText("Home Page")).toBeInTheDocument();
  });

  it("renders children when requireAdmin is set and user is staff", () => {
    renderWithProviders(
      { isAuthenticated: true, user: { username: "alice", is_staff: true } },
      <ProtectedRoute requireAdmin>
        <div>Admin Page</div>
      </ProtectedRoute>
    );
    expect(screen.getByText("Admin Page")).toBeInTheDocument();
  });

  it("redirects home when requirePta is set but user has no pta", () => {
    renderWithProviders(
      { isAuthenticated: true, user: { username: "alice", pta: null } },
      <ProtectedRoute requirePta>
        <div>Agency Page</div>
      </ProtectedRoute>
    );
    expect(screen.getByText("Home Page")).toBeInTheDocument();
  });

  it("renders children when requirePta is set and user has a pta", () => {
    renderWithProviders(
      {
        isAuthenticated: true,
        user: { username: "alice", pta: { id: "sajha", name: "Sajha" } },
      },
      <ProtectedRoute requirePta>
        <div>Agency Page</div>
      </ProtectedRoute>
    );
    expect(screen.getByText("Agency Page")).toBeInTheDocument();
  });
});
