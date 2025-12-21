import { useState, useEffect, useCallback, useRef } from 'react'

export interface STTStatus {
  recording: boolean
  model: string
  pid: number | null
  running?: boolean  // Optional: backend may provide this
  recording_start_time?: number | null  // Optional: backend may not provide this yet
}

interface UseStatusResult {
  status: STTStatus | null
  isRunning: boolean
  duration: number
  error: string | null
  refetch: () => Promise<void>
}

const DEFAULT_STATUS: STTStatus = {
  recording: false,
  model: 'turbo',
  pid: null,
  running: false,
  recording_start_time: null,
}

// In development, use a mock. In production, this would read from the file system
// For browser-based widget, we use a local server endpoint or file:// protocol
const STATUS_ENDPOINT = import.meta.env.DEV
  ? '/api/status'
  : `file://${import.meta.env.VITE_XDG_RUNTIME_DIR || '/run/user/1000'}/whisper-stt/status.json`

/**
 * Hook for monitoring STT service status
 * Polls the status file and calculates recording duration
 */
export function useStatus(pollInterval = 500): UseStatusResult {
  const [status, setStatus] = useState<STTStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [duration, setDuration] = useState(0)

  // Track recording start time client-side as fallback
  const clientStartTimeRef = useRef<number | null>(null)
  const wasRecordingRef = useRef(false)

  const fetchStatus = useCallback(async () => {
    try {
      // For development, we simulate the status
      if (import.meta.env.DEV) {
        // Check if dev server has mock endpoint
        try {
          const res = await fetch('/api/status')
          if (res.ok) {
            const data = await res.json()
            setStatus(data)
            setError(null)
            return
          }
        } catch {
          // Fall through to mock data
        }

        // Use mock data in dev mode if no endpoint
        setStatus(DEFAULT_STATUS)
        setError(null)
        return
      }

      // Production: read from file system (requires native file access)
      // This would be handled by Tauri, Electron, or a local server
      const res = await fetch(STATUS_ENDPOINT)
      if (!res.ok) {
        throw new Error('Status file not found')
      }
      const data = await res.json()
      setStatus(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setStatus(null)
    }
  }, [])

  // Poll for status updates
  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, pollInterval)
    return () => clearInterval(interval)
  }, [fetchStatus, pollInterval])

  // Track recording state changes for client-side duration fallback
  useEffect(() => {
    const isRecording = status?.recording ?? false

    // Detect recording start (transition from not recording to recording)
    if (isRecording && !wasRecordingRef.current) {
      // Use server timestamp if available, otherwise use client time
      if (status?.recording_start_time) {
        clientStartTimeRef.current = status.recording_start_time
      } else {
        clientStartTimeRef.current = Date.now() / 1000
      }
    }

    // Detect recording stop
    if (!isRecording && wasRecordingRef.current) {
      clientStartTimeRef.current = null
    }

    wasRecordingRef.current = isRecording
  }, [status?.recording, status?.recording_start_time])

  // Calculate duration when recording
  useEffect(() => {
    if (!status?.recording) {
      setDuration(0)
      return
    }

    const startTime = status.recording_start_time ?? clientStartTimeRef.current
    if (!startTime) {
      setDuration(0)
      return
    }

    const updateDuration = () => {
      const now = Date.now() / 1000
      const elapsed = now - startTime
      setDuration(Math.max(0, elapsed))
    }

    updateDuration()
    const interval = setInterval(updateDuration, 100) // Update every 100ms for smooth display
    return () => clearInterval(interval)
  }, [status?.recording, status?.recording_start_time])

  // Determine if service is running (use backend 'running' field if available, else check pid)
  const isRunning = status?.running ?? (status?.pid !== null && status?.pid !== undefined)

  return {
    status,
    isRunning,
    duration,
    error,
    refetch: fetchStatus,
  }
}

// Available models for the dropdown
export const AVAILABLE_MODELS = [
  { id: 'tiny', label: 'Tiny', description: 'Fastest, lowest accuracy' },
  { id: 'base', label: 'Base', description: 'Fast, basic accuracy' },
  { id: 'small', label: 'Small', description: 'Balanced speed/accuracy' },
  { id: 'medium', label: 'Medium', description: 'Good accuracy' },
  { id: 'large', label: 'Large', description: 'High accuracy' },
  { id: 'large-v3', label: 'Large V3', description: 'Best accuracy' },
  { id: 'turbo', label: 'Turbo', description: 'Large V3 optimized' },
] as const
