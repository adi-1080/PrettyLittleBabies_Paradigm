import { useEffect, useRef, useState } from "react";
import { formatMessageTime } from "../lib/utils";
import { useAuthStore } from "../store/useAuthStore";
import { useChatStore } from "../store/useChatStore";
import { useAutopilotStore } from "../store/useAutopilotStore";
import ChatHeader from "./ChatHeader";
import MessageInput from "./MessageInput";
import MessageSkeleton from "./skeletons/MessageSkeleton";
import { Check, X, Copy } from "lucide-react";
import toast from "react-hot-toast";

const ChatContainer = () => {
  const {
    messages,
    getMessages,
    isMessagesLoading,
    selectedUser,
    subscribeToMessages,
    unsubscribeToMessages,
  } = useChatStore();

  const { authUser } = useAuthStore();
  const { actions, verdicts, fetchAll } = useAutopilotStore();
  const messageEndRef = useRef(null);
  const [nudgeDismissed, setNudgeDismissed] = useState(false);

  useEffect(() => {
    getMessages(selectedUser._id);
    subscribeToMessages();
    fetchAll();
    setNudgeDismissed(false);

    return () => unsubscribeToMessages();
  }, [
    selectedUser._id,
    getMessages,
    subscribeToMessages,
    unsubscribeToMessages,
    fetchAll,
  ]);

  useEffect(() => {
    if (messageEndRef.current && messages) {
      messageEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Find the action for this contact
  const contactAction = actions.find(
    (a) => a.contact_name === selectedUser.fullName
  );
  const contactVerdict = verdicts.find(
    (v) => v.contact_name === selectedUser.fullName
  );

  const showNudge = contactAction && !nudgeDismissed;

  const handleCopy = () => {
    navigator.clipboard.writeText(contactAction.quick_copy);
    toast.success("Copied to clipboard!");
  };

  const handleAccept = () => {
    navigator.clipboard.writeText(contactAction.quick_copy);
    toast.success("Action accepted & copied!");
    setNudgeDismissed(true);
  };

  const handleReject = () => {
    toast("Action dismissed", { icon: "👋" });
    setNudgeDismissed(true);
  };

  if (isMessagesLoading) {
    return (
      <div className="flex-1 flex flex-col overflow-auto">
        <ChatHeader /> <MessageSkeleton /> <MessageInput />
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-auto">
      <ChatHeader />
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message._id}
            className={`chat ${
              message.senderID === authUser._id ? "chat-end" : "chat-start"
            }`}
            ref={messageEndRef}
          >
            <div className="chat-image avatar">
              <div className="size-10 rounded-full border">
                <img
                  src={
                    message.senderID === authUser._id
                      ? authUser.profilePicture || "/avatar.png"
                      : selectedUser.profilePicture || "/avatar.png"
                  }
                  alt="profile pic"
                />
              </div>
            </div>
            <div className="chat-header mb-1">
              <time className="text-xs opacity-50 ml-1">
                {formatMessageTime(message.createdAt)}
              </time>
            </div>
            <div className={`chat-bubble flex flex-col ${message.senderID === authUser._id ? "chat-bubble-primary" : ""}`}>
              {message.image && (
                <img
                  src={message.image}
                  alt="Attachment"
                  className="sm:max-w-[200px] rounded-md mb-2"
                />
              )}
              {message.text && <p>{message.text}</p>}
            </div>
          </div>
        ))}
      </div>

      {/* Nudge Bar */}
      {showNudge && (
        <div className="border-t border-base-300 bg-base-200 px-4 py-2">
          <div className="flex items-center gap-2">
            <span
              className={`badge badge-sm ${
                contactAction.action_type === "Reaction"
                  ? "badge-success"
                  : contactAction.action_type === "Nudge"
                  ? "badge-warning"
                  : "badge-error"
              }`}
            >
             
              {contactAction.action_type}
            </span>
            <div className="flex-1 text-sm font-mono truncate bg-base-300 rounded px-2 py-1">
              {contactAction.quick_copy}
            </div>
            <button
              className="btn btn-ghost btn-xs"
              title="Copy"
              onClick={handleCopy}
            >
              <Copy className="w-3.5 h-3.5" />
            </button>
            <button
              className="btn btn-success btn-xs"
              title="Accept"
              onClick={handleAccept}
            >
              <Check className="w-3.5 h-3.5" />
            </button>
            <button
              className="btn btn-error btn-xs"
              title="Reject"
              onClick={handleReject}
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      <MessageInput />
    </div>
  );
};

export default ChatContainer;
