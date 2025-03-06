'use client'

import React from 'react';
import {
    ColumnDef,
    ColumnFiltersState,
    SortingFn,
    SortingState,
} from '@tanstack/react-table';
import { unmarshall } from "@aws-sdk/util-dynamodb";
import { useSearchParams } from 'next/navigation';
import { renderSubComponent, Table } from './AssetsTable';
import { Person, IAsset, IRef, IS3Object } from "./types";
import TnbBookNav from "./../_components/TnbBookNav";

enum MediumEnum {
    PAPER = "P",
    DIGITAL = "D",
    PAPER_AND_DIGITAL = "P+D",
}

const person1: Person = {
    firstName: "Jeff",
    lastName: "Belzebos",
    age: 99,
    visits: 1,
    progress: 3,
    createdAt: new Date(1999, 1, 1),
    status: "cool-guy",
    rank: 1,
}
const person2: Person = {
    firstName: "Bill",
    lastName: "Gates of Hell",
    age: 666,
    visits: 1,
    progress: 3,
    createdAt: new Date(2004, 2, 25),
    status: "cool-guy",
    rank: 1,
}
const person3: Person = {
    firstName: "Larry",
    lastName: "Hellison",
    age: 999,
    visits: 1,
    progress: 3,
    createdAt: new Date(2020, 1, 15),
    status: "db-guy",
    rank: 1,
}

//custom sorting logic for one of our enum columns
const sortStatusFn: SortingFn<Person> = (rowA, rowB, _columnId) => {
    const statusA = rowA.original.status;
    const statusB = rowB.original.status;
    const statusOrder = ['cool-guy', 'db-guy', 'lame-guy'];
    return statusOrder.indexOf(statusA) - statusOrder.indexOf(statusB);
}

const columns: ColumnDef<Person>[] = [
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
        accessorKey: 'firstName',
        cell: info => info.getValue(),
        //this column will sort in ascending order by default since it is a string column
    },
    {
        accessorFn: row => row.lastName,
        id: 'lastName',
        cell: info => info.getValue(),
        header: () => <span>Last Name</span>,
        sortUndefined: 'last', //force undefined values to the end
        sortDescFirst: false, //first sort order will be ascending (nullable values can mess up auto detection of sort order)
    },
    {
        accessorKey: 'age',
        header: () => 'Age',
        //this column will sort in descending order by default since it is a number column
        meta: {
            filterVariant: 'range',
        },
    },
    {
        accessorKey: 'visits',
        header: () => <span>Visits</span>,
        sortUndefined: 'last', //force undefined values to the end
    },
    {
        accessorKey: 'status',
        header: 'Status',
        sortingFn: sortStatusFn, //use our custom sorting function for this enum column
        meta: {
            filterVariant: 'select',
        },
    },
    {
        accessorKey: 'createdAt',
        header: 'Created At',
        enableColumnFilter: false,
        // enableSorting: false
        sortingFn: 'datetime' //make sure table knows this is a datetime column
    },
]

function getLastPart(s: string): string {
    let split = s.split("/");
    return split[split.length - 1];
}

const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
const stage = "test";
// the paths should be consistent with backend
const pathAssetMetadata = "assets";
const pathAssetS3List = "list-assets"; // ListObject req to s3
const pathAssetRetrieve = "asset-retrieve";
const pathRefMetadata = "refs";

export default function AssetsComponent(): React.JSX.Element {
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
    const [sorting, setSorting] = React.useState<SortingState>([]);
    const [data, setData] = React.useState<Person[]>([person1, person2, person3]);
    const [loadingTable, setLoadingTable] = React.useState<boolean>(true);
    const [loadingExistsCol, setLoadingExistsCol] = React.useState<boolean>(true);
    const [assetMetadata, setAssetMetadata] = React.useState<IAsset[]>([]);
    const [assetS3List, setAssetS3List] = React.useState<IS3Object[]>([]);
    const [refMetadata, setRefMetadata] = React.useState<IRef[]>([]);

    const fetchAssetMetadata = React.useCallback(async (inputSlug: string) => {
        setLoadingTable(true);
        try {
            const resp = await fetch(`${endpoint}/${stage}/${pathAssetMetadata}?slug=${inputSlug}`);
            const respJson = await resp.json();
            const items = respJson.Items || [];
            const tempAssetMetadata: IAsset[] = [];
            for (let i = 0; i < items.length; i++) {
                // unmarshall "records" column and extend the temp array with it
                tempAssetMetadata.push(...Object.values(unmarshall(items[i].records?.L || [])));
            }
            setAssetMetadata(tempAssetMetadata);
            setLoadingTable(false);
        } catch (e) {
            console.error(e);
            // setAssetMetadata([]);
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
                data={data}
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
