import { describe, it, expect, beforeEach } from "vitest";
import Auth from "../auth";
import {
  ACTIVATION_FAILURE,
  ACTIVATION_SUCCESS,
  AUTHENTICATION_FAILURE,
  AUTHENTICATION_SUCCESS,
  LOGIN_FAILURE,
  LOGIN_SUCCESS,
  LOGOUT,
  PASSWORD_RESET_CONFIRM_FAILURE,
  PASSWORD_RESET_CONFIRM_SUCCESS,
  PASSWORD_RESET_FAILURE,
  PASSWORD_RESET_SUCCESS,
  REGISTRATION_FAILURE,
  REGISTRATION_SUCCESS,
  USER_LOAD_FAILURE,
  USER_LOAD_SUCCESS,
} from "../../actions/types";

const baseState = {
  access: null,
  refresh: null,
  isAuthenticated: null,
  user: null,
};

describe("Auth reducer", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("returns the initial state for an unknown action", () => {
    expect(Auth(baseState, { type: "SOMETHING_ELSE" })).toEqual(baseState);
  });

  it("AUTHENTICATION_SUCCESS marks the user authenticated", () => {
    const state = Auth(baseState, { type: AUTHENTICATION_SUCCESS });
    expect(state.isAuthenticated).toBe(true);
  });

  it("AUTHENTICATION_FAILURE marks the user unauthenticated", () => {
    const state = Auth(baseState, { type: AUTHENTICATION_FAILURE });
    expect(state.isAuthenticated).toBe(false);
  });

  it("REGISTRATION_SUCCESS marks the user unauthenticated (must still log in)", () => {
    const state = Auth(baseState, { type: REGISTRATION_SUCCESS });
    expect(state.isAuthenticated).toBe(false);
  });

  it("LOGIN_SUCCESS stores tokens in localStorage and state", () => {
    const state = Auth(baseState, {
      type: LOGIN_SUCCESS,
      payload: { access: "access-token", refresh: "refresh-token" },
    });
    expect(state.access).toBe("access-token");
    expect(state.refresh).toBe("refresh-token");
    expect(state.isAuthenticated).toBe(true);
    expect(window.localStorage.getItem("access")).toBe("access-token");
    expect(window.localStorage.getItem("refresh")).toBe("refresh-token");
  });

  it.each([LOGIN_FAILURE, REGISTRATION_FAILURE, LOGOUT])(
    "%s clears tokens from localStorage and state",
    (type) => {
      window.localStorage.setItem("access", "stale-access");
      window.localStorage.setItem("refresh", "stale-refresh");
      const state = Auth(
        { ...baseState, access: "stale-access", refresh: "stale-refresh" },
        { type }
      );
      expect(state.access).toBeNull();
      expect(state.refresh).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(window.localStorage.getItem("access")).toBeNull();
      expect(window.localStorage.getItem("refresh")).toBeNull();
    }
  );

  it("USER_LOAD_SUCCESS stores the user payload", () => {
    const user = { id: 1, username: "alice", is_staff: false };
    const state = Auth(baseState, { type: USER_LOAD_SUCCESS, payload: user });
    expect(state.user).toEqual(user);
  });

  it("USER_LOAD_FAILURE clears the user", () => {
    const state = Auth(
      { ...baseState, user: { id: 1 } },
      { type: USER_LOAD_FAILURE }
    );
    expect(state.user).toBeNull();
  });

  it.each([
    PASSWORD_RESET_SUCCESS,
    PASSWORD_RESET_FAILURE,
    PASSWORD_RESET_CONFIRM_SUCCESS,
    PASSWORD_RESET_CONFIRM_FAILURE,
    ACTIVATION_SUCCESS,
    ACTIVATION_FAILURE,
  ])("%s logs the user out (clears tokens, deauthenticates)", (type) => {
    window.localStorage.setItem("access", "stale-access");
    window.localStorage.setItem("refresh", "stale-refresh");
    const state = Auth(
      { ...baseState, isAuthenticated: true },
      { type }
    );
    expect(state.isAuthenticated).toBe(false);
    expect(window.localStorage.getItem("access")).toBeNull();
    expect(window.localStorage.getItem("refresh")).toBeNull();
  });
});
