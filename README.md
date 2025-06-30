# Simple WebRTC Video Call Application

This project is a basic one-to-one WebRTC video calling application. It allows two users to connect peer-to-peer over the web using a simple signaling server for call setup.

## Features

*   Local video and audio preview.
*   One-to-one video and audio calls.
*   Ability to join a call "room" by name.
*   Mute/unmute local audio.
*   Mute/unmute local video.
*   Status messages for user feedback.
*   Basic signaling server using Node.js and WebSockets.
*   Uses public STUN servers for NAT traversal.

## Technologies Used

*   **Frontend:**
    *   HTML5
    *   CSS3
    *   JavaScript (ES6+)
    *   WebRTC APIs (`getUserMedia`, `RTCPeerConnection`)
*   **Backend (Signaling Server):**
    *   Node.js
    *   `ws` library (for WebSockets)
*   **NAT Traversal:**
    *   STUN (Session Traversal Utilities for NAT) - using public Google STUN servers.

## Project Structure

```
.
├── index.html            # Main HTML file for the client UI
├── style.css             # CSS styles for the client UI
├── script.js             # Client-side JavaScript for WebRTC logic and UI interaction
├── signaling-server/
│   ├── server.js         # Node.js WebSocket signaling server
│   └── package.json      # Node.js project file for the server
└── README.md             # This file
```

## Setup and Running the Application

### Prerequisites

*   Node.js and npm installed (for running the signaling server).
*   A modern web browser that supports WebRTC (e.g., Chrome, Firefox, Edge, Safari).
*   Access to your computer's camera and microphone.

### 1. Start the Signaling Server

1.  Open your terminal or command prompt.
2.  Navigate to the `signaling-server` directory:
    ```bash
    cd path/to/your/project/signaling-server
    ```
