'use client'

import "./../_styles/treeView.css";
import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { DynamoDBClient, QueryCommand } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";

const ddbClient = new DynamoDBClient({
    region: "eu-west-1",
    credentials: {
        accessKeyId: process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID!,
        secretAccessKey: process.env.NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY!,
    },
});

const marshallOptions = {
    convertEmptyValues: false,
    removeUndefinedValues: true,
    convertClassInstanceToMap: false,
};

const unmarshallOptions = {
    wrapNumbers: false,
};

const ddbDocClient = DynamoDBDocumentClient.from(ddbClient, {
    marshallOptions,
    unmarshallOptions,
});

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
            const cmd = new QueryCommand({
                TableName: dbTable,
                KeyConditionExpression: "slug = :slug",
                ExpressionAttributeValues: {
                    ":slug": { "S": pk }
                },
            });
            const headings: IHeadings = {};
            const resp = await ddbDocClient.send(cmd);
            const items = resp.Items || [];
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
