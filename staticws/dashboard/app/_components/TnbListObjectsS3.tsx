'use client'

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import TnbBookNav from "./TnbBookNav";
import { endpoint, getGitBranch } from "./../constants";

function getLastPart(s: string): string {
    let split = s.split("/");
    return split[split.length - 1];
}

type IS3Object = {
    keyEncoded: string,
    key: string,
    lastModified: string,
    size: number | undefined,
}

export default function DynamicComponent({ backendPath, targetPath }: { backendPath: string, targetPath: string }) {
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const stage = getGitBranch();
    // const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
    const [tableData, setTableData] = useState<IS3Object[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    useEffect(() => {
        async function fetchData(inputSlug: string) {
            setLoading(true);
            try {
                const response = await fetch(`${endpoint}/${stage}/${backendPath}?slug=${inputSlug}`);
                const json = await response.json();
                const tempTableData: IS3Object[] = [];
                for (let i = 0; i < json.length; i++) {
                    tempTableData.push({
                        keyEncoded: btoa(json[i].Key) || "",
                        key: getLastPart(json[i].Key || ""),
                        lastModified: new Date(json[i].LastModified).toString() || "",
                        size: json[i].Size || undefined,
                    });
                }
                setTableData(tempTableData);
                setLoading(false);
            } catch (e) {
                console.error(e);
                setLoading(false);
            }
        };
        if (slug) {
            fetchData(slug);
        }
    }, [slug, backendPath]);
    return (
        <>
            <div className="container">
                {slug && <TnbBookNav slug={slug} color="secondary"></TnbBookNav>}
                {tableData.length > 0 && <table className="table">
                    <thead>
                        <tr>
                            <th scope="col">Link</th>
                            <th scope="col">File Name</th>
                            <th scope="col">Last Modified</th>
                            <th scope="col">Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        {
                            tableData.map((val: IS3Object, idx: number) => (
                                <tr key={idx}>
                                    <td>
                                        <Link href={{
                                            pathname: targetPath,
                                            query: { key: val.keyEncoded },
                                        }} className="btn btn-outline-secondary btn-sm" role="button">
                                            ▶
                                        </Link>
                                    </td>
                                    <td>{val.key}</td>
                                    <td>{val.lastModified}</td>
                                    <td>{val.size}</td>
                                </tr>
                            ))
                        }
                    </tbody>
                </table >}
                {!loading && tableData.length == 0 && <div className="d-flex justify-content-center">
                    <h4>No files found. Please remember that files are
                        generated <strong>after</strong> you change a file in
                        your working directory.</h4>
                </div>}
                {loading && <div className="d-flex justify-content-center">
                    <h4>Please wait for the items to load...</h4>
                    <div className="spinner-grow text-secondary" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                </div>}
            </div>
        </>
    )
}
