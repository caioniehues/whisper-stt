import { useCallback } from 'react'
import { BarWidget } from '@/components/BarWidget'

/**
 * Whisper STT Bar Widget Application
 *
 * A compact, professional audio hardware-inspired widget for controlling
 * the Whisper STT service from Hyprland/Wayland bars.
 *
 * Communication with the Python backend:
 * - In production, uses Tauri commands or subprocess calls to `stt` CLI
 * - In development, actions are logged to console
 */
function App() {
  // Action handlers - these would communicate with the Python backend
  const handleToggleRecording = useCallback(() => {
    if (import.meta.env.DEV) {
      console.log('[STT] Toggle recording')
      return
    }
    // Production: call stt toggle-recording
    invokeCommand('toggle-recording')
  }, [])

  const handleStartService = useCallback((model: string) => {
    if (import.meta.env.DEV) {
      console.log('[STT] Start service with model:', model)
      return
    }
    // Production: call stt daemon -m <model>
    invokeCommand('start', { model })
  }, [])

  const handleStopService = useCallback(() => {
    if (import.meta.env.DEV) {
      console.log('[STT] Stop service')
      return
    }
    // Production: call stt stop
    invokeCommand('stop')
  }, [])

  const handleChangeModel = useCallback((model: string) => {
    if (import.meta.env.DEV) {
      console.log('[STT] Change model to:', model)
      return
    }
    // Production: restart service with new model
    invokeCommand('change-model', { model })
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      {/* Demo container with some context */}
      <div className="flex flex-col items-center gap-6">
        {/* The actual widget */}
        <BarWidget
          onToggleRecording={handleToggleRecording}
          onStartService={handleStartService}
          onStopService={handleStopService}
          onChangeModel={handleChangeModel}
        />

        {/* Development mode indicator */}
        {import.meta.env.DEV && (
          <div className="text-xs text-foreground-muted text-center max-w-xs">
            <p className="mb-2">Development Mode</p>
            <p className="opacity-60">
              Actions logged to console. Connect to STT service for live data.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Invoke a command on the backend
 * In Tauri, this would use @tauri-apps/api
 * For standalone, this calls the stt CLI via subprocess
 */
function invokeCommand(command: string, args?: Record<string, unknown>) {
  // Check if running in Tauri
  if (window.__TAURI__) {
    const { invoke } = window.__TAURI__
    invoke(`stt_${command}`, args)
    return
  }

  // Fallback: Use fetch to local server endpoint
  fetch(`/api/command/${command}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(args),
  }).catch(console.error)
}

// Extend Window for Tauri
declare global {
  interface Window {
    __TAURI__?: {
      invoke: (cmd: string, args?: Record<string, unknown>) => Promise<unknown>
    }
  }
}

export default App
