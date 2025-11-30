/**
 * Electron main process
 */
import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { startBackend, stopBackend, waitForHealth } from './backendProcess';
import { registerIpcHandlers } from './ipcHandlers';

let mainWindow: BrowserWindow | null = null;

async function createWindow() {
  // Start FastAPI backend
  console.log('Starting backend...');
  await startBackend();
  await waitForHealth('http://127.0.0.1:4100/health', 30000);
  console.log('Backend ready');

  // Create browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  // Load renderer
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  registerIpcHandlers();
  createWindow();
});

app.on('window-all-closed', () => {
  stopBackend();
  app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
