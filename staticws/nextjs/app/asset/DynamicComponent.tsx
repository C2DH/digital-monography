'use client'

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { DynamoDBClient, GetItemCommand } from "@aws-sdk/client-dynamodb";
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

export default function DynamicTable() {
    const searchParams = useSearchParams();
    const pk = searchParams?.get("pk");
    const bucket = "https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com";
    const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com"

    useEffect(() => {
        async function fetchData() {
            console.error("fetchData");
            try {
                const response = await fetch(`${endpoint}/test/gpu?pk=${pk}`);
                const json = await response.json();
                console.log("JSON", JSON.stringify(json));
            } catch (e) {
                console.error(e);
            }
        };
        fetchData();
    }, [pk]);

    return (
        <>
            <p>hello</p>
            <p>{pk}</p>
            {/* <p>{bucket}/{atob(pk)}</p>
            <p>https://cpy-dgtmon-dev-apkg-upload.s3.eu-west-1.amazonaws.com/guidelines-for-drafting-manuscripts/assets/03_docx_advanced_elements/orange_low_resolution.png</p>
            <img src="https://cpy-dgtmon-dev-apkg-upload.s3.eu-west-1.amazonaws.com/guidelines-for-drafting-manuscripts/assets/03_docx_advanced_elements/orange_low_resolution.png"></img>
            <p>{bucket}/read/{atob(pk)}</p>
            <p>https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com/read/guidelines-for-drafting-manuscripts/assets/03_docx_advanced_elements/orange_low_resolution.png</p>
            // */}
            <img src={`${bucket}/read/${atob(pk || "")}`}></img>
            <p>{`${bucket}/read/${atob(pk || "")}`}</p>
            {/* <p>https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com/read/guidelines-for-drafting-manuscripts/assets/03_docx_advanced_elements/orange_low_resolution.png</p>
            <img src="https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com/read/guidelines-for-drafting-manuscripts/assets/03_docx_advanced_elements/orange_low_resolution.png"></img> */}
        </>
    )
}
