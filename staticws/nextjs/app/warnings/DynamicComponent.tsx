'use client'

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import TnbMarkdown from "./TnbMarkdown";

export default function DynamicComponent() {
    const [warnings, setWarnings] = useState<any[]>([]);
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
                console.log("JSON.stringify(json)", JSON.stringify(json));
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
                {warnings && warnings.map((warning, idx) => (
                    <div className="card" key={idx}>
                        <div className="card-header">
                            <a data-bs-toggle="collapse"
                                href={`#collapse-${warning.id}`}
                                role="button"
                                aria-expanded="false"
                                aria-controls={`collapse-${warning.id}`}
                            >
                                {warning.problem}
                            </a>
                        </div>
                        <div className="collapse" id={`collapse-${warning.id}`}>
                            <div className="card card-body">
                                <span>
                                    <p><b>{warning.problem} </b>{warning.recommend}</p>
                                    <div className="row">
                                        <div className="col-1">
                                        </div>
                                        <div className="col-9">
                                            <TnbMarkdown content={warning.prev_elem} />
                                        </div>
                                    </div>
                                    <div className="row">
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
                                    </div>
                                </span>
                            </div>
                        </div>
                    </div>
                ))}

            </div>
        </>
    )
}
