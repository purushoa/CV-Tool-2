
import React, { useState } from "react";

import {
  NavLink,
  useNavigate
} from "react-router-dom";

import {
  Home,
  UserRound,
  FileText,
  Settings,
  Menu,
  LogOut
} from "lucide-react";

import { useStore } from "../store/CVStore";
import { Logo } from "./Logo";

export function Sidebar() {

  const { account, setAccount } = useStore();

  const nav = useNavigate();

  const [open, setOpen] = useState(false);

  const links = [
    [Home, "Home", "/dashboard"],
    [UserRound, "My Information", "/information"],
    [FileText, "My CVs", "/my-cvs"],
    [Settings, "Settings", "/settings"]
  ];

  return (
    <>

      <button
        className="cv-mobile-menu fixed left-4 top-4 z-50 rounded-xl p-3 shadow md:hidden"
        onClick={() => setOpen(!open)}
        aria-label="Toggle sidebar"
      >
        <Menu />
      </button>

      {open && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/40 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={`cv-app-sidebar fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r px-4 py-7 transition-transform md:translate-x-0 ${
          open
            ? "translate-x-0"
            : "-translate-x-full"
        }`}
      >

        <div className="px-3">
          <Logo />
        </div>

        <p className="cv-sidebar-label mt-12 px-3 text-xs font-bold uppercase tracking-widest">
          Workspace
        </p>

        <nav className="mt-4 space-y-2">

          {links.map(([Icon, title, to]) => (

            <NavLink
              key={to}
              onClick={() => setOpen(false)}
              to={to}
              className={({ isActive }) =>
                `cv-nav-link flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition ${
                  isActive ? "cv-nav-active" : ""
                }`
              }
            >

              <Icon size={19} />

              {title}

            </NavLink>

          ))}

        </nav>

        <div className="cv-sidebar-footer mt-auto border-t pt-5">

          <div className="mb-4 flex items-center gap-3 px-2">

            <span className="cv-user-avatar flex h-10 w-10 items-center justify-center rounded-full font-bold">

              {(account?.name || "G")[0].toUpperCase()}

            </span>

            <div className="min-w-0">

              <p className="cv-user-name truncate text-sm font-bold">
                {account?.name || "Guest user"}
              </p>

              <p className="cv-sidebar-label truncate text-xs">
                {account?.email || "Frontend demo"}
              </p>

            </div>

          </div>

          <button
            className="cv-nav-link flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold"
            onClick={() => {
              setAccount(null);
              nav("/");
            }}
          >

            <LogOut size={18} />

            Log out

          </button>

        </div>

      </aside>

    </>
  );
}
