'use client'

import React from 'react';
import {
    ColumnDef,
    ColumnFiltersState,
    SortingState,
} from '@tanstack/react-table';
import { unmarshall } from "@aws-sdk/util-dynamodb";
import { useSearchParams } from 'next/navigation';
import { Table } from './AssetsTable';
import { AssetDetails } from "./AssetDetails";
import { IAsset, ITableRow, IRef, IS3Object } from "./types";
import TnbBookNav from "./../_components/TnbBookNav";

const columns: ColumnDef<ITableRow>[] = [
    {
        id: 'expander',
        header: () => null,
        cell: ({ row }) => {
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
        cell: (info) => info.getValue() ? "✅" : "❌",
        enableColumnFilter: false,
    },
]

/* Convert s3 object size in bytes to a human readable format. */
function formatBytes(bytes: number | undefined, decimals = 2): string {
    if (typeof bytes == "undefined" || !+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

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
// the paths must be consistent with backend
const pathAssetMetadata = "assets";
const pathAssetS3List = "list-assets";
const pathRefMetadata = "refs";

export default function AssetsComponent(): React.JSX.Element {
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
    const [sorting, setSorting] = React.useState<SortingState>([]);
    const [loadingTable, setLoadingTable] = React.useState<boolean>(true);
    const [table, setTable] = React.useState<ITableRow[]>([]);
    const [assetMetadata, setAssetMetadata] = React.useState<IAsset[]>([]);
    const [assetS3List, setAssetS3List] = React.useState<IS3Object[]>([]);
    const [refMetadata, setRefMetadata] = React.useState<IRef[]>([]);
    /* 
    This function:
    1) fetches data from dynamoDb about assets metadata,
    2) fetches data from s3 about objects (s3:ListObjects),
    3) iterates over assets from step 1 and adds "exists" property from s3
       - this data will be used to be displayed on the main table,
    4) updates react state based on 1, 2 and 3.
     */
    const fetchAssetsData = React.useCallback(async (inputSlug: string) => {
        try {
            const [assetsResp, s3objectsResp] = await Promise.all([
                fetch(`${endpoint}/${stage}/${pathAssetMetadata}?slug=${inputSlug}`),
                fetch(`${endpoint}/test/${pathAssetS3List}?slug=${inputSlug}`),
            ]);
            const assetsJson = await assetsResp.json();
            const s3objectsJson = await s3objectsResp.json();
            // assets metadata list
            const assetsItems = assetsJson.Items || [];
            const tempTable: ITableRow[] = [];
            const tempAssetMetadata: IAsset[] = [];
            for (let i = 0; i < assetsItems.length; i++) {
                // unmarshall "records" column and extend the temp array with it
                let assetRecords = Object.values(unmarshall(assetsItems[i].records?.L || []));
                tempAssetMetadata.push(...assetRecords);
            }
            // s3 objects list
            const tempAssetS3List: IS3Object[] = [];
            const tempAssetS3Mapping = {};
            for (let i = 0; i < s3objectsJson.length; i++) {
                tempAssetS3Mapping[s3objectsJson[i].Key] = s3objectsJson[i];
                tempAssetS3List.push({
                    ETag: s3objectsJson[i].ETag,
                    Key: s3objectsJson[i].Key,
                    LastModified: new Date(s3objectsJson[i].LastModified),
                    Size: s3objectsJson[i].Size,
                    SizeAsStr: formatBytes(s3objectsJson[i].Size),
                    StorageClass: s3objectsJson[i].StorageClass,
                });
            }
            // data to display in the table
            for (let j = 0; j < tempAssetMetadata.length; j++) {
                let asset = tempAssetMetadata[j];
                let s3key = `${asset.slug}/${asset.fp}`;
                tempTable.push({
                    pk: asset.pk,
                    fp: getLastPart(asset.fp),
                    location: getLastPart(asset.location || ""),
                    trunc_caption: getTruncatedCaption(asset.caption),
                    alttext: asset.alttext,
                    is_color: asset.is_color,
                    is_on_paper: asset.is_on_paper,
                    is_ready: asset.is_ready,
                    exists: Object.hasOwn(tempAssetS3Mapping, s3key) ? true : false,
                })
            }
            // set react state
            setAssetMetadata(tempAssetMetadata);
            setAssetS3List(tempAssetS3List);
            setTable(tempTable);
            setLoadingTable(false);
        } catch (e) {
            console.error(e);
            setAssetMetadata([]);
            setAssetS3List([]);
            setTable([]);
            setLoadingTable(false);
        }
    }, [])
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
            setRefMetadata([]);
        }
    }, [])
    React.useEffect(() => {
        if (slug) {
            fetchAssetsData(slug);
            fetchRefMetadata(slug);
        }
    }, [fetchAssetsData, fetchRefMetadata, slug]);

    return (
        <>
            {slug && <TnbBookNav slug={slug} color="secondary"></TnbBookNav>}
            {!loadingTable && <Table
                data={table}
                columns={columns}
                additionalData={{ assetMetadata, assetS3List, refMetadata }}
                // getRowCanExpand={() => true}
                renderSubComponent={AssetDetails}
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
