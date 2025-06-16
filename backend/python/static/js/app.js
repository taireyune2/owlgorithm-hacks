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
  // const data = {
  //   "session_id": sessionId,
  //   "resume": {
  //     "email": "tyler@gmail.com",
  //     "phone": "5103879999",
  //     "rawText": "# Micheal Li\n\n**Email:** micheal.li@example.com  \n**Phone:** (123) 456-7890  \n**Location:** San Francisco, CA  \n**GitHub:** [github.com/michaelli](https://github.com/michaelli)  \n**LinkedIn:** [linkedin.com/in/michaelli](https://linkedin.com/in/michaelli)\n\n---\n\n## \ud83e\uddd1\u200d\ud83d\udcbb Summary\n\nMotivated junior software engineer with hands-on experience building scalable backend services using Java and AWS. Strong understanding of REST APIs, microservices architecture, and CI/CD pipelines. Eager to contribute to impactful projects and grow within a collaborative engineering team.\n\n---\n\n## \ud83d\udee0\ufe0f Technical Skills\n\n- **Languages:** Java, Python, SQL  \n- **Backend:** Spring Boot, REST APIs, JUnit  \n- **Cloud:** AWS (EC2, S3, Lambda, RDS)  \n- **DevOps:** Git, Docker, Jenkins, GitHub Actions  \n- **Databases:** MySQL, PostgreSQL, DynamoDB  \n- **Tools:** IntelliJ, Postman, Maven, VS Code\n\n---\n\n## \ud83d\udcbc Experience\n\n### Backend Engineering Intern  \n**Acme Tech Solutions \u2013 San Jose, CA**  \n*Jan 2024 \u2013 May 2024*\n\n- Developed and deployed RESTful APIs using Spring Boot and Java to support customer account management features.\n- Integrated AWS services (S3, RDS, Lambda) for secure file storage and backend processing.\n- Wrote unit and integration tests using JUnit, increasing backend code coverage by 35%.\n- Collaborated with senior engineers in Agile sprints and contributed to code reviews and design discussions.\n\n---\n\n## \ud83e\uddea Projects\n\n### Cloud File Upload Service  \nA secure and scalable file upload platform using AWS.\n\n- Implemented backend service in Java with Spring Boot.\n- Used **AWS S3** for file storage and **AWS Lambda** for asynchronous processing.\n- Managed deployments with **GitHub Actions** and **Docker** containers.\n\n### Student Course Registration API  \nA RESTful API for managing course registrations in a mock university system.\n\n- Built using Spring Boot, Java, and MySQL.\n- Supported CRUD operations for students and courses with validation and error handling.\n- Wrote automated tests to ensure API reliability and performance.\n\n---\n\n## \ud83c\udf93 Education\n\n**B.S. in Computer Science**  \nUniversity of California, Davis  \n*Graduated: Dec 2023*\n\n- Relevant Coursework: Data Structures, Algorithms, Cloud Computing, Software Engineering\n- Member of the ACM Student Chapter\n\n---\n\n## \ud83d\udcdc Certifications\n\n- AWS Certified Cloud Practitioner (2024)\n- Java Programming Nanodegree \u2013 Udacity (2023)\n\n---\n\n## \ud83c\udf31 Interests\n\nOpen source contributions, backend architecture, cloud infrastructure, hiking"
  //   }
  //   "job_description": {
  //     "link": "some website",
  //     "rawText": "asdf"
  //   }
  // };
  const data = {
    "session_id": sessionId,
    "resume": {
      "email": "tyler@gmail.com",
      "phone": "5103879999",
      "rawText": "# Micheal Li\n\n**Email:** micheal.li@example.com  \n**Phone:** (123) 456-7890  \n**Location:** San Francisco, CA  \n**GitHub:** [github.com/michaelli](https://github.com/michaelli)  \n**LinkedIn:** [linkedin.com/in/michaelli](https://linkedin.com/in/michaelli)\n\n---\n\n## \ud83e\uddd1\u200d\ud83d\udcbb Summary\n\nMotivated junior software engineer with hands-on experience building scalable backend services using Java and AWS. Strong understanding of REST APIs, microservices architecture, and CI/CD pipelines. Eager to contribute to impactful projects and grow within a collaborative engineering team.\n\n---\n\n## \ud83d\udee0\ufe0f Technical Skills\n\n- **Languages:** Java, Python, SQL  \n- **Backend:** Spring Boot, REST APIs, JUnit  \n- **Cloud:** AWS (EC2, S3, Lambda, RDS)  \n- **DevOps:** Git, Docker, Jenkins, GitHub Actions  \n- **Databases:** MySQL, PostgreSQL, DynamoDB  \n- **Tools:** IntelliJ, Postman, Maven, VS Code\n\n---\n\n## \ud83d\udcbc Experience\n\n### Backend Engineering Intern  \n**Acme Tech Solutions \u2013 San Jose, CA**  \n*Jan 2024 \u2013 May 2024*\n\n- Developed and deployed RESTful APIs using Spring Boot and Java to support customer account management features.\n- Integrated AWS services (S3, RDS, Lambda) for secure file storage and backend processing.\n- Wrote unit and integration tests using JUnit, increasing backend code coverage by 35%.\n- Collaborated with senior engineers in Agile sprints and contributed to code reviews and design discussions.\n\n---\n\n## \ud83e\uddea Projects\n\n### Cloud File Upload Service  \nA secure and scalable file upload platform using AWS.\n\n- Implemented backend service in Java with Spring Boot.\n- Used **AWS S3** for file storage and **AWS Lambda** for asynchronous processing.\n- Managed deployments with **GitHub Actions** and **Docker** containers.\n\n### Student Course Registration API  \nA RESTful API for managing course registrations in a mock university system.\n\n- Built using Spring Boot, Java, and MySQL.\n- Supported CRUD operations for students and courses with validation and error handling.\n- Wrote automated tests to ensure API reliability and performance.\n\n---\n\n## \ud83c\udf93 Education\n\n**B.S. in Computer Science**  \nUniversity of California, Davis  \n*Graduated: Dec 2023*\n\n- Relevant Coursework: Data Structures, Algorithms, Cloud Computing, Software Engineering\n- Member of the ACM Student Chapter\n\n---\n\n## \ud83d\udcdc Certifications\n\n- AWS Certified Cloud Practitioner (2024)\n- Java Programming Nanodegree \u2013 Udacity (2023)\n\n---\n\n## \ud83c\udf31 Interests\n\nOpen source contributions, backend architecture, cloud infrastructure, hiking"
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