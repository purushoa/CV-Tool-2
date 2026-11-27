
import React, { useState, useEffect } from "react";

import {
  Save,
  RotateCcw,
  Sun,
  Moon,
  Monitor,
  Palette,
  LayoutTemplate,
  Download
} from "lucide-react";

import { templates } from "../data";
import { useStore } from "../store/CVStore";
import { Workspace } from "../components/Shared";


/* DEFAULT PREFERENCES */

const defaultPreferences = {
  theme: "light",
  compact: false,
  template: "modern",
  accent: "#2563eb",
  font: "Inter",
  exportFormat: "pdf"
};


/* SETTINGS PAGE */

export default function SettingsPage() {

  const { setToast } = useStore();


  /* LOAD SAVED PREFERENCES */

  const [preferences, setPreferences] = useState(() => {

    try {

      const saved = JSON.parse(
        localStorage.getItem("cvtool_preferences")
      );

      return {
        ...defaultPreferences,
        ...saved
      };

    } catch {

      return { ...defaultPreferences };

    }

  });


  /* IMMEDIATE APPEARANCE PREVIEW */

  useEffect(() => {

    window.dispatchEvent(

      new CustomEvent("cv-preferences-preview", {

        detail: {
          theme: preferences.theme,
          compact: preferences.compact
        }

      })

    );

  }, [
    preferences.theme,
    preferences.compact
  ]);


  /* UPDATE PREFERENCE */

  const updatePreference = (key, value) => {

    setPreferences(previous => ({
      ...previous,
      [key]: value
    }));

  };


  /* SAVE PREFERENCES */

  const savePreferences = () => {

    localStorage.setItem(
      "cvtool_preferences",
      JSON.stringify(preferences)
    );

    window.dispatchEvent(
      new Event("cv-preferences-changed")
    );

    setToast("Preferences saved successfully");

  };


  /* RESET PREFERENCES */

  const resetPreferences = () => {

    setPreferences({ ...defaultPreferences });

    localStorage.setItem(
      "cvtool_preferences",
      JSON.stringify(defaultPreferences)
    );

    window.dispatchEvent(
      new Event("cv-preferences-changed")
    );

    setToast("Default preferences restored");

  };


  /* AVAILABLE ACCENT COLORS */

  const colors = [
    "#2563eb",
    "#047857",
    "#7c3aed",
    "#e11d48",
    "#334155",
    "#ea580c",
    "#0891b2",
    "#111827"
  ];


  return (

    <Workspace
      title="Settings"
      subtitle="Customize your CV Tool workspace."
    >

      <div className="max-w-3xl space-y-6">


        {/* =====================================
            APPEARANCE SETTINGS
        ===================================== */}

        <div className="panel space-y-6 p-7">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-blue-50 p-3 text-blue-600">
              <Palette size={22} />
            </div>

            <div>

              <h2 className="text-lg font-bold">
                Appearance
              </h2>

              <p className="text-sm text-slate-500">
                Personalize your workspace appearance.
              </p>

            </div>

          </div>


          {/* WORKSPACE THEME */}

          <div>

            <label className="mb-3 block text-sm font-semibold">
              Workspace theme
            </label>

            <div className="grid grid-cols-3 gap-3">

              {[
                {
                  value: "light",
                  label: "Light",
                  Icon: Sun
                },
                {
                  value: "dark",
                  label: "Dark",
                  Icon: Moon
                },
                {
                  value: "system",
                  label: "System",
                  Icon: Monitor
                }
              ].map(({ value, label, Icon }) => (

                <button

                  key={value}

                  type="button"

                  aria-pressed={
                    preferences.theme === value
                  }

                  onClick={() =>
                    updatePreference("theme", value)
                  }

                  className={`flex flex-col items-center gap-3 rounded-xl border-2 p-5 transition ${
                    preferences.theme === value
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-slate-200 hover:border-blue-300"
                  }`}

                >

                  <Icon size={25} />

                  <span className="text-sm font-semibold">
                    {label}
                  </span>

                </button>

              ))}

            </div>

          </div>


          {/* COMPACT WORKSPACE */}

          <div className="flex items-center justify-between gap-4 border-t pt-5">

            <div>

              <h3 className="text-sm font-bold">
                Compact workspace
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                Reduce spacing to display more content.
              </p>

            </div>

            <button

              type="button"

              role="switch"

              aria-label="Compact workspace"

              aria-checked={preferences.compact}

              onClick={() =>
                updatePreference(
                  "compact",
                  !preferences.compact
                )
              }

              className={`relative h-6 w-11 shrink-0 rounded-full transition ${
                preferences.compact
                  ? "bg-blue-600"
                  : "bg-slate-300"
              }`}

            >

              <span

                style={{
                  backgroundColor: "#ffffff"
                }}

                className={`absolute left-1 top-1 h-4 w-4 rounded-full transition-transform ${
                  preferences.compact
                    ? "translate-x-5"
                    : "translate-x-0"
                }`}

              />

            </button>

          </div>

        </div>


        {/* =====================================
            CV PREFERENCES
        ===================================== */}

        <div className="panel space-y-6 p-7">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-blue-50 p-3 text-blue-600">
              <LayoutTemplate size={22} />
            </div>

            <div>

              <h2 className="text-lg font-bold">
                CV preferences
              </h2>

              <p className="text-sm text-slate-500">
                Choose your preferred CV design.
              </p>

            </div>

          </div>


          {/* DEFAULT CV TEMPLATE */}

          <div>

            <label className="mb-2 block text-sm font-semibold">
              Default CV template
            </label>

            <select

              className="field w-full"

              value={preferences.template}

              onChange={e =>
                updatePreference(
                  "template",
                  e.target.value
                )
              }

            >

              {templates.map(template => (

                <option
                  key={template.id}
                  value={template.id}
                >

                  {template.name}

                </option>

              ))}

            </select>

          </div>


          {/* DEFAULT ACCENT COLOR */}

          <div>

            <label className="mb-3 block text-sm font-semibold">
              Default accent color
            </label>

            <div className="flex flex-wrap gap-3">

              {colors.map(color => (

                <button

                  key={color}

                  type="button"

                  title={color}

                  aria-label={`Select color ${color}`}

                  aria-pressed={
                    preferences.accent === color
                  }

                  onClick={() =>
                    updatePreference("accent", color)
                  }

                  style={{
                    backgroundColor: color
                  }}

                  className={`flex h-10 w-10 items-center justify-center rounded-full transition ${
                    preferences.accent === color
                      ? "ring-2 ring-blue-500 ring-offset-2"
                      : "hover:scale-110"
                  }`}

                >

                  {preferences.accent === color && (

                    <span className="text-lg font-bold text-white">
                      ✓
                    </span>

                  )}

                </button>

              ))}


              {/* CUSTOM COLOR PICKER */}

              <input

                type="color"

                aria-label="Choose custom accent color"

                title="Custom color"

                value={preferences.accent}

                onChange={e =>
                  updatePreference(
                    "accent",
                    e.target.value
                  )
                }

                className="h-10 w-10 cursor-pointer rounded-lg border"

              />

            </div>

          </div>


          {/* DEFAULT FONT */}

          <div>

            <label className="mb-2 block text-sm font-semibold">
              Default font
            </label>

            <select

              className="field w-full"

              value={preferences.font}

              onChange={e =>
                updatePreference(
                  "font",
                  e.target.value
                )
              }

            >

              <option value="Inter">
                Inter
              </option>

              <option value="Arial">
                Arial
              </option>

              <option value="Georgia">
                Georgia
              </option>

            </select>

          </div>

        </div>


        {/* =====================================
            EXPORT PREFERENCES
        ===================================== */}

        <div className="panel space-y-6 p-7">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-blue-50 p-3 text-blue-600">
              <Download size={22} />
            </div>

            <div>

              <h2 className="text-lg font-bold">
                Export preferences
              </h2>

              <p className="text-sm text-slate-500">
                Choose your preferred download format.
              </p>

            </div>

          </div>


          {/* EXPORT FORMAT OPTIONS */}

          <div className="space-y-3">

            {[
              {
                value: "pdf",
                title: "PDF document (.pdf)",
                description:
                  "Preserves your CV design and formatting."
              },
              {
                value: "docx",
                title: "Microsoft Word (.docx)",
                description:
                  "Allows editing after downloading."
              }
            ].map(format => (

              <label

                key={format.value}

                className={`flex cursor-pointer items-center justify-between gap-4 rounded-xl border-2 p-4 ${
                  preferences.exportFormat === format.value
                    ? "border-blue-600 bg-blue-50"
                    : "border-slate-200"
                }`}

              >

                <div>

                  <p className="text-sm font-bold">
                    {format.title}
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    {format.description}
                  </p>

                </div>

                <input

                  type="radio"

                  name="exportFormat"

                  value={format.value}

                  checked={
                    preferences.exportFormat === format.value
                  }

                  onChange={e =>
                    updatePreference(
                      "exportFormat",
                      e.target.value
                    )
                  }

                  className="h-4 w-4 accent-blue-600"

                />

              </label>

            ))}

          </div>

        </div>


        {/* =====================================
            SAVE AND RESET BUTTONS
        ===================================== */}

        <div className="panel p-6">

          <div className="flex flex-wrap gap-3">


            {/* SAVE BUTTON */}

            <button

              type="button"

              className="btn-primary"

              onClick={savePreferences}

            >

              <Save size={18} />

              Save preferences

            </button>


            {/* RESET BUTTON */}

            <button

              type="button"

              className="btn-outline"

              onClick={resetPreferences}

            >

              <RotateCcw size={18} />

              Reset defaults

            </button>

          </div>

          <p className="mt-4 text-xs text-slate-500">
            Your preferences are saved locally in your
            browser.
          </p>

        </div>

      </div>

    </Workspace>

  );

}
