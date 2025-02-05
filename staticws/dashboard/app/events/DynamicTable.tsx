'use client'

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import TnbBookNav from "./../_components/TnbBookNav";

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
    const [loading, setLoading] = useState<boolean>(true);
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const dbTable = "dgtmon-dev-dyndb-audit-tbl";

    const fetchRecords = async (pk: string) => {
        try {
            setLoading(true);
            const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
            const resp = await fetch(`${endpoint}/test/events?slug=${pk}`);
            const respJson = await resp.json();
            const records = (respJson.Items || []).map((rec) => {
                const timestamp = rec.timestamp.S ? new Date(rec.timestamp.S) : new Date(1970);
                return {
                    filename: rec.filename.S ? rec.filename.S : "",
                    msg: rec.msg.S ? rec.msg.S : "",
                    status: Number(rec.status.N),
                    module: Number(rec.module.N),
                    timestamp: timestamp,
                }
            }).sort((a: IAuditEvent, b: IAuditEvent) => (a.timestamp < b.timestamp ? 1 : -1));
            setTableData(records);
            setLoading(false);
        } catch (err) {
            setLoading(false);
            console.error(err);
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
            {!loading && tableData && <table className="table">
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
                        tableData.map((val: IAuditEvent, idx: number) => (
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
            </table>}
            {loading && <div className="d-flex justify-content-center">
                <h4>Please wait for the items to load...</h4>
                <div className="spinner-grow text-secondary" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>}
        </>
    )
}
