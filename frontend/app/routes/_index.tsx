import type { MetaFunction } from "@remix-run/node";
import { WebSocketAudio } from "./WebSocketAudio";
import { UploadResume, uploadResumeRawTextDataVar } from "./UploadResume";
import { JobDescriptionInput, JobDescriptionVar } from "./JobDescriptionInput";
import { Button } from "@mui/material";
import { StartSession } from "./StartSession";
import { useState } from "react";
import { useReactiveVar } from "@apollo/client";
import { StartSessionMascot } from "./StartSessionMascot";

export const meta: MetaFunction = () => {
  return [
    { title: "Behavioral Interview Assistant" },
    {
      name: "description",
      content:
        "Prepare for your behavioral interviews with AI-driven insights and personalized feedback. Enhance your interview skills and ace your next job opportunity.",
    },
  ];
};

export default function Index() {
  const [startSession, setStartSession] = useState(false);
  const resumeData = useReactiveVar(uploadResumeRawTextDataVar);
  const jobDescriptionInput = useReactiveVar(JobDescriptionVar);
  return (
    <div className="flex flex-row w-full h-screen bg-gray-100 gap-[10px]">
      <div className="flex flex-col mx-4  my-4 px-4 pb-20 h-96 w-[600px]">
        <div className="text-4xl font-bold mt-4 mb-6">Live Interview</div>
        <div className="text-lg font-bold mt-4 text-gray-500 mb-8">
          Start Your First Interview
        </div>
        <div className="mb-12">
          <UploadResume />
        </div>
        <div className="mb-12">
          <JobDescriptionInput />
        </div>
        <div>
          <StartSession
            disabled={!!resumeData && !!jobDescriptionInput ? false : true}
            onStartSession={() => setStartSession(true)}
          />
        </div>
      </div>

      <div className="flex mt-[68px]">
        {startSession && (
          <div className="text-2xl font-bold text-center mb-4">
            <StartSessionMascot />
          </div>
        )}
        {startSession && (
          <div className="w-[900px] ">
            <WebSocketAudio />
          </div>
        )}
      </div>
    </div>
  );
}
