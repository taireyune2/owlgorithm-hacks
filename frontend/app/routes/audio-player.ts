export async function startAudioPlayerWorklet(
  onSpeakingStatus?: (speaking: boolean) => void
): Promise<[AudioWorkletNode, AudioContext]> {
  // 1. Create an AudioContext
  const audioContext = new AudioContext({
    sampleRate: 24000,
  });

  // 2. Load your custom processor code
  const workletURL = new URL(
    "/worklets/pcm-player-processor.js",
    window.location.origin
  );
  await audioContext.audioWorklet.addModule(workletURL);

  // 3. Create an AudioWorkletNode
  const audioPlayerNode = new AudioWorkletNode(
    audioContext,
    "pcm-player-processor"
  );

  // 4. Connect to the destination
  audioPlayerNode.connect(audioContext.destination);

  // 5. Listen for speaking status from the processor
  if (onSpeakingStatus) {
    audioPlayerNode.port.onmessage = (event) => {
      if (typeof event.data?.speaking === "boolean") {
        onSpeakingStatus(event.data.speaking);
      }
    };
  }

  // The audioPlayerNode.port is how we send messages (audio data) to the processor
  return [audioPlayerNode, audioContext];
}
