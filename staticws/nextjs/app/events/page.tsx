'use client'

import { Suspense } from 'react';
import TnbStatusTracker from "../_components/TnbStatusTracker";


export default function Page() {
    return (
        <>
            <div>
                <h1>Events</h1>
                <Suspense>
                    <TnbStatusTracker></TnbStatusTracker>
                </Suspense>
            </div>
        </>
    );
}
