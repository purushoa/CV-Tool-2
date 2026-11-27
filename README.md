# CV Tool — updated from original frontend

This version retains the original dashboard, pages, store, and builder source from CV-Tool-Organized-Frontend(1).zip. Shared.jsx is now a compatibility re-export for 12 individual JSX components. The templates array contains 13 designs; gallery filtering, thumbnail previews and full-size CV rendering have been updated.

## Run
Open this folder in VS Code and run:

```bash
npm install
npm run dev
```

Frontend demo only: authentication and saving rely on the existing frontend store. PDF export behavior follows the original builder; verify print layout for long CVs. ATS compatibility is not guaranteed.
