const { app, BrowserWindow, screen } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const net = require('net');

let mainWindow;
let pythonProcess;

// Check if a port is already in use
function isPortInUse(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => resolve(true));
    server.once('listening', () => { server.close(); resolve(false); });
    server.listen(port);
  });
}

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  const W = 360, H = 600;
  mainWindow = new BrowserWindow({
    width: W, height: H,
    x: width - W - 16,
    y: height - H - 16,
    frame:       false,
    transparent: true,
    alwaysOnTop: true,
    resizable:   false,
    webPreferences: {
      nodeIntegration:  true,
      contextIsolation: false,
    }
  });

  const isDev = process.env.NODE_ENV !== 'production';
  mainWindow.loadURL(isDev ? 'http://localhost:5173' : `file://${path.join(__dirname, 'dist', 'index.html')}`);
  mainWindow.setOpacity(0.95);
  mainWindow.on('closed', () => { mainWindow = null; });
}

async function startPythonBackend() {
  const inUse = await isPortInUse(8765);
  if (inUse) {
    console.log('[Electron] Port 8765 already in use — skipping Python spawn');
    return;
  }

  const pythonExe = path.join(__dirname, '..', 'backend', 'venv', 'Scripts', 'python.exe');
  const mainScript = path.join(__dirname, '..', 'backend', 'main.py');

  pythonProcess = spawn(pythonExe, [mainScript], {
    cwd: path.join(__dirname, '..', 'backend'),
  });

  pythonProcess.stdout.on('data', d => process.stdout.write(`[PY] ${d}`));
  pythonProcess.stderr.on('data', d => process.stderr.write(`[PY ERR] ${d}`));
  pythonProcess.on('close', code => console.log(`[PY] exited with code ${code}`));
}

app.whenReady().then(async () => {
  await startPythonBackend();
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => { if (!mainWindow) createWindow(); });

app.on('will-quit', () => {
  if (pythonProcess) pythonProcess.kill('SIGTERM');
});
