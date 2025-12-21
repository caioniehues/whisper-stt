import type { Plugin } from 'vite'

interface MockStatus {
  recording: boolean
  model: string
  pid: number | null
  recording_start_time: number | null
}

/**
 * Vite plugin that provides a mock STT status API for development
 * Simulates the status.json file that the daemon would write
 */
export function mockApiPlugin(): Plugin {
  let mockStatus: MockStatus = {
    recording: false,
    model: 'turbo',
    pid: 12345,
    recording_start_time: null,
  }

  return {
    name: 'mock-stt-api',
    configureServer(server) {
      // GET /api/status - returns current mock status
      server.middlewares.use('/api/status', (req, res, next) => {
        if (req.method === 'GET') {
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify(mockStatus))
          return
        }
        next()
      })

      // POST /api/command/:command - handles commands
      server.middlewares.use('/api/command', (req, res, next) => {
        if (req.method !== 'POST') {
          next()
          return
        }

        const url = new URL(req.url!, `http://${req.headers.host}`)
        const command = url.pathname.replace('/api/command/', '')

        let body = ''
        req.on('data', (chunk) => {
          body += chunk
        })
        req.on('end', () => {
          const args = body ? JSON.parse(body) : {}

          switch (command) {
            case 'toggle-recording':
              mockStatus.recording = !mockStatus.recording
              mockStatus.recording_start_time = mockStatus.recording
                ? Date.now() / 1000
                : null
              console.log(`[Mock API] Recording: ${mockStatus.recording}`)
              break

            case 'start':
              mockStatus.pid = 12345
              mockStatus.model = args.model || 'turbo'
              mockStatus.recording = false
              mockStatus.recording_start_time = null
              console.log(`[Mock API] Started with model: ${mockStatus.model}`)
              break

            case 'stop':
              mockStatus.pid = null
              mockStatus.recording = false
              mockStatus.recording_start_time = null
              console.log('[Mock API] Stopped')
              break

            case 'change-model':
              mockStatus.model = args.model || 'turbo'
              console.log(`[Mock API] Model changed to: ${mockStatus.model}`)
              break

            default:
              console.log(`[Mock API] Unknown command: ${command}`)
          }

          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ success: true, status: mockStatus }))
        })
      })

      // Demo mode toggle endpoint
      server.middlewares.use('/api/demo', (req, res, next) => {
        if (req.method === 'POST') {
          // Toggle recording every 5 seconds for demo
          setInterval(() => {
            mockStatus.recording = !mockStatus.recording
            mockStatus.recording_start_time = mockStatus.recording
              ? Date.now() / 1000
              : null
          }, 5000)

          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ message: 'Demo mode started' }))
          return
        }
        next()
      })
    },
  }
}
