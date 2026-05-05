import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

// connect React to index.html
const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);