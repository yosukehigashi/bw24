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
                // @TODO: Insecure?
                crossOrigin="anonymous"                     
                // className={styles.logo}
                id={`image-${imageIdx}`}
                src={url}
                alt="Next.js Logo"
                height={200}
                // priority
                />
        </div>
    )
}

function getBase64Image(img: any) {
    var canvas = document.createElement("canvas");
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    var ctx = canvas.getContext("2d");
    ctx?.drawImage(img, 0, 0);
    var dataURL = canvas.toDataURL("image/png");
    return dataURL.replace(/^data:image\/?[A-z]*;base64,/, "");
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

    const fetchApplyTrend = async (imageIdx: number) => {
        const imageBase64 = getBase64Image(document.getElementById("image-" + imageIdx));

        console.log('imageBase64', imageBase64);

        const response = await fetch(`http://127.0.0.1:8080/edit`, {
            method: "POST",
            headers: {
            "Content-Type": "application/json"
            },
            body: JSON.stringify({
                images: imageBase64,
                trend: "pizza_party"
            }),
        });

        const data = await response.json();
        console.log(data)
    }

    const handleApplyTrend = () => {
        selectedImages.forEach(fetchApplyTrend);
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