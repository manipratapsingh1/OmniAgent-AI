import React from 'react';

export const AuthContext = React.createContext({
  auth: {
    isAuthenticated: false,
    user: null,
    token: null,
    refreshToken: null
  },
  setAuth: () => {}
});
