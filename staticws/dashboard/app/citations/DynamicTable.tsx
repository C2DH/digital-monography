'use client'

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import TnbBookNav from "./../_components/TnbBookNav";

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
    const [loading, setLoading] = useState<boolean>(true);
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const dbTable = "dgtmon-dev-dyndb-citations-tbl";

    const fetchRecords = async (pk: string) => {
        try {
            setLoading(true);
            const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
            const resp = await fetch(`${endpoint}/test/citations?slug=${pk}`);
            const respJson = await resp.json();
            const tableItems: ICitationGroup[] = [];
            for (let i = 0; i < (respJson.Items || []).length; i++) {
                let records = respJson.Items![i].records.L || [];
                for (let j = 0; j < records.length; j++) {
                    tableItems.push({
                        location: getNestedStr(records[j], "file_name"),
                        plainCitation: getNestedStr(records[j], "plainCitation"),
                    })
                }
            }
            setTableData(tableItems);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setLoading(false);
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
                        <th scope="col">Location</th>
                        <th scope="col">Citation</th>
                    </tr>
                </thead>
                <tbody>
                    {
                        tableData.map((val: ICitationGroup, idx: number) => (
                            <tr key={idx}>
                                <td>{val.location}</td>
                                <td>{val.plainCitation}</td>
                            </tr>
                        ))
                    }

                </tbody>
            </table >}
            {loading && <div className="d-flex justify-content-center">
                <h4>Please wait for the items to load...</h4>
                <div className="spinner-grow text-secondary" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>}
        </>
    )
}
