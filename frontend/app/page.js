
"use client";

import { useEffect, useState } from "react";
import styles from "./page.module.css";
import { checkBackendHealth } from "./lib/api";

const initialChats = [
  {
    id: 1,
    name: "Alex",
    initials: "A",
    color: "#647da8",
    message: "Скинь потом ссылку на репозиторий",
    time: "13:42",
    unread: 2,
    online: true,
  },
  {
    id: 2,
    name: "Daniel",
    initials: "D",
    color: "#9a779e",
    message: "Сегодня собираемся?",
    time: "12:18",
    unread: 0,
    online: true,
  },
  {
    id: 3,
    name: "Mika",
    initials: "M",
    color: "#628f85",
    message: "Я отправил тебе файлы",
    time: "Вчера",
    unread: 0,
    online: false,
  },
];

const initialMessages = {
  1: [
    { id: 1, text: "Как продвигается DevChat?", mine: false, time: "13:38" },
    { id: 2, text: "Нормально, уже поднял Django и базу", mine: true, time: "13:40" },
    { id: 3, text: "Скинь потом ссылку на репозиторий", mine: false, time: "13:42" },
  ],
  2: [
    { id: 1, text: "Сегодня собираемся?", mine: false, time: "12:18" },
  ],
  3: [
    { id: 1, text: "Я отправил тебе файлы", mine: false, time: "Вчера" },
  ],
};

