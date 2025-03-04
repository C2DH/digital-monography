'use client'

import "./../_styles/treeView.css";
import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import TnbBookNav from "./../_components/TnbBookNav";

type ICountMap = {
    [fileName: string]: number;
}

type IHeading = {
    text: string,
    level: string,
    fileName: string,
}

type IHeadings = {
    [key: string]: IHeading[],
}

function getNestedStr(rec: any, attr: string): string {
    if (rec && rec.M && Object.hasOwn(rec.M, attr) && Object.hasOwn(rec.M[attr], "S")) {
        return rec.M[attr].S;
    } else {
        return "";
    }
}

function getNestedNum(rec: any, attr: string): number {
    if (rec && rec.M && Object.hasOwn(rec.M, attr) && Object.hasOwn(rec.M[attr], "N")) {
        return Number(rec.M[attr].N);
    } else {
        return 0;
    }
}

export default function DynamicListGroup(): React.JSX.Element {
    const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
    const [data, setData] = useState<IHeadings>({});
    const [loading, setLoading] = useState<boolean>(true);
    const [wordCount, setWordCount] = useState<ICountMap>({});
    const [charCount, setCharCount] = useState<ICountMap>({});

    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const dbTable = "dgtmon-dev-dyndb-headings-tbl";

    useEffect(() => {
        const wCount = {};
        const cCount = {};
        const fetchRecords = async (pk: string) => {
            try {
                setLoading(true);
                const resp = await fetch(`${endpoint}/test/headings?slug=${pk}`);
                const respJson = await resp.json();
                const headings: IHeadings = {};
                const items = respJson.Items || [];
                for (let i = 0; i < items.length; i++) {
                    let records = items[i].records?.L || [];
                    const fileName = getNestedStr(records[0], "file_name");
                    wCount[fileName] = getNestedNum(records[0], "word_count");
                    cCount[fileName] = getNestedNum(records[0], "char_count");
                    for (let j = 0; j < records.length; j++) {
                        const text = getNestedStr(records[j], "text");
                        let level = getNestedStr(records[j], "level");
                        level = level.replace(/\D+/g, ''); // TODO: backend should produce "1" instead of "h1"
                        if (!Object.hasOwn(headings, fileName)) {
                            headings[fileName] = [];
                        }
                        headings[fileName].push({
                            fileName: fileName,
                            text: text,
                            level: level,
                        });
                    }
                }
                setData(headings);
                setWordCount(wCount);
                setCharCount(cCount);
                setLoading(false);
            } catch (err) {
                setLoading(false);
                console.error(err);
            }
        };
        const fetchObjectFromS3 = async (aSlug: string) => {
            try {
                const configKey = btoa(`${aSlug}/_config.yml`)
                const getPreSignedUrlResp = await fetch(`${endpoint}/test/gpu?type=asset&key=${configKey}`);
                const preSignedUrljson = await getPreSignedUrlResp.json();
                const preSignedUrl = preSignedUrljson["presigned_url"];
                const resp = await fetch(preSignedUrl);
                const blob = await resp.blob();
                const yml = await blob.text();
                console.log("config", yml);
            } catch (e) {
                console.error(e);
            }
        };
        if (slug) {
            fetchRecords(slug);
            fetchObjectFromS3(slug);
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
                                {wordCount[file] > 0 && <small> {wordCount[file]} words</small>}
                                {charCount[file] > 0 && <small> {charCount[file]} characters</small>}
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
