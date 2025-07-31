'use client'

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import TnbBookNav from "./../_components/TnbBookNav";
import { API_ENDPOINT, API_STAGE } from "./../constants";

function getNestedStr(rec: any, attr: string): string {
    const dataType = "S";
    if (rec && rec.M && Object.hasOwn(rec.M, attr) && Object.hasOwn(rec.M[attr], dataType)) {
        return rec.M[attr][dataType];
    } else {
        return "";
    }
}

type ICitationGroup = {
    pk: string
    file_name: string
    citation_schema: string
    formattedCitation: string
    noteIndex: number
    plainCitation: string
    slug: string
}

export default function DynamicTable() {
    const [tableData, setTableData] = useState<ICitationGroup[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const fetchDbRecords = async (aSlug: string) => {
        try {
            setLoading(true);
            // const resp = await fetch(`${API_ENDPOINT}/${API_STAGE}/citations?slug=${aSlug}`);
            const resp = await fetch(`http://localhost:8001/citations/groups/list?slug=${aSlug}`);
            const tableItems = await resp.json();
            setTableData(tableItems);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setLoading(false);
        }
    };
    useEffect(() => {
        if (slug) {
            fetchDbRecords(slug);
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
                                <td>{val.file_name}</td>
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
