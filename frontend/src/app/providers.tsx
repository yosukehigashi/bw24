'use client';

import { FluentProvider } from "@fluentui/react-provider";
import React from "react"
import { VenueProvider } from "./venueProvider";
import { webLightTheme } from "@fluentui/tokens";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <FluentProvider theme={webLightTheme}>
            <VenueProvider>
                {children}
            </VenueProvider>
        </FluentProvider>
    );

}