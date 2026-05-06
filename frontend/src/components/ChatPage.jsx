import { useState, useEffect, useContext } from "react";
import axios from "axios";
import { v4 as uuidv4 } from "uuid";
import { AppContext } from "../App";

const ChatPage = () => {
    const { messages, setMessages } = useContext(AppContext);
    const [input, setInput] = useState("");

    const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

    const [sessionId] = useState(() => {
        let storedSession = localStorage.getItem("session_id");

        if (!storedSession) {
            storedSession = uuidv4();
            localStorage.setItem("session_id", storedSession);
        }

        return storedSession;
    });

    useEffect(() => {
        axios
            .get(`${BASE_URL}/chat-history/${sessionId}`)
            .then((res) => {
                const history = res.data.flatMap((chat) => [
                    { type: "user", text: chat.question },
                    { type: "bot", text: chat.answer, sources: chat.sources },
                ]);
                setMessages(history);
            })
            .catch(() => {});
    }, [sessionId, setMessages]);

    const handleSend = async () => {
        if(!input.trim()) return;

        const userQuestion = input.trim();

        setInput("");

        const userMessage = {
            type: "user",
            text: userQuestion,
        };

        setMessages((prev) => [...prev, userMessage]);

        try{
            const res = await axios.post(`${BASE_URL}/ask`, {
                question: userQuestion,
                session_id: sessionId,
            });

            const fullText = res.data.answer;

            let currentText = "";

            const botMessage = {
                type: "bot",
                text: "",
                sources: res.data.sources,
            };

            setMessages((prev) => [...prev, botMessage]);

            const index = messages.length + 1; 

            const interval = setInterval(() => {
            if (currentText.length < fullText.length) {
                currentText += fullText[currentText.length];

                setMessages((prev) => {
                const updated = [...prev];
                updated[index] = {
                    ...updated[index],
                    text: currentText,
                };
                return updated;
                });

            } else {
                clearInterval(interval);
            }
            }, 20);
        } 
        catch (err) {
            setMessages((prev) => [
                ...prev,
                { type: "bot", text: "Error connecting to server."},
            ]);
        }
    };

    return (
        <div className="chatcontainer">
            <div className="chatMessages">
                {messages.map((msg, index) => (
                    <div
                        key={index}
                        className={msg.type === "user"? "userMessage" : "botMessage"}
                    >
                        {msg.text}

                        {msg.sources && msg.sources.length > 0 && (
                            <div style={{ fontSize: "12px", marginTop: "12px"}}>
                                <b>Sources: </b> {msg.sources.join(", ")}
                            </div>
                        )}
                    </div>
                ))}
            </div>


            <div className="QuestionInputBar">
                <input
                    type="text"
                    className="askQuestion"
                    placeholder="Ask something..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter") handleSend();
                    }}
                />
                <button className="sendBtn" onClick={handleSend}>
                    Send
                </button>
            </div>
        </div>
    );
};

export default ChatPage;
