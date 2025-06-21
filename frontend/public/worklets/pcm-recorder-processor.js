class PCMRecorderProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = [];
  }

  process(inputs) {
    if (inputs.length > 0 && inputs[0].length > 0) {
      const inputChannel = inputs[0][0];
      for (let i = 0; i < inputChannel.length; i++) {
        const s = Math.max(-1, Math.min(1, inputChannel[i])) * 0x7fff;
        this.buffer.push(s);
      }

      if (this.buffer.length >= 160) {
        const int16Buffer = new Int16Array(this.buffer.slice(0, 160));
        this.buffer = this.buffer.slice(160);
        this.port.postMessage(int16Buffer.buffer, [int16Buffer.buffer]);
      }
    }
    return true;
  }
}

registerProcessor("pcm-recorder-processor", PCMRecorderProcessor);
