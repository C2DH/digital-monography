'use client'

import { Suspense } from 'react';
import DynamicListGroup from "./DynamicComponent";

export default function Page() {
    return (
        <>
            <div className="container">
                <h1 className="mt-5">Headings</h1>
                <div className="d-flex flex-column p-4 justify-content-center">
                    <Suspense>
                        <DynamicListGroup></DynamicListGroup>
                    </Suspense>
                </div>
            </div>
        </>
    );
}
