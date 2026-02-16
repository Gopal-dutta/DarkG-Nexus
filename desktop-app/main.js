const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");

let backendProcess = null;
let win = null;

function createWindow() {
  win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webSecurity: false,
      allowRunningInsecureContent: true,
    },
  });

  win.loadFile("index.html");
  win.setMenuBarVisibility(false);
}

function startBackend() {
  const isDev = !app.isPackaged;
  
  // Try two possible paths for the EXE to be safe
  const pathsToTry = isDev ? [
    path.join(__dirname, "..", "backend", "dist", "darkg_backend", "darkg_backend.exe"),
    "D:\\DarkG-Nexus\\backend\\dist\\darkg_backend\\darkg_backend.exe"
  ] : [
    path.join(process.resourcesPath, "backend", "darkg_backend.exe"),
    path.join(process.resourcesPath, "app.asar.unpacked", "backend", "darkg_backend.exe")
  ];

  let scriptPath = pathsToTry.find(p => fs.existsSync(p));

  if (!scriptPath) {
    console.error("CRITICAL: Backend EXE not found at expected locations.");
    return;
  }

  console.log("Launching backend from:", scriptPath);

  try {
    backendProcess = spawn(scriptPath, [], {
      cwd: path.dirname(scriptPath),
      detached: false,
      shell: false // Prevents empty CMD windows popping up
    });

    backendProcess.stdout.on("data", (data) => console.log(`Backend Log: ${data}`));
    backendProcess.stderr.on("data", (data) => console.error(`Backend Error: ${data}`));

    backendProcess.on("close", (code) => {
      console.log(`Backend process exited with code ${code}`);
      // Auto-restart if it crashes early
      if (code !== 0) setTimeout(startBackend, 5000);
    });

  } catch (e) {
    console.error("Execution failed:", e);
  }
}

app.whenReady().then(() => {
  startBackend();
  createWindow();
});

// Hard kill the backend on exit
app.on("before-quit", () => {
  if (backendProcess) {
    console.log("Terminating backend...");
    backendProcess.kill('SIGTERM');
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});