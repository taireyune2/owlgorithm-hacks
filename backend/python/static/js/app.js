/**
* Copyright 2025 Google LLC
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

/**
 * app.js: JS code for the adk-streaming sample app.
 */

/**
 * WebSocket handling
 */

// Connect the server with a WebSocket connection
const sessionId = Math.random().toString().substring(10);
const ws_url =
  "ws://" + window.location.host + "/ws/" + sessionId;
let websocket = null;

// Get DOM elements
const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("message");
const messagesDiv = document.getElementById("messages");
let currentMessageId = null;
let isRecording = false;
const micStatus = document.getElementById('mic-status');

// WebSocket handlers
function connectWebsocket() {
  // Connect websocket
  websocket = new WebSocket(ws_url);

  // Handle connection open
  websocket.onopen = function () {
    // Connection opened messages
    console.log("WebSocket connection opened.");
    document.getElementById("messages").textContent = "Connection opened";
  };

  // Handle incoming messages
  websocket.onmessage = function (event) {
    // Parse the incoming message
    const message_from_server = JSON.parse(event.data);
    console.log("[AGENT TO CLIENT] ", message_from_server);

    // Check if the turn is complete
    // if turn complete, add new message
    if (
      message_from_server.turn_complete &&
      message_from_server.turn_complete == true
    ) {
      currentMessageId = null;
      return;
    }

    // If it's audio, play it
    if (message_from_server.mime_type == "audio/pcm" && audioPlayerNode) {
      audioPlayerNode.port.postMessage(_base64ToArray(message_from_server.data));
    }

    // If it's a text, print it
    if (message_from_server.mime_type == "text/plain") {
      // add a new message for a new turn
      if (currentMessageId == null) {
        currentMessageId = Math.random().toString(36).substring(7);
        const message = document.createElement("p");
        message.id = currentMessageId;
        // Append the message element to the messagesDiv
        messagesDiv.appendChild(message);
      }

      // Add message text to the existing message element
      const message = document.getElementById(currentMessageId);
      message.textContent += message_from_server.data;

      // Scroll down to the bottom of the messagesDiv
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  };
}

function uploadBackground() {
  /// hard coded json body
  const data = {
    "session_id": sessionId,
    "resume": {
      "email": "tyler@gmail.com",
      "phone": "5103879999",
      "rawText": "# \ud83e\udde0 Machine Learning Engineer\n\n**Location:** San Francisco, CA (Hybrid)  \n**Employment Type:** Full-time  \n**Team:** AI/ML Engineering  \n**Experience Level:** Mid to Senior Level\n\n---\n\n## \ud83d\udccc About the Role\n\nWe are looking for a **Machine Learning Engineer** to join our dynamic AI/ML team. You will help design, build, and deploy scalable machine learning systems that power intelligent features and insights for our products. This is an opportunity to have a meaningful impact by working on cutting-edge models and data pipelines in a collaborative environment.\n\n---\n\n## \ud83d\udcbc Responsibilities\n\n- Design, implement, and optimize machine learning models for production use.\n- Collaborate with data scientists, engineers, and product managers to define requirements and success metrics.\n- Develop and maintain scalable data pipelines for training and inference.\n- Conduct rigorous model evaluations and performance tuning.\n- Stay current with the latest advancements in machine learning and deep learning.\n- Own and maintain the ML model lifecycle including versioning, testing, monitoring, and retraining.\n- Write clean, maintainable, and well-documented code.\n\n---\n\n## \ud83d\udee0\ufe0f Requirements\n\n- Bachelor's or Master's degree in Computer Science, Engineering, Mathematics, or related field.\n- 3+ years of hands-on experience in machine learning, deep learning, or applied AI.\n- Proficiency in Python and ML libraries such as TensorFlow, PyTorch, scikit-learn, XGBoost, etc.\n- Solid understanding of data structures, algorithms, and software engineering principles.\n- Experience deploying ML models to production (e.g., using Docker, Kubernetes, or cloud services).\n- Familiarity with ML model evaluation, interpretability, and monitoring tools.\n\n---\n\n## \u2705 Bonus Points\n\n- Experience with MLOps tools (MLflow, SageMaker, Vertex AI, etc.).\n- Contributions to open source ML projects.\n- Experience with large-scale distributed systems.\n- Background in NLP, computer vision, or time series modeling.\n\n---\n\n## \ud83c\udf1f What We Offer\n\n- Competitive compensation and equity packages.\n- Comprehensive health, dental, and vision insurance.\n- Generous PTO and flexible work hours.\n- Professional development stipend and learning opportunities.\n- A supportive team culture that encourages innovation and autonomy.\n\n---\n\n**Join us and help shape the future of intelligent systems.**  \nApply now or reach out to [careers@example.com](mailto:careers@example.com) with any questions."
    },
    "job_description": {
      "link": "some website",
      "rawText": "About the Role\n\nWe are looking for a skilled and motivated Backend Engineer to join our AI Platform team to build and scale production-ready APIs powered by Gemini, Google\u2019s state-of-the-art multimodal models. In this role, you will design, develop, and optimize API services that make AI capabilities accessible, secure, and performant for downstream applications.\n\nYou\u2019ll work alongside machine learning engineers, frontend developers, and product managers to bring intelligent features to life, with a strong emphasis on reliability, observability, and scalability.\n\n\u2e3b\n\nResponsibilities\n\t\u2022\tDesign and implement scalable REST and/or gRPC APIs for Gemini-powered features.\n\t\u2022\tWork closely with ML teams to productionize Gemini model calls (e.g., prompt templating, streaming output, retries).\n\t\u2022\tBuild and manage asynchronous job pipelines and caching layers to handle long-running or expensive model inference tasks.\n\t\u2022\tSecure APIs with proper authentication/authorization (OAuth2, JWT, API keys).\n\t\u2022\tWrite integration and unit tests to ensure reliability and correctness.\n\t\u2022\tMonitor and improve performance using observability tools (e.g., OpenTelemetry, Prometheus, Grafana).\n\t\u2022\tCollaborate cross-functionally to define API interfaces and service SLAs.\n\t\u2022\tEnsure the APIs are documented, versioned, and easy to consume.\n\n\u2e3b\n\nMinimum Qualifications\n\t\u2022\t3+ years of experience building backend services in Python, Go, Java, or similar.\n\t\u2022\tProficiency in designing and maintaining RESTful APIs and/or gRPC services.\n\t\u2022\tExperience with containerized environments (Docker, Kubernetes, ECS).\n\t\u2022\tFamiliarity with cloud infrastructure (GCP, AWS, or Azure).\n\t\u2022\tStrong understanding of API security best practices and performance tuning.\n\t\u2022\tComfort working with large-scale data or model outputs (e.g., token streaming, pagination, rate limits).\n\n\u2e3b\n\nPreferred Qualifications\n\t\u2022\tExperience integrating with large language models (LLMs) or generative AI APIs (Gemini, OpenAI, Claude).\n\t\u2022\tExposure to vector stores, embedding pipelines, or RAG systems.\n\t\u2022\tFamiliarity with API gateways (e.g., Kong, Apigee) and traffic management.\n\t\u2022\tKnowledge of FastAPI, Flask, or equivalent modern Python frameworks.\n\t\u2022\tContributions to open-source AI or API tooling."
    }
  };
  const url = "http://localhost:8000/upload";
  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
  .then(response => {
    if (!response.ok) throw new Error('Network response was not ok');
    return response.json();
  })
  .then(result => {
    console.log('Success:', result);
  })
  .catch(error => {
    console.error('Error:', error);
  });
}
/**
 * Audio handling
 */

let audioPlayerNode;
let audioPlayerContext;
let audioRecorderNode;
let audioRecorderContext;
let micStream;

// Import the audio worklets
import { startAudioPlayerWorklet } from "./audio-player.js";
import { startAudioRecorderWorklet } from "./audio-recorder.js";

// Start audio
function startAudio() {
  // Start audio output
  startAudioPlayerWorklet().then(([node, ctx]) => {
    audioPlayerNode = node;
    audioPlayerContext = ctx;
  });

  // Start audio input
  startAudioRecorderWorklet(
    // Audio recorder handler
    function audioRecorderHandler(pcmData) {
      // Send the pcm data as base64
      // Send a message to the server as a JSON string
      if (websocket && websocket.readyState == WebSocket.OPEN) {
        const messageJson = JSON.stringify({
          mime_type: "audio/pcm",
          data: _arrayBufferToBase64(pcmData),
        });
        websocket.send(messageJson);
      }
      console.log("[CLIENT TO AGENT] sent %s bytes", pcmData.byteLength);
    }
  ).then(
    ([node, ctx, stream]) => {
      audioRecorderNode = node;
      audioRecorderContext = ctx;
      micStream = stream;
    }
  );
}

// Start the audio only when the user clicked the button
// (due to the gesture requirement for the Web Audio API)
const startAudioButton = document.getElementById("startAudioButton");
startAudioButton.addEventListener("click", () => {
  if (!isRecording) {
    startAudioButton.disabled = true;
    uploadBackground();
    startAudio();
    connectWebsocket(); // reconnect with the audio mode
    isRecording = true;
    startAudioButton.classList.add('mic-active');
    micStatus.textContent = 'Recording... Speak now';
  }
});

// End button handler
const endButton = document.getElementById('end-button');
endButton.addEventListener('click', () => {
  if (isRecording) {
    isRecording = false;
    startAudioButton.classList.remove('mic-active');
    micStatus.textContent = 'Click the icon to start recording';
  }
});


// Decode Base64 data to Array
function _base64ToArray(base64) {
  const binaryString = window.atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

// Encode an array buffer with Base64
function _arrayBufferToBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}