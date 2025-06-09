import Lottie from "lottie-react";
import mascotAnimation from "./talking.json";
export const InterviewerMascot = ({ speaking }: { speaking: boolean }) => {
  return (
    <Lottie
      animationData={mascotAnimation}
      loop={speaking}
      autoPlay={speaking}
    ></Lottie>
  );
};
