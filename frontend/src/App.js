import React, { useState, useEffect, useRef } from "react";
import "@/App.css";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "./components/ui/avatar";
import { ScrollArea } from "./components/ui/scroll-area";
import { Separator } from "./components/ui/separator";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentSession, setCurrentSession] = useState(null);
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState({ provider: "openai", name: "gpt-5" });
  const [isStarted, setIsStarted] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadAvailableModels();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadAvailableModels = async () => {
    try {
      const response = await axios.get(`${API}/models`);
      setAvailableModels(response.data.models);
    } catch (error) {
      console.error("Failed to load models:", error);
      toast.error("Failed to load AI models");
    }
  };

  const createNewSession = async () => {
    try {
      const sessionName = `AI Learning Session - ${new Date().toLocaleDateString()}`;
      const response = await axios.post(`${API}/chat/session`, {
        session_name: sessionName
      });
      setCurrentSession(response.data);
      setIsStarted(true);
      toast.success("New learning session started! 🎉");
      return response.data;
    } catch (error) {
      console.error("Failed to create session:", error);
      toast.error("Failed to start session");
      return null;
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;
    if (!currentSession) {
      const session = await createNewSession();
      if (!session) return;
    }

    const userMessage = {
      id: Date.now(),
      message: inputMessage,
      response: "",
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/chat/message`, {
        session_id: currentSession.id,
        message: inputMessage,
        model_provider: selectedModel.provider,
        model_name: selectedModel.name
      });

      const aiMessage = {
        ...response.data,
        isUser: false
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error("Failed to send message:", error);
      toast.error("Oops! The AI couldn't respond right now. Try again!");
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        message: "",
        response: "Sorry, I'm having trouble thinking right now. Can you try asking me again? 🤔",
        isUser: false,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getModelDisplayInfo = () => {
    const model = availableModels.find(m => 
      m.provider === selectedModel.provider && m.name === selectedModel.name
    );
    return model || { display_name: "AI Assistant", kid_friendly_description: "Your AI helper!" };
  };

  if (!isStarted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        {/* Header */}
        <div className="bg-white/80 backdrop-blur-sm border-b border-indigo-100 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-white text-xl">🤖</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  AI Learning Lab
                </h1>
                <p className="text-sm text-gray-600">For curious minds aged 8-12</p>
              </div>
            </div>
          </div>
        </div>

        {/* Hero Section */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center space-y-8">
            {/* Hero Image */}
            <div className="relative">
              <img 
                src="https://images.unsplash.com/photo-1588072432836-e10032774350"
                alt="Kids learning AI"
                className="w-full max-w-md mx-auto rounded-2xl shadow-2xl"
                data-testid="hero-image"
              />
              <div className="absolute -top-4 -right-4 w-16 h-16 bg-yellow-400 rounded-full flex items-center justify-center shadow-lg animate-bounce">
                <span className="text-2xl">✨</span>
              </div>
            </div>

            {/* Hero Text */}
            <div className="space-y-4">
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight">
                Learn How AI Works!
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Discover the magic behind artificial intelligence through fun conversations 
                with different AI models. Safe, educational, and super cool! 🌟
              </p>
            </div>

            {/* Features Grid */}
            <div className="grid md:grid-cols-3 gap-6 mt-12">
              <Card className="bg-white/60 backdrop-blur-sm border-indigo-200 hover:shadow-lg transition-all duration-300">
                <CardHeader>
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                    <span className="text-2xl">💬</span>
                  </div>
                  <CardTitle className="text-lg text-center text-gray-800">Chat with AI</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 text-center">
                    Ask questions and learn how AI thinks and responds to you!
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-white/60 backdrop-blur-sm border-purple-200 hover:shadow-lg transition-all duration-300">
                <CardHeader>
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                    <span className="text-2xl">🔄</span>
                  </div>
                  <CardTitle className="text-lg text-center text-gray-800">Compare Models</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 text-center">
                    Try different AI models and see how they each have unique personalities!
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-white/60 backdrop-blur-sm border-pink-200 hover:shadow-lg transition-all duration-300">
                <CardHeader>
                  <div className="w-12 h-12 bg-pink-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                    <span className="text-2xl">🛡️</span>
                  </div>
                  <CardTitle className="text-lg text-center text-gray-800">Safe Learning</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 text-center">
                    All conversations are kid-friendly with built-in safety features!
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* CTA Button */}
            <div className="pt-8">
              <Button 
                onClick={createNewSession}
                className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-8 py-4 rounded-2xl text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
                data-testid="start-learning-btn"
              >
                Start Learning! 🚀
              </Button>
            </div>
          </div>
        </div>

        {/* Decorative Elements */}
        <div className="fixed top-20 left-10 w-20 h-20 bg-yellow-200 rounded-full opacity-20 animate-pulse"></div>
        <div className="fixed bottom-20 right-10 w-16 h-16 bg-pink-200 rounded-full opacity-20 animate-pulse"></div>
        <div className="fixed top-1/2 left-20 w-12 h-12 bg-indigo-200 rounded-full opacity-20 animate-bounce"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-indigo-100 shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-white text-xl">🤖</span>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  AI Learning Lab
                </h1>
                <p className="text-xs text-gray-600">Learning Session Active</p>
              </div>
            </div>

            {/* Model Selector */}
            <div className="flex items-center space-x-3">
              <span className="text-sm text-gray-600">AI Model:</span>
              <Select
                value={`${selectedModel.provider}-${selectedModel.name}`}
                onValueChange={(value) => {
                  // Create proper mapping for model selection
                  const modelMapping = {
                    'openai-gpt-5': { provider: 'openai', name: 'gpt-5' },
                    'anthropic-claude-4-sonnet-20250514': { provider: 'anthropic', name: 'claude-4-sonnet-20250514' },
                    'gemini-gemini-2.5-pro': { provider: 'gemini', name: 'gemini-2.5-pro' }
                  };
                  const model = modelMapping[value];
                  if (model) {
                    setSelectedModel(model);
                  }
                }}
              >
                <SelectTrigger className="w-48 bg-white/80">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.map((model) => (
                    <SelectItem
                      key={`${model.provider}-${model.name}`}
                      value={`${model.provider}-${model.name}`}
                    >
                      {model.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Interface */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Card className="bg-white/60 backdrop-blur-sm border-indigo-200 shadow-xl h-[calc(100vh-200px)]">
          <CardHeader className="pb-4">
            <div className="flex items-center space-x-3">
              <Avatar className="h-10 w-10">
                <AvatarImage src="https://images.unsplash.com/photo-1593376853899-fbb47a057fa0" />
                <AvatarFallback className="bg-indigo-100">AI</AvatarFallback>
              </Avatar>
              <div>
                <CardTitle className="text-lg">{getModelDisplayInfo().display_name}</CardTitle>
                <p className="text-sm text-gray-600">{getModelDisplayInfo().kid_friendly_description}</p>
              </div>
            </div>
          </CardHeader>

          <Separator className="mx-6" />

          {/* Messages Area */}
          <CardContent className="flex-1 p-6">
            <ScrollArea className="h-[calc(100vh-400px)]" data-testid="messages-area">
              <div className="space-y-4">
                {messages.length === 0 && (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <span className="text-2xl">👋</span>
                    </div>
                    <p className="text-gray-600">
                      Hi there! I'm your AI learning buddy. Ask me anything about how AI works!
                    </p>
                  </div>
                )}

                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                        msg.isUser
                          ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white'
                          : msg.isError
                          ? 'bg-red-100 text-red-800 border border-red-200'
                          : 'bg-white text-gray-800 border border-gray-200'
                      } shadow-sm`}
                      data-testid={msg.isUser ? "user-message" : "ai-message"}
                    >
                      {msg.isUser ? (
                        <p className="text-sm">
                          {msg.message}
                        </p>
                      ) : (
                        <div className="text-sm">
                          <ReactMarkdown 
                            components={{
                              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                              ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                              ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                              li: ({ children }) => <li className="ml-2">{children}</li>,
                              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                              em: ({ children }) => <em className="italic">{children}</em>,
                              br: () => <br />,
                            }}
                          >
                            {msg.response}
                          </ReactMarkdown>
                        </div>
                      )}
                      {!msg.isUser && !msg.is_safe && (
                        <Badge variant="secondary" className="mt-2 text-xs">
                          Content Filtered
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white text-gray-800 border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input Area */}
            <div className="mt-4 flex space-x-2">
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me about AI! Try: 'How do you learn?' or 'What makes you smart?'"
                disabled={isLoading}
                className="flex-1 bg-white/80 border-indigo-200 focus:border-indigo-400 rounded-xl"
                data-testid="message-input"
              />
              <Button
                onClick={sendMessage}
                disabled={isLoading || !inputMessage.trim()}
                className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-6 rounded-xl"
                data-testid="send-message-btn"
              >
                {isLoading ? '🤔' : '🚀'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default App;