import { useState, useCallback, useEffect } from 'react'
import {
  Mic,
  MicOff,
  Power,
  PowerOff,
  ChevronDown,
  Cpu,
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useStatus, AVAILABLE_MODELS } from '@/hooks/useStatus'
import { formatSegmentDuration, cn } from '@/lib/utils'

interface BarWidgetProps {
  onToggleRecording?: () => void
  onStartService?: (model: string) => void
  onStopService?: () => void
  onChangeModel?: (model: string) => void
}

/**
 * Professional Audio Hardware-inspired STT Status Widget
 *
 * Features:
 * - LED segment display for recording duration
 * - Status LED indicators (recording/ready/stopped)
 * - Hardware panel aesthetic with subtle shadows
 * - Dropdown menu for service control
 */
export function BarWidget({
  onToggleRecording,
  onStartService,
  onStopService,
  onChangeModel,
}: BarWidgetProps) {
  const { status, isRunning, duration } = useStatus()
  const [selectedModel, setSelectedModel] = useState(status?.model || 'turbo')

  // Sync selectedModel when status updates (e.g., on initial load or external changes)
  useEffect(() => {
    if (status?.model && status.model !== selectedModel) {
      setSelectedModel(status.model)
    }
  }, [status?.model])

  const isRecording = status?.recording ?? false

  const handleToggleRecording = useCallback(() => {
    onToggleRecording?.()
  }, [onToggleRecording])

  const handleToggleService = useCallback(() => {
    if (isRunning) {
      onStopService?.()
    } else {
      onStartService?.(selectedModel)
    }
  }, [isRunning, onStartService, onStopService, selectedModel])

  const handleModelChange = useCallback((model: string) => {
    setSelectedModel(model)
    onChangeModel?.(model)
  }, [onChangeModel])

  return (
    <div className="relative hardware-panel rounded-lg px-3 py-2 flex items-center gap-3 select-none">
      {/* Status LED */}
      <StatusLED isRunning={isRunning} isRecording={isRecording} />

      {/* Main Display Area - Click to toggle recording */}
      <button
        onClick={handleToggleRecording}
        disabled={!isRunning}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        className={cn(
          "flex items-center gap-2 px-2 py-1 rounded-md transition-all duration-200",
          "hover:bg-background-hover/50 active:bg-background-hover",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "focus:outline-none focus:ring-1 focus:ring-accent/50"
        )}
      >
        {/* Microphone Icon */}
        <div className={cn(
          "relative w-5 h-5 flex items-center justify-center",
          isRecording && "text-status-error recording-led",
          !isRecording && isRunning && "text-status-success ready-led",
          !isRunning && "text-foreground-muted"
        )}>
          {isRecording ? (
            <Mic className="w-4 h-4" strokeWidth={2.5} />
          ) : (
            <MicOff className="w-4 h-4" strokeWidth={2} />
          )}
        </div>

        {/* Segment Display */}
        <SegmentDisplay
          value={isRecording ? formatSegmentDuration(duration) : '--:--'}
          isActive={isRecording}
        />
      </button>

      {/* Dropdown Menu */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            className={cn(
              "flex items-center gap-1 px-2 py-1.5 rounded-md",
              "text-foreground-secondary hover:text-foreground",
              "hover:bg-background-hover/50 transition-colors",
              "focus:outline-none focus:ring-1 focus:ring-accent/50"
            )}
          >
            <span className="text-xs font-mono uppercase tracking-wide">
              {status?.model || 'STT'}
            </span>
            <ChevronDown className="w-3 h-3 opacity-60" />
          </button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end" sideOffset={8}>
          {/* Service Control */}
          <DropdownMenuLabel>Service</DropdownMenuLabel>

          <DropdownMenuItem onClick={handleToggleService}>
            {isRunning ? (
              <>
                <PowerOff className="w-4 h-4 text-status-error" />
                <span>Stop Service</span>
              </>
            ) : (
              <>
                <Power className="w-4 h-4 text-status-success" />
                <span>Start Service</span>
              </>
            )}
          </DropdownMenuItem>

          {isRunning && (
            <DropdownMenuItem onClick={handleToggleRecording}>
              {isRecording ? (
                <>
                  <MicOff className="w-4 h-4 text-status-error" />
                  <span>Stop Recording</span>
                </>
              ) : (
                <>
                  <Mic className="w-4 h-4 text-status-success" />
                  <span>Start Recording</span>
                </>
              )}
            </DropdownMenuItem>
          )}

          <DropdownMenuSeparator />

          {/* Model Selection */}
          <DropdownMenuLabel>
            <div className="flex items-center gap-2">
              <Cpu className="w-3 h-3" />
              <span>Model</span>
            </div>
          </DropdownMenuLabel>

          <DropdownMenuRadioGroup
            value={selectedModel}
            onValueChange={handleModelChange}
          >
            {AVAILABLE_MODELS.map((model) => (
              <DropdownMenuRadioItem
                key={model.id}
                value={model.id}
                className="flex items-center justify-between"
              >
                <div className="flex flex-col">
                  <span className="font-medium">{model.label}</span>
                  <span className="text-xs text-foreground-muted">
                    {model.description}
                  </span>
                </div>
                {status?.model === model.id && isRunning && (
                  <span className="text-[10px] text-accent font-medium uppercase tracking-wider ml-2">
                    Active
                  </span>
                )}
              </DropdownMenuRadioItem>
            ))}
          </DropdownMenuRadioGroup>

          <DropdownMenuSeparator />

          {/* Status Footer */}
          <div className="px-2 py-1.5 text-xs text-foreground-muted flex items-center justify-between">
            <span>PID: {status?.pid ?? '—'}</span>
            <span className={cn(
              "flex items-center gap-1",
              isRunning ? "text-status-success" : "text-status-error"
            )}>
              <span className={cn(
                "w-1.5 h-1.5 rounded-full",
                isRunning ? "bg-status-success" : "bg-status-error"
              )} />
              {isRunning ? 'Running' : 'Stopped'}
            </span>
          </div>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Decorative screws */}
      <div className="absolute top-1 left-1 screw" />
      <div className="absolute top-1 right-1 screw" />
    </div>
  )
}

