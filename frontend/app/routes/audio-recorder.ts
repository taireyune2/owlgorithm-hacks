export async function startAudioRecorderWorklet(
  callback: (pcmData: ArrayBuffer) => void
): Promise<[AudioWorkletNode, AudioContext, MediaStream]> {
  const audioContext = new AudioContext({
    sampleRate: 24000,
  });

  // ✅ Use the correct recorder processor
  const workletURL = new URL('/worklets/pcm-recorder-processor.js', window.location.origin);
  await audioContext.audioWorklet.addModule(workletURL);

  const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const source = audioContext.createMediaStreamSource(micStream);

  const recorderNode = new AudioWorkletNode(audioContext, 'pcm-recorder-processor');

  // ✅ Get data from processor and pass to callback
  recorderNode.port.onmessage = (event) => {
    const pcmData = event.data as ArrayBuffer;
    callback(pcmData);
  };

  source.connect(recorderNode); // Connect mic to processor

  return [recorderNode, audioContext, micStream];
}
