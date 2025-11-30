/**
 * TypeScript definitions for Electron preload API
 */

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

declare global {
  interface Window {
    atlas: AtlasAPI;
  }
}

export {};
