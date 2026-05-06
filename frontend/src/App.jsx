import React, { createContext, useState, useMemo } from "react";
import "./App.css";
import ChatPage from "./components/ChatPage";
import DocumentsPage from "./components/DocumentsPage";
import { ThemeToggle } from "./components/ThemeToggle";
import useLocalStorage from "use-local-storage-state";

export const AppContext = createContext();

const App = () => {
  const preference = window.matchMedia("(prefers-color-scheme: dark)").matches;

  const [isDark, setIsDark] = useLocalStorage("isDark", {
    defaultValue: preference,
  });


  const [activePage, setActivePage] = useState(
    () => localStorage.getItem("activePage") || "chat"
  );

  const handlePageChange = (page) => {
    localStorage.setItem("activePage", page);
    setActivePage(page);
  };

  const [messages, setMessages] = useState([]);

  const contextValue = useMemo(() => {
    return { isDark, setIsDark, messages, setMessages };
  }, [isDark, messages]);

  return (
    <AppContext.Provider value={contextValue}>
      <div className="App" data-theme={isDark ? "dark" : "light"}>

        <div className="navbar">
          <div className="navButtons">
            <button
              className={`navButton ${activePage === "chat" ? "active" : ""}`}
              onClick={() => handlePageChange("chat")}
            >
              Chat
            </button>
            <button
              className={`navButton ${activePage === "documents" ? "active" : ""}`}
              onClick={() => handlePageChange("documents")}
            >
              Documents
            </button>
          </div>
          <ThemeToggle />
        </div>

        <div className="pageContainer">
          {activePage === "chat" && <ChatPage />}
          {activePage === "documents" && <DocumentsPage />}
        </div>

        <div className="footer">
          © 2026 Company Knowledge Assistant
        </div>
      </div>
    </AppContext.Provider>
  );
};

export default App;