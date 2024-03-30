"use client";

import React from 'react';
import { useVenueContext } from '../venueProvider';

export default function VenuePage() {
    const { value, setValue } = useVenueContext();

    console.log('I am here with value', value);

    return (
        <div>
            <h1>Venue page</h1>
        </div>
    )
}