import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, ComposedChart } from 'recharts'
import { TrendingUp, TrendingDown, Activity, DollarSign, BarChart3, Search, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import { io } from 'socket.io-client'
import './App.css'

// Use environment variables or fallback to localhost
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'
const WEBSOCKET_URL = import.meta.env.VITE_WEBSOCKET_URL || 'http://localhost:5000'
const API_KEY = 'demo-api-key-12345678'

function App() {
  const [tokens, setTokens] = useState([])
  const [selectedToken, setSelectedToken] = useState(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [velocityData, setVelocityData] = useState([])
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)

  // Initialize WebSocket connection
  useEffect(() => {
    const socketInstance = io(WEBSOCKET_URL, {
      auth: {
        api_key: API_KEY
      }
    })

    socketInstance.on('connect', () => {
      console.log('Connected to WebSocket')
      setConnected(true)
      setSocket(socketInstance)
    })

    socketInstance.on('disconnect', () => {
      console.log('Disconnected from WebSocket')
      setConnected(false)
    })

    socketInstance.on('token_update', (data) => {
      console.log('Received token update:', data)
      setLastUpdate(new Date())
      // Update token in the list
      setTokens(prevTokens => 
        prevTokens.map(token => 
          token.id === data.token_id 
            ? { ...token, quote: { USD: { ...token.quote?.USD, ...data.data } } }
            : token
        )
      )
      
      // Update selected token if it matches
      if (selectedToken && selectedToken.id === data.token_id) {
        setSelectedToken(prev => ({
          ...prev,
          quote: { USD: { ...prev.quote?.USD, ...data.data } }
        }))
      }
    })

    socketInstance.on('market_update', (data) => {
      console.log('Received market update:', data)
      setLastUpdate(new Date())
    })

    return () => {
      socketInstance.disconnect()
    }
  }, [])

  // Fetch tokens data
  const fetchTokens = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/tokens?limit=20`, {
        headers: {
          'X-API-Key': API_KEY
        }
      })
      const data = await response.json()
      if (data.status.error_code === 0) {
        setTokens(data.data)
        if (data.data.length > 0 && !selectedToken) {
          setSelectedToken(data.data[0])
        }
      }
    } catch (error) {
      console.error('Error fetching tokens:', error)
    } finally {
      setLoading(false)
    }
  }

  // Subscribe to token updates via WebSocket
  const subscribeToToken = (tokenId) => {
    if (socket && connected) {
      socket.emit('subscribe_token', {
        token_id: tokenId,
        metrics: ['price', 'volume', 'velocity']
      })
    }
  }

  // Generate mock velocity chart data
  const generateVelocityData = (currentVelocity) => {
    const data = []
    const baseVelocity = currentVelocity || 0.5
    for (let i = 23; i >= 0; i--) {
      data.push({
        time: `${i}h`,
        velocity: Math.max(0, baseVelocity + (Math.random() - 0.5) * 0.2),
        volume: Math.random() * 10000 + 1000
      })
    }
    return data
  }

  useEffect(() => {
    fetchTokens()
    const interval = setInterval(fetchTokens, 300000) // Refresh every 5 minutes
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (selectedToken) {
      setVelocityData(generateVelocityData(selectedToken.quote?.USD?.velocity))
      subscribeToToken(selectedToken.id)
    }
  }, [selectedToken, socket, connected])

  const filteredTokens = tokens.filter(token =>
    token.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    token.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatNumber = (num) => {
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B'
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M'
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K'
    return num?.toFixed(2) || '0'
  }

  const formatCurrency = (num) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 8
    }).format(num || 0)
  }

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'decreasing':
        return <TrendingDown className="h-4 w-4 text-red-500" />
      default:
        return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const getTrendColor = (change) => {
    if (change > 0) return 'text-green-500'
    if (change < 0) return 'text-red-500'
    return 'text-gray-500'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100">
                Token Metrics Dashboard
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mt-2">
                Real-time cryptocurrency token velocity and market data
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                {connected ? (
                  <Wifi className="h-4 w-4 text-green-500" />
                ) : (
                  <WifiOff className="h-4 w-4 text-red-500" />
                )}
                <span className={`text-sm ${connected ? 'text-green-500' : 'text-red-500'}`}>
                  {connected ? 'Live' : 'Offline'}
                </span>
              </div>
              {lastUpdate && (
                <span className="text-xs text-muted-foreground">
                  Last update: {lastUpdate.toLocaleTimeString()}
                </span>
              )}
              <Button onClick={fetchTokens} disabled={loading} className="gap-2">
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </div>

        {/* Market Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{tokens.length}</div>
              <p className="text-xs text-muted-foreground">Active tokens tracked</p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Velocity</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {tokens.length > 0 
                  ? (tokens.reduce((sum, token) => sum + (token.quote?.USD?.velocity || 0), 0) / tokens.length).toFixed(3)
                  : '0.000'
                }
              </div>
              <p className="text-xs text-muted-foreground">Average token velocity</p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Market Cap</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${formatNumber(tokens.reduce((sum, token) => sum + (token.quote?.USD?.market_cap || 0), 0))}
              </div>
              <p className="text-xs text-muted-foreground">Combined market cap</p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">24h Volume</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${formatNumber(tokens.reduce((sum, token) => sum + (token.quote?.USD?.volume_24h || 0), 0))}
              </div>
              <p className="text-xs text-muted-foreground">Total 24h volume</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Token List */}
          <div className="lg:col-span-1">
            <Card className="h-fit">
              <CardHeader>
                <CardTitle>Tokens</CardTitle>
                <CardDescription>Select a token to view detailed metrics</CardDescription>
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search tokens..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-8"
                  />
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="max-h-96 overflow-y-auto">
                  {filteredTokens.map((token) => (
                    <div
                      key={token.id}
                      className={`p-4 border-b cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 transition-all duration-200 ${
                        selectedToken?.id === token.id ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 border-l-4 border-l-blue-500' : ''
                      }`}
                      onClick={() => setSelectedToken(token)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">{token.symbol}</div>
                          <div className="text-sm text-muted-foreground truncate max-w-32">{token.name}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-medium">{formatCurrency(token.quote?.USD?.price)}</div>
                          <div className={`text-sm ${getTrendColor(token.quote?.USD?.percent_change_24h)}`}>
                            {token.quote?.USD?.percent_change_24h > 0 ? '+' : ''}
                            {token.quote?.USD?.percent_change_24h?.toFixed(2)}%
                          </div>
                        </div>
                      </div>
                      <div className="mt-2 flex items-center justify-between">
                        <Badge variant="outline" className="text-xs">
                          V: {token.quote?.USD?.velocity?.toFixed(3) || '0.000'}
                        </Badge>
                        {getTrendIcon(token.quote?.USD?.velocity_trend)}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Token Details */}
          <div className="lg:col-span-2 space-y-6">
            {selectedToken && (
              <>
                {/* Token Info Card */}
                <Card className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-2xl flex items-center gap-2">
                          {selectedToken.symbol}
                          {connected && <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />}
                        </CardTitle>
                        <CardDescription>{selectedToken.name}</CardDescription>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold">{formatCurrency(selectedToken.quote?.USD?.price)}</div>
                        <div className={`text-lg ${getTrendColor(selectedToken.quote?.USD?.percent_change_24h)}`}>
                          {selectedToken.quote?.USD?.percent_change_24h > 0 ? '+' : ''}
                          {selectedToken.quote?.USD?.percent_change_24h?.toFixed(2)}% (24h)
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <div className="text-sm text-muted-foreground">Market Cap</div>
                        <div className="text-lg font-semibold">${formatNumber(selectedToken.quote?.USD?.market_cap)}</div>
                      </div>
                      <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <div className="text-sm text-muted-foreground">24h Volume</div>
                        <div className="text-lg font-semibold">${formatNumber(selectedToken.quote?.USD?.volume_24h)}</div>
                      </div>
                      <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <div className="text-sm text-muted-foreground">Velocity</div>
                        <div className="text-lg font-semibold flex items-center gap-2">
                          {selectedToken.quote?.USD?.velocity?.toFixed(3) || '0.000'}
                          {getTrendIcon(selectedToken.quote?.USD?.velocity_trend)}
                        </div>
                      </div>
                      <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <div className="text-sm text-muted-foreground">7d Change</div>
                        <div className={`text-lg font-semibold ${getTrendColor(selectedToken.quote?.USD?.percent_change_7d)}`}>
                          {selectedToken.quote?.USD?.percent_change_7d > 0 ? '+' : ''}
                          {selectedToken.quote?.USD?.percent_change_7d?.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Velocity Chart */}
                <Card className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <CardTitle>Token Velocity Trend</CardTitle>
                    <CardDescription>24-hour velocity and volume correlation</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={velocityData}>
                          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                          <XAxis dataKey="time" />
                          <YAxis yAxisId="left" />
                          <YAxis yAxisId="right" orientation="right" />
                          <Tooltip 
                            contentStyle={{
                              backgroundColor: 'rgba(255, 255, 255, 0.95)',
                              border: '1px solid #e2e8f0',
                              borderRadius: '8px',
                              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                            }}
                          />
                          <Bar
                            yAxisId="right"
                            dataKey="volume"
                            fill="#10b981"
                            opacity={0.3}
                            name="Volume ($)"
                            radius={[2, 2, 0, 0]}
                          />
                          <Line
                            yAxisId="left"
                            type="monotone"
                            dataKey="velocity"
                            stroke="#3b82f6"
                            strokeWidth={3}
                            name="Velocity"
                            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                            activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
                          />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

