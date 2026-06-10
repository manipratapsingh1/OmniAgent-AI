/**
 * Application Routes
 * Centralized route definitions for consistency
 */

export const ROUTES = {
  // Auth Routes
  LOGIN: "/login",
  SIGNUP: "/signup",

  // Protected Routes
  DASHBOARD: "/",
  CHAT: "/chat",
  DOCUMENTS: "/documents",
  SETTINGS: "/settings",
  PROFILE: "/profile",

} as const;

export const ROUTE_LABELS = {
  [ROUTES.DASHBOARD]: "Dashboard",
  [ROUTES.CHAT]: "Chat",
  [ROUTES.DOCUMENTS]: "Documents",
  [ROUTES.SETTINGS]: "Settings",
  [ROUTES.PROFILE]: "Profile",
} as const;

export const PROTECTED_ROUTES = [
  ROUTES.DASHBOARD,
  ROUTES.CHAT,
  ROUTES.DOCUMENTS,
  ROUTES.SETTINGS,
  ROUTES.PROFILE,
] as const;
