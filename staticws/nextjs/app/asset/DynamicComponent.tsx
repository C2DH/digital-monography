'use client'

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

function getNestedStr(rec: any, attr: string): string {
    const dataType = "S";
    if (rec && rec.M && Object.hasOwn(rec.M, attr) && Object.hasOwn(rec.M[attr], dataType)) {
        return rec.M[attr][dataType];
    } else {
        return "";
    }
}

function getNestedBool(rec: any, attr: string): boolean | undefined {
    const dataType = "BOOL";
    if (rec && rec.M && Object.hasOwn(rec.M, attr) && Object.hasOwn(rec.M[attr], dataType)) {
        return (rec.M[attr][dataType]);
    } else {
        return undefined;
    }
}

function getAsHtml(s: string): string {
    if (s.toLowerCase().endsWith(".docx")) {
        return s.substring(0, s.length - 5) + ".html";
    } else if (s.toLowerCase().endsWith(".ipynb")) {
        return s.substring(0, s.length - 6) + ".html";
    } else {
        return s;
    };
}

export default function DynamicTable() {
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const pk = searchParams?.get("pk");
    const dbTable = "dgtmon-dev-dyndb-assets-tbl";
    const bucket = "https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com";
    const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
    const [assetSrc, setAssetSrc] = useState<string>("");
    const [tableData, setTableData] = useState<any[]>([]);
    const s3Key = atob(pk || "");

    const [alttext, setAlttext] = useState<string>("");
    const [author, setAuthor] = useState<string>("");
    const [caption, setCaption] = useState<string>("");
    const [exists, setExists] = useState<boolean | undefined>(undefined);
    const [input, setInput] = useState<string>("");
    const [location, setLocation] = useState<string>("");
    const [locationName, setLocationName] = useState<string>("");
    const [source, setSource] = useState<string>("");

    useEffect(() => {
        async function fetchObjectFromS3(key: string) {
            try {
                const response = await fetch(`${endpoint}/test/gpu?type=asset&key=${key}`);
                const json = await response.json();
                setAssetSrc(json["presigned_url"]);
            } catch (e) {
                console.error(e);
            }
        };
        // if (pk) {
        //     fetchObjectFromS3(pk);
        // }
        // TODO: fetch s3 obj from the "endpoint", not the "bucket"
    }, [pk]);
    useEffect(() => {
        if (!slug || !s3Key) {
            return;
        }
        const fetchRecords = async (aSlug: string) => {
            const cmd = new QueryCommand({
                TableName: dbTable,
                KeyConditionExpression: "slug = :slug",
                ExpressionAttributeValues: {
                    ":slug": { "S": aSlug }
                },
            });
            const resp = await ddbDocClient.send(cmd);
            const items = resp.Items || [];
            const filePath = s3Key.split("/").slice(1).join("/");
            for (let i = 0; i < items.length; i++) {
                let records = items[i].records?.L || [];
                for (let j = 0; j < records.length; j++) {
                    const digitalinput = getNestedStr(records[j], "digitalinput");
                    const paperinput = getNestedStr(records[j], "paperinput");
                    const location = getNestedStr(records[j], "location");
                    setLocationName(location.split("/")[location.split("/").length - 1]);
                    if (filePath == digitalinput) {
                        setAlttext(getNestedStr(records[j], "alttext"));
                        setAuthor(getNestedStr(records[j], "author"));
                        setCaption(getNestedStr(records[j], "caption"));
                        setExists(getNestedBool(records[j], "digitalexists"));
                        setInput(getNestedStr(records[j], "digitalinput"));
                        setLocation(location);
                        setSource(getNestedStr(records[j], "source"));
                        return;
                    } else if (paperinput != digitalinput && filePath == paperinput) {
                        setAlttext(getNestedStr(records[j], "alttext"));
                        setAuthor(getNestedStr(records[j], "author"));
                        setCaption(getNestedStr(records[j], "caption"));
                        setExists(getNestedBool(records[j], "paperexists"));
                        setInput(getNestedStr(records[j], "paperinput"));
                        setLocation(location);
                        setSource(getNestedStr(records[j], "source"));
                        return;
                    }
                }
            }
            return null;
        };
        fetchRecords(slug);
    }, [slug, pk]);
    const imgSrc = `${bucket}/read/${s3Key}`
    return (
        <>
            <div className="container">
                <h3>{caption}</h3>
                {/* 
                <a className="btn btn-outline-secondary">◀ Previous </a>
                <a className="btn btn-outline-secondary">▶ Next</a>
                */}
                <div className="row align-items-start">
                    <div className="row">
                        <div className="col">
                            {imgSrc && <img src={imgSrc} className="img-fluid float-left"></img>}
                            {/* {assetSrc && <img src={assetSrc} className="img-fluid float-left"></img>} */}
                        </div>
                        <div className="col">
                            <table>
                                <tbody>
                                    {input && <tr><th>File</th><td>{input}</td></tr>}
                                    {location && <tr><th>Location</th><td>{location}</td></tr>}
                                    {alttext && <tr><th>Alt text</th><td>{alttext}</td></tr>}
                                    {author && <tr><th>Author</th><td>{author}</td></tr>}
                                    {exists && <tr><th>Does the file exist?</th><td>{exists}</td></tr>}
                                    {source && <tr><th>Credit line/Copyright information</th><td>{source}</td></tr>}
                                </tbody>
                            </table>
                            <div className="btn-group-vertical">
                                {locationName && <a
                                    href={`https://www.dropbox.com/home/Aplikacje/drpb-upload-alert-test/${slug}?preview=${locationName}`}
                                    target="_blank"
                                    className="btn btn-outline-secondary btn-sm"
                                >Location in a shared folder</a>}
                                {locationName && <a href={`${bucket}/read/${slug}/${getAsHtml(locationName)}`}
                                    target="_blank"
                                    className="btn btn-outline-secondary btn-sm"
                                >See in the digital version</a>}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}
