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

type IAssetRecord = {
    name: string,
    alttext: string,
    caption: string,
    location: string,
    licensename: string,
    isColor?: boolean,
    isOnPaper: boolean,
    isReady: boolean,
}

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
        console.log("to boolean", rec.M[attr][dataType]);
        return (rec.M[attr][dataType]);
    } else {
        return undefined;
    }
}

function getEmoticonForBool(val: boolean | undefined): string {
    switch (val) {
        case true:
            return "✅";
        case false:
            return "❌";
        case undefined:
            return "❓";
        default:
            return "❓";
    }
}

export default function DynamicTable() {
    const [tableData, setTableData] = useState<IAssetRecord[]>([]);
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const dbTable = "dgtmon-dev-dyndb-assets-tbl";

    const fetchRecords = async (pk: string) => {
        try {
            const cmd = new QueryCommand({
                TableName: dbTable,
                KeyConditionExpression: "slug = :slug",
                ExpressionAttributeValues: {
                    ":slug": { "S": pk }
                },
            });
            const formatedData: IAssetRecord[] = [];
            const resp = await ddbDocClient.send(cmd);
            const items = resp.Items || [];
            for (let i = 0; i < items.length; i++) {
                let records = items[i].records?.L || [];
                for (let j = 0; j < records.length; j++) {
                    console.log('records[j]', records[j]);
                    const digitalinput = getNestedStr(records[j], "digitalinput");
                    const paperinput = getNestedStr(records[j], "paperinput");
                    const alttext = getNestedStr(records[j], "alttext");
                    const caption = getNestedStr(records[j], "caption");
                    const location = getNestedStr(records[j], "location");
                    const licensename = getNestedStr(records[j], "licensename");
                    const isColor = getNestedBool(records[j], "iscolor");
                    const isReady = getNestedBool(records[j], "isready") || false;
                    const isOnPaper = paperinput != "" ? true : false;
                    if (digitalinput != paperinput && paperinput != "") {
                        formatedData.push({
                            name: paperinput,
                            alttext: alttext,
                            caption: caption,
                            location: location,
                            licensename: licensename,
                            isColor: isColor,
                            isOnPaper: isOnPaper,
                            isReady: isReady,
                        });
                    }
                    formatedData.push({
                        name: digitalinput,
                        alttext: alttext,
                        caption: caption,
                        location: location,
                        licensename: licensename,
                        isColor: isColor,
                        isOnPaper: isOnPaper,
                        isReady: isReady,
                    });
                }
            }
            setTableData(formatedData);
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
            <table className="table">
                <thead>
                    <tr>
                        <th scope="col">Name</th>
                        <th scope="col">Location</th>
                        <th scope="col">Alt text</th>
                        <th scope="col">Caption</th>
                        <th scope="col">License</th>
                        <th scope="col">Is color?</th>
                        <th scope="col">Is on paper?</th>
                        <th scope="col">Is ready?</th>
                    </tr>
                </thead>
                <tbody>
                    {
                        tableData && tableData.map((val: IAssetRecord, idx: number) => (
                            <tr key={idx}>
                                <td>{val.name}</td>
                                <td>{val.location}</td>
                                <td>{val.alttext}</td>
                                <td>{val.caption}</td>
                                <td>{val.licensename}</td>
                                <td>{getEmoticonForBool(val.isColor)}</td>
                                <td>{getEmoticonForBool(val.isOnPaper)}</td>
                                <td>{getEmoticonForBool(val.isReady)}</td>
                            </tr>
                        ))
                    }
                </tbody>
            </table>
        </>
    )
}
