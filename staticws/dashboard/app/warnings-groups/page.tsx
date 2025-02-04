'use client'

import { Suspense } from 'react';
import TnbListObjectsS3 from "./../_components/TnbListObjectsS3";

export default function Page() {
    return (
        <>
            <div className="container">
                <h1 className="mt-5">Warnings Per File</h1>
                <div className="d-flex flex-column p-4 justify-content-center">
                    <Suspense>
                    <TnbListObjectsS3
                            backendPath={"list-warnings"}
                            targetPath={"/warnings"}>
                        </TnbListObjectsS3>
                    </Suspense>
                </div>
            </div>
        </>
    );
}
