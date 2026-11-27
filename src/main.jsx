
import React, { useEffect } from "react";

import { createRoot } from "react-dom/client";

import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useLocation
} from "react-router-dom";

import { CheckCircle2 } from "lucide-react";

import {
  StoreProvider,
  useStore
} from "./store/CVStore";

import HomePage from "./pages/HomePage";
import TemplatesPage from "./pages/TemplatesPage";
import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";
import MyCVs from "./pages/MyCVs";
import Information from "./pages/Information";
import SettingsPage from "./pages/SettingsPage";
import Builder from "./pages/CVBuilder";

import "./index.css";


/* =========================================
   READ SAVED PREFERENCES
========================================= */

function getPreferences() {

  try {

    return JSON.parse(
      localStorage.getItem("cvtool_preferences")
    ) || {};

  } catch {

    return {};

  }

}


/* =========================================
   APPLICATION APPEARANCE CONTROLLER
========================================= */

function ThemeController() {

  const location = useLocation();

  useEffect(() => {

    const root = document.documentElement;

    const pathname = location.pathname
      .replace(/\/+$/, "")
      .toLowerCase();

    const workspacePages = [
      "/dashboard",
      "/my-cvs",
      "/information",
      "/settings"
    ];

    const isWorkspace =
      workspacePages.includes(pathname) ||
      pathname.startsWith("/builder/");


    /* SYSTEM THEME */

    const media = window.matchMedia(
      "(prefers-color-scheme: dark)"
    );


    /* LOAD PREFERENCES */

    let preferences = getPreferences();


    /* APPLY APPEARANCE */

    const applyAppearance = () => {

      // Keep public pages in normal light mode

      if (!isWorkspace) {

        root.classList.remove("cv-dark");

        root.classList.remove("cv-compact");

        return;

      }


      /* DARK MODE */

      const theme = preferences.theme || "light";

      const isDark =
        theme === "dark" ||
        (
          theme === "system" &&
          media.matches
        );

      root.classList.toggle(
        "cv-dark",
        isDark
      );


      /* COMPACT WORKSPACE */

      root.classList.toggle(
        "cv-compact",
        preferences.compact === true
      );

    };


    /* HANDLE SAVED PREFERENCES */

    const handlePreferencesChanged = () => {

      preferences = getPreferences();

      applyAppearance();

    };


    /* HANDLE IMMEDIATE SETTINGS PREVIEW */

    const handlePreferencesPreview = event => {

      preferences = {

        ...preferences,

        ...event.detail

      };

      applyAppearance();

    };


    /* APPLY WHEN PAGE LOADS */

    applyAppearance();


    /* LISTEN FOR SYSTEM THEME CHANGES */

    media.addEventListener(
      "change",
      applyAppearance
    );


    /* LISTEN FOR SAVED SETTINGS */

    window.addEventListener(
      "cv-preferences-changed",
      handlePreferencesChanged
    );


    /* LISTEN FOR SETTINGS PREVIEW */

    window.addEventListener(
      "cv-preferences-preview",
      handlePreferencesPreview
    );


    /* LISTEN FOR STORAGE CHANGES */

    window.addEventListener(
      "storage",
      handlePreferencesChanged
    );


    /* CLEAN UP EVENT LISTENERS */

    return () => {

      media.removeEventListener(
        "change",
        applyAppearance
      );

      window.removeEventListener(
        "cv-preferences-changed",
        handlePreferencesChanged
      );

      window.removeEventListener(
        "cv-preferences-preview",
        handlePreferencesPreview
      );

      window.removeEventListener(
        "storage",
        handlePreferencesChanged
      );

    };

  }, [location.pathname]);

  return null;

}


/* =========================================
   TOAST NOTIFICATION
========================================= */

function Toast() {

  const { toast } = useStore();

  return toast ? (

    <div

      role="status"

      className="fixed bottom-6 right-6 z-50 flex max-w-sm items-center gap-3 rounded-xl bg-slate-900 px-5 py-4 text-sm font-semibold text-white shadow-xl"

    >

      <CheckCircle2
        className="text-green-400"
        size={18}
      />

      {toast}

    </div>

  ) : null;

}


/* =========================================
   APPLICATION ROUTES
========================================= */

function App() {

  return (

    <StoreProvider>

      <BrowserRouter>

        <ThemeController />

        <Routes>

          <Route
            path="/"
            element={<HomePage />}
          />

          <Route
            path="/templates"
            element={<TemplatesPage />}
          />

          <Route
            path="/login"
            element={<AuthPage />}
          />

          <Route
            path="/signup"
            element={<AuthPage signup />}
          />

          <Route
            path="/dashboard"
            element={<Dashboard />}
          />

          <Route
            path="/my-cvs"
            element={<MyCVs />}
          />

          <Route
            path="/information"
            element={<Information />}
          />

          <Route
            path="/settings"
            element={<SettingsPage />}
          />

          <Route
            path="/builder/:id"
            element={<Builder />}
          />

          <Route
            path="*"
            element={<Navigate to="/" replace />}
          />

        </Routes>

        <Toast />

      </BrowserRouter>

    </StoreProvider>

  );

}


/* =========================================
   START APPLICATION
========================================= */

createRoot(
  document.getElementById("root")
).render(<App />);
