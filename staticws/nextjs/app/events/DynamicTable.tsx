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

const StageName = {
    // make sure the values are consistent with src/_common/constants.py
    10: "entrypoint",
    20: "dropbox",
    30: "preparer",
    40: "verifier",
    60: "github",
    70: "builder",
}

const StatusIcons = {
    // make sure the values are consistent with src/_common/audit.py
    0: "⚠️",
    1: "...",
    2: "✅",
}


type IAuditEvent = {
    filename: string,
    msg: string,
    status: number,
    module: number,
    timestamp: Date,
}

export default function DynamicTable() {
    const [tableData, setTableData] = useState<IAuditEvent[]>([]);
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const dbTable = "dgtmon-dev-dyndb-audit-tbl"; // TODO: decouple from specific table

    const fetchRecords = async (pk: string) => {
        try {
            const cmd = new QueryCommand({
                TableName: dbTable,
                KeyConditionExpression: "slug = :slug",
                ExpressionAttributeValues: {
                    ":slug": { "S": pk }
                },
            })
            const resp = await ddbDocClient.send(cmd)
            const records = (resp.Items || []).map((rec) => {
                const timestamp = rec.timestamp.S ? new Date(rec.timestamp.S) : new Date(1970);
                return {
                    filename: rec.filename.S ? rec.filename.S : "",
                    msg: rec.msg.S ? rec.msg.S : "",
                    status: Number(rec.status.N),
                    module: Number(rec.module.N),
                    timestamp: timestamp,
                }
            }).sort((a: IAuditEvent, b: IAuditEvent) => (a.timestamp > b.timestamp ? 1 : -1))
            setTableData(records);
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
                        <th scope="col">Time</th>
                        <th scope="col">File</th>
                        <th scope="col">Message</th>
                        <th scope="col">Stage</th>
                        <th scope="col">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {
                        tableData && tableData.map((val: IAuditEvent, idx: number) => (
                            <tr key={idx}>
                                <td>{val.timestamp.toUTCString()}</td>
                                <td>{val.filename}</td>
                                <td>{val.msg}</td>
                                <td>{StageName[val.module]}</td>
                                <td>{StatusIcons[val.status]}</td>
                            </tr>
                        ))
                    }
                </tbody>
            </table>
        </>
    )
}
