'use client'

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import TnbBookNav from "./../_components/TnbBookNav";
import { API_ENDPOINT, API_STAGE } from "./../constants";

type ICitationItem = {
    pk: string
    loc: string
    id: number
    file_name: string
    citationId: string
    uris: string
    itemData: any
}

type ICitationGroup = {
    pk: string
    loc: string
    file_name: string
    citation_schema: string
    formattedCitation: string
    noteIndex: number
    plainCitation: string
    slug: string
    citation_items: ICitationItem[]
}

export default function DynamicListGroup(): React.JSX.Element {
    const [data, setData] = useState<ICitationGroup[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    useEffect(() => {
        const fetchFromDb = async (aSlug: string) => {
            try {
                const [citationGroups, citationItems] = await Promise.all([
                    fetch(`${API_ENDPOINT}/${API_STAGE}/api/citations/groups/list?slug=${aSlug}`),
                    fetch(`${API_ENDPOINT}/${API_STAGE}/api/citations/items/list?slug=${aSlug}`),
                ]);
                const citationGroupsJson = await citationGroups.json();
                const citationItemsJson = await citationItems.json();
                for (let i = 0; i < citationItemsJson.length; i++) {
                    citationItemsJson[i].itemData = JSON.parse(citationItemsJson[i].itemData);
                    for (let j = 0; j < citationGroupsJson.length; j++) {
                        if (!Object.hasOwn(citationGroupsJson[j], "citation_items")) {
                            citationGroupsJson[j].citation_items = [];
                        }
                        if (citationGroupsJson[j].pk === citationItemsJson[i].citationId) {
                            citationGroupsJson[j].citation_items.push(citationItemsJson[i]);
                        }
                    }
                }
                setData(citationGroupsJson);
                setLoading(false);
            } catch (e) {
                setLoading(false);
                console.error(e);
            }
        }
        if (slug) {
            fetchFromDb(slug);
        }
    }, [slug]);

    return (
        <>
            {slug && <TnbBookNav slug={slug} color="secondary"></TnbBookNav>}
            {!loading && data && <ul className="list-group">
                {data.map((group: ICitationGroup, idx: number) => (
                    <React.Fragment key={idx}>
                        <li className="list-group-item list-group-item-primary" key={idx}>
                            Citation <i>"{group.plainCitation}"</i> in {group.file_name}
                        </li>
                        {group && group.citation_items.map((item: ICitationItem, i: number) => (
                            <li className="list-group-item" key={i}>
                                {item.itemData && Object.entries(item.itemData).map(([key, value]: [string, any]) => {
                                    return <ul key={`${item.citationId}-${key}`}><li><strong>{key}</strong>: {JSON.stringify(value)}</li></ul>
                                })}
                            </li>
                        ))}
                    </React.Fragment>
                ))}
            </ul>}
            {loading && <div className="d-flex justify-content-center">
                <h4>Please wait for the data to load...</h4>
                <div className="spinner-grow text-secondary" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>}
        </>
    )
}
