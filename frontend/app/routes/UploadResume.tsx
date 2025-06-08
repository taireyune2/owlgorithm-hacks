import { Button } from "@mui/material";
import { UploadCloudIcon, UploadIcon } from "lucide-react";
import { useState } from "react";

export const UploadResume = () => {
  const [parseData, setParseData] = useState<any>(null);

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf") {
      alert("Please upload a PDF file.");
      return;
    }

    try {
      const pdfjsLib = await import("pdfjs-dist/build/pdf");

      // ✅ Configure worker (must match the path you placed it in `public`)
      pdfjsLib.GlobalWorkerOptions.workerSrc = "/pdfjs/pdf.worker.js";

      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

      let fullText = "";
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const content = await page.getTextContent();
        fullText += content.items.map((item: any) => item.str).join(" ") + "\n";
      }

      // ✅ Basic text extraction
      const extractData = (text: string) => {
        const email = text.match(
          /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}/
        )?.[0];
        const phone = text.match(
          /(\+?\d{1,2}[\s.-]?)?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}/
        )?.[0];
        return {
          email: email ?? null,
          phone: phone ?? null,
          rawText: text,
        };
      };

      const resumeJson = extractData(fullText);
      // Send to backend
      await fetch("/api/resume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(resumeJson),
      });

      setParseData(resumeJson);
      console.log("Parsed Resume:", resumeJson);
    } catch (error) {
      console.error("Failed to parse PDF:", error);
      alert("An error occurred while processing the PDF.");
    }
  };

  // console.log("Parsed Data:", parseData.rawText);
  // Send to backend
  //   await fetch("/api/resume", {
  //     method: "POST",
  //     headers: { "Content-Type": "application/json" },
  //     body: JSON.stringify(parseData.rawText),
  //   });
  // };
  return (
    <div className="flex items-center justify-between ml-3 w-[500px]">
      <div className="text-lg font-bold">
        <UploadCloudIcon className="inline mr-2" />
        Upload Resume
      </div>
      <Button
        variant="contained"
        color="primary"
        component="label"
        sx={{ width: 200 }}
      >
        <input
          className="hidden"
          type="file"
          accept=".pdf"
          onChange={handleUpload}
        />
        <UploadIcon className="mr-2" />
        Upload Resume
      </Button>
    </div>
  );
};
