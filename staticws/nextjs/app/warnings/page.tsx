'use client'

import { Suspense } from 'react';
import { useEffect } from 'react';
import DynamicComponent from "./DynamicComponent";

export default function Page() {
    useEffect(() => {
        require("bootstrap/dist/js/bootstrap.bundle.min.js");
    }, []);
    return (
        <>
            <main>
                <div className="container">
                    <h1 className="mt-5">Warnings Messages</h1>
                    <div className="d-flex flex-column flex-md-row p-4 gap-4 py-md-5 align-items-center justify-content-center">
                        <Suspense>
                            <DynamicComponent></DynamicComponent>
                        </Suspense>
                    </div>
                </div>
            </main>
        </>
    );
}
