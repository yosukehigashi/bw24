"use client"

import React from 'react';

import { Button } from "@fluentui/react-button";
import { Input } from "@fluentui/react-input";
import { Label } from "@fluentui/react-label";
import { Spinner } from "@fluentui/react-spinner";
import { Display } from "@fluentui/react-text";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useId } from "@fluentui/react-components";
import styles from "./page.module.css";
import { useVenueContext } from './venueProvider';

export const GetVenueForm = () => {
    const router = useRouter()
    const [url, setUrl] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const largeId = useId("input-large");
    const { value, setValue } = useVenueContext();
  
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
  
      const data = await response.json();
      console.log('venueId:', venueId);
      setIsLoading(false);
      console.log('response:', data);
      setValue({ id: venueId, initialImageUrls: data?.urls, title: data?.title });
      router.push(`/venue`);
    }
    
    return (
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
    );
}