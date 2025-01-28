'use client'

import "./../_styles/treeView.css";
import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import TnbBookNav from "./../_components/TnbBookNav";

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

export default function DynamicListGroup(): JSX.Element {
    const [data, setData] = useState<IHeadings>({});
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const dbTable = "dgtmon-dev-dyndb-headings-tbl";

    const fetchRecords = async (pk: string) => {
        try {
            const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
            const resp = await fetch(`${endpoint}/test/headings?slug=${pk}`);
            const respJson = await resp.json();
            const headings: IHeadings = {};
            const items = respJson.Items || [];
            for (let i = 0; i < items.length; i++) {
                let records = items[i].records?.L || [];
                for (let j = 0; j < records.length; j++) {
                    const fileName = getNestedStr(records[j], "file_name");
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
        } catch (err) {
            console.log("Error", err);
        }
    };

    useEffect(() => {
        if (slug) {
            fetchRecords(slug);
        }
    }, [slug]);

    return (
        <>
            {slug && <TnbBookNav slug={slug} color="secondary"></TnbBookNav>}
            {data && Object.entries(data)
                .map(([file, headings]: [string, IHeading[]], idx: number) => {
                    return (
                        <ul className="list-group" key={idx}>
                            <li className="list-group-item list-group-item-primary" key={file}><b>{file}</b></li>
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
        </>
    )
}
