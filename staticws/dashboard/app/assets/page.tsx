'use client'

import { Suspense } from 'react';
import AssetsComponent from "./AssetsComponent";

export default function Page() {
    return (
        <>
            <div>
                <h1 className="mt-5">Assets</h1>
                {/* <div className="d-flex flex-column p-4 justify-content-center" style={{ width: '50%' }}> */}
                {/* <div className="overflow-x-auto p-4 justify-content-center" style={{ width: '100%' }}> */}
                {/* <div className="p-4 justify-content-center" style={{ width: '100%' }}> */}
                {/* <div className="d-flex flex-column p-4 justify-content-center" style={{ width: '100%' }}> */}
                <div className="d-flex flex-column p-4 justify-content-center">
                    <Suspense>
                        <AssetsComponent></AssetsComponent>
                    </Suspense>
                </div>
            </div>
        </>
    );
}
