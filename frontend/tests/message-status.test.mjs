import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { getMessageReadStatus } from "../app/lib/message-status.mjs";
import { mergeMessage } from "../app/lib/messages.mjs";

test("persisted outgoing messages show the server-saved state until the peer cursor passes them", () => {
  const message = { id: 12, content: "hello", deleted_at: null };

  assert.equal(getMessageReadStatus(message, null), "saved");
  assert.equal(getMessageReadStatus(message, 11), "saved");
  assert.equal(getMessageReadStatus(message, 12), "read");
  assert.equal(getMessageReadStatus(message, 18), "read");
});

test("pending, failed, invalid, and deleted messages never show a successful status", () => {
  assert.equal(getMessageReadStatus(null, null), null);
  assert.equal(getMessageReadStatus({ content: "pending" }, null), null);
  assert.equal(getMessageReadStatus({ id: "12" }, 12), null);
  assert.equal(getMessageReadStatus({ id: 12, deleted_at: "2026-01-01T00:00:00Z" }, 12), null);
});

test("history reconciliation and websocket events upsert messages without duplicates or reordering", () => {
  const first = { id: 1, content: "first", created_at: "2026-02-01T10:00:00Z" };
  const second = { id: 2, content: "second", created_at: "2026-02-01T10:01:00Z" };
  const third = { id: 3, content: "third", created_at: "2026-02-01T10:02:00Z" };
  const afterReconnection = [second, third].reduce(mergeMessage, [first, second]);
  assert.deepEqual(afterReconnection, [first, second, third]);
  assert.equal(afterReconnection.filter((message) => message.id === second.id).length, 1);

  const edited = { ...second, content: "edited" };
  const afterUpdateEvent = mergeMessage(afterReconnection, edited);
  assert.equal(afterUpdateEvent.length, 3);
  assert.equal(afterUpdateEvent[1].content, "edited");
});

test("all statically referenced interface labels exist in English and Russian", () => {
  const translations = readFileSync(new URL("../app/lib/translations.js", import.meta.url), "utf8");
  const page = readFileSync(new URL("../app/page.js", import.meta.url), "utf8");
  const enStart = translations.indexOf("en: {");
  const ruStart = translations.indexOf("ru: {");
  const objectEnd = translations.indexOf("\n};", ruStart);
  const enExtrasStart = translations.indexOf("Object.assign(translations.en");
  const ruExtrasStart = translations.indexOf("Object.assign(translations.ru");
  const enBlock = `${translations.slice(enStart, ruStart)}${translations.slice(enExtrasStart, ruExtrasStart)}`;
  const ruBlock = `${translations.slice(ruStart, objectEnd)}${translations.slice(ruExtrasStart)}`;
  const keysIn = (block) => new Set([...block.matchAll(/^\s*([A-Za-z][\w]*):\s*["'`]/gm)].map((match) => match[1]));
  const referencedKeys = new Set([...page.matchAll(/\bt\.([A-Za-z][\w]*)/g)].map((match) => match[1]));
  ["realtimeConnecting", "realtimeConnected", "realtimeReconnecting", "savedOnServer"]
    .forEach((key) => referencedKeys.add(key));

  for (const key of referencedKeys) {
    assert.ok(keysIn(enBlock).has(key), `English translation is missing t.${key}`);
    assert.ok(keysIn(ruBlock).has(key), `Russian translation is missing t.${key}`);
  }
});
