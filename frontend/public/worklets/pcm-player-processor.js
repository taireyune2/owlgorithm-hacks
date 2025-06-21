/**
 * An audio worklet processor that stores the PCM audio data sent from the main thread
 * to a buffer and plays it.
 */
class PCMPlayerProcessor extends AudioWorkletProcessor {
  constructor() {
    super();

    // Init buffer
    this.bufferSize = 24000 * 180; // 24kHz x 180 seconds
    this.buffer = new Float32Array(this.bufferSize);
    this.writeIndex = 0;
    this.readIndex = 0;

    // Handle incoming messages from main thread
    this.port.onmessage = (event) => {
      // Reset the buffer when 'endOfAudio' message received
      if (event.data.command === "endOfAudio") {
        this.readIndex = this.writeIndex; // Clear the buffer
        console.log("endOfAudio received, clearing the buffer.");
        return;
      }

      // Handle stop command for immediate audio stop
      if (event.data.type === "stop") {
        this.readIndex = this.writeIndex; // Clear the buffer
        console.log("Stop command received, clearing the buffer immediately.");
        return;
      }

      // Decode the base64 data to int16 array.
      const int16Samples = new Int16Array(event.data);

      // Add the audio data to the buffer
      this._enqueue(int16Samples);
    };
  }

  // Push incoming Int16 data into our ring buffer.
  _enqueue(int16Samples) {
    for (let i = 0; i < int16Samples.length; i++) {
      // Convert 16-bit integer to float in [-1, 1]
      const floatVal = int16Samples[i] / 32768;

      // Store in ring buffer for left channel only (mono)
      this.buffer[this.writeIndex] = floatVal;
      this.writeIndex = (this.writeIndex + 1) % this.bufferSize;

      // Overflow handling (overwrite oldest samples)
      if (this.writeIndex === this.readIndex) {
        this.readIndex = (this.readIndex + 1) % this.bufferSize;
      }
    }
  }

  // The system calls `process()` ~128 samples at a time (depending on the browser).
  // We fill the output buffers from our ring buffer.
  process(inputs, outputs) {
    let sum = 0;
    // Write a frame to the output
    const output = outputs[0];
    const framesPerBlock = output[0].length;
    for (let frame = 0; frame < framesPerBlock; frame++) {
      const sample = this.buffer[this.readIndex] || 0;
      // Write the sample(s) into the output buffer
      output[0][frame] = this.buffer[this.readIndex]; // left channel
      if (output[1]) {
        output[1][frame] = sample; // right channel
      }
      sum += Math.abs(sample);

      // Move the read index forward unless underflowing
      if (this.readIndex != this.writeIndex) {
        this.readIndex = (this.readIndex + 1) % this.bufferSize;
      }
    }
    const avg = sum / framesPerBlock;
    this.port.postMessage({ speaking: avg > 0.01 });

    // Returning true tells the system to keep the processor alive
    return true;
  }
}

registerProcessor("pcm-player-processor", PCMPlayerProcessor);
