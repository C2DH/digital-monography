'use client'

import { Suspense } from 'react';
import DynamicTable from "./DynamicTable";

export default function Page() {
    return (
        <>
            <div>
                <h1>Assets</h1>
                <Suspense>
                    <DynamicTable></DynamicTable>
                </Suspense>
            </div>
        </>
    );
}
