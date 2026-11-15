export function mergeMessage(messages, message) {
  const merged = messages.some((item) => item.id === message.id)
    ? messages.map((item) => (item.id === message.id ? message : item))
    : [...messages, message];
  return merged.sort((left, right) => (
    new Date(left.created_at) - new Date(right.created_at) || left.id - right.id
  ));
}
