'use client'

import { useState, useRef } from 'react'
import { Mic, MicOff, Loader2 } from 'lucide-react'
import { api } from '../services/api'
import { toast } from 'sonner'

interface VoiceCommandProps {
  onCommandExecuted?: (command: string) => void
  onTaskCreated?: () => void
}

export default function VoiceCommand({
  onCommandExecuted,
  onTaskCreated,
}: VoiceCommandProps) {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const recognitionRef = useRef<any | null>(null)

  const startListening = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      toast.error('Voice commands are not supported in your browser')
      return
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition
    recognitionRef.current = new SpeechRecognition()
    recognitionRef.current.continuous = false
    recognitionRef.current.interimResults = false
    recognitionRef.current.lang = 'en-US'

    recognitionRef.current.onstart = () => {
      setIsListening(true)
      toast.info('Listening... speak now')
    }

    recognitionRef.current.onresult = async (event: any) => {
      const transcript = event.results[0][0].transcript
      setIsProcessing(true)
      try {
        // Send voice command to backend for parsing
        const parsed = await api.chat.smartParse(transcript)
        toast.success(`Parsed: ${parsed.title}`)
        onCommandExecuted?.(JSON.stringify(parsed))
      } catch (error) {
        console.error('Failed to process voice command:', error)
        toast.error('Failed to process voice command')
      } finally {
        setIsProcessing(false)
        setIsListening(false)
      }
    }

    recognitionRef.current.onend = () => {
      setIsListening(false)
    }

    recognitionRef.current.onerror = (event: any) => {
      // Handle network errors gracefully
      if (event.error === 'network') {
        console.warn('Speech recognition network error - check internet connection')
        toast.error('No internet connection. Voice commands require internet access.')
      } else if (event.error === 'not-allowed') {
        console.warn('Speech recognition blocked - microphone permission denied')
        toast.error('Microphone access denied. Please allow microphone access in browser settings.')
      } else if (event.error === 'no-speech') {
        // No speech detected - not really an error, just user didn't speak
        setIsListening(false)
        return
      } else {
        console.warn('Speech recognition error:', event.error)
        toast.error(`Speech recognition error: ${event.error}`)
      }
      setIsListening(false)
    }

    recognitionRef.current.start()
  }

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      setIsListening(false)
    }
  }

  return (
    <button
      onClick={isListening ? stopListening : startListening}
      disabled={isProcessing}
      className={`rounded-full p-2 transition-all ${
        isListening
          ? 'bg-red-500 animate-pulse hover:bg-red-600'
          : isProcessing
            ? 'bg-gray-300 cursor-not-allowed'
            : 'bg-neutral-500 hover:bg-neutral-600'
      }`}
      aria-label={isListening ? 'Stop listening' : 'Start voice command'}
      title={
        isListening
          ? 'Stop listening'
          : isProcessing
            ? 'Processing...'
            : 'Start voice command'
      }
    >
      {isProcessing ? (
        <Loader2 className="h-5 w-5 animate-spin text-white" />
      ) : isListening ? (
        <MicOff className="h-5 w-5 text-white" />
      ) : (
        <Mic className="h-5 w-5 text-white" />
      )}
    </button>
  )
}
