'use client'

import { Suspense } from 'react';
import DynamicComponent from "./DynamicComponent";

export default function Page() {
    return (
        <>
            <div className="container">
                <h1 className="mt-5">Warnings Per File</h1>
                <div className="d-flex flex-column p-4 justify-content-center">
                    <Suspense>
                        <DynamicComponent></DynamicComponent>
                    </Suspense>
                </div>
            </div>
        </>
    );
}
