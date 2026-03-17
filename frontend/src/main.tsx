/**
 * App entry point: mount the React app into the DOM.
 * Global styles are loaded from index.css.
 */
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

createRoot(document.getElementById("root")!).render(<App />);
