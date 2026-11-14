"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import { registerAccount } from "./lib/auth";
import { useAuth } from "./lib/auth-context";
import {
  getPreferredLanguage,
  LANGUAGE_STORAGE_KEY,
  subscribeToLanguage,
  translations,
} from "./lib/translations";
import styles from "./auth.module.css";

function LanguagePicker({ language, t }) {
  function changeLanguage(event) {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, event.target.value);
    window.dispatchEvent(new Event("devchat-language-change"));
  }
  return (
    <label className={styles.languagePicker}>
      <span className={styles.visuallyHidden}>{t.language}</span>
      <select value={language} onChange={changeLanguage}>
        <option value="en">EN</option>
        <option value="ru">RU</option>
      </select>
    </label>
  );
}

function AuthFrame({ children }) {
  const language = useSyncExternalStore(
    subscribeToLanguage,
    getPreferredLanguage,
    () => "en",
  );
  const t = translations[language];
  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  return (
    <main className={styles.screen}>
      <div className={styles.glow} aria-hidden="true" />
      <header className={styles.topbar}>
        <Link className={styles.brand} href="/" aria-label="DevChat">
          <Image src="/branding/devchat-avatar.png" alt="" width={40} height={40} priority />
          <span>Dev<span>Chat</span></span>
        </Link>
        <LanguagePicker language={language} t={t} />
      </header>
      <section className={styles.card} aria-labelledby="auth-title">
        {children({ language, t })}
      </section>
      <p className={styles.footer}>DevChat · {t.privateInviteOnly}</p>
    </main>
  );
}

export function LoginPage() {
  const { status, signIn } = useAuth();
  const router = useRouter();
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  useEffect(() => {
    if (status === "authenticated") router.replace("/");
  }, [status, router]);

  return <AuthFrame>{({ t }) => (
    <>
      <p className={styles.eyebrow}>{t.welcomeBack}</p>
      <h1 id="auth-title">{t.signInTitle}</h1>
      <p className={styles.description}>{t.signInDescription}</p>
      <form className={styles.form} onSubmit={async (event) => {
        event.preventDefault();
        setError("");
        setSubmitting(true);
        const formData = new FormData(event.currentTarget);
        try {
          await signIn({ username: formData.get("username"), password: formData.get("password") });
          router.replace("/");
        } catch (requestError) {
          setError(requestError.status === 401 ? t.invalidCredentials : requestError.status === 429 ? t.tooManyRequests : t.requestFailed);
        } finally {
          setSubmitting(false);
        }
      }}>
        <label>{t.username}<input name="username" autoComplete="username" required maxLength={150} /></label>
        <label>{t.password}<input name="password" type="password" autoComplete="current-password" required /></label>
        {error && <p className={styles.error} role="alert">{error}</p>}
        {status === "error" && <p className={styles.error} role="status">{t.sessionCheckFailed}</p>}
        <button className={styles.submit} disabled={submitting || status === "loading"}>
          {submitting ? t.signingIn : t.signIn}
        </button>
      </form>
      <p className={styles.switch}>{t.noAccount} <Link href="/register">{t.createAccount}</Link></p>
    </>
  )}</AuthFrame>;
}

export function RegisterPage() {
  const { status } = useAuth();
  const router = useRouter();
  const language = useSyncExternalStore(subscribeToLanguage, getPreferredLanguage, () => "en");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const t = translations[language];
  useEffect(() => { document.documentElement.lang = language; }, [language]);
  useEffect(() => {
    if (status === "authenticated") router.replace("/");
  }, [status, router]);

  return <AuthFrame>{({ t }) => success ? (
    <div role="status">
      <p className={styles.eyebrow}>{t.accountCreated}</p>
      <h1 id="auth-title">{t.readyToSignIn}</h1>
      <p className={styles.description}>{t.registrationSuccess}</p>
      <Link className={styles.submitLink} href="/login">{t.signIn}</Link>
    </div>
  ) : (
    <>
      <p className={styles.eyebrow}>{t.invitationRequired}</p>
      <h1 id="auth-title">{t.createAccount}</h1>
      <p className={styles.description}>{t.registerDescription}</p>
      <form className={styles.form} onSubmit={async (event) => {
        event.preventDefault();
        setError("");
        setSubmitting(true);
        const formData = new FormData(event.currentTarget);
        try {
          await registerAccount({
            username: formData.get("username"),
            password: formData.get("password"),
            invite_code: formData.get("invite_code"),
          });
          setSuccess(true);
        } catch (requestError) {
          const fieldError = requestError.fields?.invite_code?.[0] || requestError.fields?.username?.[0] || requestError.fields?.password?.[0];
          setError(requestError.status === 429 ? t.tooManyRequests : fieldError ? t.registrationInvalid : t.requestFailed);
        } finally {
          setSubmitting(false);
        }
      }}>
        <label>{t.username}<input name="username" autoComplete="username" required minLength={3} maxLength={150} /></label>
        <label>{t.password}<input name="password" type="password" autoComplete="new-password" required minLength={8} /></label>
        <label>{t.inviteCode}<input name="invite_code" autoComplete="off" required maxLength={32} /></label>
        <p className={styles.hint}>{t.passwordHint}</p>
        {error && <p className={styles.error} role="alert">{error}</p>}
        <button className={styles.submit} disabled={submitting || status === "loading"}>
          {submitting ? t.creatingAccount : t.createAccount}
        </button>
      </form>
      <p className={styles.switch}>{t.haveAccount} <Link href="/login">{t.signIn}</Link></p>
    </>
  )}</AuthFrame>;
}
