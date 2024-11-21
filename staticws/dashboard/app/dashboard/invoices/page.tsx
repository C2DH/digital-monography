'use client'

import { useState, useEffect } from 'react'
// import S3 from 'aws-sdk/clients/s3';
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import {
  DynamoDBDocumentClient,
  DeleteCommand,
  ScanCommand,
  paginateScan,
} from "@aws-sdk/lib-dynamodb";

type QuoteData = {
  id: number, quote: string, author: string
};

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

export default function Page() {
  // external Api
  const [data, setData] = useState<QuoteData[]>([]);
  const [isLoading, setLoading] = useState(true);

  useEffect(() => {
    fetch("https://dummyjson.com/quotes/random/3")
      .then((res) => res.json())
      .then((data) => {
        console.log(">>data", data);
        setData(data);
        setLoading(false);
      })
  }, [])

  // DynamoDB Api

  const [dyndbData, setDynDbData] = useState<any>([]);

  const scanTable = async () => {
    try {
      let myData = await ddbDocClient.send(new ScanCommand({ TableName: "dgtmon-dev-dyndb-statuses-tbl" }));
      console.log("myData", myData);
      setDynDbData(myData.Items);
    } catch (err) {
      console.log("Error", err);
    }
  };

  const deleteItem = async (primaryKeyValue: string) => {
    try {
      await ddbDocClient.send(
        new DeleteCommand({
          TableName: "dgtmon-dev-dyndb-statuses-tbl",
          Key: {
            uuid: primaryKeyValue,
          },
        })
      );
      console.log("Success - item deleted");
      scanTable();
    } catch (err) {
      console.log("Error", err);
    }
  };

  useEffect(() => {
    scanTable();
  }, []);

  if (isLoading) return <p>Loading...</p>
  if (!data) return <p>No profile data</p>

  return (<div>
    <h1>Testing page</h1>
    <br />
    <br />
    <b>Data from external API</b>
    {/* {data && <p>{JSON.stringify(data)}</p>} */}
    <ul>
      {data && data.map(({ id, quote, author }: QuoteData) => (
        <li key={id}>* {quote} - {author}</li>
      ))}
    </ul>
    <hr />
    <br />
    <br />
    <b>Data from DynamoDB</b>
    <table className="w-full text-sm  text-gray-500 dark:text-gray-400">
      <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
        <tr>
          <th scope="col" className="text-center py-3">
            First Name
          </th>
          <th scope="col" className="text-center py-3">
            Last Name
          </th>
          <th scope="col" className="text-center py-3">
            City
          </th>
          <th scope="col" className="text-center py-3">
            Quote
          </th>
          <th scope="col" className="text-center py-3">
            Actions
          </th>
        </tr>
      </thead>
      <tbody>
        {dyndbData &&
          dyndbData.map((row: any, idx: number) => (
            <tr key={idx} className="border-b dark:border-gray-700">
              <td className="text-center py-3">{row.first_name}</td>
              <td className="text-center py-3">{row.last_name}</td>
              <td className="text-center py-3">{row.city}</td>
              <td className="text-center py-3">{row.quote}</td>
              <td className="text-center py-3">
                <button
                  id="apple-imac-27-dropdown-button"
                  className="inline-block px-6 py-2.5 bg-red-600 text-white font-medium text-xs leading-tight uppercase rounded shadow-md hover:bg-red-700 hover:shadow-lg focus:bg-red-700 focus:shadow-lg focus:outline-none focus:ring-0 active:bg-red-800 active:shadow-lg transition duration-150 ease-in-out"
                  type="button"
                  onClick={() => deleteItem(row.uuid)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
      </tbody>
    </table>



  </div>);
}

// https://docs.aws.amazon.com/sdk-for-javascript/v3/developer-guide/javascript_dynamodb_code_examples.html

// JS + DynamoDB + Next.js + secrets from env
// https://github.com/sumesh-r/dynamo-nextjs/blob/4e047b03f1e569a74d4704b15a09ba20ad1003e6/src/app/page.js#L4

// TS + DynamoDB + CognitoIdentityPool
// https://github.com/weilueluo/personal-site/blob/8a8635362411e45b406da4de141779e2e1565b65/src/shared/dynamo.ts#L2

// TS + S3 + Next.js + secrets from env
// https://github.com/uudeok/omuk/blob/da282e1dee053615b2202f8e23e11215f803d578/hooks/useS3FileUploader.ts#L4
