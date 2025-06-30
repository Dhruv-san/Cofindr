const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 8080 });

// Store connected clients and their rooms
// For simplicity, using an object to store rooms, where each room is a Set of clients (WebSockets)
// In a production scenario, you might use a more robust data structure or a database
const rooms = {};
let clientIdCounter = 0; // Counter for assigning unique client IDs

console.log('Signaling server started on ws://localhost:8080');

wss.on('connection', (ws) => {
    ws.id = ++clientIdCounter; // Assign a unique ID to this client connection
    console.log(`Client ${ws.id} connected`);
    let currentRoom = null; // Keep track of the room this client is in

    ws.on('message', (message) => {
        let data;
        try {
            data = JSON.parse(message);
        } catch (e) {
            console.error('Failed to parse message or message is not JSON:', message);
            ws.send(JSON.stringify({ type: 'error', message: 'Invalid JSON message received.' }));
            return;
        }

        console.log(`Client ${ws.id} sent message of type ${data.type}:`, data); // Enhanced log

        switch (data.type) {
            case 'join':
                const roomName = (typeof data.roomName === 'string') ? data.roomName.trim() : '';
                if (!roomName) {
                    console.log(`Client ${ws.id} tried to join with invalid room name.`);
                    ws.send(JSON.stringify({ type: 'error', message: 'A valid room name is required to join.' }));
                    return;
                }

                currentRoom = roomName;
                if (!rooms[currentRoom]) {
                    rooms[currentRoom] = new Set();
                    console.log(`Client ${ws.id} created and joined room '${currentRoom}'.`);
                } else {
                    console.log(`Client ${ws.id} attempting to join existing room '${currentRoom}'.`);
                }

                // Ensure client is not already in the room set before checking size and adding
                // This prevents issues if a client somehow sends 'join' multiple times for the same room
                // without disconnecting.
                if (!rooms[currentRoom].has(ws) && rooms[currentRoom].size >= 2) {
                    ws.send(JSON.stringify({ type: 'error', message: `Room '${currentRoom}' is full.` }));
                    console.log(`Client ${ws.id} denied joining room '${currentRoom}' as it is full. Current occupants: ${Array.from(rooms[currentRoom]).map(c => c.id).join(', ')}`);
                    currentRoom = null;
                    return;
                }

                if (!rooms[currentRoom].has(ws)) {
                    rooms[currentRoom].add(ws);
                }
                console.log(`Client ${ws.id} is in room '${currentRoom}'. Room occupants: ${Array.from(rooms[currentRoom]).map(c => c.id).join(', ')}. Total: ${rooms[currentRoom].size}`);

                // Notify client they joined successfully
                ws.send(JSON.stringify({ type: 'join_success', roomName: currentRoom, message: `Successfully joined room '${currentRoom}'.` }));

                // If room now has 2 people, notify them they can start WebRTC negotiation
                if (rooms[currentRoom].size === 2) {
                    console.log(`Room '${currentRoom}' is now full. Notifying peers ${Array.from(rooms[currentRoom]).map(c => c.id).join(' and ')}.`);
                    rooms[currentRoom].forEach(peer => {
                        try {
                            if (peer.readyState === WebSocket.OPEN) {
                                peer.send(JSON.stringify({ type: 'peer_joined', message: 'Peer has joined. Ready to connect.' }));
                            }
                        } catch (e) {
                            console.error(`Error sending 'peer_joined' to peer ${peer.id} in room ${currentRoom}:`, e);
                        }
                    });
                }
                break;

            // WebRTC Signaling Messages (offer, answer, candidate)
            // These messages are simply forwarded to the other client in the room
            case 'offer':
            case 'answer':
            case 'candidate':
                if (!currentRoom || !rooms[currentRoom]) {
                    ws.send(JSON.stringify({ type: 'error', message: 'You are not in a room to send signaling messages.' }));
                    return;
                }
                // Broadcast to other clients in the same room
                rooms[currentRoom].forEach(peer => {
                    if (peer !== ws && peer.readyState === WebSocket.OPEN) {
                        try {
                            peer.send(message); // Forward the original JSON string
                            console.log(`Client ${ws.id} forwarded ${data.type} to peer ${peer.id} in room '${currentRoom}'`);
                        } catch (e) {
                             console.error(`Error forwarding ${data.type} from ${ws.id} to ${peer.id}:`, e);
                        }
                    }
                });
                break;

            case 'hangup':
                 if (!currentRoom || !rooms[currentRoom]) {
                    ws.send(JSON.stringify({ type: 'error', message: 'You are not in a room to hang up.' }));
                    return;
                }
                console.log(`Client ${ws.id} initiated hangup in room '${currentRoom}'.`);
                rooms[currentRoom].forEach(peer => {
                    if (peer !== ws && peer.readyState === WebSocket.OPEN) {
                       try {
                            peer.send(JSON.stringify({ type: 'peer_hangup' }));
                            console.log(`Forwarded hangup from client ${ws.id} to peer ${peer.id} in room '${currentRoom}'`);
                        } catch (e) {
                            console.error(`Error sending 'peer_hangup' from ${ws.id} to ${peer.id}:`, e);
                        }
                    }
                });
                break;

            default:
                console.log(`Client ${ws.id} sent unknown message type: '${data.type}'`);
                ws.send(JSON.stringify({ type: 'error', message: `Unknown message type: ${data.type}` }));
        }
    });

    function handleDisconnect() {
        console.log(`Client ${ws.id} disconnected.`);
        if (currentRoom && rooms[currentRoom]) {
            const wasInRoom = rooms[currentRoom].delete(ws); // Attempt to remove the client
            if (wasInRoom) { // Only proceed if the client was actually in the set for this room
                console.log(`Client ${ws.id} removed from room '${currentRoom}'. New room size: ${rooms[currentRoom].size}`);
                // Notify the other client in the room that their peer has left
                rooms[currentRoom].forEach(peer => {
                    if (peer.readyState === WebSocket.OPEN) { // Ensure peer is still connected
                        try {
                            peer.send(JSON.stringify({ type: 'peer_left', message: 'The other peer has left the room.' }));
                            console.log(`Notified peer ${peer.id} in room '${currentRoom}' that client ${ws.id} has left.`);
                        } catch (e) {
                            console.error(`Error sending 'peer_left' to peer ${peer.id} after ${ws.id} disconnected:`, e);
                        }
                    }
                });

                if (rooms[currentRoom].size === 0) {
                    console.log(`Room '${currentRoom}' is now empty and will be removed.`);
                    delete rooms[currentRoom];
                }
            } else {
                 console.log(`Client ${ws.id} disconnected but was not found in room '${currentRoom}'s active set. No 'peer_left' sent.`);
            }
        } else if (currentRoom) {
            // This case might occur if the room was already deleted due to other client disconnecting first
             console.log(`Client ${ws.id} disconnected, but room '${currentRoom}' no longer exists or client was not in it.`);
        } else {
            console.log(`Client ${ws.id} disconnected without being in a specific room.`);
        }
        currentRoom = null; // Clear the room reference for this closed WebSocket instance
    }

    ws.on('close', () => {
        handleDisconnect();
    });

    ws.on('error', (error) => {
        console.error(`WebSocket error for client ${ws.id}:`, error.message);
        // Consider if handleDisconnect() should be called here too.
        // If an error occurs, 'close' will usually follow, so handleDisconnect will be called.
        // If 'close' doesn't follow an 'error', then manual cleanup might be needed.
        // For simplicity, we rely on 'close' for cleanup.
    });
});

