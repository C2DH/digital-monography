'use client'

import { Suspense } from 'react';
import DynamicComponent from "./DynamicComponent";

export default function Page() {
    return (
        <>
            <div>
                <h1>Warnings Per File</h1>
                <Suspense>
                    <DynamicComponent></DynamicComponent>
                </Suspense>
            </div>
        </>
    );
}
