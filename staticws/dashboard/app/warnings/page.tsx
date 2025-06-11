'use client'

import { Suspense, useEffect } from 'react';
import DynamicComponent from "./DynamicComponent";

export default function Page() {
    useEffect(() => {
        require("bootstrap/dist/js/bootstrap.bundle.min.js");
    }, []);
    return (
        <>
            <div className="container">
                <h1 className="mt-5">Warnings Messages</h1>
                <p>
                    The digital publishing platform scans the submitted manuscript
                    and checks each line against the predefined rules.
                    If an element violates a rule, the platform flags it as a warning.
                    Click on the drop-down to see the fragment of the manuscript where the issue was raised
                    as well as a description of the problem.
                    The &ldquo;👉&rdquo; character will point where the element that has violated
                    a rule starts and ends.
                </p>
                <div className="d-flex flex-column flex-md-row p-4 gap-4 py-md-5 align-items-center justify-content-center">
                    <Suspense>
                        <DynamicComponent></DynamicComponent>
                    </Suspense>
                </div>
            </div>
        </>
    );
}
