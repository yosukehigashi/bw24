"use client"

import Image from "next/image";
import styles from "./page.module.css";
import { useRouter } from 'next/navigation'

import {
  FluentProvider,
  webLightTheme,
  Button,
  Text,
  Display,
  Label,
  Input,
  useId,
  Spinner,
} from "@fluentui/react-components";
import { useState } from "react";

export default function Home() {
  const router = useRouter()
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const largeId = useId("input-large");

  const handleFetchVenue = async () => {
    const venueId = url.replace("https://www.instabase.jp/space/", "");
    fetchVenue(venueId?.toString() || "");
  }

  const fetchVenue = async (venueId: string) => {
    setIsLoading(true);
    const response = await fetch(`http://127.0.0.1:8080/venue/${venueId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json"
      },
    });

    // const data = await response.json();
    console.log('venueId:', venueId);
    setIsLoading(false);
    router.push(`/venue`);
  }

  return (
    <FluentProvider theme={webLightTheme}>
      <main className={styles.main}>
        <div className={styles.wrapper}>
          <Display>Instabase business suite</Display>

          <div className={styles.form}>
            <div className={styles.wrapperInput}>
              <Label size="large" htmlFor={largeId}>
                Venue url
              </Label>
              <Input size="large" id={largeId} onChange={(event) => {
                setUrl(event.target.value);
              }}/>
            </div>

            <Button appearance="primary" onClick={handleFetchVenue} icon={isLoading ? <Spinner size="tiny" /> : undefined}>Find my venue</Button>
          </div>
        </div>
        {/* <div className={styles.description}>
          <p>
            Get started by editing&nbsp;
            <code className={styles.code}>src/app/page.tsx</code>
          </p>
          <div>
            <a
              href="https://vercel.com?utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
              target="_blank"
              rel="noopener noreferrer"
            >
              By{" "}
              <Image
                src="/vercel.svg"
                alt="Vercel Logo"
                className={styles.vercelLogo}
                width={100}
                height={24}
                priority
              />
            </a>
          </div>
        </div>

        <div className={styles.center}>
          <Image
            className={styles.logo}
            src="/next.svg"
            alt="Next.js Logo"
            width={180}
            height={37}
            priority
          />
        </div>

        <div className={styles.grid}>
          <a
            href="https://nextjs.org/docs?utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
            className={styles.card}
            target="_blank"
            rel="noopener noreferrer"
          >
            <h2>
              Docs <span>-&gt;</span>
            </h2>
            <p>Find in-depth information about Next.js features and API.</p>
          </a>

          <a
            href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
            className={styles.card}
            target="_blank"
            rel="noopener noreferrer"
          >
            <h2>
              Learn <span>-&gt;</span>
            </h2>
            <p>Learn about Next.js in an interactive course with&nbsp;quizzes!</p>
          </a>

          <a
            href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
            className={styles.card}
            target="_blank"
            rel="noopener noreferrer"
          >
            <h2>
              Templates <span>-&gt;</span>
            </h2>
            <p>Explore starter templates for Next.js.</p>
          </a>

          <a
            href="https://vercel.com/new?utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
            className={styles.card}
            target="_blank"
            rel="noopener noreferrer"
          >
            <h2>
              Deploy <span>-&gt;</span>
            </h2>
            <p>
              Instantly deploy your Next.js site to a shareable URL with Vercel.
            </p>
          </a>
        </div> */}
      </main>
    </FluentProvider>
  );
}