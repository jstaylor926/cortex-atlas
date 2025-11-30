/**
 * Electron preload script - exposes safe APIs to renderer
 */
import { contextBridge, ipcRenderer } from 'electron';

// Type definitions for the exposed API
export interface FileEntry {
  name: string;
  isDir: boolean;
}

export interface AtlasAPI {
  selectProjectRoot: () => Promise<string | null>;
  dev: {
    readDir: (projectId: string, relPath: string) => Promise<FileEntry[]>;
    readFile: (projectId: string, filePath: string) => Promise<string>;
    writeFile: (projectId: string, filePath: string, content: string) => Promise<void>;
  };
  terminal: {
    start: (projectId: string) => Promise<{ terminalId: string }>;
    send: (terminalId: string, data: string) => Promise<void>;
    onData: (callback: (payload: any) => void) => void;
    stop: (terminalId: string) => void;
    resize: (terminalId: string, cols: number, rows: number) => Promise<void>;
  };
}

// Expose Atlas API to renderer
contextBridge.exposeInMainWorld('atlas', {
  // File dialogs
  selectProjectRoot: () => ipcRenderer.invoke('dialog:selectProjectRoot'),

  // Dev workspace - File operations
  dev: {
    readDir: (projectId: string, relPath: string) =>
      ipcRenderer.invoke('dev:readDir', { projectId, relPath }),

    readFile: (projectId: string, filePath: string) =>
      ipcRenderer.invoke('dev:readFile', { projectId, filePath }),

    writeFile: (projectId: string, filePath: string, content: string) =>
      ipcRenderer.invoke('dev:writeFile', { projectId, filePath, content })
  },

  // Terminal
  terminal: {
    start: (projectId: string) =>
      ipcRenderer.invoke('terminal:start', { projectId }),

    send: (terminalId: string, data: string) =>
      ipcRenderer.invoke('terminal:send', { terminalId, data }),

    onData: (callback: (payload: any) => void) =>
      ipcRenderer.on('terminal:data', (_event, payload) => callback(payload)),

    stop: (terminalId: string) =>
      ipcRenderer.send('terminal:stop', { terminalId }),

    resize: (terminalId: string, cols: number, rows: number) =>
      ipcRenderer.invoke('terminal:resize', { terminalId, cols, rows })
  }
} as AtlasAPI);

// Declare global window type
declare global {
  interface Window {
    atlas: AtlasAPI;
  }
}
