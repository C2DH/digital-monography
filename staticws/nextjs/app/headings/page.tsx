'use client'

import { Suspense } from 'react';
import DynamicListGroup from "./DynamicComponent";

export default function Page() {
    return (
        <>
            <div>
                <h1>Headings</h1>
                <Suspense>
                    <DynamicListGroup></DynamicListGroup>
                </Suspense>
            </div>
        </>
    );
}
