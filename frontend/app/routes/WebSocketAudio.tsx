import { useState, useRef, useEffect } from 'react';
import { startAudioPlayerWorklet } from './audio-player';
import { startAudioRecorderWorklet } from './audio-recorder';

interface Message {
  id: string;
  text: string;
}

export const WebSocketAudio = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [micStatus, setMicStatus] = useState('Click the icon to start recording');
  const [messages, setMessages] = useState<Message[]>([]);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);

  const messagesDivRef = useRef<HTMLDivElement>(null);
  const currentMessageIdRef = useRef<string | null>(null);
  const audioPlayerNodeRef = useRef<AudioWorkletNode | null>(null);
  const wsUrlRef = useRef<string>('');

  useEffect(() => {
    if (typeof window !== 'undefined') {

      const sessionId = Math.random().toString().substring(10);
      wsUrlRef.current = `ws://localhost:8000/ws/${sessionId}`;
    }
  }, []);

  const base64ToArray = (base64: string): ArrayBuffer => {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  };

  const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  };

  const connectWebsocket = () => {
    if (!wsUrlRef.current) return;

    const ws = new WebSocket(`${wsUrlRef.current}?is_audio=true`);

    ws.onopen = () => {
      console.log('WebSocket connection opened.');
      setMessages([{ id: 'status', text: 'Connection opened' }]);
    };

    ws.onmessage = (event) => {
      const message_from_server = JSON.parse(event.data);
      console.log('[AGENT TO CLIENT]', message_from_server);

      if (message_from_server.turn_complete) {
        currentMessageIdRef.current = null;
        return;
      }

      if (message_from_server.mime_type === 'audio/pcm' && audioPlayerNodeRef.current) {
        audioPlayerNodeRef.current.port.postMessage(base64ToArray(message_from_server.data));
      }

      if (message_from_server.mime_type === 'text/plain') {
        if (!currentMessageIdRef.current) {
          currentMessageIdRef.current = Math.random().toString(36).substring(7);
          setMessages((prev) => [...prev, { id: currentMessageIdRef.current!, text: '' }]);
        }

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === currentMessageIdRef.current
              ? { ...msg, text: msg.text + message_from_server.data }
              : msg
          )
        );

        setTimeout(() => {
          if (messagesDivRef.current) {
            messagesDivRef.current.scrollTop = messagesDivRef.current.scrollHeight;
          }
        }, 0);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed.');
      setMessages([{ id: 'status', text: 'Connection closed' }]);
    };

    ws.onerror = (e) => {
      console.log('WebSocket error:', e);
    };

    setWebsocket(ws);
  };

  const startAudio = async () => {
    const [playerNode] = await startAudioPlayerWorklet();
    audioPlayerNodeRef.current = playerNode;

    await startAudioRecorderWorklet((pcmData: ArrayBuffer) => {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        const messageJson = JSON.stringify({
          mime_type: 'audio/pcm',
          data: arrayBufferToBase64(pcmData),
        });
        websocket.send(messageJson);
        console.log('[CLIENT TO AGENT] sent %s bytes', pcmData.byteLength);
      }
    });
  };

  const handleStartAudio = () => {
    if (!isRecording) {
      setIsRecording(true);
      setMicStatus('Recording... Speak now');
      startAudio();
      connectWebsocket();
    }
  };

  const handleEndAudio = () => {
    if (isRecording) {
      setIsRecording(false);
      setMicStatus('Click the icon to start recording');
    }
  };

  return (
    <div className="max-w-xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-center mb-4">🎧 Live Audio Chat</h2>

      <div className="flex gap-4 mb-4">
        <button
          onClick={handleStartAudio}
          disabled={isRecording}
          className={`flex-1 py-2 rounded ${
            isRecording ? 'bg-red-500 cursor-not-allowed' : 'bg-green-500 hover:bg-green-600'
          } text-white font-semibold transition-colors duration-200`}
        >
          {isRecording ? 'Recording...' : 'Start Recording'}
        </button>

        <button
          onClick={handleEndAudio}
          className="flex-1 py-2 rounded bg-blue-500 hover:bg-blue-600 text-white font-semibold transition-colors duration-200"
        >
          End
        </button>
      </div>

      <div className="text-sm font-medium text-gray-600 mb-2">{micStatus}</div>

      <div
        ref={messagesDivRef}
        className="border border-gray-300 rounded p-2 h-48 overflow-y-auto bg-gray-50 text-sm"
      >
        {messages.map((msg) => (
          <p key={msg.id} className="mb-1">{msg.text}</p>
        ))}
      </div>
    </div>
  );
};
