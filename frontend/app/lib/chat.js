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

export async function sendMessage(conversationId, content) {
  const data = await postWithCsrf(
    `/conversations/${conversationId}/messages/`,
    { content },
  );
  return data.message;
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
