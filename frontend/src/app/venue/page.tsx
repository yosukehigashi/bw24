"use client";

import React, { useState } from 'react';
import { useVenueContext } from '../venueProvider';

import { LargeTitle, Subtitle1 } from '@fluentui/react-text';

import styles from "./venue.module.css";
import { Checkbox } from '@fluentui/react-checkbox';

import {
    Dialog,
    DialogTrigger,
    DialogSurface,
    DialogTitle,
    DialogBody,
    DialogActions,
    DialogContent,
    Button,
    Spinner,
    Divider,
    Input,
    Label,
  } from "@fluentui/react-components";

import { Radio, RadioGroup } from "@fluentui/react-components";

const TRENDS = ['pizza_party', 'karaoke', 'poetry_reading']
const AD_PLATFORMS = ['Google', 'Facebook', 'Yahoo']

const IS_MOCKING = false;
const FAKE_RESULTS = [
    {
        images: ['https://via.placeholder.com/150', 'https://via.placeholder.com/150'],
        trend: 'pizza_party'
    },
    {
        images: ['https://via.placeholder.com/150', 'https://via.placeholder.com/150'],
        trend: 'karaoke'
    },
    {
        images: ['https://via.placeholder.com/150', 'https://via.placeholder.com/150'],
        trend: 'poetry_reading'
    }
]

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

const ResultPhoto = ({ base64 }: { base64: string }) => {
    return (
        <div className={styles.wrapperResultPhoto}>
            <img src={`data:image/png;base64, ${base64}`} height={200} />
            <div className={styles.wrapperDownloadButton}>
                <Button as={"a"} href={`data:image/png;base64, ${base64}`} download>Download</Button>
            </div>
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

type ResultLineItem = {
    images: string[];
    trend: string;
}

export default function VenuePage() {
    const [selectedImages, setSelectedImages] = useState<number[]>([]);
    const [selectedTrend, setSelectedTrend] = useState<string | undefined>();
    const [isApplyTrendsLoading, setIsApplyTrendsLoading] = useState<boolean>(false);
    const [isAdvertiseLoading, setIsAdvertiseLoading] = useState<boolean>(false);
    const [resultsArray, setResultsArray] = useState<ResultLineItem[]>([]);
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
                trend: selectedTrend,
                tags: value?.tags
            }),
        });

        const data = await response.json();
        return data;
    }

    const handleApplyTrend = async () => {
        setIsApplyTrendsLoading(true);
        // const promises = selectedImages.forEach(fetchApplyTrend);
        const promises = selectedImages.map(fetchApplyTrend);

        const results = await Promise.all(promises);
        const transformedResults = results.reduce((acc, result) => {
            return {
                images: [...acc.images, result.image],
                trend: selectedTrend
            }
        }, {images: [], trend: selectedTrend})

        setResultsArray([...resultsArray, transformedResults]);
        setIsApplyTrendsLoading(false);

        console.log('results', results)
    }

    const handleAdvertise = () => {
        console.log('Advertise');
    }

    return (
        <div className={styles.main}>
            <div className={styles.container}>
                <div className={styles.wrapperTitle}>
                    <LargeTitle>{value?.title}</LargeTitle>
                </div>

                <Subtitle1>Initial photos</Subtitle1>
                <div className={styles.wrapperPhotos}>
                    {value?.initialImageUrls?.map((url, idx) => {
                        console.log('url', url)
                        return <Photo url={url} key={url} imageIdx={idx} onCheckboxClick={toggleImageFromSelection} />
                    })}
                </div>

                <div className={styles.wrapperDivider}>
                    <Divider />
                </div>

                <Subtitle1>Actions</Subtitle1>
                <div className={styles.controlPannel}>
                    <Button onClick={handleUpscale}>Upscale</Button>
                    
                    <Dialog>
                        <DialogTrigger disableButtonEnhancement>
                            <Button>Apply trend</Button>
                        </DialogTrigger>
                        <DialogSurface>
                            <DialogBody>
                            <DialogTitle>Choose a trend for your space</DialogTitle>
                            <DialogContent>
                            <RadioGroup>
                                {TRENDS.map((trend) => {
                                    return <Radio key={trend} value={trend} label={trend} onChange={() => setSelectedTrend(trend)} />
                                })}
                            </RadioGroup>
                            </DialogContent>
                            <DialogActions>
                                <DialogTrigger disableButtonEnhancement>
                                <Button appearance="secondary">Close</Button>
                                </DialogTrigger>
                                <Button appearance="primary" onClick={handleApplyTrend}>Apply trend</Button>
                                {isApplyTrendsLoading && <Spinner size='large' />}
                            </DialogActions>
                            </DialogBody>
                        </DialogSurface>
                    </Dialog>
                </div>

                <div className={styles.wrapperDivider}>
                    <Divider />
                </div>

                <Subtitle1>Results</Subtitle1>
                {(!IS_MOCKING ? resultsArray : FAKE_RESULTS).map((result, idx) => {
                    return (
                        <div className={styles.wrapperResultRow} key={idx}>
                            <Subtitle1>#{idx}: {result.trend}</Subtitle1>
                            <div className={styles.wrapperPhotos}>
                                {result.images.map((base64, idx) => {
                                    return <ResultPhoto base64={base64} key={idx} />
                                })}
                            </div>
                            
                        <Dialog>
                            <DialogTrigger disableButtonEnhancement>
                                <Button>Advertise</Button>
                            </DialogTrigger>
                            <DialogSurface>
                                <DialogBody>
                                    <DialogTitle>Choose an advertising platform</DialogTitle>
                                    <DialogContent>
                                        <RadioGroup>
                                            {AD_PLATFORMS.map((trend) => {
                                                return <Radio key={trend} value={trend} label={trend} />
                                            })}
                                        </RadioGroup>

                                        <div className={styles.wrapperBudget}>
                                            <DialogTitle>Budget</DialogTitle>
                                            
                                            <div className={styles.wrapperBudgetInput}>
                                                <Label>
                                                    Advertising budget in Japanese yen (¥)
                                                </Label>
                                                <Input type="number" />
                                            </div>
                                        </div>
                                    </DialogContent>
                                    <DialogActions>
                                        <DialogTrigger disableButtonEnhancement>
                                        <Button appearance="secondary">Close</Button>
                                        </DialogTrigger>
                                        <Button appearance="primary" onClick={handleAdvertise}>Advertise</Button>
                                        {isAdvertiseLoading && <Spinner size='large' />}
                                    </DialogActions>
                                </DialogBody>
                            </DialogSurface>
                        </Dialog>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}