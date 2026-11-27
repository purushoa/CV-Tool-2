
import React, {
  createContext,
  useContext,
  useEffect,
  useState
} from "react";

import {
  blankCV,
  sampleCV,
  templates
} from "../data";


/* STORE CONTEXT */

const Store = createContext(null);

export const useStore = () => useContext(Store);

const uid = () => crypto.randomUUID();


/* READ SAVED USER PREFERENCES */

function getPreferences() {

  try {

    return JSON.parse(
      localStorage.getItem("cvtool_preferences")
    ) || {};

  } catch {

    return {};

  }

}


/* STORE PROVIDER */

export function StoreProvider({ children }) {


  /* SAVED CVS */

  const [cvs, setCVs] = useState(() => {

    try {

      const saved = JSON.parse(
        localStorage.getItem("cvtool_cvs")
      );

      return Array.isArray(saved)
        ? saved
        : [sampleCV()];

    } catch {

      return [sampleCV()];

    }

  });


  /* USER ACCOUNT */

  const [account, setAccount] = useState(() => {

    try {

      return JSON.parse(
        localStorage.getItem("cvtool_account")
      ) || null;

    } catch {

      return null;

    }

  });


  /* TOAST NOTIFICATION */

  const [toast, setToast] = useState("");


  /* SAVE CVS AUTOMATICALLY */

  useEffect(() => {

    localStorage.setItem(
      "cvtool_cvs",
      JSON.stringify(cvs)
    );

  }, [cvs]);


  /* SAVE ACCOUNT AUTOMATICALLY */

  useEffect(() => {

    localStorage.setItem(
      "cvtool_account",
      JSON.stringify(account)
    );

  }, [account]);


  /* AUTOMATICALLY HIDE NOTIFICATIONS */

  useEffect(() => {

    if (!toast) return;

    const timer = setTimeout(
      () => setToast(""),
      3500
    );

    return () => clearTimeout(timer);

  }, [toast]);


  /* CREATE NEW CV WITH SAVED PREFERENCES */

  const createCV = () => {

    const preferences = getPreferences();

    const cv = blankCV();


    // Apply preferred CV template

    if (
      preferences.template &&
      templates.some(
        template => template.id === preferences.template
      )
    ) {

      cv.template = preferences.template;

    }


    // Apply preferred accent color

    if (
      typeof preferences.accent === "string" &&
      /^#[0-9a-fA-F]{6}$/.test(preferences.accent)
    ) {

      cv.accent = preferences.accent;

    }


    // Apply preferred font

    const supportedFonts = [
      "Inter",
      "Arial",
      "Georgia"
    ];

    if (supportedFonts.includes(preferences.font)) {

      cv.font = preferences.font;

    }


    // Save preferred export format

    if (
      preferences.exportFormat === "pdf" ||
      preferences.exportFormat === "docx"
    ) {

      cv.exportFormat = preferences.exportFormat;

    }


    // Add new CV without changing existing CVs

    setCVs(previous => [
      cv,
      ...previous
    ]);

    return cv.id;

  };


  /* UPDATE EXISTING CV */

  const updateCV = (id, fn) => {

    setCVs(previous =>

      previous.map(cv =>

        cv.id === id

          ? {
              ...fn(cv),
              updatedAt: new Date().toISOString()
            }

          : cv

      )

    );

  };


  /* DUPLICATE EXISTING CV */

  const duplicateCV = id => {

    setCVs(previous => {

      const original = previous.find(
        cv => cv.id === id
      );

      if (!original) {

        return previous;

      }

      const duplicate = {

        ...structuredClone(original),

        id: uid(),

        name: original.name + " (Copy)",

        updatedAt: new Date().toISOString()

      };

      return [
        duplicate,
        ...previous
      ];

    });

  };


  /* PROVIDE STORE TO APPLICATION */

  return (

    <Store.Provider

      value={{

        cvs,
        setCVs,

        account,
        setAccount,

        toast,
        setToast,

        createCV,
        updateCV,
        duplicateCV

      }}

    >

      {children}

    </Store.Provider>

  );

}
