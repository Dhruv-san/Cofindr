document.addEventListener('DOMContentLoaded', () => {
    const localVideo = document.getElementById('localVideo');
    const remoteVideo = document.getElementById('remoteVideo');
    const roomNameInput = document.getElementById('roomName');
    const statusMessagesDiv = document.getElementById('statusMessages');

    const startCallButton = document.getElementById('startCall');
    const endCallButton = document.getElementById('endCall');
    const muteAudioButton = document.getElementById('muteAudio');
    const muteVideoButton = document.getElementById('muteVideo');

    let localStream;
    let peerConnection;
    let ws; // WebSocket connection
    let currentRoomName;
    let isCallInitiator = false; // Helps determine who sends the offer

    let isAudioMuted = false;
    let isVideoMuted = false;

    // AI Agent related variables
    let speechRecognition;
    let isAIListening = false;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    // STUN server configuration (using public Google STUN servers)
    const peerConnectionConfig = {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
            // You might need a TURN server for NAT traversal in more complex network scenarios
        ]
    };

    // Disable buttons that are not yet functional or depend on call state
    endCallButton.disabled = true;

    // Helper function to update status messages
    function updateStatus(message, type = 'info') { // type can be 'info', 'success', 'error'
        statusMessagesDiv.textContent = message;
        statusMessagesDiv.className = 'status'; // Reset classes
        if (type === 'error') {
            statusMessagesDiv.classList.add('error');
        } else if (type === 'success') {
            statusMessagesDiv.classList.add('success');
        }
        console.log(`Status: [${type}] ${message}`);
    }


    // Function to access local media
    async function getLocalMedia() {
        updateStatus('Requesting media permissions...');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            console.log('Local media stream obtained');
            updateStatus('Media permissions granted.', 'success');
            localStream = stream;
            localVideo.srcObject = stream;
            // Enable mute buttons once the stream is active
            muteAudioButton.disabled = false;
            muteVideoButton.disabled = false;
            // Start call button will be enabled by WebSocket connection success
        } catch (error) {
            console.error('Error accessing media devices.', error);
            let message = 'Error accessing media devices. Please check permissions.';
            if (error.name === 'NotFoundError') {
                message = 'Media device not found. Please ensure camera/microphone are connected.';
            } else if (error.name === 'NotAllowedError') {
                message = 'Permission to use media devices was denied. Please allow access in browser settings.';
            } else if (error.name === 'AbortError') {
                message = 'Media device access request was aborted.';
            } else if (error.name === 'SecurityError') {
                message = 'Media device access denied due to security settings (e.g. not HTTPS).';
            }
            updateStatus(message, 'error');
            // alert(`Error accessing media devices: ${error.name} - ${error.message}`); // Replaced by status update
            startCallButton.disabled = true;
            roomNameInput.disabled = true;
            muteAudioButton.disabled = true;
            muteVideoButton.disabled = true;
        }
    }

    function connectWebSocket() {
        updateStatus('Connecting to signaling server...');
        ws = new WebSocket('ws://localhost:8080');

        ws.onopen = () => {
            console.log('Connected to signaling server');
            updateStatus('Connected to signaling server.', 'success');
            if (localStream) { // Ensure media is ready before enabling
                roomNameInput.disabled = false;
                startCallButton.disabled = false;
            } else {
                updateStatus('Media not ready, waiting for permissions...', 'info');
            }
        };

        ws.onmessage = async (message) => {
            const data = JSON.parse(message.data);
            console.log('Received message from signaling server:', data);

            switch (data.type) {
                case 'join_success':
                    updateStatus(`Successfully joined room: ${data.roomName}. Waiting for peer...`, 'success');
                    currentRoomName = data.roomName;
                    startCallButton.disabled = true;
                    roomNameInput.disabled = true;
                    endCallButton.disabled = false;
                    break;
                case 'peer_joined':
                    updateStatus('Peer joined. Initiating call...', 'info');
                    if (!peerConnection) {
                        isCallInitiator = true;
                        await createPeerConnectionAndOffer();
                    }
                    break;
                case 'offer':
                    updateStatus('Received offer. Creating answer...', 'info');
                    if (!peerConnection) {
                        isCallInitiator = false;
                        await createPeerConnection(); // Create PC if it doesn't exist
                    }
                    try {
                        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
                        const answer = await peerConnection.createAnswer();
                        await peerConnection.setLocalDescription(answer);
                        sendMessage({ type: 'answer', sdp: answer, roomName: currentRoomName });
                        updateStatus('Answer sent.', 'info');
                    } catch (e) {
                        console.error("Error handling offer:", e);
                        updateStatus(`Error handling offer: ${e.message}`, 'error');
                    }
                    break;
                case 'answer':
                    updateStatus('Received answer. Call should be established soon.', 'info');
                     try {
                        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
                    } catch (e) {
                        console.error("Error setting remote description from answer:", e);
                        updateStatus(`Error processing answer: ${e.message}`, 'error');
                    }
                    break;
                case 'candidate':
                    try {
                        if (data.candidate && peerConnection && peerConnection.remoteDescription) { // Only add if PC exists and remote desc is set
                            await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
                            console.log('Added received ICE candidate');
                        } else {
                            console.warn('Received ICE candidate but peerConnection or remoteDescription is not ready.', data.candidate);
                        }
                    } catch (e) {
                        console.error('Error adding received ICE candidate', e);
                        updateStatus(`Error adding ICE candidate: ${e.message}`, 'error');
                    }
                    break;
                case 'peer_hangup':
                    updateStatus('Peer has hung up.', 'info');
                    handleHangup(false);
                    break;
                case 'peer_left':
                    updateStatus('Peer has left the room.', 'info');
                    handleHangup(false);
                    break;
                case 'error':
                    console.error('Error from signaling server:', data.message);
                    updateStatus(`Server error: ${data.message}`, 'error');
                    // alert(`Error from server: ${data.message}`); // Replaced by status update
                    if (data.message.includes("full")) {
                        resetCallState(false); // Don't try to re-acquire media if room was full
                    }
                    break;
                default:
                    console.log('Unknown message type from server:', data.type);
                    updateStatus(`Received unknown message type: ${data.type}`, 'info');
            }
        };

        ws.onclose = () => {
            console.log('Disconnected from signaling server');
            updateStatus('Disconnected from signaling server. Please refresh.', 'error');
            handleHangup(false);
            startCallButton.disabled = true;
            roomNameInput.disabled = true;
            // alert('Disconnected from signaling server. Please refresh to try again.'); // Replaced
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateStatus('Could not connect to signaling server. Ensure it is running and refresh.', 'error');
            startCallButton.disabled = true;
            roomNameInput.disabled = true;
            // alert('Could not connect to signaling server. Please ensure it is running and refresh.'); // Replaced
        };
    }

    // Call getLocalMedia first, then connectWebSocket inside its success path or afterwards
    (async () => {
        await getLocalMedia();
        if (localStream) {
            connectWebSocket();
        } else {
            // Error already handled by getLocalMedia's updateStatus
            roomNameInput.disabled = true;
            startCallButton.disabled = true;
        }
    })();


    function sendMessage(message) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(message));
        } else {
            console.error('WebSocket is not connected.');
            updateStatus('Cannot send message: Not connected to server.', 'error');
        }
    }

    async function createPeerConnection() {
        if (peerConnection) {
            console.warn("PeerConnection already exists. Reusing existing one for setup.");
            // Potentially reset parts of it if needed, or ensure it's in a clean state.
            // For now, we assume if it exists, it's either being configured or is active.
        } else {
            updateStatus('Creating peer connection...', 'info');
            peerConnection = new RTCPeerConnection(peerConnectionConfig);
        }

        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                sendMessage({ type: 'candidate', candidate: event.candidate, roomName: currentRoomName });
                console.log('Sent ICE candidate:', event.candidate);
            }
        };

        peerConnection.ontrack = (event) => {
            console.log('Received remote track');
            if (remoteVideo.srcObject !== event.streams[0]) {
                remoteVideo.srcObject = event.streams[0];
                updateStatus('Remote video connected.', 'success');
                console.log('Displaying remote stream');
            }
        };
         peerConnection.oniceconnectionstatechange = () => {
            if (peerConnection) {
                console.log('ICE connection state change:', peerConnection.iceConnectionState);
                updateStatus(`ICE Connection: ${peerConnection.iceConnectionState}`);
                if (peerConnection.iceConnectionState === 'failed' ||
                    peerConnection.iceConnectionState === 'disconnected' ||
                    peerConnection.iceConnectionState === 'closed') {
                    // updateStatus(`Call disconnected: ${peerConnection.iceConnectionState}`, 'error');
                    // handleHangup(false); // Could lead to loops if server also sends peer_left
                    stopSpeechRecognition(); // Stop AI listening if call disconnects
                } else if (peerConnection.iceConnectionState === 'connected' || peerConnection.iceConnectionState === 'completed') {
                    updateStatus('Call connected.', 'success');
                    // Start AI listening when call is connected
                    startSpeechRecognition();
                }
            }
        };


        // Add local stream tracks to the peer connection
        if (localStream) {
            localStream.getTracks().forEach(track => {
                // Check if track is already added to avoid errors
                const sender = peerConnection.getSenders().find(s => s.track === track);
                if (!sender) {
                    peerConnection.addTrack(track, localStream);
                }
            });
            console.log('Ensured local stream tracks are added to peer connection');
        } else {
            console.error("Local stream not available when creating peer connection");
            updateStatus('Local media stream not available for call.', 'error');
        }
    }

    async function createPeerConnectionAndOffer() {
        await createPeerConnection();
        try {
            updateStatus('Creating offer...', 'info');
            const offer = await peerConnection.createOffer();
            await peerConnection.setLocalDescription(offer);
            sendMessage({ type: 'offer', sdp: offer, roomName: currentRoomName });
            updateStatus('Offer sent.', 'info');
        } catch (e) {
            console.error("Error creating offer:", e);
            updateStatus(`Error creating offer: ${e.message}`, 'error');
        }
    }


    // Mute Audio Button
    muteAudioButton.addEventListener('click', () => {
        if (!localStream) return;
        isAudioMuted = !isAudioMuted;
        localStream.getAudioTracks().forEach(track => track.enabled = !isAudioMuted);
        muteAudioButton.textContent = isAudioMuted ? 'Unmute Audio' : 'Mute Audio';
        updateStatus(isAudioMuted ? 'Audio Muted' : 'Audio Unmuted', 'info');
        console.log(isAudioMuted ? 'Audio Muted' : 'Audio Unmuted');
    });

    // Mute Video Button
    muteVideoButton.addEventListener('click', () => {
        if (!localStream) return;
        isVideoMuted = !isVideoMuted;
        localStream.getVideoTracks().forEach(track => track.enabled = !isVideoMuted);
        muteVideoButton.textContent = isVideoMuted ? 'Unmute Video' : 'Mute Video';
        updateStatus(isVideoMuted ? 'Video Muted' : 'Video Unmuted', 'info');
        console.log(isVideoMuted ? 'Video Muted' : 'Video Unmuted');
    });

    // Start Call Button Logic
    startCallButton.addEventListener('click', async () => {
        const room = roomNameInput.value.trim();
        if (!room) {
            updateStatus('Please enter a room name.', 'error');
            // alert('Please enter a room name.'); // Replaced
            return;
        }
        if (!localStream) {
            updateStatus('Local media is not available. Please check permissions.', 'error');
            // alert('Local media is not available. Please check camera/microphone permissions.'); // Replaced
            return;
        }
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            updateStatus('Not connected to the signaling server. Please wait or refresh.', 'error');
            // alert('Not connected to the signaling server. Please wait or refresh.'); // Replaced
            return;
        }

        currentRoomName = room;
        updateStatus(`Attempting to join room: ${currentRoomName}...`, 'info');
        sendMessage({ type: 'join', roomName: currentRoomName });
        // Offer creation is now handled by 'peer_joined' or explicitly called in that flow
    });


    function handleHangup(initiatedByThisClient = true) {
        updateStatus(initiatedByThisClient ? 'Ending call...' : 'Call ended by peer.', 'info');
        console.log('Handling hangup.');
        stopSpeechRecognition(); // Stop AI listening when call ends

        if (peerConnection) {
            peerConnection.close();
            peerConnection = null;
            console.log('PeerConnection closed.');
        }

        remoteVideo.srcObject = null;

        if (initiatedByThisClient && ws && ws.readyState === WebSocket.OPEN && currentRoomName) {
            sendMessage({ type: 'hangup', roomName: currentRoomName });
            console.log('Sent hangup message to peer.');
        }

        resetCallState(initiatedByThisClient); // Pass flag to control media re-acquisition
    }

    function resetCallState(isInitiatedByLocalClientHangup = false) {
        console.log('Resetting call state.');
        updateStatus('Call ended. Ready for new call.', 'info');

        remoteVideo.srcObject = null;
        isCallInitiator = false;
        // currentRoomName = null; // Keep currentRoomName if user wants to rejoin same room quickly? Or clear it. Let's clear.
        // currentRoomName = null; // This is cleared later or on new join.

        startCallButton.disabled = false;
        roomNameInput.disabled = false; // Allow changing room
        endCallButton.disabled = true;

        // Only re-acquire media if it was stopped or if not a local hangup action
        // If local client hung up, assume they might want to keep their media for a quick new call.
        // If call ended due to peer leaving or error, it's safer to ensure media is fresh.
        if (!isInitiatedByLocalClientHangup && (!localStream || localStream.getTracks().some(track => track.readyState === 'ended'))) {
            updateStatus('Re-acquiring media devices...', 'info');
            getLocalMedia().then(() => {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    startCallButton.disabled = false;
                    roomNameInput.disabled = false;
                } else {
                    connectWebSocket();
                }
            });
        } else if (ws && ws.readyState === WebSocket.OPEN) {
            // If WS is still open and media is fine
            startCallButton.disabled = false;
            roomNameInput.disabled = false;
        } else if (!ws || ws.readyState !== WebSocket.OPEN) {
            // If WS is closed, attempt to reconnect
            updateStatus('WebSocket closed. Attempting to reconnect...', 'info');
            connectWebSocket();
        }
        // Clear current room name to ensure new join logic works correctly
        currentRoomName = null;
    }


    // End Call Button
    endCallButton.addEventListener('click', () => {
        console.log('End Call button clicked by user.');
        handleHangup(true);
    });

    // Initialize button states & status
    muteAudioButton.disabled = true;
    muteVideoButton.disabled = true;
    startCallButton.disabled = true;
    roomNameInput.disabled = true;
    endCallButton.disabled = true;
    updateStatus('Initializing - please wait for media and server connection.', 'info');


    // --- AI Agent STT Functions ---
    function initializeSpeechRecognition() {
        if (!SpeechRecognition) {
            updateStatus('Speech Recognition API not supported by this browser.', 'error');
            console.error('Speech Recognition API not supported.');
            return;
        }

        speechRecognition = new SpeechRecognition();
        speechRecognition.continuous = true; // Listen continuously
        speechRecognition.interimResults = true; // Get interim results
        speechRecognition.lang = 'en-US'; // Set language

        speechRecognition.onstart = () => {
            isAIListening = true;
            updateStatus('AI is listening...', 'info');
            console.log('Speech recognition started.');
        };

        speechRecognition.onresult = async (event) => { // Made async
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            // Display interim transcript (optional)
            if (interimTranscript) {
                // console.log('Interim transcript:', interimTranscript);
                // updateStatus(`Listening... (Heard: ${interimTranscript})`, 'info');
            }

            if (finalTranscript) {
                console.log('Final transcript:', finalTranscript);
                updateStatus(`You said: "${finalTranscript}"`, 'info');
                // Temporarily stop listening to process and respond
                // so AI doesn't try to transcribe its own speech or user speaking over it.
                // We will restart it after AI speaks in later steps.
                // For now, just log it. Next step will be to process this.
                // stopSpeechRecognition(); // Stop for now, will be handled by AI response flow

                // Placeholder for processing finalTranscript and getting AI response
                // This will be handled in the next plan step.
                // For now, we can re-start listening after a short delay if continuous listening is desired
                // without an AI response yet.
                // Or simply let it continue if continuous is robust enough.
                // Let's make it so it stops and waits for AI response step to restart it.
                if (isAIListening) { // Check if it was supposed to be listening
                    speechRecognition.stop(); // It will trigger 'onend' where we can decide to restart
                }
                if (isAIListening) { // Check if it was supposed to be listening
                    // speechRecognition.stop(); // It will trigger 'onend' where we can decide to restart
                                              // Let STT stop naturally or via onend if continuous=false
                                              // For continuous=true, it might keep running.
                                              // The AI response logic will handle restarting STT after TTS.
                }
                // Call the async getAIResponse and await its result
                const aiResponse = await getAIResponse(finalTranscript.trim());
                updateStatus(`AI Responding (logic): ${aiResponse}`, 'info');

                // Next step will be to speak this aiResponse using TTS (already handled by speakAIResponse)
                // For now, we'll simulate the TTS finishing and restart listening for next user input. (This comment is now slightly outdated)
                // This will be replaced by actual TTS end event in next step.
                if (peerConnection && (peerConnection.iceConnectionState === 'connected' || peerConnection.iceConnectionState === 'completed')) {
                    // Simulate delay for AI speaking, then restart listening.
                    // setTimeout(() => {
                    //    if (!isAIListening) startSpeechRecognition();
                    // }, 1000); // Placeholder for TTS duration
                    // Actual restart will be handled after TTS in next step.
                    // For now, speechRecognition.onend will handle the state.
                    // If speechRecognition.continuous = true, it might not even stop.
                    // If continuous is false, or we explicitly stop it, onend will trigger.
                    // Let's ensure it stops so TTS doesn't get transcribed.
                    if(isAIListening) speechRecognition.stop();
                    // The TTS step will be responsible for restarting STT.
                    if (aiResponse) {
                        speakAIResponse(aiResponse);
                    } else {
                        // No response from AI (e.g. it was an empty transcript, or API error handled by getAIResponse returning empty/fallback)
                        // so restart listening if call is active
                        if (peerConnection && (peerConnection.iceConnectionState === 'connected' || peerConnection.iceConnectionState === 'completed') && !isAIListening) {
                           updateStatus('AI had no specific reply. Listening again.', 'info');
                           setTimeout(() => startSpeechRecognition(), 100); // Brief delay before restarting
                        }
                    }
                }
            }
        };

        speechRecognition.onerror = (event) => {
            isAIListening = false;
            console.error('Speech recognition error:', event.error);
            let errorMessage = `Speech recognition error: ${event.error}`;
            if (event.error === 'no-speech') {
                errorMessage = 'No speech detected. AI stopped listening.';
            } else if (event.error === 'audio-capture') {
                errorMessage = 'Audio capture error. Is microphone working?';
            } else if (event.error === 'not-allowed') {
                errorMessage = 'Speech recognition permission denied.';
            } else if (event.error === 'network') {
                errorMessage = 'Network error during speech recognition.';
            }
            updateStatus(errorMessage, 'error');
        };

        speechRecognition.onend = () => {
            isAIListening = false;
            console.log('Speech recognition ended.');
            // If the call is still active and we want continuous listening (after AI response or timeout), restart it.
            // This will be refined when AI response logic is added.
            // For now, don't automatically restart. It will be started again if needed by other logic.
            // if (peerConnection && (peerConnection.iceConnectionState === 'connected' || peerConnection.iceConnectionState === 'completed')) {
            //    // Potentially restart here if desired, e.g. speechRecognition.start();
            //    updateStatus('AI stopped listening. Call active.', 'info');
            // } else {
            //    updateStatus('AI stopped listening.', 'info');
            // }
             if (!peerConnection || (peerConnection.iceConnectionState !== 'connected' && peerConnection.iceConnectionState !== 'completed')) {
                updateStatus('AI stopped listening as call ended or disconnected.', 'info');
            } else {
                 // If call is still active, it means STT stopped, possibly after a final result.
                 // The AI response logic (next step) will be responsible for restarting it if needed.
                 updateStatus('AI temporarily stopped listening (waiting for AI response processing).', 'info');
            }

        };
    }

    function startSpeechRecognition() {
        if (!localStream) {
            updateStatus('Cannot start AI listening: Local media not available.', 'error');
            return;
        }
        if (speechRecognition && !isAIListening) {
            try {
                speechRecognition.start();
            } catch (e) {
                // This can happen if it's already started or in a bad state
                console.error("Error starting speech recognition:", e);
                if (e.name === 'InvalidStateError') {
                    // Try to re-initialize if in invalid state (though onend should handle most of this)
                    initializeSpeechRecognition();
                    if(speechRecognition) speechRecognition.start();
                } else {
                    updateStatus('Could not start AI listening.', 'error');
                }
            }
        } else if (!speechRecognition) {
            updateStatus('Speech recognition not initialized.', 'error');
        }
    }

    function stopSpeechRecognition() {
        if (speechRecognition && isAIListening) {
            speechRecognition.stop(); // This will trigger onend
            isAIListening = false; // Manually set, as onend might be async
            updateStatus('AI listening stopped.', 'info');
        }
    }

    // Initialize STT engine when the script loads
    if (SpeechRecognition) {
        initializeSpeechRecognition();
    } else {
        updateStatus('Speech Recognition API not supported by this browser. AI agent features will be limited.', 'error');
        console.warn('Speech Recognition API not available.');
    }

    // --- AI Response Logic with OpenAI Integration ---
    async function getAIResponse(text) {
        const lowerText = text.toLowerCase().trim();
        updateStatus(`AI processing: "${lowerText}"`, 'info');

        if (!lowerText) {
            console.log("No text provided to AI, skipping OpenAI call.");
            return ""; // Don't process empty strings
        }

        // IMPORTANT: REPLACE 'YOUR_OPENAI_API_KEY_GOES_HERE' WITH YOUR ACTUAL KEY FOR LOCAL TESTING ONLY.
        // DO NOT COMMIT THIS KEY TO VERSION CONTROL. FOR PRODUCTION, USE A BACKEND PROXY.
        const OPENAI_API_KEY = 'YOUR_OPENAI_API_KEY_GOES_HERE';

        if (OPENAI_API_KEY === 'YOUR_OPENAI_API_KEY_GOES_HERE') {
            console.warn("OpenAI API key is a placeholder. Using fallback keyword logic.");
            updateStatus("OpenAI API key not set. Using placeholder responses.", "error");
            // Fallback to keyword logic if key is not set
            if (lowerText.includes("hello") || lowerText.includes("hi")) {
                return "Hello there! (Fallback) How can I help you today?";
            } else if (lowerText.includes("help")) {
                return "I am a basic AI. (Fallback) What do you need help with?";
            } else {
                return `I heard: "${text}". (Fallback) OpenAI key needed for full response.`;
            }
        }

        const apiUrl = 'https://api.openai.com/v1/chat/completions';
        const messages = [
            { role: "system", content: "You are a friendly and concise AI call center agent. Your name is JulesBot." },
            { role: "user", content: text }
        ];

        try {
            updateStatus('Sending to OpenAI...', 'info');
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${OPENAI_API_KEY}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: 'gpt-3.5-turbo', // Or 'gpt-4' if you have access and prefer
                    messages: messages,
                    max_tokens: 100, // Adjust as needed
                    temperature: 0.7 // Adjust for creativity vs. determinism
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({})); // Try to parse error, default to empty obj
                console.error('OpenAI API Error:', response.status, errorData);
                updateStatus(`Error from OpenAI: ${response.status} - ${errorData.error?.message || 'Unknown error'}`, 'error');
                return `Sorry, I encountered an issue with the AI service (status ${response.status}).`;
            }

            const data = await response.json();
            if (data.choices && data.choices.length > 0 && data.choices[0].message && data.choices[0].message.content) {
                const aiMessage = data.choices[0].message.content.trim();
                console.log("OpenAI Response:", aiMessage);
                return aiMessage;
            } else {
                console.error('OpenAI response format unexpected:', data);
                updateStatus('Received an unexpected response from OpenAI.', 'error');
                return "Sorry, I received an unusual response from the AI service.";
            }

        } catch (error) {
            console.error('Error calling OpenAI API:', error);
            updateStatus(`Network or other error calling OpenAI: ${error.message}`, 'error');
            return "Sorry, I couldn't connect to the AI service at the moment.";
        }
    }

    // --- AI Agent TTS Functions ---
    function speakAIResponse(textToSpeak) {
        if (!('speechSynthesis' in window)) {
            updateStatus('Speech Synthesis API not supported by this browser.', 'error');
            console.error('Speech Synthesis API not supported.');
            // Fallback: If TTS not available, still restart STT for next input if call active
            if (peerConnection && (peerConnection.iceConnectionState === 'connected' || peerConnection.iceConnectionState === 'completed') && !isAIListening) {
                updateStatus('TTS not available. Ready for next input.', 'info');
                setTimeout(() => startSpeechRecognition(), 500); // Restart listening after a short delay
            }
            return;
        }

        // Cancel any ongoing speech first to prevent overlap if user speaks quickly
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        // utterance.lang = 'en-US'; // Optional: set language, voice, rate, pitch
        // const voices = window.speechSynthesis.getVoices();
        // utterance.voice = voices.find(v => v.name === 'Google US English'); // Example: selecting a voice

        utterance.onstart = () => {
            updateStatus(`AI Speaking: "${textToSpeak}"`, 'info');
            console.log(`AI Speaking: ${textToSpeak}`);
            // Temporarily ensure STT is definitely off while AI speaks
            if (isAIListening) {
                speechRecognition.stop(); // Stop STT, onend will set isAIListening = false
            }
        };

        utterance.onend = () => {
            console.log('AI finished speaking.');
            updateStatus('AI finished speaking. Listening for your response...', 'info');
            // Restart speech recognition if the call is still active
            if (peerConnection && (peerConnection.iceConnectionState === 'connected' || peerConnection.iceConnectionState === 'completed') && !isAIListening) {
                startSpeechRecognition();
            }
        };

        utterance.onerror = (event) => {
            console.error('SpeechSynthesis Error:', event.error);
            updateStatus(`Error speaking AI response: ${event.error}`, 'error');
            // Even if TTS fails, try to restart STT for next user input
            if (peerConnection && (peerConnection.iceConnectionState === 'connected' || peerConnection.iceConnectionState === 'completed') && !isAIListening) {
                updateStatus('TTS Error. Ready for next input.', 'info');
                 setTimeout(() => startSpeechRecognition(), 500);
            }
        };

        window.speechSynthesis.speak(utterance);
    }

});
