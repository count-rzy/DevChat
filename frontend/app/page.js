"use client";

import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";
import { checkBackendHealth, getApiBaseUrl } from "./lib/api";
import { useAuth } from "./lib/auth-context";
import {
  getPreferredLanguage,
  LANGUAGE_STORAGE_KEY,
  subscribeToLanguage,
  translations,
} from "./lib/translations";
import {
  createConversation,
  deleteMessage,
  editMessage,
  getConversationWebSocketUrl,
  getConversations,
  getEligibleUsers,
  getMessages,
  markConversationRead,
  getMyProfile,
  sendMessage,
  toggleMessageReaction,
  removeMyAvatar,
  uploadMyAvatar,
  updateMyProfile,
} from "./lib/chat";
import { getMessageReadStatus } from "./lib/message-status.mjs";
import { mergeMessage } from "./lib/messages.mjs";

const REACTION_EMOJIS = ["\u{1F44D}", "\u2764\uFE0F", "\u{1F602}", "\u{1F62E}", "\u{1F622}"];
const ACTION_ICONS = {
  reply: "M10 8L5 12l5 4M5 12h9a5 5 0 0 1 5 5",
  reaction: "M12 3a9 9 0 1 0 9 9 4 4 0 0 1-4-4 4 4 0 0 1-5-5ZM8 10h.01M16 10h.01M8 14s1.5 2 4 2 4-2 4-2",
  edit: "M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L9 17l-4 1 1-4Z",
  more: "M5 12h.01M12 12h.01M19 12h.01",
};