// To run this server:
// 1. Make sure you have Node.js installed.
// 2. Navigate to the `signaling-server` directory in your terminal.
// 3. Run `npm install ws` if you haven't already.
// 4. Run `node server.js`.
// The server will then be listening for WebSocket connections on ws://localhost:8080.
//
// Client-side messages expected by this server:
// - To join a room: { "type": "join", "roomName": "yourRoomName" }
// - WebRTC offer:  { "type": "offer", "sdp": { ... } } (sdp content depends on WebRTC)
// - WebRTC answer: { "type": "answer", "sdp": { ... } } (sdp content depends on WebRTC)
// - ICE candidate: { "type": "candidate", "candidate": { ... } } (candidate content depends on WebRTC)
// - Hangup:      { "type": "hangup" }
//
// Server-side messages sent to clients:
// - Error:          { "type": "error", "message": "Error description" }
// - Join success:   { "type": "join_success", "roomName": "joinedRoomName", "message": "Success message" }
// - Peer joined:    { "type": "peer_joined", "message": "Notification message" } (when room is full or another joins)
// - WebRTC offer:   (forwarded from other client)
// - WebRTC answer:  (forwarded from other client)
// - ICE candidate:  (forwarded from other client)
// - Peer hangup:    { "type": "peer_hangup" }
// - Peer left:      { "type": "peer_left", "message": "Notification message" }
//
// This is a very basic signaling server for one-on-one calls.
// It lacks proper authentication, robust error handling for all edge cases,
// and scalability for many rooms or users.
// Room names are simple strings and rooms are limited to 2 participants.
//
// Next steps in the main plan will involve making the client-side `script.js`
// connect to this server and use these message types.
