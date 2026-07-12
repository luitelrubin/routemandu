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
} from "../actions/types";

const initialState = {
  access: localStorage.getItem("access"),
  refresh: localStorage.getItem("refresh"),
  isAuthenticated: null,
  user: null,
};

const Auth = (state = initialState, action) => {
  const { type, payload } = action;

  switch (type) {
    case AUTHENTICATION_SUCCESS:
      return {
        ...state,
        isAuthenticated: true,
      };
    case AUTHENTICATION_FAILURE:
    case REGISTRATION_SUCCESS:
      return {
        ...state,
        isAuthenticated: false,
      };
    case LOGIN_SUCCESS:
      localStorage.setItem("access", payload.access);
      localStorage.setItem("refresh", payload.refresh);
      return {
        ...state,
        access: payload.access,
        refresh: payload.refresh,
        isAuthenticated: true,
      };
    case LOGIN_FAILURE:
    case REGISTRATION_FAILURE:
    case LOGOUT:
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      return {
        ...state,
        access: null,
        refresh: null,
        isAuthenticated: false,
      };
    case USER_LOAD_SUCCESS:
      return {
        ...state,
        user: payload,
      };
    case USER_LOAD_FAILURE:
      return {
        ...state,
        user: null,
      };
    case PASSWORD_RESET_SUCCESS:
    case PASSWORD_RESET_FAILURE:
    case PASSWORD_RESET_CONFIRM_SUCCESS:
    case PASSWORD_RESET_CONFIRM_FAILURE:
    case ACTIVATION_SUCCESS:
    case ACTIVATION_FAILURE:
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      return {
        ...state,
        isAuthenticated: false,
      };
    default:
      return state;
  }
};

export default Auth;
