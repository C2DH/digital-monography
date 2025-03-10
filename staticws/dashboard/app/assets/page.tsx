'use client'

import { Suspense } from 'react';
import AssetsComponent from "./AssetsComponent";

export default function Page() {
    return (
        <>
            <div>
                <h1 className="mt-5">Assets</h1>
                <div className="d-flex flex-column p-4 justify-content-center">
                    <Suspense>
                        <AssetsComponent></AssetsComponent>
                    </Suspense>
                </div>
            </div>
        </>
    );
}
