'use client'

import { Suspense } from 'react';
import DynamicTable from "./DynamicTable";

export default function Page() {

    // if (slug == null) {
    //     return (<>
    //         <b>Error: the url is missing the <i>slug</i> search parameter.</b>
    //         <p>A valid slug should end with a search query, e.g. <code>/assets?slug=my-slug</code></p>
    //     </>
    //     )
    // }
    return (
        <>
            <div>
                <h1>Details</h1>
                <Suspense>
                    <DynamicTable></DynamicTable>
                </Suspense>
            </div>
        </>
    );
}
