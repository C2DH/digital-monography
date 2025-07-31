'use client'

import "./../_styles/treeView.css";
import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import TnbBookNav from "./../_components/TnbBookNav";
// import { API_ENDPOINT, API_STAGE } from "./../constants";

type ICountMap = {
    [fileName: string]: number;
}

type IHeading = {
    file_name: string
    file_num: number
    h_num: number
    elem: string
    level: string
    text: string
    word_count: number
    char_count: number
    target: string
    slug: string
}

type IHeadings = {
    [key: string]: IHeading[],
}

export default function DynamicListGroup(): React.JSX.Element {
    // const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
    const [data, setData] = useState<IHeadings>({});
    const [loading, setLoading] = useState<boolean>(true);
    const [wordCount, setWordCount] = useState<ICountMap>({});
    const [charCount, setCharCount] = useState<ICountMap>({});

    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    useEffect(() => {
        const wCount = {};
        const cCount = {};
        const fetchFromDb = async (aSlug: string) => {
            try {
                // const resp = await fetch(`${API_ENDPOINT}/${API_STAGE}/headings/list?slug=${aSlug}`);
                const resp = await fetch(`http://localhost:8001/headings/list?slug=${aSlug}`);
                const dbRecords = await resp.json();
                const sortedRecords = dbRecords.sort((a: IHeading, b: IHeading) => {
                    if (a.file_num !== b.file_num) {
                        return a.file_num - b.file_num;
                    }
                    return a.h_num - b.h_num;
                });
                const headings: IHeadings = {};
                for (let i = 0; i < sortedRecords.length; i++) {
                    let rec = sortedRecords[i];
                    if (!Object.hasOwn(headings, rec.file_name)) {
                        headings[rec.file_name] = [];
                        wCount[rec.file_name] = rec.word_count;
                        cCount[rec.file_name] = rec.char_count;
                    }
                    headings[rec.file_name].push(rec);
                }
                setData(headings);
                setWordCount(wCount);
                setCharCount(cCount);
                setLoading(false);
            } catch (e) {
                setLoading(false);
                console.error(e);
            }
        }
        const fetchObjectFromS3 = async (aSlug: string) => {
            /* 
            We can fetch the _config.yml file from S3, but I don't see why
            */
            // try {
            //     const configKey = btoa(`${aSlug}/_config.yml`);
            //     const getPreSignedUrlResp = await fetch(`${API_ENDPOINT}/${API_STAGE}/gpu?type=asset&key=${configKey}`);
            //     const preSignedUrljson = await getPreSignedUrlResp.json();
            //     const preSignedUrl = preSignedUrljson["presigned_url"];
            //     const resp = await fetch(preSignedUrl);
            //     const blob = await resp.blob();
            //     const yml = await blob.text();
            //     console.log("config", yml);
            // } catch (e) {
            //     console.error(e);
            // }
        };
        if (slug) {
            // fetchObjectFromS3(slug);
            fetchFromDb(slug);
        }
    }, [slug]);

    return (
        <>
            {slug && <TnbBookNav slug={slug} color="secondary"></TnbBookNav>}
            {!loading && <div>
                <b>Word count: </b>
                <p>{Object.values(wordCount).reduce((a, b) => a + b, 0)}</p>
                <b>Character count: </b>
                <p>{Object.values(charCount).reduce((a, b) => a + b, 0)}</p>
            </div>}
            {!loading && data && Object.entries(data)
                .map(([file, headings]: [string, IHeading[]], idx: number) => {
                    return (
                        <ul className="list-group" key={idx}>
                            <li className="list-group-item list-group-item-primary" key={file}>
                                <b>{file}</b>
                                {headings[0].word_count > 0 && <small> {headings[0].word_count} words</small>}
                                {headings[0].char_count > 0 && <small> {headings[0].char_count} characters</small>}
                            </li>
                            {headings && headings.map((h: IHeading, i: number) => (
                                <li className="list-group-item"
                                    key={i}>
                                    <span className={`indent${h.level}`}></span>
                                    {h.text}
                                </li>
                            ))}
                        </ul>
                    )
                })}
            {loading && <div className="d-flex justify-content-center">
                <h4>Please wait for the data to load...</h4>
                <div className="spinner-grow text-secondary" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>}
        </>
    )
}
