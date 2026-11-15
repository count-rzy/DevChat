export function getMessageReadStatus(message, otherLastReadMessageId) {
  if (!message || message.deleted_at || !Number.isInteger(message.id)) return null;
  return Number.isInteger(otherLastReadMessageId) && otherLastReadMessageId >= message.id
    ? "read"
    : "saved";
}
