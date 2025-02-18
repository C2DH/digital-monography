'use client'

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import TnbMarkdown from "./TnbMarkdown";

type IWarning = {
    id: string
    problem: string
    recommend: string
    elem: string
    // prev_elem: string
    // curr_elem: string
    // next_elem: string
    [key: string]: any
}

export default function DynamicComponent() {
    const [warnings, setWarnings] = useState<IWarning[]>([]);
    const searchParams = useSearchParams();
    const key = searchParams?.get("key");
    const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
    useEffect(() => {
        async function fetchObjectFromS3(inputKey: string) {
            try {
                const getPreSignedUrlResp = await fetch(`${endpoint}/test/gpu?type=warnings&key=${inputKey}`);
                const preSignedUrljson = await getPreSignedUrlResp.json();
                const preSignedUrl = preSignedUrljson["presigned_url"];
                const resp = await fetch(preSignedUrl);
                const json = await resp.json();
                setWarnings(json);
            } catch (e) {
                console.error(e);
            }
        };
        if (key) {
            fetchObjectFromS3(key);
        }
    }, [key]);
    return (
        <>
            <div className="container">
                <div className="accordion" id="warnings-accordion">
                    {warnings.map((warning: IWarning, idx: number) => (
                        <div className="accordion-item" key={idx}>
                            <h2 className="accordion-header" id="warnings-heading">
                                <button
                                    className="accordion-button collapsed"
                                    type="button"
                                    data-bs-toggle="collapse"
                                    data-bs-target={`#collapse-${warning.id}`}
                                    aria-expanded="true"
                                    aria-controls={`collapse-${warning.id}`}
                                >
                                    {warning.problem}
                                </button>
                            </h2>
                            <div
                                id={`collapse-${warning.id}`}
                                className="accordion-collapse collapse"
                                aria-labelledby="warnings-heading"
                                data-bs-parent="#warnings-accordion">
                                <div className="accordion-body">
                                    <TnbMarkdown content={`**${warning.problem}** ${warning.recommend}`} />
                                    <hr />
                                    <div className="row">
                                        <div className="col-1">
                                        </div>
                                        <div className="col-9">
                                            <TnbMarkdown content={warning.elem} />
                                        </div>
                                    </div>
                                    {/* <div className="row">
                                        <div className="col-1">
                                            👉
                                        </div>
                                        <div className="col-9">
                                            <TnbMarkdown content={warning.curr_elem} />
                                        </div>
                                    </div>
                                    <div className="row">
                                        <div className="col-1">
                                        </div>
                                        <div className="col-9">
                                            <TnbMarkdown content={warning.next_elem} />
                                        </div>
                                    </div> */}
                                </div>
                            </div>
                        </div>
                    ))}
                    {warnings.length == 0 && <div className="d-flex justify-content-center">
                        <h4>Please wait for the warnings to load...</h4>
                        <div className="spinner-grow text-secondary" role="status">
                            <span className="visually-hidden">Loading...</span>
                        </div>
                    </div>}
                </div>
            </div>
        </>
    )
}
