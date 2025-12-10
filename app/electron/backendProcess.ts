/**
 * Backend process manager
 */
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';

let backendProcess: ChildProcess | null = null;

export async function startBackend(): Promise<void> {
  // Check if backend is already running
  try {
    const response = await fetch('http://127.0.0.1:4100/health');
    if (response.ok) {
      console.log('Backend already running, skipping spawn');
      return;
    }
  } catch (e) {
    // Backend not running, proceed to spawn
  }

  const isDev = process.env.NODE_ENV === 'development';

  // In development, use the backend from parent directory and venv python
  // In production, use bundled backend and system/bundled python
  const backendDir = isDev
    ? path.join(__dirname, '../../backend')
    : path.join(process.resourcesPath, 'backend');

  const pythonPath = isDev
    ? path.join(backendDir, 'venv/bin/python')
    : 'python3'; // Or bundled Python path in production

  const scriptPath = path.join(backendDir, 'uvicorn_entry.py');

  console.log(`Spawning backend: ${pythonPath} ${scriptPath}`);

  backendProcess = spawn(pythonPath, [scriptPath, '--port', '4100'], {
    cwd: backendDir,
    env: { ...process.env }
  });

  backendProcess.stdout?.on('data', (data) => {
    console.log(`[Backend] ${data}`);
  });

  backendProcess.stderr?.on('data', (data) => {
    console.error(`[Backend Error] ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend exited with code ${code}`);
  });
}

export function stopBackend(): void {
  if (backendProcess) {
    backendProcess.kill('SIGTERM');
    backendProcess = null;
  }
}

export async function waitForHealth(
  url: string,
  timeout: number = 30000
): Promise<void> {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch (e) {
      // Not ready yet
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  throw new Error('Backend health check timeout');
}
