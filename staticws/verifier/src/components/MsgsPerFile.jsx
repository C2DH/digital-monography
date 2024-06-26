import React, { useEffect, useState } from 'react';
// import AWS from "aws-sdk";
import S3 from 'aws-sdk/clients/s3';
// import AWS from 'aws-sdk';
import Msg from "../components/Msg.jsx";

const MsgsPerFile = ({ file }) => {

    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    console.log("file", file);

    useEffect(() => {
        console.log("useEffect");
        const fetchDataForPosts = async () => {
            try {
                const s3 = new S3({
                    accessKeyId: 'your-access-key-id',
                    secretAccessKey: 'your-secret-access-key',
                    region: 'your-region'
                });
                console.log(s3);
                const response = await fetch(
                    `https://jsonplaceholder.typicode.com/posts?_limit=8`
                );
                if (!response.ok) {
                    throw new Error(`HTTP error: Status ${response.status}`);
                }
                let msgsData = await response.json();
                console.log("msgsData", msgsData);
                setData(msgsData);
                setError(null);
            } catch (err) {
                setError(err.message);
                setData(null);
            } finally {
                setLoading(false);
            }
        };

        fetchDataForPosts();


        // const s3 = new AWS.S3({
        //     accessKeyId: 'your-access-key-id',
        //     secretAccessKey: 'your-secret-access-key',
        //     region: 'your-region'
        // });

        // const params = {
        //     Bucket: 'your-bucket-name',
        //     Key: 'your-file-key'
        // };

        // s3.getObject(params, (err, data) => {
        //     if (err) console.log(err, err.stack);
        //     else setWarnings(JSON.parse(data.Body.toString()));
        // });
    }, []);

    return (
        <>
            <p>MsgsPerFile</p>
        </>
    );
};

export default MsgsPerFile;
