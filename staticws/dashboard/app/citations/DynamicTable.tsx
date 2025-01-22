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

type ICitationGroup = {
    location: string,
    plainCitation: string,
}

export default function DynamicTable() {
    const [tableData, setTableData] = useState<ICitationGroup[]>([]);
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const dbTable = "dgtmon-dev-dyndb-citations-tbl";

    const fetchRecords = async (pk: string) => {
        try {
            const cmd = new QueryCommand({
                TableName: dbTable,
                KeyConditionExpression: "slug = :slug",
                ExpressionAttributeValues: {
                    ":slug": { "S": pk }
                },
            });
            const resp = await ddbDocClient.send(cmd);
            const tableItems: ICitationGroup[] = [];
            for (let i = 0; i < (resp.Items || []).length; i++) {
                let records = resp.Items![i].records.L || [];
                for (let j = 0; j < records.length; j++) {
                    tableItems.push({
                        location: getNestedStr(records[j], "file_name"),
                        plainCitation: getNestedStr(records[j], "plainCitation"),
                    })
                }
            }
            setTableData(tableItems);
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
                        <th scope="col">Location</th>
                        <th scope="col">Citation</th>
                    </tr>
                </thead>
                <tbody>
                    {
                        tableData && tableData.map((val: ICitationGroup, idx: number) => (
                            <tr key={idx}>
                                <td>{val.location}</td>
                                <td>{val.plainCitation}</td>
                            </tr>
                        ))
                    }

                </tbody>
            </table >
        </>
    )
}
