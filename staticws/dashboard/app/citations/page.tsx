'use client'

import { Suspense } from 'react';
import DynamicTable from "./DynamicTable";

export default function Page() {
    return (
        <>
            <div className="container">
                <h1 className="mt-5">Citations</h1>
                <div className="d-flex flex-column p-4 justify-content-center">
                    <Suspense>
                        <DynamicTable></DynamicTable>
                    </Suspense>
                </div>
            </div>
        </>
    );
}