3.  Install dependencies (if you haven't already):
    ```bash
    npm install
    ```
4.  Start the server:
    ```bash
    node server.js
    ```
    You should see the message: `Signaling server started on ws://localhost:8080`. Keep this terminal window open.

### 2. Run the Client Application

1.  Open the `index.html` file in your web browser. You can do this by:
    *   Dragging the `index.html` file into a browser window.
    *   Opening it directly via the file path (e.g., `file:///path/to/your/project/index.html`).
2.  The browser will likely ask for permission to use your camera and microphone. **Allow** access. You should see your local video.
3.  To test a call:
    *   Open `index.html` in a **second browser tab** or a different browser window on the same computer.
    *   Allow camera/microphone access for the second client as well.
    *   In the **first client**, enter a room name (e.g., `mytestroom`) and click "Start Call".
    *   In the **second client**, enter the **same room name** (`mytestroom`) and click "Start Call".
    *   The two clients should connect, and you should see the remote video in each client's "Remote Video" section.

## Important Considerations

*   **NAT Traversal:** This application uses public STUN servers. For more reliable connectivity across diverse network environments (especially symmetric NATs), a **TURN server** would be required. This has not been implemented in this basic version.
*   **Security:**
    *   The signaling server communication (`ws://`) is not encrypted. For production, `wss://` (WebSocket Secure) should be used, requiring an SSL certificate on the signaling server.
    *   The `index.html` is served via `file:///`. For WebRTC features like `getUserMedia` to work reliably without flags on some browsers, especially when moving to `wss://`, you'd typically serve the frontend files over HTTPS using a simple web server.
*   **Scalability:** The current signaling server is very basic and not designed for a large number of users or rooms.
*   **Error Handling:** Basic error handling and status messages are in place, but a production application would require more comprehensive error management.

## Development Notes

*   Client-side JavaScript (`script.js`) handles media access, WebRTC peer connections, and signaling server interactions.
*   The signaling server (`signaling-server/server.js`) manages WebSocket connections, room logic (max 2 users per room), and forwards WebRTC signaling messages (offers, answers, ICE candidates) between peers.

---

## Potential Next Steps & Enhancements

This basic application serves as a foundation. Here are some potential areas for future development to create a more feature-rich and robust video calling service:

1.  **TURN Server Integration:**
    *   **Why:** Essential for reliable connectivity across all types of NATs (especially symmetric NATs) and restrictive firewalls where STUN alone is insufficient.
    *   **How:** Set up a TURN server (e.g., Coturn, or use a managed service) and add its credentials to the `iceServers` configuration in `script.js`. This allows media traffic to be relayed through the TURN server when a direct peer-to-peer connection cannot be established.

2.  **Secure Signaling (WSS) and HTTPS for Frontend:**
    *   **Why:** Critical for security and user privacy. `getUserMedia` and other WebRTC features have stricter requirements when not on `localhost`, often mandating HTTPS.
    *   **How (Signaling):** Configure the Node.js WebSocket server (`ws`) to use `wss` (WebSocket Secure). This typically involves obtaining an SSL/TLS certificate for your server's domain and configuring the Node.js HTTPS module to serve the WebSocket server over TLS.
    *   **How (Frontend):** Serve the `index.html`, `style.css`, and `script.js` files over HTTPS using a web server (e.g., Nginx, Apache, or even a simple Node.js Express server configured for HTTPS).

3.  **Improved User Interface (UI) and User Experience (UX):**
    *   **Why:** Enhance usability and provide a more professional look and feel.
    *   **How:**
        *   Refine CSS for better aesthetics.
        *   Add user presence indicators (e.g., who is in the room).
        *   Implement clearer call state indicators (e.g., "Ringing...", "Connecting...", "Call Failed").
        *   Consider a frontend framework (React, Vue, Angular) for managing more complex UI states and components.

4.  **Group Video Calls:**
    *   **Why:** Support for multi-party conversations.
    *   **How:** This is a significant architectural change. Instead of full mesh (where every client sends/receives video to/from every other client, which doesn't scale well), you'd typically introduce a **Selective Forwarding Unit (SFU)** or **Multipoint Control Unit (MCU)**.
        *   **SFU (e.g., Janus, Jitsi Videobridge, Medooze, mediasoup):** Each client sends their media to the SFU, and the SFU forwards it to other participants. Clients still decode multiple streams.
        *   **MCU:** Mixes media streams on the server, sending a single composite stream to each client. More server CPU intensive.
    *   The signaling server logic would also need substantial updates to manage group rooms, track multiple peers, and handle their media streams.

5.  **Screen Sharing:**
    *   **Why:** Allow users to share their screen content.
    *   **How:** Use the `getDisplayMedia()` API (similar to `getUserMedia()`) in `script.js` to capture the screen. Add a new `RTCRtpSender` to the `RTCPeerConnection` for the screen sharing track and signal this new track to the peer.

6.  **Text Chat:**
    *   **Why:** Provide a text-based communication channel alongside video/audio.
    *   **How:** Use WebRTC Data Channels (`RTCDataChannel`) for peer-to-peer text message exchange, or relay chat messages through the existing WebSocket signaling server. Data Channels are generally preferred for P2P data.

7.  **Scalable and Robust Signaling:**
    *   **Why:** Handle more concurrent users, rooms, and provide better reliability.
    *   **How:**
        *   Potentially move from a simple in-memory `rooms` object to a database (e.g., Redis, PostgreSQL) for storing room and user states.
        *   Implement horizontal scaling for the signaling server (multiple instances behind a load balancer with a shared state mechanism).
        *   Add proper authentication and authorization.

8.  **Advanced Features:**
    *   Call recording (server-side or client-side).
    *   Bandwidth management and adaptive video quality.
    *   Virtual backgrounds.
    *   Noise suppression.

Developing these features involves progressively more complex client-side WebRTC logic, more sophisticated signaling server capabilities, and often dedicated media server components (like SFUs/MCUs for group calls). Each step builds upon the foundational understanding of WebRTC and real-time communication principles.
```