function formatTime(value, language) {
  if (!value) return "";
  return new Intl.DateTimeFormat(language === "ru" ? "ru-RU" : "en-US", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function initials(value) {
  return value?.trim()?.slice(0, 1)?.toLocaleUpperCase() || "?";
}

function Avatar({ name, url, className = "" }) {
  const [imageFailed, setImageFailed] = useState(false);
  const src = url ? new URL(url, getApiBaseUrl()).toString() : null;
  return (
    <span className={`${styles.avatar} ${className}`} aria-hidden="true">
      {src && !imageFailed
        ? <Image className={styles.avatarImage} src={src} alt="" fill sizes="64px" unoptimized onError={() => setImageFailed(true)} />
        : initials(name)}
    </span>
  );
}

function MessageActionIcon({ name }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d={ACTION_ICONS[name]} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MessageReadStatus({ isRead, savedLabel, readLabel }) {
  const label = isRead ? readLabel : savedLabel;
  return (
    <span
      className={`${styles.messageReadStatus} ${isRead ? styles.messageReadStatusRead : ""}`}
      role="img"
      aria-label={label}
      title={label}
    >
      <svg viewBox="0 0 24 16" fill="none" aria-hidden="true">
        <path d="m2 8 4 4L16 2" />
        {isRead && <path d="m9 8 4 4L23 2" />}
      </svg>
    </span>
  );
}

export default function Home() {
  const router = useRouter();
  const { user, status, signOut, refreshUser, clearSession } = useAuth();
  const language = useSyncExternalStore(
    subscribeToLanguage,
    getPreferredLanguage,
    () => "en",
  );
  const t = translations[language];
  const [conversations, setConversations] = useState([]);
  const [eligibleUsers, setEligibleUsers] = useState([]);
  const [profile, setProfile] = useState(null);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [loadedConversationId, setLoadedConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [nextBefore, setNextBefore] = useState(null);
  const [draft, setDraft] = useState("");
  const [search, setSearch] = useState("");
  const [contactSearch, setContactSearch] = useState("");
  const [loadingApp, setLoadingApp] = useState(true);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [sending, setSending] = useState(false);
  const [newConversationOpen, setNewConversationOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [profileDraft, setProfileDraft] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [avatarBusy, setAvatarBusy] = useState(false);
  const [error, setError] = useState("");
  const [backendStatus, setBackendStatus] = useState("checking");
  const [realtimeStatus, setRealtimeStatus] = useState("connecting");
  const [replyTarget, setReplyTarget] = useState(null);
  const [editingMessageId, setEditingMessageId] = useState(null);
  const [partnerTyping, setPartnerTyping] = useState(false);
  const [touchActionsMessageId, setTouchActionsMessageId] = useState(null);
  const [reactionPickerMessageId, setReactionPickerMessageId] = useState(null);
  const [moreMenuMessageId, setMoreMenuMessageId] = useState(null);
  const longPressTimerRef = useRef(null);
  const longPressHandledRef = useRef(false);
  const socketRef = useRef(null);
  const composerRef = useRef(null);
  const typingStopTimerRef = useRef(null);
  const partnerTypingTimerRef = useRef(null);

  const handleUnauthorized = useCallback((requestError) => {
    if (requestError.status !== 401) return false;
    clearSession();
    router.replace("/login");
    return true;
  }, [clearSession, router]);

  const markReadThrough = useCallback(async (conversationId, messageId) => {
    if (document.visibilityState !== "visible") return;
    try {
      const updated = await markConversationRead(conversationId, messageId);
      setConversations((previous) => previous.map((conversation) => (
        conversation.id === updated.id ? updated : conversation
      )));
    } catch (requestError) {
      if (requestError.status === 401) handleUnauthorized(requestError);
    }
  }, [handleUnauthorized]);

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  useEffect(() => {
    if (status === "anonymous") router.replace("/login");
  }, [status, router]);

  useEffect(() => {
    let active = true;
    if (status !== "authenticated") return () => { active = false; };

    Promise.all([getConversations(), getEligibleUsers(), getMyProfile()])
      .then(([nextConversations, users, nextProfile]) => {
        if (!active) return;
        setConversations(nextConversations);
        setEligibleUsers(users);
        setProfile(nextProfile);
        setActiveConversationId((current) => current ?? nextConversations[0]?.id ?? null);

        const localLanguage = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
        if (!localLanguage && nextProfile.preferred_language) {
          window.localStorage.setItem(LANGUAGE_STORAGE_KEY, nextProfile.preferred_language);
          window.dispatchEvent(new Event("devchat-language-change"));
        }
      })
      .catch((requestError) => {
        if (!active) return;
      if (!handleUnauthorized(requestError)) {
          setError(t.loadFailed);
        }
      })
      .finally(() => {
        if (active) setLoadingApp(false);
      });

    return () => { active = false; };
  }, [status, router, t.loadFailed, handleUnauthorized]);

  useEffect(() => {
    let active = true;
    if (!activeConversationId || status !== "authenticated") {
      return () => { active = false; };
    }

    getMessages(activeConversationId)
      .then((page) => {
        if (!active) return;
        setMessages(page.messages);
        setNextBefore(page.next_before);
        setLoadedConversationId(activeConversationId);
        const newest = page.messages.at(-1);
        if (newest) markReadThrough(activeConversationId, newest.id);
      })
      .catch((requestError) => {
        if (!active) return;
        if (!handleUnauthorized(requestError)) setError(t.loadFailed);
        setMessages([]);
        setLoadedConversationId(activeConversationId);
      });
    return () => { active = false; };
  }, [activeConversationId, status, router, t.loadFailed, handleUnauthorized, markReadThrough]);

  useEffect(() => {
    if (
      status !== "authenticated"
      || !activeConversationId
      || loadedConversationId !== activeConversationId
    ) return undefined;

    let disposed = false;
    let socket;
    let reconnectTimer;
    let fallbackTimer;
    let heartbeatTimer;
    let retryDelay = 1000;
    const reconcileHistory = async () => {
      try {
        const page = await getMessages(activeConversationId);
        if (disposed) return;
        setMessages((previous) => page.messages.reduce(mergeMessage, previous));
        const newestMessage = page.messages.at(-1);
        if (newestMessage) await markReadThrough(activeConversationId, newestMessage.id);
        try {
          const latestConversations = await getConversations();
          if (!disposed) setConversations(latestConversations);
        } catch (requestError) {
          if (!disposed && !handleUnauthorized(requestError)) setError(t.loadFailed);
        }
      } catch (requestError) {
        if (!disposed && !handleUnauthorized(requestError)) setError(t.loadFailed);
      }
    };

    const receiveMessage = (message) => {
      setMessages((previous) => mergeMessage(previous, message));
      if (message.sender.id !== user?.id && !message.deleted_at) {
        markReadThrough(activeConversationId, message.id);
      }
      setConversations((previous) => {
        const updated = previous.map((conversation) => (
          conversation.id === activeConversationId
            ? {
              ...conversation,
              last_message: {
                id: message.id,
                content: message.content,
                sender_id: message.sender.id,
                created_at: message.created_at,
                is_deleted: Boolean(message.deleted_at),
              },
              unread_count: (
                message.sender.id !== user?.id
                && document.visibilityState !== "visible"
                && message.id > (conversation.last_message?.id || 0)
              )
                ? (conversation.unread_count || 0) + 1
                : conversation.unread_count,
            }
            : conversation
        ));
        return updated.sort((left, right) => (
          new Date(right.last_message?.created_at || right.created_at)
          - new Date(left.last_message?.created_at || left.created_at)
        ));
      });
    };

    const connect = () => {
      if (disposed) return;
      let nextSocket;
      try {
        nextSocket = new WebSocket(getConversationWebSocketUrl(activeConversationId));
      } catch {
        setRealtimeStatus("reconnecting");
        reconnectTimer = window.setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 2, 30000);
        return;
      }
      socket = nextSocket;
      socketRef.current = nextSocket;

      nextSocket.onopen = () => {
        if (disposed || socket !== nextSocket) return;
        retryDelay = 1000;
        setRealtimeStatus("connected");
        reconcileHistory();
        heartbeatTimer = window.setInterval(() => {
          if (nextSocket.readyState === WebSocket.OPEN) {
            nextSocket.send(JSON.stringify({ type: "ping" }));
          }
        }, 30000);
      };

      nextSocket.onmessage = (event) => {
        if (disposed || socket !== nextSocket) return;
        let payload;
        try {
          payload = JSON.parse(event.data);
        } catch {
          return;
        }
        if ((payload.type === "message.created" || payload.type === "message.updated") && payload.message) {
          receiveMessage(payload.message);
        }
        if (payload.type === "typing.changed" && payload.user_id !== user?.id) {
          setPartnerTyping(payload.is_typing);
          window.clearTimeout(partnerTypingTimerRef.current);
          if (payload.is_typing) {
            partnerTypingTimerRef.current = window.setTimeout(() => setPartnerTyping(false), 3000);
          }
        }
        if (payload.type === "conversation.read") {
          setConversations((previous) => previous.map((conversation) => (
            conversation.id === activeConversationId
              ? { ...conversation, other_last_read_message_id: payload.message_id }
              : conversation
          )));
        }
      };

      nextSocket.onclose = (event) => {
        if (socket !== nextSocket) return;
        window.clearInterval(heartbeatTimer);
        if (disposed) return;
        if (event.code === 4401) {
          clearSession();
          router.replace("/login");
          return;
        }
        setRealtimeStatus("reconnecting");
        reconnectTimer = window.setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 2, 30000);
      };

      nextSocket.onerror = () => nextSocket.close();
    };

    connect();
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") reconcileHistory();
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    fallbackTimer = window.setInterval(() => {
      if (socket?.readyState !== WebSocket.OPEN) reconcileHistory();
    }, 10000);

    return () => {
      disposed = true;
      window.clearTimeout(reconnectTimer);
      window.clearInterval(fallbackTimer);
      window.clearInterval(heartbeatTimer);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (socket && socket.readyState < WebSocket.CLOSING) {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "typing", is_typing: false }));
        }
        socket.close();
      }
      if (socketRef.current === socket) socketRef.current = null;
      window.clearTimeout(typingStopTimerRef.current);
      window.clearTimeout(partnerTypingTimerRef.current);
    };
  }, [
    activeConversationId,
    loadedConversationId,
    status,
    handleUnauthorized,
    clearSession,
    router,
    user?.id,
    markReadThrough,
    t.loadFailed,
  ]);

  useEffect(() => {
    let active = true;
    checkBackendHealth().then((result) => {
      if (active) setBackendStatus(result.status === "ok" && result.database === "connected" ? "ok" : "offline");
    });
    return () => { active = false; };
  }, []);

  const activeConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === activeConversationId) || null,
    [conversations, activeConversationId],
  );
  const loadingMessages = Boolean(activeConversationId && loadedConversationId !== activeConversationId);
  const contact = activeConversation?.other_user;
  const filteredConversations = conversations.filter((conversation) => {
    const name = conversation.other_user.display_name || conversation.other_user.username;
    return name.toLocaleLowerCase().includes(search.toLocaleLowerCase());
  });
  const filteredUsers = eligibleUsers.filter((eligibleUser) => {
    const name = eligibleUser.display_name || eligibleUser.username;
    return name.toLocaleLowerCase().includes(contactSearch.toLocaleLowerCase());
  });

  const changeLanguage = useCallback(async (nextLanguage) => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, nextLanguage);
    window.dispatchEvent(new Event("devchat-language-change"));
    if (!profile) return;
    try {
      const updated = await updateMyProfile({ preferred_language: nextLanguage });
      setProfile(updated);
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(t.profileSaveFailed);
    }
  }, [profile, t.profileSaveFailed, handleUnauthorized]);

  async function startConversation(selectedUser) {
    setError("");
    try {
      const conversation = await createConversation(selectedUser.id);
      setConversations((previous) => [
        conversation,
        ...previous.filter((item) => item.id !== conversation.id),
      ]);
      setActiveConversationId(conversation.id);
      setReplyTarget(null);
      setEditingMessageId(null);
      setNewConversationOpen(false);
      setContactSearch("");
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(t.loadFailed);
    }
  }

  async function submitMessage(event) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || !activeConversation || sending) return;
    if (content.length > 4000) {
      setError(t.messageTooLong);
      return;
    }

    setSending(true);
    setError("");
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "typing", is_typing: false }));
    }
    window.clearTimeout(typingStopTimerRef.current);
    try {
      const sent = editingMessageId
        ? await editMessage(activeConversation.id, editingMessageId, content)
        : await sendMessage(activeConversation.id, content, replyTarget?.id);
      setMessages((previous) => mergeMessage(previous, sent));
      setConversations((previous) => {
        const updated = previous.map((conversation) => conversation.id === activeConversation.id
          ? { ...conversation, last_message: { id: sent.id, content: sent.content, sender_id: sent.sender.id, created_at: sent.created_at, is_deleted: Boolean(sent.deleted_at) } }
          : conversation);
        return updated.sort((left, right) => new Date(right.last_message?.created_at || right.created_at) - new Date(left.last_message?.created_at || left.created_at));
      });
      setDraft("");
      setReplyTarget(null);
      setEditingMessageId(null);
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(editingMessageId ? t.messageOperationFailed : t.sendFailed);
    } finally {
      setSending(false);
    }
  }

  function changeDraft(event) {
    const value = event.target.value;
    setDraft(value);
    const socket = socketRef.current;
    if (socket?.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: "typing", is_typing: Boolean(value.trim()) }));
    window.clearTimeout(typingStopTimerRef.current);
    if (value.trim()) {
      typingStopTimerRef.current = window.setTimeout(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "typing", is_typing: false }));
        }
      }, 1800);
    }
  }

  async function removeMessage(message) {
    setError("");
    try {
      const deleted = await deleteMessage(activeConversation.id, message.id);
      setMessages((previous) => mergeMessage(previous, deleted));
      if (editingMessageId === message.id) {
        setEditingMessageId(null);
        setDraft("");
      }
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(t.messageOperationFailed);
    }
  }

  async function reactToMessage(message, emoji) {
    try {
      const updated = await toggleMessageReaction(activeConversation.id, message.id, emoji);
      setMessages((previous) => mergeMessage(previous, updated));
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(t.messageOperationFailed);
    }
  }

  function closeMessageMenus() {
    setReactionPickerMessageId(null);
    setMoreMenuMessageId(null);
  }

  useEffect(() => {
    const openMessageId = reactionPickerMessageId ?? moreMenuMessageId;
    if (openMessageId === null) return undefined;
    const closeOnOutsidePointer = (event) => {
      const messageElement = event.target.closest("[data-message-id]");
      if (messageElement?.getAttribute("data-message-id") !== String(openMessageId)) {
        closeMessageMenus();
      }
    };
    document.addEventListener("pointerdown", closeOnOutsidePointer);
    return () => document.removeEventListener("pointerdown", closeOnOutsidePointer);
  }, [reactionPickerMessageId, moreMenuMessageId]);

  useEffect(() => () => window.clearTimeout(longPressTimerRef.current), []);

  function handleMessagePointerDown(event, messageId) {
    if (event.pointerType !== "touch") return;
    longPressHandledRef.current = false;
    window.clearTimeout(longPressTimerRef.current);
    longPressTimerRef.current = window.setTimeout(() => {
      longPressHandledRef.current = true;
      setTouchActionsMessageId(messageId);
    }, 500);
  }

  function handleMessagePointerUp(event, messageId) {
    window.clearTimeout(longPressTimerRef.current);
    if (event.pointerType !== "touch" || event.target.closest("button")) return;
    if (longPressHandledRef.current) {
      longPressHandledRef.current = false;
      return;
    }
    setTouchActionsMessageId((current) => current === messageId ? null : messageId);
    closeMessageMenus();
  }

  async function loadOlderMessages() {
    if (!nextBefore || !activeConversation || loadingOlder) return;
    setLoadingOlder(true);
    try {
      const page = await getMessages(activeConversation.id, nextBefore);
      setMessages((previous) => [...page.messages, ...previous]);
      setNextBefore(page.next_before);
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(t.loadFailed);
    } finally {
      setLoadingOlder(false);
    }
  }

  async function submitProfile(event) {
    event.preventDefault();
    setSavingProfile(true);
    setError("");
    try {
      const saved = await updateMyProfile(profileDraft);
      setProfile(saved);
      setConversations((previous) => previous.map((conversation) => ({
        ...conversation,
        other_user: conversation.other_user.id === user.id
          ? { ...conversation.other_user, display_name: saved.display_name || user.username }
          : conversation.other_user,
      })));
      if (saved.preferred_language !== language) {
        window.localStorage.setItem(LANGUAGE_STORAGE_KEY, saved.preferred_language);
        window.dispatchEvent(new Event("devchat-language-change"));
      }
      setProfileOpen(false);
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(t.profileSaveFailed);
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleAvatarUpload(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setAvatarBusy(true);
    setError("");
    try {
      const saved = await uploadMyAvatar(file);
      setProfile(saved);
      setProfileDraft((previous) => ({ ...previous, avatar_url: saved.avatar_url }));
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(t.avatarSaveFailed);
    } finally {
      setAvatarBusy(false);
    }
  }

  async function handleAvatarRemove() {
    setAvatarBusy(true);
    setError("");
    try {
      const saved = await removeMyAvatar();
      setProfile(saved);
      setProfileDraft((previous) => ({ ...previous, avatar_url: null }));
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(t.avatarSaveFailed);
    } finally {
      setAvatarBusy(false);
    }
  }

  async function handleSignOut() {
    setError("");
    try {
      await signOut();
      router.replace("/login");
    } catch (requestError) {
      if (requestError.status === 401) {
        clearSession();
        router.replace("/login");
      } else {
        setError(t.requestFailed);
      }
    }
  }

  if (status === "loading" || (status === "authenticated" && loadingApp)) {
    return <main className={styles.authLoading} role="status">{t.loading}</main>;
  }
  if (status === "anonymous") return null;
  if (status === "error") {
    return (
      <main className={styles.authLoading}>
        <p>{t.sessionCheckFailed}</p>
        <button onClick={() => refreshUser().catch(() => setError(t.serverUnavailable))}>{t.retry}</button>
        {error && <p role="alert">{error}</p>}
      </main>
    );
  }

  return (
    <main className={styles.app}>
      <aside className={styles.sidebar} aria-label={t.messages}>
        <header className={styles.sidebarHeader}>
          <div className={styles.brand}>
            <Image className={styles.brandIconImage} src="/branding/devchat-avatar.png" alt="" width={35} height={35} priority />
            <span>Dev<span className={styles.brandAccent}>Chat</span></span>
          </div>
          <button className={`${styles.iconButton} ${styles.newConversationButton}`} aria-label={t.newConversation} title={t.newConversation} onClick={() => setNewConversationOpen(true)}>+</button>
        </header>

        <div className={styles.searchBox}>
          <span aria-hidden="true">⌕</span>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={t.searchChats} aria-label={t.searchChatsLabel} />
        </div>

        <div className={styles.sectionLabel}>{t.messages}<span>{conversations.length}</span></div>
        <div className={styles.chatList}>
          {filteredConversations.map((conversation) => {
            const other = conversation.other_user;
            const name = other.display_name || other.username;
            const preview = conversation.last_message?.is_deleted
              ? t.deletedMessage
              : conversation.last_message?.content || t.noMessages;
            return (
                <button key={conversation.id} className={`${styles.chatItem} ${activeConversationId === conversation.id ? styles.activeChat : ""}`} onClick={() => { setActiveConversationId(conversation.id); setReplyTarget(null); setEditingMessageId(null); setDraft(""); }} aria-pressed={activeConversationId === conversation.id}>
                <Avatar name={name} url={other.avatar_url} />
                <span className={styles.chatInfo}>
                  <span className={styles.chatTopLine}><span className={styles.chatName}>{name}</span><span className={styles.chatTime}>{formatTime(conversation.last_message?.created_at, language)}</span></span>
                  <span className={styles.chatBottomLine}><span className={styles.lastMessage}>{preview}</span>{conversation.unread_count > 0 && <span className={styles.unreadBadge} aria-label={`${conversation.unread_count} ${t.unread}`}>{conversation.unread_count}</span>}</span>
                </span>
              </button>
            );
          })}
          {filteredConversations.length === 0 && <p className={styles.emptySearch}>{search ? t.noResults : t.noConversations}</p>}
        </div>

        <footer className={styles.profile}>
          <button className={`${styles.profileAvatar} ${styles.profileButton}`} onClick={() => { setProfileDraft(profile); setProfileOpen(true); }} aria-label={t.profile} title={t.profile}><Avatar name={profile?.display_name || user?.username} url={profile?.avatar_url} /></button>
          <button className={styles.profileInfoButton} onClick={() => { setProfileDraft(profile); setProfileOpen(true); }}>
            <span className={styles.profileInfo}><strong>{profile?.display_name || user?.username}</strong><span>@{user?.username}</span></span>
          </button>
          <div className={styles.profileActions}>
            <label className={styles.languagePicker}>
              <span className={styles.visuallyHidden}>{t.language}</span>
              <select value={language} onChange={(event) => changeLanguage(event.target.value)}><option value="en">EN</option><option value="ru">RU</option></select>
            </label>
            <button className={`${styles.iconButton} ${styles.logoutButton}`} aria-label={t.signOut} title={t.signOut} onClick={handleSignOut}>↪</button>
          </div>
        </footer>
      </aside>

      <section className={styles.conversation} aria-label={contact ? `${t.messages}: ${contact.display_name || contact.username}` : t.messages}>
        {contact ? (
          <>
            <header className={styles.conversationHeader}>
              <Avatar name={contact.display_name || contact.username} url={contact.avatar_url} />
              <div className={styles.contactInfo}><strong>{contact.display_name || contact.username}</strong><span>{partnerTyping ? t.typing : `@${contact.username}`}</span></div>
            </header>
            <div className={styles.messages} role="log" aria-label={t.messageHistory} aria-live="polite">
              {nextBefore && <button className={styles.loadOlder} disabled={loadingOlder} onClick={loadOlderMessages}>{loadingOlder ? t.loading : t.loadOlder}</button>}
              {loadingMessages ? <p className={styles.emptyConversation}>{t.loading}</p> : messages.length === 0 ? <p className={styles.emptyConversation}>{t.noMessages}</p> : messages.map((message) => {
                const mine = message.sender.id === user.id;
                const readStatus = mine
                  ? getMessageReadStatus(message, activeConversation?.other_last_read_message_id)
                  : null;
                return (
                  <div key={message.id} className={`${styles.messageRow} ${mine ? styles.myMessageRow : ""}`}>
                    <div
                      className={`${styles.messageBubble} ${mine ? styles.myMessage : ""} ${touchActionsMessageId === message.id ? styles.messageActionsVisible : ""}`}
                      data-message-id={message.id}
                      onPointerDown={(event) => handleMessagePointerDown(event, message.id)}
                      onPointerUp={(event) => handleMessagePointerUp(event, message.id)}
                      onPointerCancel={() => window.clearTimeout(longPressTimerRef.current)}
                      onContextMenu={(event) => {
                        event.preventDefault();
                        setTouchActionsMessageId(message.id);
                      }}
                      onKeyDown={(event) => {
                        if (event.key === "Escape") {
                          const trigger = event.currentTarget.querySelector(
                            moreMenuMessageId === message.id
                              ? "[data-more-trigger]"
                              : "[data-reaction-trigger]",
                          );
                          setTouchActionsMessageId(null);
                          closeMessageMenus();
                          trigger?.focus();
                        }
                      }}
                      onBlur={(event) => {
                        if (!event.currentTarget.contains(event.relatedTarget)) closeMessageMenus();
                      }}
                    >
                      {message.reply_to && (
                        <div className={styles.replyPreview}>
                          <strong>{message.reply_to.sender_name}</strong>
                          <span>{message.reply_to.deleted ? t.deletedMessage : message.reply_to.content}</span>
                        </div>
                      )}
                      <p className={message.deleted_at ? styles.deletedMessage : ""}>
                        {message.deleted_at ? t.deletedMessage : message.content}
                      </p>
                      {message.edited_at && !message.deleted_at && <span className={styles.editedLabel}>{t.edited}</span>}
                      <span className={styles.messageTime}>
                        <time dateTime={message.created_at}>{formatTime(message.created_at, language)}</time>
                        {readStatus && (
                          <MessageReadStatus
                            isRead={readStatus === "read"}
                            savedLabel={t.savedOnServer}
                            readLabel={t.read}
                          />
                        )}
                      </span>
                      {message.reactions?.length > 0 && (
                        <div className={styles.reactionList} role="group" aria-label={t.messageReactions}>
                          {message.reactions.map((reaction) => (
                            <button
                              key={reaction.emoji}
                              type="button"
                              aria-pressed={reaction.reacted}
                              aria-label={t.toggleReaction.replace("{emoji}", reaction.emoji).replace("{count}", reaction.count)}
                              onClick={() => reactToMessage(message, reaction.emoji)}
                            >
                              <span aria-hidden="true">{reaction.emoji}</span><span>{reaction.count}</span>
                            </button>
                          ))}
                        </div>
                      )}
                      {!message.deleted_at && (
                        <>
                          <div className={styles.messageActionsToolbar} role="group" aria-label={t.messageActions}>
                            <button type="button" aria-label={t.reply} title={t.reply} onClick={() => { setReplyTarget(message); setEditingMessageId(null); setDraft(""); setTouchActionsMessageId(null); composerRef.current?.focus(); }}>
                              <MessageActionIcon name="reply" />
                            </button>
                            <button
                              type="button"
                              aria-label={t.addReaction}
                              title={t.addReaction}
                              data-reaction-trigger="true"
                              aria-haspopup="true"
                              aria-expanded={reactionPickerMessageId === message.id}
                              aria-controls={`reaction-picker-${message.id}`}
                              onClick={() => { setMoreMenuMessageId(null); setReactionPickerMessageId((current) => current === message.id ? null : message.id); }}
                            >
                              <MessageActionIcon name="reaction" />
                            </button>
                            {mine && (
                              <button type="button" aria-label={t.edit} title={t.edit} onClick={() => { setEditingMessageId(message.id); setReplyTarget(null); setDraft(message.content); setTouchActionsMessageId(null); composerRef.current?.focus(); }}>
                                <MessageActionIcon name="edit" />
                              </button>
                            )}
                            {mine && (
                              <button
                                type="button"
                                data-more-trigger="true"
                                aria-haspopup="true"
                                aria-label={t.moreMessageActions}
                                title={t.moreMessageActions}
                                aria-expanded={moreMenuMessageId === message.id}
                                aria-controls={`message-menu-${message.id}`}
                                onClick={() => { setReactionPickerMessageId(null); setMoreMenuMessageId((current) => current === message.id ? null : message.id); }}
                              >
                                <MessageActionIcon name="more" />
                              </button>
                            )}
                          </div>
                          {reactionPickerMessageId === message.id && (
                            <div id={`reaction-picker-${message.id}`} className={styles.messagePopover} role="group" aria-label={t.chooseReaction}>
                              {REACTION_EMOJIS.map((emoji) => (
                                <button key={emoji} type="button" aria-label={t.reactWith.replace("{emoji}", emoji)} onClick={() => { reactToMessage(message, emoji); setReactionPickerMessageId(null); setTouchActionsMessageId(null); }}>
                                  {emoji}
                                </button>
                              ))}
                            </div>
                          )}
                          {mine && moreMenuMessageId === message.id && (
                            <div id={`message-menu-${message.id}`} className={`${styles.messagePopover} ${styles.moreMessageMenu}`} role="group" aria-label={t.moreMessageActions}>
                              <button type="button" className={styles.deleteMessageAction} onClick={() => { removeMessage(message); setMoreMenuMessageId(null); setTouchActionsMessageId(null); }}>
                                {t.delete}
                              </button>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            {(replyTarget || editingMessageId) && (
              <div className={styles.composerContext}>
                <span>
                  <strong>{editingMessageId ? t.editingMessage : t.replyingTo}</strong>
                  {editingMessageId ? draft : replyTarget?.deleted_at ? t.deletedMessage : replyTarget?.content}
                </span>
                <button type="button" aria-label={t.cancel} onClick={() => { setReplyTarget(null); setEditingMessageId(null); setDraft(""); }}>{t.cancel}</button>
              </div>
            )}
            <form className={styles.composer} onSubmit={submitMessage}>
              <input ref={composerRef} value={draft} onChange={changeDraft} maxLength={4000} placeholder={t.messagePlaceholder.replace("{name}", contact.display_name || contact.username)} aria-label={t.messagePlaceholder.replace("{name}", contact.display_name || contact.username)} disabled={sending} />
              <button type="submit" className={styles.sendButton} aria-label={t.sendMessage} disabled={sending || !draft.trim()}>
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 12L20 4L14 20L11 13L4 12Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" /><path d="M11 13L20 4" stroke="currentColor" strokeWidth="1.7" /></svg>
              </button>
            </form>
          </>
        ) : (
          <div className={styles.emptyState}>
            <Image src="/branding/devchat-avatar.png" alt="" width={68} height={68} />
            <h1>{t.selectConversation}</h1>
            <button className={styles.emptyAction} onClick={() => setNewConversationOpen(true)}>{t.startConversation}</button>
          </div>
        )}
        <div className={styles.encryptionNote}>
          <span>◆</span> DevChat · {t.persistentMessages}
          <span className={styles.connectionStatus}> · {backendStatus === "ok" ? t.djangoPostgresConnected : t.serverUnavailable}</span>
          <span className={styles.connectionStatus}> · {t[`realtime${realtimeStatus[0].toUpperCase()}${realtimeStatus.slice(1)}`]}</span>
          {error && <span className={styles.inlineError} role="alert"> · {error}</span>}
        </div>
      </section>

      {newConversationOpen && (
        <div className={styles.modalBackdrop} onMouseDown={(event) => { if (event.target === event.currentTarget) setNewConversationOpen(false); }}>
          <section className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="new-conversation-title">
            <header className={styles.modalHeader}><div><p className={styles.modalEyebrow}>{t.findPeople}</p><h2 id="new-conversation-title">{t.newConversation}</h2></div><button className={styles.iconButton} onClick={() => setNewConversationOpen(false)} aria-label={t.cancel}>×</button></header>
            <input className={styles.modalSearch} value={contactSearch} onChange={(event) => setContactSearch(event.target.value)} placeholder={t.findPeople} aria-label={t.findPeople} autoFocus />
            <div className={styles.userChoices}>
              {filteredUsers.map((eligibleUser) => <button key={eligibleUser.id} className={styles.userChoice} onClick={() => startConversation(eligibleUser)}><Avatar name={eligibleUser.display_name || eligibleUser.username} url={eligibleUser.avatar_url} /><span><strong>{eligibleUser.display_name || eligibleUser.username}</strong><small>@{eligibleUser.username}</small></span><span className={styles.choiceArrow}>›</span></button>)}
              {filteredUsers.length === 0 && <p className={styles.emptySearch}>{eligibleUsers.length ? t.noResults : t.noUsers}</p>}
            </div>
          </section>
        </div>
      )}

      {profileOpen && profileDraft && (
        <div className={styles.modalBackdrop} onMouseDown={(event) => { if (event.target === event.currentTarget) setProfileOpen(false); }}>
          <section className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="profile-title">
            <header className={styles.modalHeader}><div><p className={styles.modalEyebrow}>@{user?.username}</p><h2 id="profile-title">{t.profile}</h2></div><button className={styles.iconButton} onClick={() => setProfileOpen(false)} aria-label={t.cancel}>×</button></header>
            <form className={styles.profileForm} onSubmit={submitProfile}>
              <div className={styles.avatarControls}>
                <Avatar name={profileDraft.display_name || user?.username} url={profileDraft.avatar_url} className={styles.profilePreview} />
                <label className={styles.avatarUploadButton}>
                  {avatarBusy ? t.saving : t.changeAvatar}
                  <input type="file" accept="image/jpeg,image/png,image/webp" onChange={handleAvatarUpload} disabled={avatarBusy} />
                </label>
                {profileDraft.avatar_url && <button type="button" className={styles.removeAvatarButton} onClick={handleAvatarRemove} disabled={avatarBusy}>{t.removeAvatar}</button>}
              </div>
              <label>{t.displayName}<input maxLength={80} value={profileDraft.display_name || ""} onChange={(event) => setProfileDraft({ ...profileDraft, display_name: event.target.value })} /></label>
              <label>{t.description}<textarea maxLength={500} rows={4} value={profileDraft.description || ""} onChange={(event) => setProfileDraft({ ...profileDraft, description: event.target.value })} /></label>
              <label>{t.language}<select value={profileDraft.preferred_language || "en"} onChange={(event) => setProfileDraft({ ...profileDraft, preferred_language: event.target.value })}><option value="en">English</option><option value="ru">Русский</option></select></label>
              <div className={styles.modalActions}><button type="button" className={styles.cancelButton} onClick={() => setProfileOpen(false)}>{t.cancel}</button><button className={styles.saveButton} disabled={savingProfile}>{savingProfile ? t.saving : t.save}</button></div>
            </form>
          </section>
        </div>
      )}
    </main>
  );
}
