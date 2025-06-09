import Lottie from "lottie-react";
import mascotAnimation from "./talking.json";
import { useEffect, useRef } from "react";
export const InterviewerMascot = ({ speaking }: { speaking: boolean }) => {
  const lottieRef = useRef<any>(null);
  useEffect(() => {
    if (!lottieRef.current) return;
    if (speaking) {
      lottieRef.current?.play();
    } else {
      lottieRef.current?.stop();
    }
  }, [speaking]);
  return (
    <Lottie
      width={600}
      lottieRef={lottieRef}
      animationData={mascotAnimation}
      loop={true}
      autoPlay={false}
    ></Lottie>
  );
};
