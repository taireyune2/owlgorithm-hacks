(async () => {
    if (typeof window !== 'undefined') {
        try {
            // Create an AudioContext
            const audioContext = new AudioContext();

            // Load the audio worklet module
            await audioContext.audioWorklet.addModule('/worklets/pcm-player-processor.js');

            // Create an AudioWorkletNode
            const audioPlayerNode = new AudioWorkletNode(audioContext, 'pcm-player-processor');

            // Connect the node to the audio context destination
            audioPlayerNode.connect(audioContext.destination);

            console.log('Audio worklet setup complete.');
        } catch (error) {
            console.error('Error loading audio worklet module:', error);
        }
    } else {
        console.warn('AudioWorkletProcessor is not available in this environment.');
    }
})(); 