export default function Home() {
  const [chats, setChats] = useState(initialChats);
  const [activeChat, setActiveChat] = useState(1);
  const [messages, setMessages] = useState(initialMessages);
  const [draft, setDraft] = useState("");
  const [search, setSearch] = useState("");
  const [backendStatus, setBackendStatus] = useState({
    status: "checking",
    database: "unknown",
  });

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      const result = await checkBackendHealth();

      if (!cancelled) {
        setBackendStatus(result);
      }
    }

    loadHealth();

    return () => {
      cancelled = true;
    };
  }, []);

  const currentChat = chats.find((chat) => chat.id === activeChat);
  const currentMessages = messages[activeChat] || [];

  const filteredChats = chats.filter((chat) =>
    chat.name.toLowerCase().includes(search.toLowerCase()),
  );

  function sendMessage(event) {
    event.preventDefault();

    const text = draft.trim();
    if (!text) return;

    const message = {
      id: Date.now(),
      text,
      mine: true,
      time: new Date().toLocaleTimeString("ru-RU", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setMessages((previous) => ({
      ...previous,
      [activeChat]: [...(previous[activeChat] || []), message],
    }));

    setChats((previous) =>
      previous.map((chat) =>
        chat.id === activeChat
          ? { ...chat, message: text, time: message.time, unread: 0 }
          : chat,
      ),
    );

    setDraft("");
  }

  const connectionMessage =
    backendStatus.status === "checking"
      ? "Проверка соединения..."
      : backendStatus.status === "ok"
        ? backendStatus.database === "connected"
          ? "Django подключён · PostgreSQL подключён"
          : "Django доступен · ошибка PostgreSQL"
        : backendStatus.status === "offline"
          ? "Сервер недоступен"
          : "Ошибка сервера";

  return (
    <main className={styles.app}>
      <aside className={styles.sidebar}>
        <header className={styles.sidebarHeader}>
          <div className={styles.brand}>
            <div className={styles.brandIcon}>D</div>
            <span>
              Dev<span className={styles.brandAccent}>Chat</span>
            </span>
          </div>
          <button className={styles.iconButton} aria-label="Новое сообщение">
            +
          </button>
        </header>

        <div className={styles.searchBox}>
          <span>⌕</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Поиск чатов..."
            aria-label="Поиск чатов"
          />
          <kbd>⌘ K</kbd>
        </div>

        <div className={styles.sectionLabel}>
          СООБЩЕНИЯ <span>{chats.length}</span>
        </div>

        <div className={styles.chatList}>
          {filteredChats.map((chat) => (
            <button
              key={chat.id}
              className={`${styles.chatItem} ${
                activeChat === chat.id ? styles.activeChat : ""
              }`}
              onClick={() => setActiveChat(chat.id)}
            >
              <div
                className={styles.avatar}
                style={{ "--avatar-color": chat.color }}
              >
                {chat.initials}
                {chat.online && <span className={styles.onlineDot} />}
              </div>

              <div className={styles.chatInfo}>
                <div className={styles.chatTopLine}>
                  <span className={styles.chatName}>{chat.name}</span>
                  <span className={styles.chatTime}>{chat.time}</span>
                </div>
                <div className={styles.chatBottomLine}>
                  <span className={styles.lastMessage}>{chat.message}</span>
                  {chat.unread > 0 && (
                    <span className={styles.unreadBadge}>{chat.unread}</span>
                  )}
                </div>
              </div>
            </button>
          ))}

          {filteredChats.length === 0 && (
            <p className={styles.emptySearch}>Ничего не найдено</p>
          )}
        </div>

        <footer className={styles.profile}>
          <div className={`${styles.avatar} ${styles.profileAvatar}`}>R</div>
          <div className={styles.profileInfo}>
            <strong>Your profile</strong>
            <span>Dev mode</span>
          </div>
          <button className={styles.iconButton} aria-label="Настройки">
            ⚙
          </button>
        </footer>
      </aside>

      {currentChat && (
        <section className={styles.conversation}>
          <header className={styles.conversationHeader}>
            <div
              className={styles.avatar}
              style={{ "--avatar-color": currentChat.color }}
            >
              {currentChat.initials}
              {currentChat.online && <span className={styles.onlineDot} />}
            </div>
            <div className={styles.contactInfo}>
              <strong>{currentChat.name}</strong>
              <span>
                <span
                  className={
                    currentChat.online ? styles.statusDot : styles.offlineDot
                  }
                />
                {currentChat.online ? "В сети" : "Не в сети"}
              </span>
            </div>
            <div className={styles.headerActions}>
              <button className={styles.iconButton} aria-label="Поиск в чате">
                ⌕
              </button>
              <button className={styles.iconButton} aria-label="Дополнительно">
                ···
              </button>
            </div>
          </header>

          <div className={styles.messages}>
            <div className={styles.dayDivider}>
              <span>Сегодня</span>
            </div>

            {currentMessages.map((message) => (
              <div
                key={message.id}
                className={`${styles.messageRow} ${
                  message.mine ? styles.myMessageRow : ""
                }`}
              >
                <div
                  className={`${styles.messageBubble} ${
                    message.mine ? styles.myMessage : ""
                  }`}
                >
                  <p>{message.text}</p>
                  <span className={styles.messageTime}>
                    {message.time}{" "}
                    {message.mine && (
                      <span className={styles.checkmark}>✓✓</span>
                    )}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <form className={styles.composer} onSubmit={sendMessage}>
            <button
              type="button"
              className={styles.attachButton}
              aria-label="Прикрепить файл"
            >
              +
            </button>
            <input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={`Написать ${currentChat.name}...`}
              aria-label="Текст сообщения"
            />
            <span className={styles.composerHint}>Enter ↵</span>
            <button
              type="submit"
              className={styles.sendButton}
              aria-label="Отправить сообщение"
            >
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path
                  d="M4 12L20 4L14 20L11 13L4 12Z"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinejoin="round"
                />
                <path
                  d="M11 13L20 4"
                  stroke="currentColor"
                  strokeWidth="1.7"
                />
              </svg>
            </button>
          </form>

          <div className={styles.encryptionNote}>
            <span>◆</span> DevChat · Локальный прототип
            <span className={styles.connectionStatus}>
              {" · "}
              {connectionMessage}
            </span>
          </div>
        </section>
      )}
    </main>
  );
}