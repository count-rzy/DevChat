export const LANGUAGE_STORAGE_KEY = "devchat-language";
export const SUPPORTED_LANGUAGES = ["en", "ru"];

export const translations = {
  en: {
    newMessage: "New message",
    searchChats: "Search chats...",
    searchChatsLabel: "Search chats",
    messages: "MESSAGES",
    noResults: "No chats found",
    yourProfile: "Your profile",
    devMode: "Dev mode",
    settings: "Settings",
    online: "Online",
    offline: "Offline",
    searchConversation: "Search conversation",
    moreOptions: "More options",
    today: "Today",
    attachFile: "Attach file",
    writeTo: "Message {name}...",
    messageText: "Message text",
    sendMessage: "Send message",
    localPrototype: "Local prototype",
    checkingConnection: "Checking connection...",
    djangoPostgresConnected: "Django connected · PostgreSQL connected",
    djangoDatabaseError: "Django available · PostgreSQL error",
    serverUnavailable: "Server unavailable",
    serverError: "Server error",
    language: "Interface language",
  },
  ru: {
    newMessage: "Новое сообщение",
    searchChats: "Поиск чатов...",
    searchChatsLabel: "Поиск чатов",
    messages: "СООБЩЕНИЯ",
    noResults: "Ничего не найдено",
    yourProfile: "Ваш профиль",
    devMode: "Режим разработки",
    settings: "Настройки",
    online: "В сети",
    offline: "Не в сети",
    searchConversation: "Поиск в чате",
    moreOptions: "Дополнительно",
    today: "Сегодня",
    attachFile: "Прикрепить файл",
    writeTo: "Написать {name}...",
    messageText: "Текст сообщения",
    sendMessage: "Отправить сообщение",
    localPrototype: "Локальный прототип",
    checkingConnection: "Проверка соединения...",
    djangoPostgresConnected: "Django подключён · PostgreSQL подключён",
    djangoDatabaseError: "Django доступен · ошибка PostgreSQL",
    serverUnavailable: "Сервер недоступен",
    serverError: "Ошибка сервера",
    language: "Язык интерфейса",
  },
};

export function getPreferredLanguage() {
  const savedLanguage = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (SUPPORTED_LANGUAGES.includes(savedLanguage)) return savedLanguage;

  const browserLanguage = window.navigator.language
    .toLowerCase()
    .split("-")[0];
  return SUPPORTED_LANGUAGES.includes(browserLanguage) ? browserLanguage : "en";
}

export function subscribeToLanguage(onChange) {
  window.addEventListener("storage", onChange);
  window.addEventListener("devchat-language-change", onChange);

  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener("devchat-language-change", onChange);
  };
}
