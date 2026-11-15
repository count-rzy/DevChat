import { getApiBaseUrl } from "./api";
import { postWithCsrf, request } from "./auth";

export async function getConversations() {
  const data = await request("/conversations/");
  return data.conversations;
}

export async function getEligibleUsers() {
  const data = await request("/accounts/users/");
  return data.users;
}

export async function createConversation(otherUserId) {
  const data = await postWithCsrf("/conversations/", {
    other_user_id: otherUserId,
  });
  return data.conversation;
}

export async function getMessages(conversationId, before) {
  const query = before ? `?before=${encodeURIComponent(before)}` : "";
  return request(`/conversations/${conversationId}/messages/${query}`);
}

export async function sendMessage(conversationId, content, replyToId = null) {
  const data = await postWithCsrf(
    `/conversations/${conversationId}/messages/`,
    { content, ...(replyToId ? { reply_to_id: replyToId } : {}) },
  );
  return data.message;
}

export async function editMessage(conversationId, messageId, content) {
  const csrfToken = await request("/accounts/csrf/").then((data) => data.csrfToken);
  const data = await request(`/conversations/${conversationId}/messages/${messageId}/`, {
    method: "PATCH",
    headers: { "X-CSRFToken": csrfToken },
    body: JSON.stringify({ content }),
  });
  return data.message;
}

export async function deleteMessage(conversationId, messageId) {
  const csrfToken = await request("/accounts/csrf/").then((data) => data.csrfToken);
  const data = await request(`/conversations/${conversationId}/messages/${messageId}/`, {
    method: "DELETE",
    headers: { "X-CSRFToken": csrfToken },
  });
  return data.message;
}

export async function toggleMessageReaction(conversationId, messageId, emoji) {
  const data = await postWithCsrf(
    `/conversations/${conversationId}/messages/${messageId}/reactions/`,
    { emoji },
  );
  return data.message;
}

export async function markConversationRead(conversationId, messageId) {
  const data = await postWithCsrf(`/conversations/${conversationId}/read/`, { message_id: messageId });
  return data.conversation;
}

export function getConversationWebSocketUrl(conversationId) {
  const url = new URL(getApiBaseUrl(), window.location.href);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `${url.pathname.replace(/\/?api\/?$/, "")}/ws/conversations/${conversationId}/`;
  url.search = "";
  url.hash = "";
  return url.toString();
}

export async function getMyProfile() {
  const data = await request("/accounts/profile/");
  return data.profile;
}

export async function updateMyProfile(changes) {
  const csrfToken = await request("/accounts/csrf/").then((data) => data.csrfToken);
  const data = await request("/accounts/profile/update/", {
    method: "PATCH",
    headers: { "X-CSRFToken": csrfToken },
    body: JSON.stringify(changes),
  });
  return data.profile;
}

export async function uploadMyAvatar(file) {
  const csrfToken = await request("/accounts/csrf/").then((data) => data.csrfToken);
  const formData = new FormData();
  formData.append("avatar", file);
  const data = await request("/accounts/profile/avatar/", {
    method: "POST",
    headers: { "X-CSRFToken": csrfToken },
    body: formData,
  });
  return data.profile;
}

export async function removeMyAvatar() {
  const csrfToken = await request("/accounts/csrf/").then((data) => data.csrfToken);
  const data = await request("/accounts/profile/avatar/", {
    method: "DELETE",
    headers: { "X-CSRFToken": csrfToken },
  });
  return data.profile;
}
