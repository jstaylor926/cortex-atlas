/**
 * Terminal manager for dev workspace
 */
import { spawn as ptySpawn } from 'node-pty';
import { BrowserWindow } from 'electron';
import { v4 as uuidv4 } from 'uuid';

interface Terminal {
  id: string;
  pty: any;
  cwd: string;
}

const terminals = new Map<string, Terminal>();

export function startTerminal(cwd: string): string {
  const terminalId = uuidv4();

  const shell = process.platform === 'win32' ? 'powershell.exe' : '/bin/zsh';

  const ptyProcess = ptySpawn(shell, [], {
    name: 'xterm-color',
    cols: 80,
    rows: 24,
    cwd,
    env: process.env as any
  });

  ptyProcess.onData((data: string) => {
    // Send data to renderer
    const mainWindow = BrowserWindow.getAllWindows()[0];
    mainWindow?.webContents.send('terminal:data', {
      terminalId,
      data
    });
  });

  terminals.set(terminalId, {
    id: terminalId,
    pty: ptyProcess,
    cwd
  });

  return terminalId;
}

export function sendToTerminal(terminalId: string, data: string): void {
  const terminal = terminals.get(terminalId);
  if (terminal) {
    terminal.pty.write(data);
  }
}

export function stopTerminal(terminalId: string): void {
  const terminal = terminals.get(terminalId);
  if (terminal) {
    terminal.pty.kill();
    terminals.delete(terminalId);
  }
}

export function resizeTerminal(terminalId: string, cols: number, rows: number): void {
  const terminal = terminals.get(terminalId);
  if (terminal) {
    terminal.pty.resize(cols, rows);
  }
}
