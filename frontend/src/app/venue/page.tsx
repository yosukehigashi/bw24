"use client";

import React, { useState } from 'react';
import { useVenueContext } from '../venueProvider';

import { LargeTitle } from '@fluentui/react-text';

import styles from "./venue.module.css";
import { Checkbox } from '@fluentui/react-checkbox';
import { Button } from '@fluentui/react-button';

const Photo = ({ url, imageIdx, onCheckboxClick }: { url: string, imageIdx: number, onCheckboxClick: (idx: number) => void }) => {
    return (
        <div className={styles.wrapperPhoto}>
            <div className={styles.wrapperCheckbox}>
                <Checkbox size="large" onChange={() => onCheckboxClick(imageIdx)} />
            </div>
            <img                       
                // className={styles.logo}
                src={url}
                alt="Next.js Logo"
                height={200}
                // priority
                />
        </div>
    )
}


export default function VenuePage() {
    const [selectedImages, setSelectedImages] = useState<number[]>([]);
    const { value } = useVenueContext();

    const toggleImageFromSelection = (imageIdx: number) => {
        const isSelected = selectedImages.includes(imageIdx);
        if (isSelected) {
            setSelectedImages(selectedImages.filter((idx) => idx !== imageIdx));
        } else {
            setSelectedImages([...selectedImages, imageIdx]);
        }
    }

    const handleUpscale = () => {
        console.log('Upscale', selectedImages);
    }

    const handleApplyTrend = () => {
        console.log('handleApplyTrend', selectedImages);
    }

    return (
        <div className={styles.container}>
            <div className={styles.wrapperTitle}>
                <LargeTitle>{value?.title}</LargeTitle>
            </div>

            {value?.initialImageUrls?.map((url, idx) => {
                console.log('url', url)
                return <Photo url={url} key={url} imageIdx={idx} onCheckboxClick={toggleImageFromSelection} />
            })}

            <div className="controlPannel">
                <Button onClick={handleUpscale}>Upscale</Button>
                <Button onClick={handleApplyTrend}>Apply trend</Button>
            </div>
        </div>
    )
}