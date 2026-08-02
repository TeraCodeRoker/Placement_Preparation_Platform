import { createContext, useCallback, useContext, useEffect, useReducer } from "react";
import * as authApi from "../api/auth";

// Lightweight Context + reducer store (no heavyweight state lib for a surface
// this small). status: loading | authed | guest.
const AuthContext = createContext(null);

const initialState = { user: null, status: "loading" };

function reducer(state, action) {
  switch (action.type) {
    case "SET_USER":
      return { user: action.user, status: action.user ? "authed" : "guest" };
    default:
      return state;
  }
}

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // Try to restore a session on load (refresh cookie -> new access token).
  useEffect(() => {
    let active = true;
    authApi.restore().then((user) => {
      if (active) dispatch({ type: "SET_USER", user });
    });
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (creds) => {
    const user = await authApi.login(creds);
    dispatch({ type: "SET_USER", user });
    return user;
  }, []);

  const register = useCallback(async (creds) => {
    const user = await authApi.register(creds);
    dispatch({ type: "SET_USER", user });
    return user;
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    dispatch({ type: "SET_USER", user: null });
  }, []);

  const value = { ...state, login, register, logout };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
