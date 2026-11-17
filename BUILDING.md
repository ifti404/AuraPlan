# Windows portable build

AuraPlan is packaged as a 64-bit Windows folder bundle. Build it on Windows
with 64-bit Python 3.12; the frozen build does not require Python on the target
computer.

Run from PowerShell in the project folder:

```powershell
.\build_windows.ps1 -Python "C:\Path\To\Python312\python.exe"
```

The script installs dependencies into `.venv-build`, builds the application,
and creates:

- `dist\AuraPlan\AuraPlan.exe` — run directly from the extracted folder.
- `dist\AuraPlan-portable.zip` — copy this ZIP to a USB drive and extract it
  before running.

The portable folder keeps tasks and profiles in `data\` beside the executable.
Normal packaged runs without `portable.mode` use the Windows user's Local App
Data directory instead.

## Vosk voice model

The build intentionally does not download or bundle a Vosk model. Models are
large and licensed independently. Extract the model into `model\` beside
`AuraPlan.exe`, so the folder contains `am\final.mdl`, `conf\model.conf`, and
`graph\HCLG.fst`. The ZIP includes a `model\README.txt` with the same layout.
If the folder is empty, the planner still opens and voice input reports as
unavailable until a valid model is added.

The produced app is Windows x64. Rebuild on the target operating system for
macOS or Linux.
