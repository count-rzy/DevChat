"use client";

import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import styles from "./page.module.css";
import { checkBackendHealth } from "./lib/api";
import { useAuth } from "./lib/auth-context";
import {
  getPreferredLanguage,
  LANGUAGE_STORAGE_KEY,
  subscribeToLanguage,
  translations,
} from "./lib/translations";
import {
  createConversation,
  getConversations,
  getEligibleUsers,
  getMessages,
  getMyProfile,
  sendMessage,
  updateMyProfile,
} from "./lib/chat";

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
  const [error, setError] = useState("");
  const [backendStatus, setBackendStatus] = useState("checking");

  const handleUnauthorized = useCallback((requestError) => {
    if (requestError.status !== 401) return false;
    clearSession();
    router.replace("/login");
    return true;
  }, [clearSession, router]);

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
      })
      .catch((requestError) => {
        if (!active) return;
        if (!handleUnauthorized(requestError)) setError(t.loadFailed);
        setMessages([]);
        setLoadedConversationId(activeConversationId);
      });
    return () => { active = false; };
  }, [activeConversationId, status, router, t.loadFailed, handleUnauthorized]);

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
    try {
      const sent = await sendMessage(activeConversation.id, content);
      setMessages((previous) => [...previous, sent]);
      setConversations((previous) => {
        const updated = previous.map((conversation) => conversation.id === activeConversation.id
          ? { ...conversation, last_message: { content: sent.content, sender_id: user.id, created_at: sent.created_at } }
          : conversation);
        return updated.sort((left, right) => new Date(right.last_message?.created_at || right.created_at) - new Date(left.last_message?.created_at || left.created_at));
      });
      setDraft("");
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(t.sendFailed);
    } finally {
      setSending(false);
    }
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
            const preview = conversation.last_message?.content || t.noMessages;
            return (
              <button key={conversation.id} className={`${styles.chatItem} ${activeConversationId === conversation.id ? styles.activeChat : ""}`} onClick={() => setActiveConversationId(conversation.id)} aria-pressed={activeConversationId === conversation.id}>
                <span className={styles.avatar}>{initials(name)}</span>
                <span className={styles.chatInfo}>
                  <span className={styles.chatTopLine}><span className={styles.chatName}>{name}</span><span className={styles.chatTime}>{formatTime(conversation.last_message?.created_at, language)}</span></span>
                  <span className={styles.chatBottomLine}><span className={styles.lastMessage}>{preview}</span></span>
                </span>
              </button>
            );
          })}
          {filteredConversations.length === 0 && <p className={styles.emptySearch}>{search ? t.noResults : t.noConversations}</p>}
        </div>

        <footer className={styles.profile}>
          <button className={`${styles.avatar} ${styles.profileAvatar} ${styles.profileButton}`} onClick={() => { setProfileDraft(profile); setProfileOpen(true); }} aria-label={t.profile} title={t.profile}>{initials(profile?.display_name || user?.username)}</button>
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
              <span className={styles.avatar}>{initials(contact.display_name || contact.username)}</span>
              <div className={styles.contactInfo}><strong>{contact.display_name || contact.username}</strong><span>@{contact.username}</span></div>
            </header>
            <div className={styles.messages} role="log" aria-label={t.messageHistory} aria-live="polite">
              {nextBefore && <button className={styles.loadOlder} disabled={loadingOlder} onClick={loadOlderMessages}>{loadingOlder ? t.loading : t.loadOlder}</button>}
              {loadingMessages ? <p className={styles.emptyConversation}>{t.loading}</p> : messages.length === 0 ? <p className={styles.emptyConversation}>{t.noMessages}</p> : messages.map((message) => {
                const mine = message.sender.id === user.id;
                return (
                  <div key={message.id} className={`${styles.messageRow} ${mine ? styles.myMessageRow : ""}`}>
                    <div className={`${styles.messageBubble} ${mine ? styles.myMessage : ""}`}>
                      <p>{message.content}</p>
                      <time className={styles.messageTime} dateTime={message.created_at}>{formatTime(message.created_at, language)}</time>
                    </div>
                  </div>
                );
              })}
            </div>
            <form className={styles.composer} onSubmit={submitMessage}>
              <input value={draft} onChange={(event) => setDraft(event.target.value)} maxLength={4000} placeholder={t.messagePlaceholder.replace("{name}", contact.display_name || contact.username)} aria-label={t.messagePlaceholder.replace("{name}", contact.display_name || contact.username)} disabled={sending} />
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
          {error && <span className={styles.inlineError} role="alert"> · {error}</span>}
        </div>
      </section>

      {newConversationOpen && (
        <div className={styles.modalBackdrop} onMouseDown={(event) => { if (event.target === event.currentTarget) setNewConversationOpen(false); }}>
          <section className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="new-conversation-title">
            <header className={styles.modalHeader}><div><p className={styles.modalEyebrow}>{t.findPeople}</p><h2 id="new-conversation-title">{t.newConversation}</h2></div><button className={styles.iconButton} onClick={() => setNewConversationOpen(false)} aria-label={t.cancel}>×</button></header>
            <input className={styles.modalSearch} value={contactSearch} onChange={(event) => setContactSearch(event.target.value)} placeholder={t.findPeople} aria-label={t.findPeople} autoFocus />
            <div className={styles.userChoices}>
              {filteredUsers.map((eligibleUser) => <button key={eligibleUser.id} className={styles.userChoice} onClick={() => startConversation(eligibleUser)}><span className={styles.avatar}>{initials(eligibleUser.display_name || eligibleUser.username)}</span><span><strong>{eligibleUser.display_name || eligibleUser.username}</strong><small>@{eligibleUser.username}</small></span><span className={styles.choiceArrow}>›</span></button>)}
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
