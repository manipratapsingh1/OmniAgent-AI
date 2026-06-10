/**
 * Sanitize user input to prevent XSS attacks
 */
export const sanitizeInput = (input: string | null | undefined): string => {
  if (!input) return "";
  
  const div = document.createElement("div");
  div.textContent = input;
  return div.innerHTML;
};

/**
 * Sanitize HTML entities
 */
export const escapeHtml = (text: string): string => {
  const map: { [key: string]: string } = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
};

/**
 * Validate and sanitize email
 */
export const sanitizeEmail = (email: string): string => {
  return email.trim().toLowerCase();
};

/**
 * Validate file name to prevent path traversal
 */
export const sanitizeFileName = (filename: string): string => {
  // Remove path traversal attempts
  const sanitized = filename.replace(/\.\./g, "").replace(/\//g, "").replace(/\\\\/g, "");
  // Keep only safe characters
  return sanitized.replace(/[^\w\s.-]/g, "");
};
