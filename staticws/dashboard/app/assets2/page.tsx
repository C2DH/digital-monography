'use client'

import { Suspense } from 'react';
import AssetsTable from "./AssetsTable";

export default function Page() {
    return (
        <>
            <div className="container">
                <h1 className="mt-5">Assets</h1>
                <div className="d-flex flex-column p-4 justify-content-center">
                    <Suspense>
                        <AssetsTable></AssetsTable>
                    </Suspense>
                </div>
            </div>
        </>
    );
}
