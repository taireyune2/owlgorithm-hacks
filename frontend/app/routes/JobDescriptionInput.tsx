import { TextField } from "@mui/material";
import { NotebookIcon } from "lucide-react";
import { useState } from "react";

export const JobDescriptionInput = () => {
  const [jobDescriptionInput, setJobDescriptionInput] = useState("");
  console.log("Job Description Input:", jobDescriptionInput);
  return (
    <div className="flex items-center justify-between ml-3 w-[500px]">
      <div className="text-lg font-bold">
        <NotebookIcon className="inline mr-2" />
        Job Description
      </div>

      <TextField
        id="outlined-multiline-static"
        label="Job Description"
        multiline
        rows={4}
        defaultValue=""
        onChange={(e) => setJobDescriptionInput(e.target.value)}
      />
    </div>
  );
};
