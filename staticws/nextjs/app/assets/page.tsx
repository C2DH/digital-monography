'use client'

import { Suspense } from 'react';
import TnbTable from "./../_components/TnbTable";

export default function Page() {
    return (
        <>
            <div>
                <h1>Assets</h1>
                <Suspense>
                    <TnbTable></TnbTable>
                </Suspense>

            </div>
        </>
    );
}
