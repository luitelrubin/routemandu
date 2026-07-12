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
} from "./types";
import axios from "axios";
import client, { API_URL } from "../api/client";

export const checkAuthenticated = () => async (dispatch) => {
  const access = localStorage.getItem("access");
  if (!access) {
    dispatch({ type: AUTHENTICATION_FAILURE });
    return;
  }

  try {
    const res = await axios.post(`${API_URL}/auth/jwt/verify/`, {
      token: access,
    });

    if (res.data.code !== "token_not_valid") {
      dispatch({ type: AUTHENTICATION_SUCCESS });
    } else {
      dispatch({ type: AUTHENTICATION_FAILURE });
    }
  } catch (err) {
    console.error(err);
    dispatch({ type: AUTHENTICATION_FAILURE });
  }
};

export const load_user = () => async (dispatch) => {
  if (!localStorage.getItem("access")) {
    dispatch({ type: USER_LOAD_FAILURE });
    return;
  }

  try {
    const res = await client.get("/auth/users/me/");
    dispatch({ type: USER_LOAD_SUCCESS, payload: res.data });
  } catch (err) {
    console.error(err);
    dispatch({ type: USER_LOAD_FAILURE });
  }
};

export const login = (email, password) => async (dispatch) => {
  try {
    const res = await axios.post(`${API_URL}/auth/jwt/create/`, {
      email,
      password,
    });

    dispatch({ type: LOGIN_SUCCESS, payload: res.data });
    dispatch(load_user());
  } catch (err) {
    console.error(err);
    dispatch({ type: LOGIN_FAILURE });
  }
};

export const logout = () => async (dispatch) => {
  dispatch({ type: LOGOUT });
};

export const reset_password = (email) => async (dispatch) => {
  try {
    await axios.post(`${API_URL}/auth/users/reset_password/`, { email });
    dispatch({ type: PASSWORD_RESET_SUCCESS });
  } catch (err) {
    console.error(err);
    dispatch({ type: PASSWORD_RESET_FAILURE });
  }
};

export const reset_password_confirm =
  (uid, token, new_password, re_new_password) => async (dispatch) => {
    try {
      await axios.post(`${API_URL}/auth/users/reset_password_confirm/`, {
        uid,
        token,
        new_password,
        re_new_password,
      });
      dispatch({ type: PASSWORD_RESET_CONFIRM_SUCCESS });
    } catch (err) {
      console.error(err);
      dispatch({ type: PASSWORD_RESET_CONFIRM_FAILURE });
    }
  };

export const register =
  (username, email, password, confirmPassword) => async (dispatch) => {
    try {
      const res = await axios.post(`${API_URL}/auth/users/`, {
        username,
        email,
        password,
        re_password: confirmPassword,
      });

      dispatch({ type: REGISTRATION_SUCCESS, payload: res.data });
    } catch (err) {
      console.error(err);
      dispatch({ type: REGISTRATION_FAILURE });
    }
  };

export const activate = (uid, token) => async (dispatch) => {
  try {
    await axios.post(`${API_URL}/auth/users/activation/`, { uid, token });
    dispatch({ type: ACTIVATION_SUCCESS });
  } catch (err) {
    console.error(err);
    dispatch({ type: ACTIVATION_FAILURE });
  }
};
