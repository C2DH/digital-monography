'use client'

import React from 'react';
import {
    ColumnDef,
    ColumnFiltersState,
    SortingState,
} from '@tanstack/react-table';
import { unmarshall } from "@aws-sdk/util-dynamodb";
import { useSearchParams } from 'next/navigation';
import { renderSubComponent, Table } from './AssetsTable';
import { IAsset, ITableRow, IRef, IS3Object } from "./types";
import TnbBookNav from "./../_components/TnbBookNav";

const columns: ColumnDef<ITableRow>[] = [
    {
        id: 'expander',
        header: () => null,
        cell: ({ row }) => {
            // console.log("expand action");
            // console.log("row.getIsExpanded()", row.getIsExpanded());
            return row.getCanExpand() ? (
                <button
                    {...{
                        onClick: row.getToggleExpandedHandler(),
                        style: { cursor: 'pointer' },
                    }}
                >
                    {row.getIsExpanded() ? '🔽' : '▶️'}
                    {/* {row.getIsExpanded() ? '👇' : '👉'} */}
                </button>
            ) : (
                '🔵'
            )
        },
    },
    {
        accessorKey: 'fp',
        header: () => <span>Name</span>,
    },
    {
        accessorKey: 'location',
        header: () => <span>Location</span>,
        meta: {
            filterVariant: 'select',
        },
    },
    {
        accessorKey: 'trunc_caption',
        header: () => <span>Caption</span>,
        // enableColumnFilter: false,
    },
    {
        accessorKey: 'alttext',
        header: () => <span>Alt text</span>,
        // enableColumnFilter: false,
    },
    {
        accessorKey: 'is_color',
        header: () => <span>Is color?</span>,
        cell: (info) => {
            let val = info.getValue();
            switch (val) {
                case true:
                    return "✅";
                case false:
                    return "❌";
                default:
                    return "❓";
            }
        },
        enableColumnFilter: false,
        // meta: {
        //     filterVariant: 'select',
        // },
    },
    {
        accessorKey: 'is_on_paper',
        header: () => <span>Is on paper?</span>,
        cell: (info) => info.getValue() ? "✅" : "❌",
        enableColumnFilter: false,
    },
    {
        accessorKey: 'is_ready',
        header: () => <span>Is ready?</span>,
        cell: (info) => info.getValue() ? "✅" : "❌",
        enableColumnFilter: false,
    },
    {
        accessorKey: 'exists',
        header: () => <span>Exists?</span>,
        enableColumnFilter: false,
        // header: () => <div className="spinner-border spinner-border-sm" role="status"></div>,
    },
]

function getLastPart(s: string): string {
    let split = s.split("/");
    return split[split.length - 1];
}

function getTruncatedCaption(caption: string): string {
    if (caption && caption.includes(":")) {
        return caption.split(":")[1];
    } else if (!caption) {
        return "❌";
    } else {
        return caption;
    }
}

const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
const stage = "test";
// the paths should be consistent with backend
const pathAssetMetadata = "assets";
const pathAssetS3List = "list-assets";
// const pathAssetRetrieve = "asset-retrieve";
const pathRefMetadata = "refs";

export default function AssetsComponent(): React.JSX.Element {
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
    const [sorting, setSorting] = React.useState<SortingState>([]);
    const [loadingTable, setLoadingTable] = React.useState<boolean>(true);
    const [loadingExistsCol, setLoadingExistsCol] = React.useState<boolean>(true);
    const [table, setTable] = React.useState<ITableRow[]>([]);
    const [assetMetadata, setAssetMetadata] = React.useState<IAsset[]>([]);
    const [assetS3List, setAssetS3List] = React.useState<IS3Object[]>([]);
    const [refMetadata, setRefMetadata] = React.useState<IRef[]>([]);

    const fetchAssetMetadata = React.useCallback(async (inputSlug: string) => {
        setLoadingTable(true);
        try {
            const resp = await fetch(`${endpoint}/${stage}/${pathAssetMetadata}?slug=${inputSlug}`);
            const respJson = await resp.json();
            const items = respJson.Items || [];
            const tempTable: ITableRow[] = [];
            const tempAssetMetadata: IAsset[] = [];
            for (let i = 0; i < items.length; i++) {
                // unmarshall "records" column and extend the temp array with it
                let records = Object.values(unmarshall(items[i].records?.L || []));
                tempAssetMetadata.push(...records);
                for (let j = 0; j < records.length; j++) {
                    tempTable.push({
                        pk: records[j].pk,
                        fp: getLastPart(records[j].fp),
                        location: getLastPart(records[j].location),
                        trunc_caption: getTruncatedCaption(records[j].caption),
                        alttext: records[j].alttext,
                        is_color: records[j].is_color,
                        is_on_paper: records[j].is_on_paper,
                        is_ready: records[j].is_ready,
                        exists: null,
                    })
                }
            }
            setAssetMetadata(tempAssetMetadata);
            setTable(tempTable);
            setLoadingTable(false);
        } catch (e) {
            console.error(e);
            // setAssetMetadata([]);
            // setTable([]);
            setLoadingTable(false);
        }
    }, [slug])
    const fetchAssetS3List = React.useCallback(async (inputSlug: string) => {
        setLoadingExistsCol(true);
        try {
            const response = await fetch(`${endpoint}/test/${pathAssetS3List}?slug=${inputSlug}`);
            const json = await response.json();
            const tempAssetS3List: IS3Object[] = [];
            for (let i = 0; i < json.length; i++) {
                tempAssetS3List.push({
                    ETag: json[i].ETag,
                    Key: json[i].Key,
                    LastModified: new Date(json[i].LastModified),
                    Size: json[i].Size,
                    StorageClass: json[i].StorageClass,
                });
            }
            setAssetS3List(tempAssetS3List);
            setLoadingExistsCol(false);
        } catch (e) {
            console.error(e);
            // setAssetS3List([]);
            setLoadingExistsCol(false);
        }
    }, [slug])
    const fetchRefMetadata = React.useCallback(async (inputSlug: string) => {
        try {
            const resp = await fetch(`${endpoint}/${stage}/${pathRefMetadata}?slug=${inputSlug}`);
            const respJson = await resp.json();
            const items = respJson.Items || [];
            const tempRefMetadata: IRef[] = [];
            for (let i = 0; i < items.length; i++) {
                // unmarshall "records" column and extend the temp array with it
                tempRefMetadata.push(...Object.values(unmarshall(items[i].records?.L || [])));
            }
            setRefMetadata(tempRefMetadata);
        } catch (e) {
            console.error(e);
            // setRefMetadata([]);
        }
    }, [slug])
    React.useEffect(() => {
        if (slug) {
            fetchAssetMetadata(slug);
            fetchAssetS3List(slug);
            fetchRefMetadata(slug);
        }
    }, [fetchAssetMetadata, fetchAssetS3List, fetchRefMetadata, slug]);

    return (
        <>
            {slug && <TnbBookNav slug={slug} color="secondary"></TnbBookNav>}
            {!loadingTable && <Table
                data={table}
                columns={columns}
                // getRowCanExpand={() => true}
                renderSubComponent={renderSubComponent}
                columnFilters={columnFilters}
                setColumnFilters={setColumnFilters}
                sorting={sorting}
                setSorting={setSorting}
            ></Table>}
            {loadingTable && <div className="d-flex justify-content-center">
                <h4>Please wait for the data to load...</h4>
                <div className="spinner-grow text-secondary" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>}
        </>
    )
}
