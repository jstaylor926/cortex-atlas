/**
 * IPC handlers for Electron main process
 */
import { ipcMain, dialog } from 'electron';
import * as fs from 'fs/promises';
import * as path from 'path';
import { startTerminal, sendToTerminal, stopTerminal, resizeTerminal } from './terminalManager';

interface Project {
  id: string;
  name: string;
  root_path: string;
  type: string;
  created_at: string;
  updated_at: string;
  linked_notes?: any[];
}

export function registerIpcHandlers() {
  // File dialog
  ipcMain.handle('dialog:selectProjectRoot', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory']
    });
    return result.canceled ? null : result.filePaths[0];
  });

  // Dev workspace file operations
  ipcMain.handle('dev:readDir', async (_event, { projectId, relPath }) => {
    const projectRoot = await getProjectRoot(projectId);
    const fullPath = path.join(projectRoot, relPath);
    const entries = await fs.readdir(fullPath, { withFileTypes: true });

    return entries.map(entry => ({
      name: entry.name,
      isDir: entry.isDirectory()
    }));
  });

  ipcMain.handle('dev:readFile', async (_event, { projectId, filePath }) => {
    const projectRoot = await getProjectRoot(projectId);
    const fullPath = path.join(projectRoot, filePath);
    return await fs.readFile(fullPath, 'utf-8');
  });

  ipcMain.handle('dev:writeFile', async (_event, { projectId, filePath, content }) => {
    const projectRoot = await getProjectRoot(projectId);
    const fullPath = path.join(projectRoot, filePath);
    await fs.writeFile(fullPath, content, 'utf-8');
  });

  // Terminal
  ipcMain.handle('terminal:start', async (_event, { projectId }) => {
    const projectRoot = await getProjectRoot(projectId);
    const terminalId = await startTerminal(projectRoot);
    return { terminalId };
  });

  ipcMain.handle('terminal:send', async (_event, { terminalId, data }) => {
    sendToTerminal(terminalId, data);
  });

  ipcMain.on('terminal:stop', (_event, { terminalId }) => {
    stopTerminal(terminalId);
  });

  ipcMain.handle('terminal:resize', async (_event, { terminalId, cols, rows }) => {
    resizeTerminal(terminalId, cols, rows);
  });
}

async function getProjectRoot(projectId: string): Promise<string> {
  // Fetch from FastAPI backend
  try {
    const response = await fetch(`http://127.0.0.1:4100/api/projects/${projectId}`);
    if (!response.ok) {
      throw new Error(`Project ${projectId} not found`);
    }
    const project = await response.json() as Project;
    return project.root_path;
  } catch (error) {
    console.error('Error fetching project:', error);
    throw error;
  }
}
