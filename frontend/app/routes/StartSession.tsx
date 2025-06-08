import { Button } from "@mui/material";
import { ListStartIcon } from "lucide-react";

export const StartSession = ({
  onStartSession,
}: {
  onStartSession: () => void;
}) => {
  return (
    <div className="flex items-center justify-between ml-3 w-[500px]">
      <div className="text-lg font-bold">
        <ListStartIcon className="inline mr-2" />
        Start Session Here
      </div>

      <Button
        color="primary"
        variant="contained"
        className="ml-2"
        sx={{ width: 200 }}
        onClick={onStartSession}
      >
        Start Session
      </Button>
    </div>
  );
};
