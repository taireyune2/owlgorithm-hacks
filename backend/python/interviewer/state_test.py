import pytest 
from dotenv import load_dotenv

from common import logger
logger.setup({
  "level": 20,
  "env": "dev",
  "file": {
    "path": "../logs"
  },
  "console": {}
})
load_dotenv()

import logging
import json
from google.adk.sessions import InMemorySessionService
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
import random
import os

from . import state

from .state import InterviewRound


async def test_interview_prep_background():
  session_service = InMemorySessionService()
  run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    speech_config=types.SpeechConfig(
      voice_config=types.VoiceConfig(
        prebuilt_voice_config=types.PrebuiltVoiceConfig(
          voice_name=random.choice("kora")
        )
      )
    ),
    response_modalities=["AUDIO"],
    output_audio_transcription=types.AudioTranscriptionConfig(),
    input_audio_transcription=types.AudioTranscriptionConfig(),
  )

  agent_configs = {
    "name": "OwlSpeak",
  }
  resume = "# Alex Wang\n\n**Email: Location:** Menlo Park, CA  \n## \ud83e\udde0 Summary\n\nSenior Software Engineer at Meta with 9+ years of experience in large-scale machine learning infrastructure, currently maintaining and leading development efforts on the PyTorch open-source library. Passionate about creating high-performance, developer-friendly ML tools and fostering open collaboration in the AI community.\n\n---\n\n## \ud83d\udee0 Technical Skills\n\n- **Languages:** Python, C++, CUDA, Bash  \n- **ML Frameworks:** PyTorch, TensorFlow, ONNX  \n- **Tooling:** Git, CMake, Docker, Bazel, Jenkins  \n- **Cloud & Infra:** AWS, Kubernetes, TorchServe  \n- **Operating Systems:** Linux, macOS  \n\n---\n\n## \ud83e\udde9 Professional Experience\n\n### Meta \u2014 *Senior Software Engineer*  \n**Menlo Park, CA** | *Jan 2019 \u2013 Present*  \n**PyTorch Core Team**\n\n- Led the development of major features in PyTorch 2.x, including support for dynamic shapes and better integration with TorchDynamo.\n- Owned the distributed training module (`torch.distributed`), improving multi-GPU training performance by 30% across benchmarks.\n- Reviewed and merged 1,000+ pull requests from contributors across Meta and the open-source community.\n- Drove adoption of PyTorch 2.0 across internal teams, collaborating with product engineers and researchers to onboard over 100 ML workloads.\n- Maintained CI/CD pipelines and release engineering for PyTorch; improved release cadence by 25%.\n\n### Meta \u2014 *Software Engineer*  \n**Seattle, WA** | *Aug 2016 \u2013 Dec 2018*  \n**Applied Machine Learning Infrastructure**\n\n- Designed and implemented internal tools for model training, hyperparameter tuning, and experiment tracking.\n- Contributed to the backend of Meta\u2019s ML experimentation platform, used by over 500 engineers across the company.\n- Worked closely with FAIR (Facebook AI Research) to prototype and deploy new model architectures at scale.\n\n---\n\n## \ud83d\udcda Education\n\n**University of Washington**  \nB.S. in Computer Science, 2012 \u2013 2016  \n- Graduated with Honors  \n- Undergraduate Researcher in Parallel Computing Lab\n\n---\n\n## \ud83c\udfc6 Open Source & Community\n\n- **Maintainer, PyTorch** \u2014 Core contributor since 2019  \n- **Speaker** at NeurIPS, ICML, and PyTorch Developer Day  \n- **Mentor** in Meta\u2019s open-source fellowship program  \n- **Author** of internal best practices on scalable ML training\n\n---\n\n## \ud83e\uddea Projects\n\n**TorchBench** \u2014 Benchmarks suite for PyTorch models  \n**Dynamo Debugger** \u2014 Tooling for PyTorch TorchDynamo introspection and performance profiling  \n**ONNX Exporter Improvements** \u2014 Enhanced operator coverage and model fidelity during PyTorch-to-ONNX conversion\n\n---"
  job_description = "# \ud83e\udde0 Machine Learning Engineer\n\n**Location:** San Francisco, CA (Hybrid)  \n**Employment Type:** Full-time  \n**Team:** AI/ML Engineering  \n**Experience Level:** Mid to Senior Level\n\n---\n\n## \ud83d\udccc About the Role\n\nWe are looking for a **Machine Learning Engineer** to join our dynamic AI/ML team. You will help design, build, and deploy scalable machine learning systems that power intelligent features and insights for our products. This is an opportunity to have a meaningful impact by working on cutting-edge models and data pipelines in a collaborative environment.\n\n---\n\n## \ud83d\udcbc Responsibilities\n\n- Design, implement, and optimize machine learning models for production use.\n- Collaborate with data scientists, engineers, and product managers to define requirements and success metrics.\n- Develop and maintain scalable data pipelines for training and inference.\n- Conduct rigorous model evaluations and performance tuning.\n- Stay current with the latest advancements in machine learning and deep learning.\n- Own and maintain the ML model lifecycle including versioning, testing, monitoring, and retraining.\n- Write clean, maintainable, and well-documented code.\n\n---\n\n## \ud83d\udee0\ufe0f Requirements\n\n- Bachelor's or Master's degree in Computer Science, Engineering, Mathematics, or related field.\n- 3+ years of hands-on experience in machine learning, deep learning, or applied AI.\n- Proficiency in Python and ML libraries such as TensorFlow, PyTorch, scikit-learn, XGBoost, etc.\n- Solid understanding of data structures, algorithms, and software engineering principles.\n- Experience deploying ML models to production (e.g., using Docker, Kubernetes, or cloud services).\n- Familiarity with ML model evaluation, interpretability, and monitoring tools.\n\n---\n\n## \u2705 Bonus Points\n\n- Experience with MLOps tools (MLflow, SageMaker, Vertex AI, etc.).\n- Contributions to open source ML projects.\n- Experience with large-scale distributed systems.\n- Background in NLP, computer vision, or time series modeling.\n\n---\n\n## \ud83c\udf1f What We Offer\n\n- Competitive compensation and equity packages.\n- Comprehensive health, dental, and vision insurance.\n- Generous PTO and flexible work hours.\n- Professional development stipend and learning opportunities.\n- A supportive team culture that encourages innovation and autonomy.\n\n---\n\n**Join us and help shape the future of intelligent systems.**  \nApply now or reach out to [careers@example.com](mailto:careers@example.com) with any questions."
  
  interview_round = InterviewRound("123", session_service, run_config, agent_configs)
  background_info = await interview_round.prep_background(resume, job_description)

  logging.info(f"Background info: {background_info}")