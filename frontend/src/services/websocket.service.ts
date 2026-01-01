import { ref, type Ref } from 'vue'

type MessageHandler = (data: any) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private clientId: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private messageHandlers: Map<string, MessageHandler[]> = new Map()

  public connected: Ref<boolean> = ref(false)

  constructor() {
    this.clientId = this.generateClientId()
  }

  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return // Already connected
    }

    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    this.ws = new WebSocket(`${wsUrl}/ws/${this.clientId}`)

    this.ws.onopen = () => {
      this.connected.value = true
      this.reconnectAttempts = 0
      console.log('WebSocket connected')
    }

    this.ws.onclose = () => {
      this.connected.value = false
      this.attemptReconnect()
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const type = data.type
        const handlers = this.messageHandlers.get(type) || []
        handlers.forEach(handler => handler(data))

        // Also trigger 'all' handlers
        const allHandlers = this.messageHandlers.get('*') || []
        allHandlers.forEach(handler => handler(data))
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = Math.min(2000 * this.reconnectAttempts, 10000)
      console.log(`Attempting WebSocket reconnect in ${delay}ms...`)
      setTimeout(() => this.connect(), delay)
    } else {
      console.log('Max WebSocket reconnect attempts reached')
    }
  }

  on(type: string, handler: MessageHandler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, [])
    }
    this.messageHandlers.get(type)!.push(handler)
  }

  off(type: string, handler: MessageHandler) {
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index !== -1) {
        handlers.splice(index, 1)
      }
    }
  }

  send(data: object) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not connected, cannot send message')
    }
  }

  askStreaming(question: string, topK = 5) {
    this.send({
      type: 'ask',
      question,
      top_k: topK
    })
  }

  searchRealtime(query: string, topK = 10) {
    this.send({
      type: 'search',
      query,
      top_k: topK
    })
  }

  subscribe(topic: string) {
    this.send({
      type: 'subscribe',
      topic
    })
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.connected.value = false
  }

  isConnected(): boolean {
    return this.connected.value
  }
}

export default new WebSocketService()
