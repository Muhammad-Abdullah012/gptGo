let socket: WebSocket | null = null;
let reconnectAttempts = 0;
let listeners: ((data: any) => void)[] = [];

const MAX_RECONNECT_ATTEMPTS = 10;
const RECONNECT_INTERVAL = 2000;

export const connectSocket = (onMessage: (data: any) => void): Promise<void> => {
  listeners.push(onMessage);

  if (socket && socket.readyState <= 1) return Promise.resolve();

  const url = "ws://localhost:8000/ws/agent";
  socket = new WebSocket(url);

    return new Promise((resolve) => {
        socket!.onopen = () => {
            console.log("[WebSocket] Connected");
            reconnectAttempts = 0;
            resolve();
        };

        socket!.onmessage = (event) => {
            const data = JSON.parse(event.data);
            listeners.forEach((listener) => listener(data));
        };

        socket!.onclose = () => {
            console.warn("[WebSocket] Disconnected");
            attemptReconnect();
        };

        socket!.onerror = (err) => {
            console.error("[WebSocket] Error:", err);
            socket?.close();
        };
    });
};


const attemptReconnect = () => {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.error("Max reconnect attempts reached.");
        return;
    }

    reconnectAttempts++;
    setTimeout(() => {
        console.log(`Reconnecting... (${reconnectAttempts})`);
        connectSocket((data) => listeners.forEach((cb) => cb(data)));
    }, RECONNECT_INTERVAL);
};

export const sendMessage = (data: any) => {
    if (socket?.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(data));
    } else {
        console.warn("WebSocket not connected. Message not sent.");
    }
};

export const closeSocket = () => {
    socket?.close();
};
