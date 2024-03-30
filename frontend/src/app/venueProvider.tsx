"use client"

import React, { createContext, useContext, useState } from 'react';


type Venue = {
    id: string;
    title: string;
    initialImageUrls: string[];
};

// Step 1: Create the context
const VenueContext = createContext<{
    value: Venue | undefined;
    setValue: (venue: Venue) => void;

}>({
    value: undefined,
    setValue: (venue: Venue) => {},
});

// Step 2: Create a provider component
const VenueProvider = ({ children }: {children: React.ReactNode}) => {
    const [value, setValue] = useState<Venue | undefined>();
    // Your provider logic goes here

    return <VenueContext.Provider value={{
        value,
        setValue,
    }}>{children}</VenueContext.Provider>;
};

// Step 3: Create a custom hook to access the context
const useVenueContext = () => {
    const context = useContext(VenueContext);
    if (!context) {
        throw new Error('useMyContext must be used within a MyProvider');
    }
    return context;
};

// Step 4: Export the context and the provider
export { VenueContext, VenueProvider, useVenueContext };