/**
 * LED Segment Display - mimics vintage audio equipment displays
 */
function SegmentDisplay({ value, isActive }: { value: string; isActive: boolean }) {
  return (
    <div
      className={cn(
        "font-mono text-sm tracking-wider px-2 py-0.5 rounded",
        "bg-background/80 border border-border/30",
        "shadow-recess",
        isActive ? "segment-display text-accent" : "text-foreground-muted/40"
      )}
      style={{
        fontVariantNumeric: 'tabular-nums',
        minWidth: '52px',
        textAlign: 'center',
      }}
    >
      {value}
    </div>
  )
}

/**
 * Status LED - visual indicator for service state
 */
function StatusLED({ isRunning, isRecording }: { isRunning: boolean; isRecording: boolean }) {
  const statusText = isRecording ? 'Recording' : isRunning ? 'Ready' : 'Stopped'

  return (
    <div className="relative flex items-center justify-center w-3 h-3" role="status" aria-label={`Service status: ${statusText}`}>
      {/* Screen reader text */}
      <span className="sr-only">{statusText}</span>

      {/* LED housing */}
      <div className="absolute inset-0 rounded-full bg-background shadow-recess" />

      {/* LED light */}
      <div
        className={cn(
          "relative w-2 h-2 rounded-full transition-all duration-300",
          isRecording && "bg-status-error recording-led",
          !isRecording && isRunning && "bg-status-success ready-led",
          !isRunning && "bg-foreground-muted/30"
        )}
      />

      {/* LED glow effect */}
      {(isRecording || isRunning) && (
        <div
          className={cn(
            "absolute inset-0 rounded-full blur-sm opacity-50",
            isRecording && "bg-status-error",
            !isRecording && isRunning && "bg-status-success"
          )}
        />
      )}
    </div>
  )
}

export default BarWidget
