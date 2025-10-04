import { useState, useRef, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { io, Socket } from 'socket.io-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Send, ArrowLeft, Brain, Trash2, CheckCircle, Plus } from 'lucide-react'

// Generate unique session ID for each conversation
const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function Chat() {
  const { locritName } = useParams<{ locritName: string }>()
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [locrit, setLocrit] = useState<any>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const assistantMessageIdRef = useRef<string | null>(null)
  const [memoryActionInProgress, setMemoryActionInProgress] = useState(false)
  const [memoryActionStatus, setMemoryActionStatus] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string>(() => generateSessionId())

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Fetch Locrit details
  useEffect(() => {
    if (!locritName) return

    const fetchLocritDetails = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/v1/locrits/${locritName}/info`)
        if (response.ok) {
          const data = await response.json()
          setLocrit(data.locrit)
          // Set initial assistant message
          setMessages([
            {
              id: '1',
              type: 'assistant',
              content: `Bonjour ! Je suis ${data.locrit.name}. Comment puis-je vous aider aujourd'hui ?`,
              timestamp: new Date()
            }
          ])
        } else {
          console.error('Failed to fetch locrit details')
        }
      } catch (error) {
        console.error('Error fetching locrit details:', error)
      }
    }

    fetchLocritDetails()
  }, [locritName])

  // WebSocket connection
  useEffect(() => {
    if (!locritName) return

    const socketInstance = io('http://localhost:5000')

    socketInstance.on('connect', () => {
      setIsConnected(true)
      socketInstance.emit('join_chat', {
        locrit_name: locritName,
        session_id: sessionId
      })
    })

    socketInstance.on('disconnect', () => setIsConnected(false))

    socketInstance.on('chat_chunk', (data) => {
      if (data.locrit_name !== locritName || data.session_id !== sessionId) return
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1]
        if (lastMessage && lastMessage.id === assistantMessageIdRef.current) {
          // Append to the last message
          return [
            ...prev.slice(0, -1),
            { ...lastMessage, content: lastMessage.content + data.content }
          ]
        } else {
          // It's a new message, but we should have an ID.
          // This case should ideally not happen if chat_complete works correctly.
          return [
            ...prev,
            {
              id: Date.now().toString(),
              type: 'assistant',
              content: data.content,
              timestamp: new Date()
            }
          ]
        }
      })
    })

    socketInstance.on('chat_complete', () => {
      setIsTyping(false)
      assistantMessageIdRef.current = null
    })

    socketInstance.on('error', (error) => {
      console.error('WebSocket error:', error)
      setIsTyping(false)
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `Erreur: ${error.message}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    })

    setSocket(socketInstance)

    return () => {
      socketInstance.disconnect()
    }
  }, [locritName, sessionId])

  const handleSendMessage = () => {
    if (!inputMessage.trim() || isTyping || !socket) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])

    // Create a placeholder for the assistant's response
    const assistantMessageId = (Date.now() + 1).toString()
    assistantMessageIdRef.current = assistantMessageId
    const assistantMessage: Message = {
      id: assistantMessageId,
      type: 'assistant',
      content: '',
      timestamp: new Date()
    }
    setMessages(prev => [...prev, assistantMessage])

    socket.emit('chat_message', {
      locrit_name: locritName,
      session_id: sessionId,
      message: inputMessage.trim(),
      stream: true
    })

    setInputMessage('')
    setIsTyping(true)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value)

    // Auto-resize
    const textarea = e.target
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }

  const handleRememberConversation = async () => {
    if (!locritName || memoryActionInProgress) return

    setMemoryActionInProgress(true)
    setMemoryActionStatus('Saving conversation to memory...')

    try {
      const response = await fetch(`http://localhost:5000/api/v1/locrits/${locritName}/memory/store-conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: messages.filter(msg => msg.content.trim() !== ''), // Only non-empty messages
          force_update: true
        })
      })

      const result = await response.json()

      if (response.ok && result.success) {
        setMemoryActionStatus('✅ Conversation saved to memory!')
        setTimeout(() => setMemoryActionStatus(null), 3000)
      } else {
        setMemoryActionStatus(`❌ Failed to save: ${result.error || 'Unknown error'}`)
        setTimeout(() => setMemoryActionStatus(null), 5000)
      }
    } catch (error) {
      console.error('Error saving conversation:', error)
      setMemoryActionStatus('❌ Network error occurred')
      setTimeout(() => setMemoryActionStatus(null), 5000)
    } finally {
      setMemoryActionInProgress(false)
    }
  }

  const handleNewConversation = () => {
    // Generate new session ID
    const newSessionId = generateSessionId()
    setSessionId(newSessionId)

    // Clear current messages and reset initial greeting
    if (locrit) {
      setMessages([
        {
          id: '1',
          type: 'assistant',
          content: `Bonjour ! Je suis ${locrit.name}. Comment puis-je vous aider aujourd'hui ?`,
          timestamp: new Date()
        }
      ])
    }

    // Reconnect socket with new session
    if (socket) {
      socket.emit('join_chat', {
        locrit_name: locritName,
        session_id: newSessionId
      })
    }
  }

  const handleDeleteConversation = async () => {
    if (!locritName || memoryActionInProgress) return

    const confirmed = window.confirm(
      'Are you sure you want to delete this conversation? This action cannot be undone.'
    )

    if (!confirmed) return

    setMemoryActionInProgress(true)
    setMemoryActionStatus('Deleting conversation...')

    try {
      const response = await fetch(`http://localhost:5000/api/v1/locrits/${locritName}/memory/sessions/${sessionId}`, {
        method: 'DELETE'
      })

      const result = await response.json()

      if (response.ok && result.success) {
        setMemoryActionStatus('✅ Conversation deleted from memory!')
        // Start new conversation after deletion
        handleNewConversation()
        setTimeout(() => setMemoryActionStatus(null), 3000)
      } else {
        setMemoryActionStatus(`❌ Failed to delete: ${result.error || 'Unknown error'}`)
        setTimeout(() => setMemoryActionStatus(null), 5000)
      }
    } catch (error) {
      console.error('Error deleting conversation:', error)
      setMemoryActionStatus('❌ Network error occurred')
      setTimeout(() => setMemoryActionStatus(null), 5000)
    } finally {
      setMemoryActionInProgress(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      {/* Chat Header */}
      {locrit && (
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-4">
            <Link to="/my-locrits">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Retour
              </Button>
            </Link>
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🤖</span>
              <div>
                <h2 className="text-lg font-semibold">{locrit.name}</h2>
                <div className="flex items-center space-x-2">
                  <Badge variant={locrit.active ? 'default' : 'secondary'}>
                    {locrit.active ? '🟢 Actif' : '🔴 Inactif'}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {locrit.ollama_model}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Memory Management Actions */}
          <div className="flex items-center space-x-2">
            <Button
              onClick={handleNewConversation}
              disabled={memoryActionInProgress}
              variant="outline"
              size="sm"
              className="flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>Nouvelle conversation</span>
            </Button>

            <Button
              onClick={handleRememberConversation}
              disabled={memoryActionInProgress || messages.length <= 1}
              variant="outline"
              size="sm"
              className="flex items-center space-x-2"
            >
              <Brain className="h-4 w-4" />
              <span>Remember this</span>
            </Button>

            <Button
              onClick={handleDeleteConversation}
              disabled={memoryActionInProgress || messages.length <= 1}
              variant="outline"
              size="sm"
              className="flex items-center space-x-2 text-red-600 hover:text-red-700"
            >
              <Trash2 className="h-4 w-4" />
              <span>Delete conversation</span>
            </Button>
          </div>
        </div>
      )}

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-lg p-3 ${
                message.type === 'user'
                  ? 'bg-primary text-primary-foreground ml-4'
                  : 'bg-muted mr-4'
              }`}
            >
              <div className="flex items-start space-x-2">
                {message.type === 'assistant' && (
                  <span className="text-lg mt-1">🤖</span>
                )}
                <div className="flex-1">
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
                {message.type === 'user' && (
                  <span className="text-lg mt-1">👤</span>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg p-3 mr-4">
              <div className="flex items-center space-x-2">
                <span className="text-lg">🤖</span>
                <div className="flex items-center space-x-1">
                  <span className="text-sm">{locrit?.name || 'Assistant'} écrit</span>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Memory Action Status */}
      {memoryActionStatus && (
        <div className="px-4 py-2 border-t border-b bg-muted/50">
          <div className="flex items-center justify-center">
            <span className="text-sm font-medium">{memoryActionStatus}</span>
          </div>
        </div>
      )}

      {/* Message Input */}
      <div className="p-4 border-t">
        <div className="flex space-x-2">
          <textarea
            ref={textareaRef}
            value={inputMessage}
            onChange={handleTextareaChange}
            onKeyPress={handleKeyPress}
            placeholder="Tapez votre message..."
            className="flex-1 min-h-[44px] max-h-[120px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={isTyping || !locrit}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isTyping || !locrit}
            size="icon"
            className="h-[44px] w-[44px]"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}