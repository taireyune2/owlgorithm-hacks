import { useState, useRef, useEffect } from "react";
import { startAudioPlayerWorklet } from "./audio-player";
import { startAudioRecorderWorklet } from "./audio-recorder";
import { useReactiveVar } from "@apollo/client";
import { uploadResumeRawTextDataVar } from "./UploadResume";
import { JobDescriptionVar } from "./JobDescriptionInput";
import { InterviewerMascot } from "./InterviewerMascot";
import { Alert, Button } from "@mui/material";

interface Message {
  id: string;
  text: string;
  role?: "user" | "agent" | "system";
}

// Get environment variables with fallbacks
const getBackendUrl = () => {
  return process.env.VITE_BACKEND_API_URL;
};

const getWebSocketUrl = () => {
  return process.env.VITE_WEBSOCKET_URL;
};

export const WebSocketAudio = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [micStatus, setMicStatus] = useState("");
  const [uploadFailed, setUploadFailed] = useState("");
  const [role, setRole] = useState("");
  const [wsStatus, setWsStatus] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const resumeData = useReactiveVar(uploadResumeRawTextDataVar);
  const jobDescriptionInput = useReactiveVar(JobDescriptionVar);
  const messagesDivRef = useRef<HTMLDivElement>(null);
  const currentMessageIdRef = useRef<string | null>(null);
  const audioPlayerNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioPlayerContextRef = useRef<AudioContext | null>(null);
  const audioRecorderContextRef = useRef<AudioContext | null>(null);
  const audioRecorderStreamRef = useRef<MediaStream | null>(null);
  const wsUrlRef = useRef<string>("");

  const [sessionIdStarted, setSessionIdStarted] = useState("");
  useEffect(() => {
    if (typeof window !== "undefined") {
      const sessionId = Math.random().toString().substring(10);
      setSessionIdStarted(sessionId);
      // Use environment variable for WebSocket URL
      const baseWsUrl = getWebSocketUrl();
      wsUrlRef.current = `${baseWsUrl}/ws/${sessionId}`;
    }
  }, []);

  useEffect(() => {
    setWsStatus(wsStatus);
  }, []);

  // Cleanup effect to stop audio when component unmounts
  useEffect(() => {
    return () => {
      // Stop audio playback when component unmounts
      if (audioPlayerNodeRef.current) {
        audioPlayerNodeRef.current.port.postMessage({ type: "stop" });
        audioPlayerNodeRef.current = null;
      }

      // Clean up audio contexts
      if (audioPlayerContextRef.current) {
        audioPlayerContextRef.current.close();
        audioPlayerContextRef.current = null;
      }
      if (audioRecorderContextRef.current) {
        audioRecorderContextRef.current.close();
        audioRecorderContextRef.current = null;
      }

      // Stop microphone stream
      if (audioRecorderStreamRef.current) {
        audioRecorderStreamRef.current
          .getTracks()
          .forEach((track) => track.stop());
        audioRecorderStreamRef.current = null;
      }

      // Close WebSocket connection
      if (websocket) {
        websocket.close(1000, "Component unmounted");
        setWebsocket(null);
      }

      setIsSpeaking(false);
    };
  }, [websocket]);

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
    let binary = "";
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  };

  const connectWebsocket = (): Promise<WebSocket> => {
    return new Promise((resolve, reject) => {
      if (!wsUrlRef.current) return reject("No WebSocket URL");

      const ws = new WebSocket(`${wsUrlRef.current}?is_audio=true`);

      ws.onopen = () => {
        setMessages([
          { id: "status", text: "Connection opened", role: "system" },
        ]);
        resolve(ws);
      };

      ws.onmessage = (event) => {
        const message_from_server = JSON.parse(event.data);

        setWsStatus(message_from_server.status);

        if (message_from_server.turn_complete) {
          currentMessageIdRef.current = null;
          return;
        }

        if (
          message_from_server.mime_type === "audio/pcm" &&
          audioPlayerNodeRef.current
        ) {
          const audioData = base64ToArray(message_from_server.data);

          audioPlayerNodeRef.current.port.postMessage(audioData);
        }

        if (message_from_server.mime_type === "text/plain") {
          if (!currentMessageIdRef.current) {
            currentMessageIdRef.current = Math.random()
              .toString(36)
              .substring(7);
            setMessages((prev) => [
              ...prev,
              { id: currentMessageIdRef.current!, text: "" },
            ]);
          }

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === currentMessageIdRef.current
                ? {
                    ...msg,
                    text: msg.text + message_from_server.data,
                    role: "agent",
                  }
                : msg
            )
          );

          // Add breakline if this is the "Response completed by Gemini" message
          if (message_from_server.signal === "turn_complete") {
            setMessages((prev) => [
              ...prev,
              { id: "newline", text: "\n", role: "system" },
            ]);
            currentMessageIdRef.current = null;
          }

          setTimeout(() => {
            messagesDivRef.current?.scrollTo({
              top: messagesDivRef.current.scrollHeight,
            });
          }, 0);
        }
      };

      ws.onerror = (e) => {
        console.error("WebSocket error:", e);
        reject(e);
      };

      ws.onclose = () => {
        console.log("WebSocket connection closed.");

        // Stop audio playback when connection is closed
        if (audioPlayerNodeRef.current) {
          audioPlayerNodeRef.current.port.postMessage({ type: "stop" });
          audioPlayerNodeRef.current = null;
        }

        setMessages((prev) => [
          ...prev,
          { id: "status", text: "Connection closed", role: "system" },
        ]);
        setIsSpeaking(false);
      };

      setWebsocket(ws); // set to React state
    });
  };

  const handleStartAudio = async () => {
    if (isRecording) return;

    // Clear previous messages and reset state for new session
    setMessages([]);
    currentMessageIdRef.current = null;

    setIsRecording(true);
    const payload = {
      resume: {
        rawText: resumeData,
        email: null,
        phone: null,
      },
      job_description: {
        rawText: jobDescriptionInput,
        link: null,
      },
      session_id: sessionIdStarted,
    };
    try {
      const response = await fetch(`${getBackendUrl()}/upload`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        setIsRecording(false);
        const errorData = await response.json();

        setUploadFailed(
          `Upload Failed, please ensure valid job description or resume has been uploaded`
        );
        throw new Error("Failed to upload resume data");
      } else {
        setUploadFailed("");
      }

      const ws = await connectWebsocket();

      const [playerNode, playerContext] = await startAudioPlayerWorklet(
        (speaking) => {
          setIsSpeaking(speaking);
        }
      );
      audioPlayerNodeRef.current = playerNode;
      audioPlayerContextRef.current = playerContext;

      const [recorderNode, recorderContext, recorderStream] =
        await startAudioRecorderWorklet((pcmData: ArrayBuffer) => {
          if (ws.readyState === WebSocket.OPEN) {
            const messageJson = JSON.stringify({
              mime_type: "audio/pcm",
              data: arrayBufferToBase64(pcmData),
            });
            ws.send(messageJson);
            setMicStatus("");
          }
        });
      audioRecorderContextRef.current = recorderContext;
      audioRecorderStreamRef.current = recorderStream;
    } catch (error) {
      setMicStatus("Socket connection failed, please try again");
      setIsRecording(false);
    }
  };

  const handleEndAudio = () => {
    if (isRecording) {
      setIsRecording(false);

      // Immediately stop audio playback
      if (audioPlayerNodeRef.current) {
        // Send stop command to clear audio buffer
        audioPlayerNodeRef.current.port.postMessage({ type: "stop" });
        audioPlayerNodeRef.current = null;
      }

      // Clean up audio player context
      if (audioPlayerContextRef.current) {
        audioPlayerContextRef.current.close();
        audioPlayerContextRef.current = null;
      }

      // Clean up audio recorder context
      if (audioRecorderContextRef.current) {
        audioRecorderContextRef.current.close();
        audioRecorderContextRef.current = null;
      }

      // Stop and clean up microphone stream
      if (audioRecorderStreamRef.current) {
        audioRecorderStreamRef.current
          .getTracks()
          .forEach((track) => track.stop());
        audioRecorderStreamRef.current = null;
      }

      // Close WebSocket connection
      if (websocket) {
        websocket.close(1000, "Session ended by user");
        setWebsocket(null);
        setWsStatus("close");
      }

      setIsSpeaking(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-center mb-4 text-gray-600">
        Live Audio Chat
      </h2>

      <div className="flex gap-8 mb-4">
        <Button
          onClick={handleStartAudio}
          sx={{ width: 300 }}
          disabled={wsStatus == "open"}
          variant="contained"
          color={isRecording ? "success" : "primary"}
        >
          {isRecording ? "Recording..." : "Start Recording"}
        </Button>

        <Button
          variant="contained"
          sx={{ width: 300 }}
          disabled={!isRecording}
          color="secondary"
          onClick={handleEndAudio}
        >
          End
        </Button>
      </div>
      {uploadFailed && <Alert severity="error">{uploadFailed}</Alert>}
      {micStatus && <Alert severity="warning">{micStatus}</Alert>}
      <div className="sticky top-20z-10 flex justify-center mb-4">
        <InterviewerMascot speaking={isSpeaking} />
      </div>
      <div
        ref={messagesDivRef}
        className="flex flex-col border border-gray-300 rounded p-2 overflow-y-auto bg-gray-50 text-sm mx-auto h-[288px]"
      >
        <div>
          {messages.map((msg) => (
            <div key={msg.id} className="mb-1">
              {msg.id === "newline" ? (
                <div className="h-6 bg-slate-100"></div>
              ) : (
                <div
                  className={`${
                    msg.role === "system"
                      ? "bg-gray-200 text-gray-800 italic h-8 items-center flex justify-center"
                      : msg.role === "agent"
                        ? "bg-blue-100 text-blue-800 font-normal py-4"
                        : "bg-green-100 text-green-800 font-normal py-4"
                  }`}
                >
                  {msg.text}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
