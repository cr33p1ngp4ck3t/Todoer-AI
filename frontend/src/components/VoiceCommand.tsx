'use client'

import { useEffect, useRef, useState } from 'react'
import { Mic, MicOff } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from './ui/button'

interface VoiceCommandProps {
  onCommandExecuted?: (text: string) => void
}

interface SpeechRecognition {
  continuous: boolean
  interimResults: boolean
  lang: string
  onstart: (() => void) | null
  onresult: ((event: { results: { transcript: string }[][] }) => void) | null
  onend: (() => void) | null
  onerror: ((event: { error: string }) => void) | null
  start: () => void
  stop: () => void
}

type SpeechWindow = Window & {
  SpeechRecognition?: new () => SpeechRecognition
  webkitSpeechRecognition?: new () => SpeechRecognition
}

export default function VoiceCommand({ onCommandExecuted }: VoiceCommandProps) {
  const [listening, setListening] = useState(false)
  const recognition = useRef<SpeechRecognition | null>(null)

  useEffect(
    () => () => {
      if (recognition.current) {
        recognition.current.onstart = null
        recognition.current.onresult = null
        recognition.current.onend = null
        recognition.current.onerror = null
        recognition.current.stop()
      }
    },
    []
  )

  function start() {
    const speechWindow = window as SpeechWindow
    const Speech =
      speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition
    if (!Speech) {
      toast.error('Voice commands are not supported in your browser')
      return
    }
    const recorder = new Speech()
    recognition.current = recorder
    recorder.continuous = false
    recorder.interimResults = false
    recorder.lang = navigator.language || 'en-US'
    recorder.onstart = () => setListening(true)
    recorder.onend = () => setListening(false)
    recorder.onresult = (event) => {
      const text = event.results[0]?.[0]?.transcript?.trim()
      if (text) onCommandExecuted?.(text)
    }
    recorder.onerror = (event) => {
      setListening(false)
      if (event.error === 'no-speech' || event.error === 'aborted') return
      toast.error(
        event.error === 'not-allowed'
          ? 'Allow microphone access to use voice input.'
          : 'Voice input failed. Try typing your task instead.'
      )
    }
    try {
      setListening(true)
      recorder.start()
    } catch {
      setListening(false)
      toast.error('Could not start voice input. Try again.')
    }
  }

  return (
    <Button
      type="button"
      variant="outline"
      size="icon"
      aria-label={listening ? 'Stop listening' : 'Start voice command'}
      title={listening ? 'Stop listening' : 'Draft a task with your voice'}
      onClick={() => {
        if (listening) recognition.current?.stop()
        else start()
      }}
    >
      {listening ? <MicOff className="text-destructive" /> : <Mic />}
    </Button>
  )
}
